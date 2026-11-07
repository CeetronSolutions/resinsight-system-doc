"""Remove user.name and user.hash from a stacktrace CSV's CustomDimensions, in place.

CSVs are committed to the repo, so these must go before anything else reads the
file. Safe to re-run; a CSV without the fields or the column is left untouched.

Usage: strip_user_fields.py <csv>
"""

import csv
import io
import json
import os
import sys

USER_FIELDS = ("user.name", "user.hash")


def strip(csv_path):
    # Raw stacks exceed the default csv field limit.
    csv.field_size_limit(2**31 - 1)

    # newline="" keeps the LFs inside quoted stacks apart from the CRLF row ends.
    with open(csv_path, encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))

    if not rows or "CustomDimensions" not in rows[0]:
        return 0

    column = rows[0].index("CustomDimensions")
    stripped = 0

    for line, row in enumerate(rows[1:], start=2):
        if not row[column].strip():
            continue

        # Abort on bad JSON: passing it through could leave user data in the CSV.
        try:
            dimensions = json.loads(row[column])
        except json.JSONDecodeError as e:
            sys.exit(f"Error: {csv_path} record {line}: unparseable CustomDimensions: {e.msg}")

        if not isinstance(dimensions, dict):
            sys.exit(f"Error: {csv_path} record {line}: CustomDimensions is not an object")

        if any(field in dimensions for field in USER_FIELDS):
            for field in USER_FIELDS:
                dimensions.pop(field, None)
            row[column] = json.dumps(dimensions, ensure_ascii=False, separators=(",", ":"))
            stripped += 1

    if stripped:
        output = io.StringIO(newline="")
        csv.writer(output, lineterminator="\r\n").writerows(rows)

        temp_path = f"{csv_path}.tmp"
        with open(temp_path, "w", encoding="utf-8", newline="") as f:
            f.write(output.getvalue())
        os.replace(temp_path, csv_path)

    return stripped


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)

    print(f"stripped user fields from {strip(sys.argv[1])} rows")


if __name__ == "__main__":
    main()
