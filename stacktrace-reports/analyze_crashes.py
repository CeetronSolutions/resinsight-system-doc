"""
analyze_crashes.py - Identify unique call stacks in ResInsight crash report CSV files.

Usage:
    python analyze_crashes.py <csv_file> [--min-count N] [--output FILE]
"""

import argparse
import csv
import sys
from pathlib import Path

RI_PREFIXES = ("Rim", "Ria", "Rif", "Ric", "Riu", "Riv", "Rig")


def is_resinsight_frame(line: str) -> bool:
    return any(p in line for p in RI_PREFIXES) or "main at" in line


def extract_ri_frames(lines: list[str]) -> list[str]:
    return [l for l in lines if is_resinsight_frame(l)]


def parse_csv(filepath: str) -> list[dict]:
    rows = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def detect_columns(rows: list[dict]) -> tuple[str, str]:
    """Return (stack_column, timestamp_column) based on available fields."""
    if not rows:
        return "rawstack", "timestamp"
    keys = rows[0].keys()
    stack_col = "rawstack" if "rawstack" in keys else "details_0_rawStack"
    ts_col = "timestamp" if "timestamp" in keys else "timestamp [UTC]"
    return stack_col, ts_col


def group_by_stack(rows: list[dict]) -> dict:
    stack_col, ts_col = detect_columns(rows)
    stacks = {}
    for row in rows:
        raw_stack = row.get(stack_col, "")
        lines = [l.strip() for l in raw_stack.strip().splitlines() if l.strip()]
        ri_lines = extract_ri_frames(lines)
        sig_key = "\n".join(ri_lines)
        if sig_key not in stacks:
            stacks[sig_key] = {
                "count": 0,
                "first_seen": row.get(ts_col, ""),
                "stack": lines,
                "ri_frames": ri_lines,
            }
        stacks[sig_key]["count"] += 1
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
        lines.append(f"Stack #{i}  (count: {info['count']}, first seen: {info['first_seen']})")
        lines.append(f"{'=' * 70}")
        for frame in info["ri_frames"]:
            lines.append(f"  {frame}")
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
        "--output",
        metavar="FILE",
        help="Write report to FILE instead of stdout",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        print(f"Error: file not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    rows = parse_csv(str(csv_path))
    stacks = group_by_stack(rows)
    report = format_report(stacks, min_count=args.min_count)

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
