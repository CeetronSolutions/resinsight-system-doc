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
- `registry.json` — **the source of truth.** One entry per unique crash signature, carrying its occurrence counts per week (broken down by reporting `APPversion`), the linked OPM issue and its open/closed state, any fix PR, an investigation status, and notes. State persists across weeks here, not in the Markdown.
- [registry.py](./registry.py) — folds a weekly CSV into `registry.json` (`update`), regenerates the reports and index pages from it (`render`), lists unlinked signatures by impact (`worklist`), and records an investigation outcome (`set`).
- [link_issues.py](./link_issues.py) — searches OPM/ResInsight for each unlinked signature's top frame and links the issue when it confidently matches; refreshes the open/closed state of already-linked issues.
- [process_week.py](./process_week.py) — one-shot driver chaining update → link → render → worklist.
- [Analyzer](./analyze_crashes.py) — the original grouping library; `registry.py` reuses its CSV parsing and frame helpers.
- [Analyzer usage](./analyzer-README.md) — command-line reference for `registry.py` and `analyze_crashes.py`.

> **Deprecated.** `apply_known_issues.py`, `apply_new_links.py`, `unmatched_top_frames.py`, `extract_top_frames.py` and `reorder_closed.py` are superseded by the registry. Their jobs — carrying links across weeks, recording new links, prioritising unmatched frames, and moving closed stacks down — are now done by `registry.json` + `link_issues.py` + `registry.py render`. They are kept for one cycle for cross-checking and will be removed.

## Workflow

A new CSV lands every week. Drop it into `stacktrace-reports/csv/` as
`YYYY-MM-DD-query_data.csv` (only `timestamp`, `APPversion`, `rawstack` are
expected), then run the driver:

```
python stacktrace-reports/process_week.py stacktrace-reports/csv/YYYY-MM-DD-query_data.csv
```

That performs, in order:

1. **`registry.py update`** — parses the CSV, drops rows older than the minimum
   version, and folds every stack into `registry.json`. Stacks are keyed by a
   stable *normalised symbol signature* (top-5 non-handler ResInsight frame
   symbols, with `file:line`, arguments and template noise stripped), so the
   same bug keeps its identity across builds and weeks. Re-running an already
   folded week is idempotent. The rendered call stack also keeps the
   closely-related upstream `Opm::` (opm-common) and `ecl_` (libecl) frames,
   which often hold the real crash site; those frames are *not* part of the
   signature, so identity stays keyed on ResInsight's own frames.
2. **`link_issues.py`** — for each signature without a linked issue, searches
   OPM/ResInsight for its top-frame symbol and links the first issue whose title
   or body actually contains that symbol; for already-linked signatures it
   re-fetches the issue state. Paced under the GitHub search rate limit.
3. **`registry.py render`** — regenerates the week's `reports/YYYY-MM-DD.md`
   plus `index.md` and `incoming-csvs.md` from the registry. Stacks linked to a
   `CLOSED` issue are gathered under a `## Closed issues` section automatically.
4. **`registry.py worklist`** — prints the signatures still unlinked, ranked by
   total occurrences. These are the candidates for investigation.

Then **investigate the top unlinked signatures** with the `crash-triage` skill
in the ResInsight repo: it locates the crash site in source, proposes and
build-verifies a fix, and — after a human gate — files the OPM issue, pushes a
fix branch to the `magnesj` fork, opens the PR, and writes the issue/PR back
onto the signature with `registry.py set`. Signatures with no confident fix get
a `no-fix-found` status and an explanatory note instead.

Commit the CSV, `registry.json`, the regenerated report and the two index pages
together on a feature branch.

## Jekyll integration

The folder lives at the repo root (not as a Jekyll collection) so the folder name on disk matches the URL segment. Each Markdown file carries the standard `layout: default` front-matter used by pages in `_docs/`. CSV files are served as static assets by Jekyll.

## Data scope

CSVs are committed to the repo so reports remain reproducible. Before committing, confirm the CSV contains only non-identifying columns (currently `timestamp`, `rawstack`). If future exports add user-identifying fields, strip them before committing.
