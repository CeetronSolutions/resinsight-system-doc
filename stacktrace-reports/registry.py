"""registry.py - Persistent state for the ResInsight crash-triage pipeline.

The registry (`registry.json`) is the single source of truth for every unique
crash signature ever seen. Each weekly CSV is folded into it with `update`, and
the per-week reports plus the two index pages are regenerated from it with
`render`. Cross-week knowledge - the reference that carries the crash (an OPM
issue, a fix PR, or both), its open/closed state, an investigation note - lives
on the signature and therefore survives from week to week without being
re-derived from prior Markdown.

A signature is *referenced* once it carries either an OPM issue or a fix PR.
Crash triage no longer files issues: the call stack goes straight into the fix
PR body, so a PR alone is a complete reference and takes a signature off the
worklist. Older signatures still carry an issue (and sometimes both).

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
    worklist    Print unreferenced signatures, latest-version crashes first.
    set         Record an investigation outcome (issue, fix PR, status, note).

Usage
-----
    python registry.py update --csv csv/2026-06-05-query_data.csv
    python registry.py render --date 2026-06-05
    python registry.py render --all
    python registry.py worklist
    python registry.py set --id 024f64fb61b2 --pr 14473 --branch crash-triage-2026-08-06 \
                           --status pr-open
    python registry.py set --id 024f64fb61b2 --pr-state MERGED --status resolved
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
    parse_version,
)

HERE = Path(__file__).resolve().parent
REGISTRY_PATH = HERE / "registry.json"
REPORTS_DIR = HERE / "reports"
CSV_DIR = HERE / "csv"
INDEX_PATH = HERE / "index.md"
INCOMING_PATH = HERE / "incoming-csvs.md"

OPM_ISSUES_URL = "https://github.com/OPM/ResInsight/issues"
OPM_PULLS_URL = "https://github.com/OPM/ResInsight/pull"

# Statuses that mean "already handled": such a signature must never come back on
# the worklist, whether or not it carries an issue or a PR.
HANDLED_STATUS = ("investigating", "patch-proposed", "pr-open", "resolved",
                  "no-fix-found", "on-hold")

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


def entry_versions(entry: dict) -> dict[str, int]:
    """All-weeks occurrence count per reporting APPversion for one signature."""
    totals: dict[str, int] = {}
    for wk in entry["weeks"].values():
        for ver, count in (wk.get("versions") or {}).items():
            totals[ver] = totals.get(ver, 0) + count
    return totals


def latest_release_version(reg: dict) -> tuple[tuple[int, ...] | None, str]:
    """Newest *released* APPversion seen anywhere in the registry.

    Pre-release builds (`-dev.NN`, `-RC_N`) are ignored when picking the line:
    a single developer's `2026.06.2-dev.01` report must not become the yardstick
    everything else is ranked against. Crashes *on* those newer pre-release
    builds still count towards the line, since their base sorts at or above it.

    Returns (base_tuple, version_string); (None, "") when the registry carries
    no parseable release version (weeks folded before APPversion was exported).
    """
    best: tuple[int, ...] | None = None
    best_str = ""
    for entry in reg["signatures"].values():
        for ver in entry_versions(entry):
            base, has_dev = parse_version(ver)
            if base is None or has_dev:
                continue
            if best is None or base > best:
                best, best_str = base, ver
    return best, best_str


def count_from_version(entry: dict, min_base: tuple[int, ...] | None) -> int:
    """Occurrences reported by builds at or newer than `min_base`.

    Comparison is on the parsed base only, so `2026.06.1`, `2026.06.1-dev.02`
    and `2026.06.2-dev.01` all count towards a `2026.06.1` line. Unparseable
    versions are excluded - they cannot be shown to be current.
    """
    if min_base is None:
        return 0
    total = 0
    for ver, count in entry_versions(entry).items():
        base, _ = parse_version(ver)
        if base is not None and base >= min_base:
            total += count
    return total


def issue_is_closed(entry: dict) -> bool:
    iss = entry.get("opm_issue")
    return bool(iss and iss.get("state") == "CLOSED")


def pr_is_merged(entry: dict) -> bool:
    pr = entry.get("pr")
    return bool(pr and pr.get("state") == "MERGED")


def has_reference(entry: dict) -> bool:
    """The crash is recorded somewhere upstream - an issue, a fix PR, or both."""
    return bool(entry.get("opm_issue") or entry.get("pr"))


def is_closed_out(entry: dict) -> bool:
    """Nothing further is expected on this signature.

    Either the linked issue is closed, or the PR carrying the fix (and the crash
    stack, when no issue was filed) has merged, or triage settled it explicitly.
    Closed-out stacks are gathered at the bottom of the weekly report.
    """
    return (
        entry.get("status") in ("resolved", "no-fix-found")
        or issue_is_closed(entry)
        or pr_is_merged(entry)
    )


def opm_issue_line(entry: dict) -> str:
    iss = entry.get("opm_issue")
    if not iss:
        return ""
    n = iss["number"]
    return f"**OPM issue:** [#{n}]({OPM_ISSUES_URL}/{n}) — {iss['state']}"


def fix_pr_line(entry: dict) -> str:
    """Rendered link for the fix PR, which also carries the crash stack when no
    issue was filed for the signature."""
    pr = entry.get("pr")
    if not pr:
        return ""
    n = pr["number"]
    url = pr.get("url") or f"{OPM_PULLS_URL}/{n}"
    state = pr.get("state")
    line = f"**Fix PR:** [#{n}]({url})"
    return f"{line} — {state}" if state else line


def reference_lines(entry: dict) -> list[str]:
    """The issue/PR lines shown under a stack, in that order.

    A signature triaged after crash reports moved into PRs has only the PR line;
    older ones have only the issue line; both appear when both are known.
    """
    lines = [ln for ln in (opm_issue_line(entry), fix_pr_line(entry)) if ln]
    if not lines:
        return ["**Reference:** none — not triaged yet"]
    # Trailing two spaces = Markdown hard break, so issue and PR stay on
    # separate lines instead of being reflowed into one paragraph.
    return [ln + "  " for ln in lines[:-1]] + [lines[-1]]


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
    # open/unmatched (top) and closed-out (bottom), preserving the numbers - this
    # mirrors the old analyze + reorder_closed behaviour, gaps included.
    numbered = list(enumerate(members, 1))
    open_blocks: list[str] = []
    closed_blocks: list[str] = []
    for num, entry in numbered:
        block = _stack_block(entry, num, entry["weeks"][week])
        (closed_blocks if is_closed_out(entry) else open_blocks).extend(block)

    out.extend(open_blocks)
    if closed_blocks:
        out.append("## Closed issues and merged fixes")
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
    block.extend(reference_lines(entry))
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
        f"work covering them on [OPM/ResInsight]({OPM_ISSUES_URL}) when it is known "
        "— the fix PR carrying the crash stack, or an older linked issue.",
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
        if e["top_frame"] == UNSYMBOLIZED:
            # No ResInsight symbol at the fault: not individually actionable.
            continue
        if args.all:
            rows.append(e)
            continue
        # Already referenced upstream - by an issue, or (since crash stacks moved
        # into PR bodies) by a fix PR on its own. Either way it is accounted for.
        if has_reference(e):
            continue
        # A signature can be in flight before it has a PR number; status alone
        # keeps it off the list so a batch under investigation is not re-picked.
        if e["status"] in HANDLED_STATUS:
            continue
        rows.append(e)

    # Triage order is "still crashing the current release first". Ranking on the
    # all-time total instead would put bugs whose volume comes from a superseded
    # version - often already fixed - above ones users hit today.
    if args.from_version:
        min_base, min_label = parse_version(args.from_version)[0], args.from_version
        if min_base is None:
            raise SystemExit(f"Error: cannot parse --from-version: {args.from_version}")
    else:
        min_base, min_label = latest_release_version(reg)

    if min_base is None:
        print("(no APPversion data in registry - ranking by total count)")
    else:
        print(f"Ranked by occurrences on {min_label} or newer, then by total count.")
    print(f"{'cur':>4}  {'all':>4}  signature     status            top frame")

    rows.sort(key=lambda e: (-count_from_version(e, min_base), -total_count(e)))
    for e in rows:
        ref = ""
        if args.all:
            iss = e.get("opm_issue")
            pr = e.get("pr")
            parts = []
            if iss:
                parts.append(f"issue #{iss['number']}")
            if pr:
                parts.append(f"PR #{pr['number']}")
            ref = f"  ({', '.join(parts)})" if parts else ""
        print(
            f"{count_from_version(e, min_base):4d}  {total_count(e):4d}  "
            f"{e['signature_id']}  [{e['status']}]  {e['top_frame']}{ref}"
        )
    if not rows:
        print("(no untriaged signatures)")


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
        prev = entry.get("pr") or {}
        entry["pr"] = {
            "number": args.pr,
            "branch": args.branch or (prev.get("branch", "") if prev.get("number") == args.pr else ""),
            "url": f"https://github.com/{args.pr_repo}/pull/{args.pr}",
            "state": args.pr_state or (prev.get("state") if prev.get("number") == args.pr else None) or "OPEN",
        }
    elif args.pr_state:
        if not entry.get("pr"):
            raise SystemExit(f"Error: {args.id} has no PR to set --pr-state on")
        entry["pr"]["state"] = args.pr_state
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

    wl = sub.add_parser("worklist", help="untriaged signatures, latest version first")
    wl.add_argument("--all", action="store_true",
                    help="include signatures already referenced by an issue or a "
                         "fix PR, and those already handled")
    wl.add_argument("--from-version", metavar="VER",
                    help="count VER and newer as current "
                         "(default: newest released APPversion in the registry)")
    wl.set_defaults(func=cmd_worklist)

    st = sub.add_parser("set", help="record investigation outcome for a signature")
    st.add_argument("--id", required=True, help="signature_id")
    st.add_argument("--issue", type=int, help="linked OPM issue number")
    st.add_argument("--state", choices=("OPEN", "CLOSED"), help="issue state")
    st.add_argument("--pr", type=int, help="fix PR number (carries the crash stack)")
    st.add_argument("--pr-state", choices=("OPEN", "MERGED", "CLOSED"),
                    help="fix PR state (default OPEN when --pr is given)")
    st.add_argument("--branch", help="fix PR branch name")
    st.add_argument("--pr-repo", default="OPM/ResInsight", help="repo the PR targets")
    st.add_argument("--status", help=f"one of {VALID_STATUS}")
    st.add_argument("--note", help="investigation note (for uncertain/no-fix cases)")
    st.set_defaults(func=cmd_set)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
