"""Helper for the weekly stacktrace workflow: apply freshly-found OPM issue
links to a report, batch-style. Same matching logic as `apply_known_issues.py`
but the mapping comes from CLI `--link` flags rather than from prior reports.

Use this after step 4 of the workflow when you have run several
`gh search issues` calls and want to record the results in one pass instead
of editing each `**OPM issue:** none found` line by hand.

Usage:
    python apply_new_links.py reports/YYYY-MM-DD.md \\
        --link "RimX::foo=13937:CLOSED" \\
        --link "RimY::bar=13938:OPEN"

Each `--link` argument is `TOP_FRAME=ISSUE:STATE`, where `TOP_FRAME` matches
the symbol printed by `unmatched_top_frames.py` (return-type + scope::name,
template parameters included — copy/paste the exact string from that
output). Existing links are left alone; only `none found` lines are filled.
"""

import argparse
import sys
from pathlib import Path

from apply_known_issues import OPM_LINE_RE, first_meaningful_frame, iter_stacks


def parse_link(arg: str) -> tuple[str, tuple[str, str]]:
    sym, _, payload = arg.rpartition("=")
    if not sym or ":" not in payload:
        raise argparse.ArgumentTypeError(
            f"--link must be SYMBOL=ISSUE:STATE, got {arg!r}"
        )
    issue, state = payload.split(":", 1)
    state = state.upper()
    if state not in ("OPEN", "CLOSED"):
        raise argparse.ArgumentTypeError(f"state must be OPEN or CLOSED, got {state!r}")
    if not issue.isdigit():
        raise argparse.ArgumentTypeError(f"issue must be numeric, got {issue!r}")
    return sym, (issue, state)


def apply(report_path: str, mapping: dict[str, tuple[str, str]]) -> None:
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


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("report")
    ap.add_argument(
        "--link",
        action="append",
        type=parse_link,
        required=True,
        help='Repeatable. Format: "SYMBOL=ISSUE:STATE", e.g. "RimX::foo=13937:CLOSED"',
    )
    args = ap.parse_args()
    mapping = dict(args.link)
    apply(args.report, mapping)


if __name__ == "__main__":
    main()
