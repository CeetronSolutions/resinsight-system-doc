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

## Workflow

A new CSV lands every week. Processing it is five steps:

1. **Save the CSV.** Copy the weekly export into `stacktrace-reports/csv/` as `YYYY-MM-DD-query_data.csv`. Only the `timestamp` and `rawstack` columns are expected.
2. **Run the analyzer in Markdown mode.**

   ```
   python stacktrace-reports/analyze_crashes.py \
       stacktrace-reports/csv/YYYY-MM-DD-query_data.csv \
       --format md \
       --output stacktrace-reports/reports/YYYY-MM-DD.md
   ```

3. **Link to upstream issues.** For each unique stack, search [OPM/ResInsight issues](https://github.com/OPM/ResInsight/issues) using the top ResInsight-specific frame (skip `performCrashLogging` / `manageSegFailure` — those are the crash handler). Example search:

   ```
   gh search issues --repo OPM/ResInsight "RimFileSummaryCase createSummaryReaderInterfaceThreadSafe" --limit 5
   ```

   Replace `**OPM issue:** none found` with `**OPM issue:** [#NNNN](https://github.com/OPM/ResInsight/issues/NNNN)` when a match is found; leave `none found` otherwise so gaps stay visible.

4. **Update `incoming-csvs.md`.** Append a row using the total-rows and unique-stacks numbers printed by `analyze_crashes.py` (first two lines of its text output). Row template:

   ```
   | YYYY-MM-DD | [YYYY-MM-DD-query_data.csv](./csv/YYYY-MM-DD-query_data.csv) | <total> | <unique> | [YYYY-MM-DD](./reports/YYYY-MM-DD.md) |
   ```

5. **Update `index.md`.** Insert a new row at the top of the weekly-reports table with the same totals.

Commit the CSV, the generated MD, and the two updated index pages together on a feature branch.

## Jekyll integration

The folder lives at the repo root (not as a Jekyll collection) so the folder name on disk matches the URL segment. Each Markdown file carries the standard `layout: default` front-matter used by pages in `_docs/`. CSV files are served as static assets by Jekyll.

## Data scope

CSVs are committed to the repo so reports remain reproducible. Before committing, confirm the CSV contains only non-identifying columns (currently `timestamp`, `rawstack`). If future exports add user-identifying fields, strip them before committing.
