import argparse
import csv
import json
from pathlib import Path
from typing import Sequence


def _read_headers(csv_path: Path) -> list[str]:
    with csv_path.open("r", newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.reader(csv_file)
        try:
            headers = next(reader)
        except StopIteration:
            return []
    return headers


def _read_first_column_keys(csv_path: Path) -> set[str]:
    keys: set[str] = set()
    with csv_path.open("r", newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.reader(csv_file)
        next(reader, None)  # Skip header row.
        for row in reader:
            if row:
                keys.add(row[0])
    return keys


def _resolve_key_column(headers: list[str], key_column: str | None, csv_path: Path) -> str:
    if not headers:
        raise ValueError(f"CSV file has no headers: {csv_path}")
    if key_column:
        if key_column not in headers:
            raise ValueError(
                f"Column '{key_column}' not found in {csv_path}. Available columns: {headers}"
            )
        return key_column
    return headers[0]


def _read_column_keys(csv_path: Path, key_column: str | None = None) -> set[str]:
    headers = _read_headers(csv_path)
    resolved_key_column = _resolve_key_column(headers, key_column, csv_path)
    keys: set[str] = set()

    with csv_path.open("r", newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            key = row.get(resolved_key_column, "")
            if key:
                keys.add(key)

    return keys


def compare_csv_rows_by_first_column(
    base_csv: Path, updated_csv: Path, output_csv: Path, key_column: str | None = None
) -> int:
    """Find rows in updated_csv that are not in base_csv using a key column."""
    updated_headers = _read_headers(updated_csv)
    updated_key_column = _resolve_key_column(updated_headers, key_column, updated_csv)
    base_keys = _read_column_keys(base_csv, key_column)
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
    base_headers = _read_headers(base_csv)
    base_key_column = _resolve_key_column(base_headers, key_column, base_csv)
    updated_keys = _read_column_keys(updated_csv, key_column)
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
    updated_headers = _read_headers(updated_csv)
    updated_key_column = _resolve_key_column(updated_headers, key_column, updated_csv)
    base_keys = _read_column_keys(base_csv, key_column)
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


def find_duplicate_column_values(input_csv: Path, output_csv: Path, column: str) -> int:
    """Find rows with duplicate values in the specified column and write them to output_csv."""
    headers = _read_headers(input_csv)
    if column not in headers:
        raise ValueError(f"Column '{column}' not found in {input_csv}. Available columns: {headers}")

    # First pass: count occurrences of each value in the target column.
    value_counts: dict[str, int] = {}
    with input_csv.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            val = row.get(column, "")
            value_counts[val] = value_counts.get(val, 0) + 1

    duplicate_values = {val for val, count in value_counts.items() if count > 1}

    # Second pass: write rows whose column value is duplicated.
    duplicate_row_count = 0
    with input_csv.open("r", newline="", encoding="utf-8-sig") as source_file, output_csv.open(
        "w", newline="", encoding="utf-8"
    ) as destination_file:
        reader = csv.DictReader(source_file)
        writer = csv.DictWriter(destination_file, fieldnames=headers)
        writer.writeheader()
        for row in reader:
            if row.get(column, "") in duplicate_values:
                writer.writerow({field: row.get(field, "") for field in headers})
                duplicate_row_count += 1

    return duplicate_row_count


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


def export_json_items_to_csv(input_json: Path, output_csv: Path) -> int:
    """Export external_id, title, and publisher from JSON items into a CSV file."""
    with input_json.open("r", encoding="utf-8") as source_file:
        payload = json.load(source_file)

    items = payload.get("items", []) if isinstance(payload, dict) else []
    headers = ["external_id", "title", "publisher"]
    row_count = 0

    with output_csv.open("w", newline="", encoding="utf-8") as destination_file:
        writer = csv.DictWriter(destination_file, fieldnames=headers)
        writer.writeheader()

        for item in items:
            if not isinstance(item, dict):
                continue
            data = item.get("data", {})
            if not isinstance(data, dict):
                data = {}
            writer.writerow(
                {
                    "external_id": item.get("external_id", ""),
                    "title": data.get("title", ""),
                    "publisher": data.get("publisher", ""),
                }
            )
            row_count += 1

    return row_count


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare CSV files or export selected fields from JSON based on the selected mode."
        )
    )
    parser.add_argument("base_csv", type=Path, help="Path to the first (base) CSV file")
    parser.add_argument("updated_csv", type=Path, nargs="?", help="Path to the second (updated) CSV file (not required for --mode=duplicates)")
    parser.add_argument(
        "output_csv",
        type=Path,
        nargs="?",
        help="Path where the output CSV will be written (required for all modes)",
    )
    parser.add_argument(
        "--mode",
        choices=["new", "deleted", "common", "both", "duplicates", "json"],
        default="new",
        help=(
            "Comparison mode: 'new' finds rows in updated_csv not in base_csv, "
            "'deleted' finds rows in base_csv not in updated_csv, "
            "'common' finds rows with matching keys in both CSVs (using updated_csv format), "
            "'both' creates files for new and deleted rows, "
            "'duplicates' finds rows with duplicate values in --column, "
            "'json' exports external_id/title/publisher from JSON items (default: new)"
        ),
    )
    parser.add_argument(
        "--column",
        default="S3_PATH",
        help="Column name to check for duplicates (only used with --mode=duplicates, default: S3_PATH)",
    )
    parser.add_argument(
        "--key-column",
        help=(
            "Column name to use as the key for CSV comparison modes "
            "(new/deleted/common/both). Defaults to the first column in each CSV."
        ),
    )
    parser.add_argument(
        "--output-deleted",
        type=Path,
        help="Path for deleted rows output (only used with --mode=both)",
    )
    return parser.parse_args(argv)


def _require_output_csv(args: argparse.Namespace, mode: str) -> bool:
    if args.output_csv:
        return True
    print(f"Error: output_csv is required for '{mode}' mode")
    return False


def _handle_mode_new(args: argparse.Namespace) -> int:
    if not _require_output_csv(args, "new"):
        return 1
    try:
        new_rows = compare_csv_rows_by_first_column(
            args.base_csv, args.updated_csv, args.output_csv, args.key_column
        )
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1
    print(
        f"Created {args.output_csv} with {new_rows} new row(s) "
        f"(rows in updated_csv not in base_csv)."
    )
    return 0


def _handle_mode_deleted(args: argparse.Namespace) -> int:
    if not _require_output_csv(args, "deleted"):
        return 1
    try:
        deleted_rows = compare_csv_rows_deleted(
            args.base_csv, args.updated_csv, args.output_csv, args.key_column
        )
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1
    print(
        f"Created {args.output_csv} with {deleted_rows} deleted row(s) "
        f"(rows in base_csv not in updated_csv)."
    )
    return 0


def _handle_mode_common(args: argparse.Namespace) -> int:
    if not _require_output_csv(args, "common"):
        return 1
    try:
        common_rows = compare_csv_rows_common(
            args.base_csv, args.updated_csv, args.output_csv, args.key_column
        )
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1
    print(
        f"Created {args.output_csv} with {common_rows} common row(s) "
        f"(rows with matching keys in both CSVs, using updated_csv format)."
    )
    return 0


def _handle_mode_duplicates(args: argparse.Namespace) -> int:
    output_path = args.output_csv or args.updated_csv
    if not output_path:
        print("Error: output_csv is required for 'duplicates' mode")
        return 1
    try:
        dup_rows = find_duplicate_column_values(args.base_csv, output_path, args.column)
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1
    print(
        f"Created {output_path} with {dup_rows} row(s) that have duplicate '{args.column}' values."
    )
    return 0


def _handle_mode_both(args: argparse.Namespace) -> int:
    if not _require_output_csv(args, "both"):
        return 1
    if not args.output_deleted:
        print("Error: --output-deleted is required for 'both' mode")
        return 1
    try:
        new_rows, deleted_rows = compare_csv_rows_both(
            args.base_csv,
            args.updated_csv,
            args.output_csv,
            args.output_deleted,
            args.key_column,
        )
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1
    print(f"Created {args.output_csv} with {new_rows} new row(s).")
    print(f"Created {args.output_deleted} with {deleted_rows} deleted row(s).")
    return 0


def _handle_mode_json(args: argparse.Namespace) -> int:
    output_path = args.output_csv or args.updated_csv
    if not output_path:
        print("Error: output_csv is required for 'json' mode")
        return 1
    try:
        exported_rows = export_json_items_to_csv(args.base_csv, output_path)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Error: unable to process JSON file: {exc}")
        return 1
    print(
        f"Created {output_path} with {exported_rows} row(s) "
        "(external_id, title, publisher from JSON items)."
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    mode_handlers = {
        "new": _handle_mode_new,
        "deleted": _handle_mode_deleted,
        "common": _handle_mode_common,
        "duplicates": _handle_mode_duplicates,
        "both": _handle_mode_both,
        "json": _handle_mode_json,
    }
    return mode_handlers[args.mode](args)


if __name__ == "__main__":
    raise SystemExit(main())
