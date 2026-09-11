from __future__ import annotations

import csv
from pathlib import Path

from .csv_utils import read_column_keys, read_headers, resolve_key_column


def compare_csv_rows_by_first_column(
    base_csv: Path, updated_csv: Path, output_csv: Path, key_column: str | None = None
) -> int:
    """Find rows in updated_csv that are not in base_csv using a key column."""
    updated_headers = read_headers(updated_csv)
    updated_key_column = resolve_key_column(updated_headers, key_column, updated_csv)
    base_keys = read_column_keys(base_csv, key_column)
    new_row_count = 0

    with updated_csv.open("r", newline="", encoding="utf-8-sig") as source_file, output_csv.open(
        "w", newline="", encoding="utf-8"
    ) as destination_file:
        reader = csv.DictReader(source_file)
        writer = csv.DictWriter(destination_file, fieldnames=updated_headers)
        writer.writeheader()

        for row in reader:
            key = row.get(updated_key_column, "")
            if key and key not in base_keys:
                writer.writerow({field: row.get(field, "") for field in updated_headers})
                new_row_count += 1

    return new_row_count


def compare_csv_rows_deleted(
    base_csv: Path, updated_csv: Path, output_csv: Path, key_column: str | None = None
) -> int:
    """Find rows in base_csv that are not in updated_csv using a key column."""
    base_headers = read_headers(base_csv)
    base_key_column = resolve_key_column(base_headers, key_column, base_csv)
    updated_keys = read_column_keys(updated_csv, key_column)
    deleted_row_count = 0

    with base_csv.open("r", newline="", encoding="utf-8-sig") as source_file, output_csv.open(
        "w", newline="", encoding="utf-8"
    ) as destination_file:
        reader = csv.DictReader(source_file)
        writer = csv.DictWriter(destination_file, fieldnames=base_headers)
        writer.writeheader()

        for row in reader:
            key = row.get(base_key_column, "")
            if key and key not in updated_keys:
                writer.writerow({field: row.get(field, "") for field in base_headers})
                deleted_row_count += 1

    return deleted_row_count


def compare_csv_rows_common(
    base_csv: Path, updated_csv: Path, output_csv: Path, key_column: str | None = None
) -> int:
    """Find rows that exist in both CSVs using a key column and updated_csv format."""
    updated_headers = read_headers(updated_csv)
    updated_key_column = resolve_key_column(updated_headers, key_column, updated_csv)
    base_keys = read_column_keys(base_csv, key_column)
    matched_row_count = 0

    with updated_csv.open("r", newline="", encoding="utf-8-sig") as source_file, output_csv.open(
        "w", newline="", encoding="utf-8"
    ) as destination_file:
        reader = csv.DictReader(source_file)
        writer = csv.DictWriter(destination_file, fieldnames=updated_headers)
        writer.writeheader()

        for row in reader:
            key = row.get(updated_key_column, "")
            if key and key in base_keys:
                writer.writerow({field: row.get(field, "") for field in updated_headers})
                matched_row_count += 1

    return matched_row_count


def compare_csv_rows_both(
    base_csv: Path,
    updated_csv: Path,
    output_new_csv: Path,
    output_deleted_csv: Path,
    key_column: str | None = None,
) -> tuple[int, int]:
    """Find both new and deleted rows using a key column."""
    new_rows = compare_csv_rows_by_first_column(base_csv, updated_csv, output_new_csv, key_column)
    deleted_rows = compare_csv_rows_deleted(base_csv, updated_csv, output_deleted_csv, key_column)
    return new_rows, deleted_rows
