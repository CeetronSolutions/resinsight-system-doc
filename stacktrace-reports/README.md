---
title: Stacktrace Reports
permalink: /stacktrace-reports/
layout: default
---

# Stacktrace Reports

Weekly ResInsight crash telemetry, deduplicated by call-stack signature and cross-linked to the upstream work on [OPM/ResInsight](https://github.com/OPM/ResInsight) that covers it — historically an issue, and since crash triage moved to PR-referenced reports, the fix PR that carries the call stack in its body.

## Contents

- [Incoming CSVs](./incoming-csvs.md) — every raw CSV received, with row counts and a link to its weekly report.
- [Weekly reports](./index.md) — list of per-week analyses, newest first.
- `registry.json` — **the source of truth.** One entry per unique crash signature, carrying its occurrence counts per week (broken down by reporting `APPversion`), any linked OPM issue with its open/closed state, any fix PR with its `OPEN`/`MERGED`/`CLOSED` state, an investigation status, and notes. A signature counts as *referenced* once it has an issue **or** a fix PR — new triage produces only the PR. State persists across weeks here, not in the Markdown.
- [registry.py](./registry.py) — folds a weekly CSV into `registry.json` (`update`), regenerates the latest report and the index pages from it (`render`), lists untriaged signatures — no issue, no PR — latest-version-first (`worklist`), and records an investigation outcome (`set`).
- [link_issues.py](./link_issues.py) — searches OPM/ResInsight for each unreferenced signature's top frame and links the issue when it confidently matches; refreshes the state of already-linked issues and of recorded fix PRs, so a merged PR flips its signatures to `resolved`.
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
2. **`link_issues.py`** — for each signature with no reference at all, searches
   OPM/ResInsight for its top-frame symbol and links the first issue whose title
   or body actually contains that symbol; for signatures that already carry an
   issue or a fix PR it re-fetches that reference's state instead of searching.
   A PR that has merged flips its signatures to `resolved`. Paced under the
   GitHub search rate limit.
3. **`registry.py render`** — regenerates the latest week's
   `reports/YYYY-MM-DD.md` plus `index.md` and `incoming-csvs.md` from the
   registry. Each stack shows its issue and/or fix PR; stacks whose issue is
   `CLOSED`, whose fix PR is `MERGED`, or that triage settled are gathered under
   a `## Closed issues and merged fixes` section automatically, and the report
   header carries a **Closed out** count of how many of the week's stacks — and
   how many of its crash reports — landed there. Only the latest
   report is ever re-rendered: previous weeks' pages are frozen snapshots of
   what was known at the time, so do **not** use `render --all` (it rewrites
   their stack listings and issue states with today's registry contents).
4. **`registry.py worklist`** — prints the signatures with neither an issue nor
   a fix PR and not already in triage, **ranked by
   how many times they crashed the newest released `APPversion` or later**
   (`cur` column), with all-time occurrences (`all`) only as the tie-breaker.
   Ranking on the all-time total alone would promote bugs whose volume comes
   from a superseded version — often already fixed — above the ones users hit
   today. Pre-release builds (`-dev.NN`, `-RC_N`) never define the current line,
   but crashes reported *by* a build newer than it do count; `--from-version`
   pins the line manually. These are the candidates for investigation.

Then **investigate the untriaged signatures top-down** with the `crash-triage`
workflow in the ResInsight repo ([docs/agents/crash-triage.md](https://github.com/OPM/ResInsight/blob/dev/docs/agents/crash-triage.md)):
it takes a batch of 4–5, locates each crash site in source, proposes and
build-verifies a fix with a reproducing test, and — after a human gate — pushes
one batch branch to the `magnesj` fork and opens **one PR for the batch**, then
writes it back onto every signature with `registry.py set --pr`.

**No GitHub issue is created.** The call stack that motivated each fix goes in
the PR body (one section per signature, stack in a `<details>` block), so the PR
is the crash report's reference. Signatures with no confident fix get a
`no-fix-found` status and an explanatory note instead, and nothing is filed for
them.

Status flow: `new`/`linked` → `investigating` (batch picked) → `pr-open`
(PR opened, recorded with `set --pr … --status pr-open`) → `resolved` when that
PR merges. The merge is picked up automatically by `link_issues.py` on the next
weekly run, or can be recorded directly:

```
python registry.py set --id <sid> --pr-state MERGED --status resolved
python registry.py render          # latest week only
```

Signatures whose PR is still open stay at `pr-open` — do not mark them resolved
early. Older signatures that carry an OPM issue keep it; issue state is still
refreshed each week.

Commit the CSV, `registry.json`, the regenerated report and the two index pages
together on a feature branch.

## Jekyll integration

The folder lives at the repo root (not as a Jekyll collection) so the folder name on disk matches the URL segment. Each Markdown file carries the standard `layout: default` front-matter used by pages in `_docs/`. CSV files are served as static assets by Jekyll.

## Data scope

CSVs are committed to the repo so reports remain reproducible. Before committing, confirm the CSV contains only non-identifying columns (currently `timestamp`, `rawstack`). If future exports add user-identifying fields, strip them before committing.
