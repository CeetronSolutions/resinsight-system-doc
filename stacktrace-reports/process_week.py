"""process_week.py - One-shot driver for a freshly-arrived weekly crash CSV.

Replaces the seven manual steps in README.md with a single command. Given a CSV
dropped into `csv/`, it:

  1. folds the CSV into `registry.json`            (registry.py update)
  2. links issues and refreshes issue/fix-PR state  (link_issues.py)
     for every signature
  3. regenerates the week's report + index pages    (registry.py render)
  4. prints the investigation worklist - signatures (registry.py worklist)
     with no issue and no fix PR, those still
     crashing the newest released version first

After it finishes, hand the worklist to the `crash-triage` workflow in the
ResInsight repo to investigate the top untriaged signatures (step 3 of the
overall process). That workflow files no issue: the crash stack goes into the
batch fix PR, which is written back onto the signature with `registry.py set
--pr`. Nothing here posts to GitHub.

Usage:
    python process_week.py csv/2026-06-12-query_data.csv
    python process_week.py csv/2026-06-12-query_data.csv --no-link   # skip gh calls
"""

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = sys.executable


def run(script: str, *script_args: str) -> None:
    cmd = [PY, str(HERE / script), *script_args]
    print(f"\n$ {' '.join(cmd[1:])}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise SystemExit(f"{script} failed with exit code {result.returncode}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", help="path to the weekly CSV (also copy it into csv/ before committing)")
    ap.add_argument("--no-link", action="store_true",
                    help="skip the GitHub issue-linking / state-refresh step")
    ap.add_argument("--date", help="override the week date (default: from CSV name)")
    args = ap.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        raise SystemExit(f"Error: CSV not found: {csv_path}")

    update_args = ["update", "--csv", str(csv_path)]
    if args.date:
        update_args += ["--date", args.date]
    run("registry.py", *update_args)

    if not args.no_link:
        run("link_issues.py")

    render_args = ["render"]
    if args.date:
        render_args += ["--date", args.date]
    run("registry.py", *render_args)

    print("\n=== Investigation worklist (untriaged signatures, latest version first) ===")
    run("registry.py", "worklist")

    print(
        "\nNext: investigate the worklist top-down with the `crash-triage` workflow "
        "in the ResInsight repo - the `cur` column is what the current release is "
        "still crashing on, so take those first. It opens one batch fix PR carrying "
        "the crash stacks (no issue is filed) and records it with `registry.py set "
        "--pr`. Then commit the CSV, registry.json, the regenerated report and the "
        "two index pages together."
    )


if __name__ == "__main__":
    main()
