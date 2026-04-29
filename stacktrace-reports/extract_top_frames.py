"""Helper for the weekly stacktrace workflow: extract the top non-handler
ResInsight-specific frame for each stack in a generated report and group
stacks that share a signature, so we can run one `gh search issues` per
unique signature instead of one per stack."""

import re
import sys
from collections import defaultdict
from pathlib import Path

HANDLER_RE = re.compile(r"^\[\d+\]\s+(performCrashLogging|manageSegFailure)")
FRAME_RE = re.compile(r"^\[\d+\]\s+(\S.*?)(?:\(.*)?\s+at\s+(\S+):(\d+)$")
STACK_HDR_RE = re.compile(r"^## Stack #(\d+) — count (\d+)\s*$")


def first_meaningful_frame(lines):
    for line in lines:
        if HANDLER_RE.match(line):
            continue
        m = FRAME_RE.match(line)
        if not m:
            continue
        sym, path, lineno = m.groups()
        sym = sym.split("(", 1)[0].strip()
        if sym in ("main", "__libc_start_main"):
            continue
        if "RiaGuiApplication::notify" in sym:
            continue
        return sym, path
    return None


def main(report_path):
    text = Path(report_path).read_text(encoding="utf-8")
    lines = text.splitlines()

    stacks = []
    cur = None
    in_block = False
    for line in lines:
        m = STACK_HDR_RE.match(line)
        if m:
            if cur:
                stacks.append(cur)
            cur = {"num": int(m.group(1)), "count": int(m.group(2)), "frames": []}
            in_block = False
            continue
        if cur is None:
            continue
        if line.strip() == "```":
            in_block = not in_block
            continue
        if in_block:
            cur["frames"].append(line)
    if cur:
        stacks.append(cur)

    grouped = defaultdict(list)
    for s in stacks:
        sig = first_meaningful_frame(s["frames"])
        key = sig if sig else ("__none__", "")
        grouped[key].append((s["num"], s["count"]))

    rows = sorted(
        grouped.items(),
        key=lambda kv: (-sum(c for _, c in kv[1]), kv[0]),
    )
    for (sym, path), members in rows:
        total = sum(c for _, c in members)
        nums = ",".join(f"#{n}({c})" for n, c in members)
        print(f"{total:4d}  {sym}  ({path})  -> {nums}")


if __name__ == "__main__":
    main(sys.argv[1])
