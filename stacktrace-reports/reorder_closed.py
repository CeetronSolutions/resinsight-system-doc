"""Reorder a stacktrace report so any stack whose linked OPM issue is
CLOSED moves to the bottom under a `## Closed issues` header. Stacks
that are open or unmatched stay at the top in their original order.
Stack numbers are preserved so previously-published anchors remain valid.

Idempotent: running the script again on an already-reorganized report is
a no-op other than rewriting the file.

Usage:
    python reorder_closed.py reports/YYYY-MM-DD.md
"""

import re
import sys
from pathlib import Path

STACK_HDR_RE = re.compile(r"^## Stack #(\d+) — count (\d+)\s*$")
OPM_LINE_RE = re.compile(r"^\*\*OPM issue:\*\*\s*(.*)$")


def is_closed(body_lines):
    for line in body_lines:
        m = OPM_LINE_RE.match(line)
        if not m:
            continue
        return "CLOSED" in m.group(1)
    return False


def main(report_path):
    lines = Path(report_path).read_text(encoding="utf-8").splitlines()

    first_idx = next((i for i, l in enumerate(lines) if STACK_HDR_RE.match(l)), None)
    if first_idx is None:
        return

    header = lines[:first_idx]

    bodies = []
    i = first_idx
    while i < len(lines):
        if not STACK_HDR_RE.match(lines[i]):
            i += 1
            continue
        start = i
        j = i + 1
        while j < len(lines) and not lines[j].startswith("## "):
            j += 1
        bodies.append(lines[start:j])
        i = j

    open_group = [b for b in bodies if not is_closed(b)]
    closed_group = [b for b in bodies if is_closed(b)]

    out = list(header)
    for body in open_group:
        out.extend(body)
    if closed_group:
        out.append("## Closed issues")
        out.append("")
        for body in closed_group:
            out.extend(body)

    while out and out[-1] == "":
        out.pop()
    Path(report_path).write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"open_or_unmatched={len(open_group)} closed={len(closed_group)}")


if __name__ == "__main__":
    main(sys.argv[1])
