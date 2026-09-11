from __future__ import annotations

import csv
from pathlib import Path

from .csv_utils import read_headers


def find_duplicate_column_values(input_csv: Path, output_csv: Path, column: str) -> int:
    """Find rows with duplicate values in the specified column and write the first occurrence to output_csv."""
    headers = read_headers(input_csv)
    if column not in headers:
        raise ValueError(f"Column '{column}' not found in {input_csv}. Available columns: {headers}")

    # First pass: count occurrences of each value in the target column.
    value_counts: dict[str, int] = {}
    with input_csv.open("r", newline="", encoding="utf-8-sig") as input_file:
        reader = csv.DictReader(input_file)
        for row in reader:
            value = row.get(column, "")
            value_counts[value] = value_counts.get(value, 0) + 1

    duplicate_values = {value for value, count in value_counts.items() if count > 1}

    # Second pass: write only the first occurrence of rows with duplicated values.
    duplicate_row_count = 0
    seen_duplicates: set[str] = set()
    with input_csv.open("r", newline="", encoding="utf-8-sig") as source_file, output_csv.open(
        "w", newline="", encoding="utf-8"
    ) as destination_file:
        reader = csv.DictReader(source_file)
        writer = csv.DictWriter(destination_file, fieldnames=headers)
        writer.writeheader()

        for row in reader:
            value = row.get(column, "")
            if value in duplicate_values and value not in seen_duplicates:
                writer.writerow({field: row.get(field, "") for field in headers})
                seen_duplicates.add(value)
                duplicate_row_count += 1

    return duplicate_row_count
