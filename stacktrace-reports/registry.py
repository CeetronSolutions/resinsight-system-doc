"""registry.py - Persistent state for the ResInsight crash-triage pipeline.

The registry (`registry.json`) is the single source of truth for every unique
crash signature ever seen. Each weekly CSV is folded into it with `update`, and
the per-week reports plus the two index pages are regenerated from it with
`render`. Cross-week knowledge - the linked OPM issue, its open/closed state, a
proposed fix PR, an investigation note - lives on the signature and therefore
survives from week to week without being re-derived from prior Markdown.

Signature identity
------------------
A signature is keyed by the *normalised symbol* of its top-N non-handler
ResInsight frames: arguments, template parameters, `[abi:cxx11]` tags and the
`at <path>:<line>` suffix are all stripped, so the key is stable across builds
and releases (raw `file:line` numbers drift; symbols do not). Frames that carry
no crash-site information (`main`, `__libc_start_main`,
`RiaGuiApplication::notify`) are dropped before taking the top N, so stacks that
only differ in the deeper UI dispatch path merge into one entry.

The closely-related upstream libraries opm-common (`Opm::`) and libecl (`ecl_`)
are *shown* in the rendered call stack - they often hold the real crash site -
but are excluded from the signature, so signature identity stays keyed on
ResInsight's own frames and is unaffected by upstream symbol changes.

Subcommands
-----------
    update      Fold a weekly CSV into registry.json.
    render      Regenerate reports/<date>.md (one or all weeks) + the indexes.
    worklist    Print unlinked signatures ranked by total occurrence count.

Usage
-----
    python registry.py update --csv csv/2026-06-05-query_data.csv
    python registry.py render --date 2026-06-05
    python registry.py render --all
    python registry.py worklist
"""

import argparse
import hashlib
import json
import re
from datetime import date as date_cls
from pathlib import Path

from analyze_crashes import (
    DEFAULT_MIN_VERSION,
    DEFAULT_SIGNATURE_DEPTH,
    detect_columns,
    extract_shown_frames,
    filter_by_version,
    is_handler_frame,
    is_resinsight_frame,
    parse_csv,
)

HERE = Path(__file__).resolve().parent
REGISTRY_PATH = HERE / "registry.json"
REPORTS_DIR = HERE / "reports"
CSV_DIR = HERE / "csv"
INDEX_PATH = HERE / "index.md"
INCOMING_PATH = HERE / "incoming-csvs.md"

OPM_ISSUES_URL = "https://github.com/OPM/ResInsight/issues"

# Frames that carry no crash-site information: dropped before taking the top-N
# symbols that make up the signature. `main`/`__libc_start_main` are the process
# entry; `RiaGuiApplication::notify` is the Qt event-dispatch trampoline that
# appears in almost every GUI crash.
NOISE_SYMBOLS = ("main", "__libc_start_main", "RiaGuiApplication::notify")

UNSYMBOLIZED = "(unsymbolized crash site)"

_FRAME_RE = re.compile(r"^\s*\[\d+\]\s*(.*)$")


def frame_symbol(line: str) -> str:
    """Normalised symbol for a stack line.

    `[10] Foo::bar(int) const at path/x.cpp:12` -> `Foo::bar`. Strips the frame
    index, the trailing ` at <path>:<line>`, the argument list, and `[abi:cxx11]`
    tags. Template parameters in `<...>` are kept (they distinguish overloads and
    contain no line-number drift).
    """
    m = _FRAME_RE.match(line)
    body = m.group(1) if m else line.strip()
    if " at " in body:
        body = body.rsplit(" at ", 1)[0]
    sym = body.split("(", 1)[0]
    sym = sym.replace("[abi:cxx11]", "")
    return sym.strip()


def signature_symbols(shown_lines: list[str], depth: int) -> list[str]:
    """Top `depth` informative (non-handler, non-noise) symbols of a stack.

    opm/ecl frames are shown in the call stack but skipped here, so the
    signature stays keyed on ResInsight's own frames and signature identity is
    unaffected by the closely-related upstream libraries.
    """
    syms: list[str] = []
    for line in shown_lines:
        if is_handler_frame(line):
            continue
        if not is_resinsight_frame(line):
            continue
        sym = frame_symbol(line)
        if not sym or sym in NOISE_SYMBOLS:
            continue
        syms.append(sym)
        if len(syms) >= depth:
            break
    return syms


def signature_id_for(symbols: list[str]) -> str:
    key = "\n".join(symbols) if symbols else UNSYMBOLIZED
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def top_frame_for(symbols: list[str]) -> str:
    return symbols[0] if symbols else UNSYMBOLIZED


# --------------------------------------------------------------------------- #
# Registry I/O                                                                 #
# --------------------------------------------------------------------------- #
def load_registry() -> dict:
    if REGISTRY_PATH.exists():
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return {"signatures": {}}


def save_registry(reg: dict) -> None:
    # Sorted keys + trailing newline keep git diffs small and stable.
    REGISTRY_PATH.write_text(
        json.dumps(reg, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def date_from_csv_name(csv_path: Path) -> str:
    """`2026-06-05-query_data.csv` -> `2026-06-05`."""
    m = re.match(r"(\d{4}-\d{2}-\d{2})", csv_path.stem)
    if not m:
        raise ValueError(f"cannot derive date from CSV name: {csv_path.name}")
    return m.group(1)


# --------------------------------------------------------------------------- #
# update                                                                       #
# --------------------------------------------------------------------------- #
def cmd_update(args: argparse.Namespace) -> None:
    csv_path = Path(args.csv)
    if not csv_path.exists():
        raise SystemExit(f"Error: CSV not found: {csv_path}")
    week = args.date or date_from_csv_name(csv_path)

    rows = parse_csv(str(csv_path))
    stack_col, ts_col, ver_col = detect_columns(rows)
    skipped = 0
    if args.min_version:
        rows, skipped = filter_by_version(rows, ver_col, args.min_version)

    reg = load_registry()
    sigs = reg["signatures"]

    # Re-folding a week must be idempotent: drop this week's previous
    # contribution from every signature first (issue/PR/notes state is kept).
    for entry in sigs.values():
        entry["weeks"].pop(week, None)

    total = 0
    new_count = 0
    # Per-fold guard so representative_stack is refreshed from the *first* row of
    # each signature in this week (deterministic), not whichever row comes last.
    first_week_row: dict[str, bool] = {}
    for row in rows:
        raw = row.get(stack_col, "")
        ts = (row.get(ts_col, "") or "").strip()
        ver = (row.get(ver_col, "") or "").strip() if ver_col else ""
        lines = [l.strip() for l in raw.strip().splitlines() if l.strip()]
        shown_lines = extract_shown_frames(lines)
        symbols = signature_symbols(shown_lines, args.signature_depth)
        sid = signature_id_for(symbols)
        total += 1

        entry = sigs.get(sid)
        if entry is None:
            entry = {
                "signature_id": sid,
                "top_frame": top_frame_for(symbols),
                "signature_frames": symbols,
                "representative_stack": shown_lines,
                "weeks": {},
                "opm_issue": None,
                "pr": None,
                "status": "new",
                "notes": "",
            }
            sigs[sid] = entry
            new_count += 1
        elif first_week_row.get(sid) is None:
            # Refresh the displayed stack from the first row of this signature in
            # the week being folded, so signatures first seen before opm/ecl
            # frames were retained pick them up. Identity (sid) is unchanged.
            entry["representative_stack"] = shown_lines
        first_week_row[sid] = True

        wk = entry["weeks"].get(week)
        if wk is None:
            wk = {"count": 0, "first_seen": ts, "last_seen": ts, "versions": {}}
            entry["weeks"][week] = wk
        wk["count"] += 1
        # Per-week occurrence count by reporting APPversion.
        if ver:
            versions = wk.setdefault("versions", {})
            versions[ver] = versions.get(ver, 0) + 1
        # ISO-8601 UTC strings sort chronologically.
        if ts and (not wk["first_seen"] or ts < wk["first_seen"]):
            wk["first_seen"] = ts
        if ts and ts > wk["last_seen"]:
            wk["last_seen"] = ts

        entry["last_updated"] = _today()

    # Record per-week roll-up totals for the index pages.
    reg.setdefault("weeks", {})[week] = {
        "csv": csv_path.name,
        "total_rows": total,
        "unique_stacks": sum(1 for e in sigs.values() if week in e["weeks"]),
        "skipped_old_version": skipped,
    }

    save_registry(reg)
    print(
        f"week={week} total_rows={total} new_signatures={new_count} "
        f"unique_this_week={reg['weeks'][week]['unique_stacks']} skipped_old={skipped}"
    )


def _today() -> str:
    return date_cls.today().isoformat()


# --------------------------------------------------------------------------- #
# derived helpers                                                              #
# --------------------------------------------------------------------------- #
def total_count(entry: dict) -> int:
    return sum(w["count"] for w in entry["weeks"].values())


def global_first_seen(entry: dict) -> str:
    return min((w["first_seen"] for w in entry["weeks"].values() if w["first_seen"]), default="")


def global_last_seen(entry: dict) -> str:
    return max((w["last_seen"] for w in entry["weeks"].values() if w["last_seen"]), default="")


def issue_is_closed(entry: dict) -> bool:
    iss = entry.get("opm_issue")
    return bool(iss and iss.get("state") == "CLOSED")


def opm_issue_line(entry: dict) -> str:
    iss = entry.get("opm_issue")
    if not iss:
        return "**OPM issue:** none found"
    n = iss["number"]
    return f"**OPM issue:** [#{n}]({OPM_ISSUES_URL}/{n}) — {iss['state']}"


# --------------------------------------------------------------------------- #
# render                                                                       #
# --------------------------------------------------------------------------- #
def render_week(reg: dict, week: str) -> str:
    sigs = reg["signatures"]
    members = [e for e in sigs.values() if week in e["weeks"]]
    members.sort(key=lambda e: -e["weeks"][week]["count"])

    meta = reg.get("weeks", {}).get(week, {})
    csv_name = meta.get("csv", f"{week}-query_data.csv")
    total = meta.get("total_rows", sum(e["weeks"][week]["count"] for e in members))
    skipped = meta.get("skipped_old_version", 0)

    out: list[str] = []
    out.append("---")
    out.append(f"title: Stacktrace report {week}")
    out.append(f"permalink: /stacktrace-reports/reports/{week}/")
    out.append("layout: wide")
    out.append("---")
    out.append("")
    out.append(f"# Stacktrace report {week}")
    out.append("")
    out.append(f"- **Source CSV:** [{csv_name}](../csv/{csv_name})")
    out.append(f"- **Total crash reports:** {total}")
    out.append(f"- **Unique call stacks:** {len(members)}")
    if skipped:
        out.append(f"- **Rows skipped (old version):** {skipped}")
    out.append("")

    # Number every stack first (1..n by this week's count), then partition into
    # open/unmatched (top) and closed (bottom), preserving the numbers - this
    # mirrors the old analyze + reorder_closed behaviour, gaps included.
    numbered = list(enumerate(members, 1))
    open_blocks: list[str] = []
    closed_blocks: list[str] = []
    for num, entry in numbered:
        block = _stack_block(entry, num, entry["weeks"][week])
        (closed_blocks if issue_is_closed(entry) else open_blocks).extend(block)

    out.extend(open_blocks)
    if closed_blocks:
        out.append("## Closed issues")
        out.append("")
        out.extend(closed_blocks)

    while out and out[-1] == "":
        out.pop()
    return "\n".join(out) + "\n"


def _stack_block(entry: dict, num: int, wk: dict) -> list[str]:
    block = [f"## Stack #{num} — count {wk['count']}", ""]
    block.append(f"First seen: `{wk['first_seen']}`  ")
    versions = wk.get("versions") or {}
    # Trailing two spaces = Markdown hard break when a Versions line follows.
    block.append(f"Last seen: `{wk['last_seen']}`" + ("  " if versions else ""))
    if versions:
        # Most-affected version first, then version string for ties.
        parts = ", ".join(
            f"`{v}` ({c})"
            for v, c in sorted(versions.items(), key=lambda kv: (-kv[1], kv[0]))
        )
        block.append(f"Versions: {parts}")
    block.append("")
    block.append("```")
    block.extend(entry["representative_stack"])
    block.append("```")
    block.append("")
    block.append(f"**Status:** {entry.get('status', 'new')}")
    block.append("")
    block.append(opm_issue_line(entry))
    notes = (entry.get("notes") or "").strip()
    if notes:
        block.append("")
        block.append(f"**Notes:** {notes}")
    block.append("")
    return block


def render_indexes(reg: dict) -> None:
    weeks = reg.get("weeks", {})
    ordered = sorted(weeks.keys(), reverse=True)

    # index.md
    idx = [
        "---",
        "title: Weekly Stacktrace Reports",
        "permalink: /stacktrace-reports/index/",
        "layout: wide",
        "---",
        "",
        "# Weekly Stacktrace Reports",
        "",
        "Per-week deduplicated stacktrace analyses, newest first. Each report lists "
        "unique ResInsight call stacks with occurrence counts and a link to the "
        f"matching issue on [OPM/ResInsight]({OPM_ISSUES_URL}) when one is known.",
        "",
        "| Week       | Report                                | Total rows | Unique stacks |",
        "|------------|---------------------------------------|-----------:|--------------:|",
    ]
    for w in ordered:
        m = weeks[w]
        idx.append(
            f"| {w} | [{w}](./reports/{w}.md) | "
            f"{m['total_rows']:>10} | {m['unique_stacks']:>13} |"
        )
    INDEX_PATH.write_text("\n".join(idx) + "\n", encoding="utf-8")

    # incoming-csvs.md
    inc = [
        "---",
        "title: Incoming CSVs",
        "permalink: /stacktrace-reports/incoming-csvs/",
        "layout: default",
        "---",
        "",
        "# Incoming CSVs",
        "",
        "Every raw weekly crash-report CSV received from the telemetry pipeline. "
        "Each row links to the committed CSV and to the per-week stacktrace report "
        "generated from it.",
        "",
        "| Date       | CSV                                                   "
        "| Total rows | Unique stacks | Report                                |",
        "|------------|-------------------------------------------------------"
        "|-----------:|--------------:|---------------------------------------|",
    ]
    for w in sorted(weeks.keys()):
        m = weeks[w]
        csv_name = m["csv"]
        inc.append(
            f"| {w} | [{csv_name}](./csv/{csv_name}) | "
            f"{m['total_rows']:>10} | {m['unique_stacks']:>13} | "
            f"[{w}](./reports/{w}.md) |"
        )
    INCOMING_PATH.write_text("\n".join(inc) + "\n", encoding="utf-8")


def cmd_render(args: argparse.Namespace) -> None:
    reg = load_registry()
    weeks = reg.get("weeks", {})
    if args.all:
        targets = sorted(weeks.keys())
    elif args.date:
        targets = [args.date]
    else:
        targets = [max(weeks.keys())] if weeks else []

    REPORTS_DIR.mkdir(exist_ok=True)
    for w in targets:
        text = render_week(reg, w)
        (REPORTS_DIR / f"{w}.md").write_text(text, encoding="utf-8")
        print(f"rendered reports/{w}.md")

    render_indexes(reg)
    print("rendered index.md and incoming-csvs.md")


# --------------------------------------------------------------------------- #
# worklist                                                                     #
# --------------------------------------------------------------------------- #
def cmd_worklist(args: argparse.Namespace) -> None:
    reg = load_registry()
    rows = []
    for e in reg["signatures"].values():
        if e.get("opm_issue"):
            continue
        if e["top_frame"] == UNSYMBOLIZED:
            # No ResInsight symbol at the fault: not individually actionable.
            continue
        if e["status"] in ("no-fix-found",) and not args.all:
            continue
        rows.append(e)
    rows.sort(key=lambda e: -total_count(e))
    for e in rows:
        print(
            f"{total_count(e):4d}  {e['signature_id']}  [{e['status']}]  {e['top_frame']}"
        )
    if not rows:
        print("(no unlinked signatures)")


# --------------------------------------------------------------------------- #
# set                                                                          #
# --------------------------------------------------------------------------- #
VALID_STATUS = (
    "new", "linked", "investigating", "patch-proposed",
    "pr-open", "resolved", "no-fix-found", "on-hold",
)


def cmd_set(args: argparse.Namespace) -> None:
    """Record investigation outcome for a signature (used by crash-triage)."""
    reg = load_registry()
    entry = reg["signatures"].get(args.id)
    if entry is None:
        raise SystemExit(f"Error: unknown signature_id: {args.id}")

    if args.issue is not None:
        entry["opm_issue"] = {
            "number": args.issue,
            "state": args.state or "OPEN",
            "url": f"{OPM_ISSUES_URL}/{args.issue}",
        }
    if args.pr is not None:
        entry["pr"] = {
            "number": args.pr,
            "branch": args.branch or "",
            "url": f"https://github.com/{args.pr_repo}/pull/{args.pr}",
        }
    if args.status:
        if args.status not in VALID_STATUS:
            raise SystemExit(f"Error: status must be one of {VALID_STATUS}")
        entry["status"] = args.status
    if args.note is not None:
        entry["notes"] = args.note
    entry["last_updated"] = _today()

    save_registry(reg)
    print(f"updated {args.id}: status={entry['status']} "
          f"issue={entry.get('opm_issue')} pr={entry.get('pr')}")


# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    up = sub.add_parser("update", help="fold a weekly CSV into registry.json")
    up.add_argument("--csv", required=True, help="path to the weekly CSV")
    up.add_argument("--date", help="week date YYYY-MM-DD (default: from CSV name)")
    up.add_argument("--signature-depth", type=int, default=DEFAULT_SIGNATURE_DEPTH)
    up.add_argument("--min-version", default=DEFAULT_MIN_VERSION,
                    help="drop rows older than VER (empty string disables)")
    up.set_defaults(func=cmd_update)

    rd = sub.add_parser("render", help="regenerate report(s) + indexes from registry")
    g = rd.add_mutually_exclusive_group()
    g.add_argument("--date", help="render this week only")
    g.add_argument("--all", action="store_true", help="render every week")
    rd.set_defaults(func=cmd_render)

    wl = sub.add_parser("worklist", help="unlinked signatures by impact")
    wl.add_argument("--all", action="store_true", help="include no-fix-found signatures")
    wl.set_defaults(func=cmd_worklist)

    st = sub.add_parser("set", help="record investigation outcome for a signature")
    st.add_argument("--id", required=True, help="signature_id")
    st.add_argument("--issue", type=int, help="linked OPM issue number")
    st.add_argument("--state", choices=("OPEN", "CLOSED"), help="issue state")
    st.add_argument("--pr", type=int, help="fix PR number")
    st.add_argument("--branch", help="fix PR branch name")
    st.add_argument("--pr-repo", default="OPM/ResInsight", help="repo the PR targets")
    st.add_argument("--status", help=f"one of {VALID_STATUS}")
    st.add_argument("--note", help="investigation note (for uncertain/no-fix cases)")
    st.set_defaults(func=cmd_set)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
