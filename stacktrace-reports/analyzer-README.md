# Crash Report Analysis Tools

Tools for analyzing ResInsight crash report CSV files exported from the telemetry system.

## Prerequisites

- Python 3.10 or newer
- No third-party packages required (uses stdlib only)

## analyze_crashes.py

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
