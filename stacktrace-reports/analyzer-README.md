# Crash Report Analysis Tools

Tools for analyzing ResInsight crash report CSV files exported from the telemetry system.

## Prerequisites

- Python 3.10 or newer
- No third-party packages required (uses stdlib only)
- `link_issues.py` additionally needs an authenticated GitHub CLI (`gh`)

## registry.py (primary tool)

`registry.py` is the entry point for the weekly workflow; `analyze_crashes.py`
below is now a library it reuses. It maintains `registry.json`, the persistent
per-signature state.

| Subcommand | Description |
|---|---|
| `update --csv FILE [--date D] [--signature-depth N] [--min-version VER]` | Fold a weekly CSV into `registry.json`. Idempotent per week. |
| `render [--date D \| --all]` | Regenerate report(s) + `index.md` + `incoming-csvs.md` from the registry. Default: latest week. |
| `worklist [--all]` | Print unlinked signatures, highest total count first. |
| `set --id SID [--issue N --state S] [--pr N --branch B] [--status S] [--note "..."]` | Record an investigation outcome (used by the `crash-triage` skill). |

Typical run is via `process_week.py`, which chains `update` → `link_issues.py`
→ `render` → `worklist`. Signatures are keyed by their top-N non-handler frame
*symbols* (file/line and template noise stripped) so identity is stable across
builds.

## analyze_crashes.py (library / standalone)

Groups crash reports by unique call stack and prints a ranked summary. The signature used for grouping is the **top N non-handler ResInsight-specific frames** (classes prefixed with `Rim`, `Ria`, `Rif`, `Ric`, `Riu`, `Riv`, `Rig`). The crash-handler frames (`performCrashLogging`, `manageSegFailure*`) are skipped before taking the top N, so the signature focuses on the actual crash site and the immediate call path rather than the deeper UI invocation. Two reports that crash through the same library code but reach it from different UI features merge into one group.

`N` defaults to 5 and can be tuned with `--signature-depth`. Lower values are more fuzzy (more merging); higher values are stricter.

### Basic usage

```
python analyze_crashes.py <csv_file>
```

Example — analyze today's export:

```
python analyze_crashes.py "..\2026-04-09-query_data.csv"
```

### Options

| Option | Description |
|---|---|
| `--min-count N` | Only show stacks that appear at least N times |
| `--signature-depth N` | Number of top non-handler RI frames used for grouping (default: 5). Lower = more fuzzy. |
| `--min-version VER` | Drop rows whose `APPversion` is older than VER (default: `2026.02.2`). Versions with a `-dev.NN` suffix are always kept regardless of base. Pass an empty string to disable. |
| `--output FILE` | Write the report to a file instead of printing to the terminal |

### Examples

Show only stacks with 2 or more occurrences:

```
python analyze_crashes.py "..\2026-04-09-query_data.csv" --min-count 2
```

Save the full report to a text file:

```
python analyze_crashes.py "..\2026-04-09-query_data.csv" --output "..\reports\2026-04-09-analysis.txt"
```

Combine both:

```
python analyze_crashes.py "..\2026-04-09-query_data.csv" --min-count 2 --output "..\reports\2026-04-09-analysis.txt"
```

### Output format

```
Total crash reports : 53
Unique call stacks  : 13

======================================================================
Stack #1  (count: 32, first seen: 4/9/2026, 11:05:37.642 AM)
======================================================================
  [0] performCrashLogging at ResInsight/ApplicationExeCode/RiaMainTools.cpp:147
  [13] RimFileSummaryCase::createSummaryReaderInterfaceThreadSafe(...) at RimFileSummaryCase.cpp:121
  ...
```

Stacks are sorted by occurrence count, highest first.
