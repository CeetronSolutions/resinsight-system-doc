"""process_week.py - One-shot driver for a freshly-arrived weekly crash CSV.

Replaces the seven manual steps in README.md with a single command. Given a CSV
dropped into `csv/`, it:

  1. folds the CSV into `registry.json`            (registry.py update)
  2. links/refreshes OPM issues for every signature (link_issues.py)
  3. regenerates the week's report + index pages    (registry.py render)
  4. prints the investigation worklist - unlinked   (registry.py worklist)
     signatures ranked by total occurrence count

After it finishes, hand the worklist to the `crash-triage` workflow in the
ResInsight repo to investigate the top unlinked signatures (step 3 of the
overall process). Nothing here posts to GitHub.

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
    ap.add_argument("--no-link", action="store_true", help="skip the GitHub issue-linking step")
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

    print("\n=== Investigation worklist (unlinked signatures by impact) ===")
    run("registry.py", "worklist")

    print(
        "\nNext: investigate the top unlinked signatures with the `crash-triage` "
        "workflow in the ResInsight repo, then commit the CSV, registry.json, the "
        "regenerated report and the two index pages together."
    )


if __name__ == "__main__":
    main()
