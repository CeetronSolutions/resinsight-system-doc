"""Helper for the weekly stacktrace workflow: list the top non-handler frame
of every stack still marked `**OPM issue:** none found`, grouped by signature
and sorted by total occurrence count (highest impact first).

Run this after `apply_known_issues.py` to see which signatures still need a
fresh `gh search issues` call. The output mirrors `extract_top_frames.py` but
filters out stacks that are already linked.
"""

import re
import sys
from collections import defaultdict
from pathlib import Path

from apply_known_issues import OPM_LINE_RE, first_meaningful_frame, iter_stacks

STACK_HDR_RE = re.compile(r"^## Stack #(\d+) — count (\d+)\s*$")


def main(report_path: str) -> None:
    lines = Path(report_path).read_text(encoding="utf-8").splitlines()
    groups: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for start, end, frames in iter_stacks(lines):
        m = STACK_HDR_RE.match(lines[start])
        if not m:
            continue
        num, cnt = int(m.group(1)), int(m.group(2))
        opm = ""
        for k in range(start, end):
            mm = OPM_LINE_RE.match(lines[k])
            if mm:
                opm = mm.group(1).strip()
                break
        if "none found" not in opm:
            continue
        top = first_meaningful_frame(frames) or "__none__"
        groups[top].append((num, cnt))

    rows = sorted(groups.items(), key=lambda kv: (-sum(c for _, c in kv[1]), kv[0]))
    for sym, members in rows:
        total = sum(c for _, c in members)
        nums = ",".join(f"#{n}({c})" for n, c in members)
        print(f"{total:4d}  {sym}  -> {nums}")


if __name__ == "__main__":
    main(sys.argv[1])
