# Crash Report Analysis Tools

Tools for analyzing ResInsight crash report CSV files exported from the telemetry system.

## Prerequisites

- Python 3.10 or newer
- No third-party packages required (uses stdlib only)

## analyze_crashes.py

Groups crash reports by unique call stack and prints a ranked summary. The signature used for grouping is the set of ResInsight-specific frames (classes prefixed with `Rim`, `Ria`, `Rif`, `Ric`, `Riu`, `Riv`, `Rig`), so minor differences in lower-level system or Qt frames are ignored.

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
