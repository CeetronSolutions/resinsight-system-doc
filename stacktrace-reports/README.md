---
title: Stacktrace Reports
permalink: /stacktrace-reports/
layout: default
---

# Stacktrace Reports

Weekly ResInsight crash telemetry, deduplicated by call-stack signature and cross-linked to upstream issues on [OPM/ResInsight](https://github.com/OPM/ResInsight/issues).

## Contents

- [Incoming CSVs](./incoming-csvs.md) — every raw CSV received, with row counts and a link to its weekly report.
- [Weekly reports](./index.md) — list of per-week analyses, newest first.
- [Analyzer](./analyze_crashes.py) — the Python script that groups raw stack traces into unique signatures.
- [Analyzer usage](./analyzer-README.md) — full command-line reference for the script.
- [Top-frame grouper](./extract_top_frames.py) — reads a generated report and groups stacks by their first non-handler frame, so each unique signature only needs one OPM issue search.
- [Apply known issues](./apply_known_issues.py) — copies top-frame → OPM issue links from one or more prior reports into the current report, so stacks already linked in earlier weeks don't need a fresh GitHub search.
- [Unmatched top frames](./unmatched_top_frames.py) — lists the top frames of stacks still marked `**OPM issue:** none found`, grouped and sorted by total occurrence count, so the next round of GitHub searches can be prioritized by impact.
- [Apply new links](./apply_new_links.py) — batch-applies freshly-found `top-frame → OPM issue` links to a report via repeatable `--link "SYMBOL=ISSUE:STATE"` flags, so the results of step-4 searches can be recorded in one pass.
- [Reorder closed](./reorder_closed.py) — moves stacks linked to `CLOSED` issues into a `## Closed issues` section at the bottom of the report. Idempotent.

## Workflow

A new CSV lands every week. Processing it is seven steps:

1. **Save the CSV.** Copy the weekly export into `stacktrace-reports/csv/` as `YYYY-MM-DD-query_data.csv`. Only the `timestamp` and `rawstack` columns are expected.
2. **Run the analyzer in Markdown mode.**

   ```
   python stacktrace-reports/analyze_crashes.py \
       stacktrace-reports/csv/YYYY-MM-DD-query_data.csv \
       --format md \
       --output stacktrace-reports/reports/YYYY-MM-DD.md
   ```

   Stacks are grouped by their top 5 non-handler ResInsight frames, so reports that crash through the same library code but arrive from different UI invocation paths merge into one entry. Override with `--signature-depth N` (lower = more fuzzy).

3. **Carry over known links from prior reports.**

   ```
   python stacktrace-reports/apply_known_issues.py \
       stacktrace-reports/reports/YYYY-MM-DD.md \
       --prior stacktrace-reports/reports/PRIOR1.md \
       --prior stacktrace-reports/reports/PRIOR2.md
   ```

   For every stack whose top non-handler frame matches one already linked in a prior report, this fills in the same `**OPM issue:**` link. Existing links are left alone. The script's output names how many stacks were filled (`updated`) and how many still need manual search (`no_match`).

4. **Link the remaining stacks to upstream issues.** List the top frames of stacks still showing `**OPM issue:** none found`, grouped and sorted by impact:

   ```
   python stacktrace-reports/unmatched_top_frames.py stacktrace-reports/reports/YYYY-MM-DD.md
   ```

   (For the full grouping including already-linked stacks, use `extract_top_frames.py` instead.) For each unique signature, search [OPM/ResInsight issues](https://github.com/OPM/ResInsight/issues):

   ```
   gh search issues --repo OPM/ResInsight "RimFileSummaryCase createSummaryReaderInterfaceThreadSafe" --limit 5
   ```

   Fetch the issue state at the same time:

   ```
   gh issue view 13883 --repo OPM/ResInsight --json number,state
   ```

   Record the results in one pass via repeatable `--link` flags:

   ```
   python stacktrace-reports/apply_new_links.py stacktrace-reports/reports/YYYY-MM-DD.md \
       --link "RimSeismicSectionCollection::appendPartsToModel=13937:CLOSED" \
       --link "RimSummaryMultiPlot::updateReadOutSettings=13938:CLOSED"
   ```

   `SYMBOL` must match the exact string printed by `unmatched_top_frames.py` (return type + scope::name, template parameters included). Existing links are left alone; only `none found` lines are filled. Leave `none found` for signatures with no match so gaps stay visible. The state is captured at link-time — rerun `gh issue view` for stale reports if the current state matters.

5. **Move closed stacks to the bottom.**

   ```
   python stacktrace-reports/reorder_closed.py stacktrace-reports/reports/YYYY-MM-DD.md
   ```

   Stacks linked to a `CLOSED` issue are gathered under a `## Closed issues` section at the end, so open and unmatched stacks stay at the top. Stack numbers are preserved.

6. **Update `incoming-csvs.md`.** Append a row using the total-rows and unique-stacks numbers printed by `analyze_crashes.py` (first two lines of its text output). Row template:

   ```
   | YYYY-MM-DD | [YYYY-MM-DD-query_data.csv](./csv/YYYY-MM-DD-query_data.csv) | <total> | <unique> | [YYYY-MM-DD](./reports/YYYY-MM-DD.md) |
   ```

7. **Update `index.md`.** Insert a new row at the top of the weekly-reports table with the same totals.

Commit the CSV, the generated MD, and the two updated index pages together on a feature branch.

## Jekyll integration

The folder lives at the repo root (not as a Jekyll collection) so the folder name on disk matches the URL segment. Each Markdown file carries the standard `layout: default` front-matter used by pages in `_docs/`. CSV files are served as static assets by Jekyll.

## Data scope

CSVs are committed to the repo so reports remain reproducible. Before committing, confirm the CSV contains only non-identifying columns (currently `timestamp`, `rawstack`). If future exports add user-identifying fields, strip them before committing.
