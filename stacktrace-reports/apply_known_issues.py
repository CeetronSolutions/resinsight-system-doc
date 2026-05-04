"""Helper for the weekly stacktrace workflow: copy known top-frame -> OPM
issue links from prior reports into the current report. Saves a GitHub
search for any top frame whose link was already established in an earlier
week. Only fills `**OPM issue:** none found` lines; existing links are
left alone.

Usage:
    python apply_known_issues.py reports/YYYY-MM-DD.md \\
        --prior reports/PRIOR1.md [--prior reports/PRIOR2.md ...]
"""

import argparse
import re
from pathlib import Path

HANDLER_RE = re.compile(r"^\[\d+\]\s+(performCrashLogging|manageSegFailure)")
FRAME_RE = re.compile(r"^\[\d+\]\s+(\S.*?)(?:\(.*)?\s+at\s+(\S+):(\d+)$")
STACK_HDR_RE = re.compile(r"^## Stack #(\d+) — count (\d+)\s*$")
OPM_LINE_RE = re.compile(r"^\*\*OPM issue:\*\*\s*(.*)$")
ISSUE_LINK_RE = re.compile(r"#(\d+)")
STATE_RE = re.compile(r"(OPEN|CLOSED)")


def first_meaningful_frame(frames):
    for line in frames:
        if HANDLER_RE.match(line):
            continue
        m = FRAME_RE.match(line)
        if not m:
            continue
        sym = m.group(1).split("(", 1)[0].strip()
        if sym in ("main", "__libc_start_main"):
            continue
        if "RiaGuiApplication::notify" in sym:
            continue
        return sym
    return None


def iter_stacks(lines):
    """Yield (start, end, frames) for each `## Stack #N — count M` block.
    end is exclusive and stops at the next `## ` header of any kind."""
    i = 0
    while i < len(lines):
        if not STACK_HDR_RE.match(lines[i]):
            i += 1
            continue
        start = i
        j = i + 1
        while j < len(lines) and not lines[j].startswith("## "):
            j += 1
        frames = []
        in_block = False
        for line in lines[start:j]:
            if line.strip() == "```":
                in_block = not in_block
                continue
            if in_block:
                frames.append(line)
        yield start, j, frames
        i = j


def build_mapping(prior_paths):
    mapping = {}
    for p in prior_paths:
        lines = Path(p).read_text(encoding="utf-8").splitlines()
        for start, end, frames in iter_stacks(lines):
            top = first_meaningful_frame(frames)
            if not top:
                continue
            for k in range(start, end):
                m = OPM_LINE_RE.match(lines[k])
                if not m:
                    continue
                content = m.group(1).strip()
                if "none found" in content:
                    break
                im = ISSUE_LINK_RE.search(content)
                sm = STATE_RE.search(content)
                if im and sm:
                    mapping[top] = (im.group(1), sm.group(1))
                break
    return mapping


def apply(report_path, mapping):
    lines = Path(report_path).read_text(encoding="utf-8").splitlines()
    updated = 0
    skipped_already_linked = 0
    no_match = 0

    for start, end, frames in iter_stacks(lines):
        top = first_meaningful_frame(frames)
        opm_idx = None
        for k in range(start, end):
            if OPM_LINE_RE.match(lines[k]):
                opm_idx = k
                break
        if opm_idx is None:
            continue
        existing = OPM_LINE_RE.match(lines[opm_idx]).group(1).strip()
        if "none found" not in existing:
            skipped_already_linked += 1
            continue
        if top is None or top not in mapping:
            no_match += 1
            continue
        issue, state = mapping[top]
        lines[opm_idx] = (
            f"**OPM issue:** [#{issue}](https://github.com/OPM/ResInsight/issues/{issue}) — {state}"
        )
        updated += 1

    Path(report_path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        f"updated={updated} already_linked={skipped_already_linked} "
        f"no_match={no_match} mapping_size={len(mapping)}"
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("report")
    ap.add_argument("--prior", action="append", required=True, help="prior report path (repeatable)")
    args = ap.parse_args()
    mapping = build_mapping(args.prior)
    apply(args.report, mapping)


if __name__ == "__main__":
    main()
