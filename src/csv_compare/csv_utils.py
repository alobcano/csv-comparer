from __future__ import annotations

import csv
from pathlib import Path


def read_headers(csv_path: Path) -> list[str]:
    with csv_path.open("r", newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.reader(csv_file)
        try:
            headers = next(reader)
        except StopIteration:
            return []
    return headers


def resolve_key_column(headers: list[str], key_column: str | None, csv_path: Path) -> str:
    if not headers:
        raise ValueError(f"CSV file has no headers: {csv_path}")
    if key_column:
        if key_column not in headers:
            raise ValueError(
                f"Column '{key_column}' not found in {csv_path}. Available columns: {headers}"
            )
        return key_column
    return headers[0]


def read_column_keys(csv_path: Path, key_column: str | None = None) -> set[str]:
    headers = read_headers(csv_path)
    resolved_key_column = resolve_key_column(headers, key_column, csv_path)
    keys: set[str] = set()

    with csv_path.open("r", newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            key = row.get(resolved_key_column, "")
            if key:
                keys.add(key)

    return keys
