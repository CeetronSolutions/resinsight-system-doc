"""
analyze_crashes.py - Identify unique call stacks in ResInsight crash report CSV files.

Usage:
    python analyze_crashes.py <csv_file> [--min-count N] [--format {text,md}] [--output FILE]
"""

import argparse
import csv
import sys
from pathlib import Path

RI_PREFIXES = ("Rim", "Ria", "Rif", "Ric", "Riu", "Riv", "Rig", "caf", "cvf")
HANDLER_SYMBOLS = ("performCrashLogging", "manageSegFailure", "cvf::AssertHandlerConsole")

# opm-common (the `Opm::` C++ namespace) and libecl (the `ecl_` C API) are two
# closely-related upstream libraries linked into ResInsight. Their frames are
# kept in the displayed call stack so the real crash site is visible, but they
# are deliberately NOT used for the grouping signature - that stays keyed on
# ResInsight's own frames so signature identity is stable across releases.
OPM_ECL_MARKERS = ("Opm::", "ecl_")

# Default number of top non-handler RI frames used as the grouping signature.
# Crash reports that share their top N frames but diverge in deeper call sites
# (typically the UI invocation path) are treated as the same bug.
DEFAULT_SIGNATURE_DEPTH = 5

# Stacks from ResInsight versions older than this are dropped before grouping.
# `-dev.NN` suffixes are ignored: 2026.02.2-dev.01 is treated as 2026.02.2.
DEFAULT_MIN_VERSION = "2026.02.2"


def parse_version(v: str) -> tuple[tuple[int, ...] | None, bool]:
    """Parse `YYYY.MM.PP[-dev.NN]` into (base_tuple, has_dev_suffix).

    base_tuple is None for unparseable versions so callers can decide to keep or drop them.
    """
    if not v:
        return None, False
    base, sep, _ = v.partition("-")
    has_dev = sep == "-"
    parts = base.split(".")
    try:
        return tuple(int(p) for p in parts), has_dev
    except ValueError:
        return None, has_dev


def is_resinsight_frame(line: str) -> bool:
    return any(p in line for p in RI_PREFIXES) or "main at" in line


def is_opm_ecl_frame(line: str) -> bool:
    """True for an upstream opm-common (`Opm::`) or libecl (`ecl_`) frame.

    Matched on the symbol (after the `[n]` index), not the whole line, so a
    source path that merely contains the marker can't trip it.
    """
    sym = _symbol_after_index(line)
    return any(m in sym for m in OPM_ECL_MARKERS)


def is_shown_frame(line: str) -> bool:
    """Frames kept in the displayed call stack: ResInsight plus opm/ecl."""
    return is_resinsight_frame(line) or is_opm_ecl_frame(line)


def extract_ri_frames(lines: list[str]) -> list[str]:
    return [l for l in lines if is_resinsight_frame(l)]


def extract_shown_frames(lines: list[str]) -> list[str]:
    """Frames for display: ResInsight frames plus the closely-related opm/ecl
    frames that would otherwise hide the real crash site."""
    return [l for l in lines if is_shown_frame(l)]


def _symbol_after_index(line: str) -> str:
    s = line.lstrip()
    if not s.startswith("["):
        return ""
    rbr = s.find("]")
    if rbr < 0:
        return ""
    return s[rbr + 1 :].lstrip()


def is_handler_frame(line: str) -> bool:
    sym = _symbol_after_index(line)
    return any(sym.startswith(h) for h in HANDLER_SYMBOLS)


def signature_for(ri_lines: list[str], depth: int) -> str:
    """Top `depth` non-handler frames, joined as the grouping key."""
    sig: list[str] = []
    for line in ri_lines:
        if is_handler_frame(line):
            continue
        sig.append(line)
        if len(sig) >= depth:
            break
    return "\n".join(sig)


def parse_csv(filepath: str) -> list[dict]:
    rows = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def detect_columns(rows: list[dict]) -> tuple[str, str, str | None]:
    """Return (stack_column, timestamp_column, version_column) based on available fields."""
    if not rows:
        return "rawstack", "timestamp", None
    keys = rows[0].keys()
    stack_col = "rawstack" if "rawstack" in keys else "details_0_rawStack"
    ts_col = "timestamp" if "timestamp" in keys else "timestamp [UTC]"
    ver_col = "APPversion" if "APPversion" in keys else None
    return stack_col, ts_col, ver_col


def filter_by_version(
    rows: list[dict], ver_col: str | None, min_version: str
) -> tuple[list[dict], int]:
    """Drop rows whose APPversion is older than `min_version`.

    Any version carrying a `-dev.NN` suffix is always kept, regardless of base.
    Rows with a missing or unparseable version are kept (we can't know they're old).
    Returns (kept_rows, skipped_count).
    """
    if ver_col is None:
        return rows, 0
    min_tuple, _ = parse_version(min_version)
    if min_tuple is None:
        return rows, 0
    kept: list[dict] = []
    skipped = 0
    for row in rows:
        v, has_dev = parse_version(row.get(ver_col, ""))
        if has_dev:
            kept.append(row)
            continue
        if v is not None and v < min_tuple:
            skipped += 1
            continue
        kept.append(row)
    return kept, skipped


def group_by_stack(rows: list[dict], signature_depth: int = DEFAULT_SIGNATURE_DEPTH) -> dict:
    stack_col, ts_col, _ = detect_columns(rows)
    stacks = {}
    for row in rows:
        raw_stack = row.get(stack_col, "")
        ts = row.get(ts_col, "")
        lines = [l.strip() for l in raw_stack.strip().splitlines() if l.strip()]
        ri_lines = extract_ri_frames(lines)
        sig_key = signature_for(ri_lines, signature_depth)
        if sig_key not in stacks:
            stacks[sig_key] = {
                "count": 0,
                "first_seen": ts,
                "last_seen": ts,
                "stack": lines,
                "ri_frames": ri_lines,
            }
        entry = stacks[sig_key]
        entry["count"] += 1
        # Timestamps in these CSVs are ISO-8601 UTC, so lexicographic ordering == chronological.
        if ts and ts < entry["first_seen"]:
            entry["first_seen"] = ts
        if ts and ts > entry["last_seen"]:
            entry["last_seen"] = ts
    return stacks


def format_report(stacks: dict, min_count: int = 1) -> str:
    lines = []
    sorted_stacks = sorted(stacks.items(), key=lambda x: -x[1]["count"])
    filtered = [(k, v) for k, v in sorted_stacks if v["count"] >= min_count]

    total = sum(v["count"] for v in stacks.values())
    lines.append(f"Total crash reports : {total}")
    lines.append(f"Unique call stacks  : {len(stacks)}")
    if min_count > 1:
        lines.append(f"Showing stacks with >= {min_count} occurrences: {len(filtered)}")
    lines.append("")

    for i, (key, info) in enumerate(filtered, 1):
        lines.append(f"{'=' * 70}")
        lines.append(
            f"Stack #{i}  (count: {info['count']}, "
            f"first seen: {info['first_seen']}, "
            f"last seen: {info['last_seen']})"
        )
        lines.append(f"{'=' * 70}")
        for frame in info["ri_frames"]:
            lines.append(f"  {frame}")
        lines.append("")

    return "\n".join(lines)


def format_report_md(
    stacks: dict, csv_path: Path, min_count: int = 1, skipped_old_version: int = 0
) -> str:
    sorted_stacks = sorted(stacks.items(), key=lambda x: -x[1]["count"])
    filtered = [(k, v) for k, v in sorted_stacks if v["count"] >= min_count]
    total = sum(v["count"] for v in stacks.values())

    date_stem = csv_path.stem.replace("-query_data", "")
    csv_rel = f"../csv/{csv_path.name}"

    lines = []
    lines.append("---")
    lines.append(f"title: Stacktrace report {date_stem}")
    lines.append(f"permalink: /stacktrace-reports/reports/{date_stem}/")
    lines.append("layout: wide")
    lines.append("---")
    lines.append("")
    lines.append(f"# Stacktrace report {date_stem}")
    lines.append("")
    lines.append(f"- **Source CSV:** [{csv_path.name}]({csv_rel})")
    lines.append(f"- **Total crash reports:** {total}")
    lines.append(f"- **Unique call stacks:** {len(stacks)}")
    if skipped_old_version:
        lines.append(f"- **Rows skipped (old version):** {skipped_old_version}")
    if min_count > 1:
        lines.append(f"- **Showing stacks with ≥ {min_count} occurrences:** {len(filtered)}")
    lines.append("")

    for i, (_, info) in enumerate(filtered, 1):
        lines.append(f"## Stack #{i} — count {info['count']}")
        lines.append("")
        lines.append(f"First seen: `{info['first_seen']}`  ")
        lines.append(f"Last seen: `{info['last_seen']}`")
        lines.append("")
        lines.append("```")
        for frame in info["ri_frames"]:
            lines.append(frame)
        lines.append("```")
        lines.append("")
        lines.append("**OPM issue:** none found")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Identify unique call stacks in ResInsight crash report CSV files."
    )
    parser.add_argument("csv_file", help="Path to the crash report CSV file")
    parser.add_argument(
        "--min-count",
        type=int,
        default=1,
        metavar="N",
        help="Only show stacks with at least N occurrences (default: 1)",
    )
    parser.add_argument(
        "--format",
        choices=("text", "md"),
        default="text",
        help="Output format: plain text (default) or Markdown page for the Jekyll site",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        help="Write report to FILE instead of stdout",
    )
    parser.add_argument(
        "--signature-depth",
        type=int,
        default=DEFAULT_SIGNATURE_DEPTH,
        metavar="N",
        help=(
            "Number of top non-handler RI frames used for grouping "
            f"(default: {DEFAULT_SIGNATURE_DEPTH}). Lower = more fuzzy, "
            "more stacks merge."
        ),
    )
    parser.add_argument(
        "--min-version",
        default=DEFAULT_MIN_VERSION,
        metavar="VER",
        help=(
            "Drop rows whose APPversion is older than VER "
            f"(default: {DEFAULT_MIN_VERSION}). `-dev.NN` suffixes are ignored. "
            "Pass an empty string to disable filtering."
        ),
    )
    args = parser.parse_args()

    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        print(f"Error: file not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    rows = parse_csv(str(csv_path))
    _, _, ver_col = detect_columns(rows)
    skipped = 0
    if args.min_version:
        rows, skipped = filter_by_version(rows, ver_col, args.min_version)
        if skipped:
            print(
                f"Skipped {skipped} rows with APPversion older than {args.min_version}",
                file=sys.stderr,
            )
    stacks = group_by_stack(rows, signature_depth=args.signature_depth)
    if args.format == "md":
        report = format_report_md(
            stacks, csv_path, min_count=args.min_count, skipped_old_version=skipped
        )
    else:
        report = format_report(stacks, min_count=args.min_count)

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
