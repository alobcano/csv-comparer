from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .compare import (
    compare_csv_rows_both,
    compare_csv_rows_by_first_column,
    compare_csv_rows_common,
    compare_csv_rows_deleted,
)
from .duplicates import find_duplicate_column_values
from .json_export import export_json_items_to_csv


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare CSV files or export selected fields from JSON based on the selected mode."
        )
    )
    parser.add_argument("base_csv", type=Path, help="Path to the first (base) CSV file")
    parser.add_argument(
        "updated_csv",
        type=Path,
        nargs="?",
        help="Path to the second (updated) CSV file (not required for --mode=duplicates)",
    )
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
