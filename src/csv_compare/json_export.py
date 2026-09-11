from __future__ import annotations

import csv
import json
from pathlib import Path


def export_json_items_to_csv(input_json: Path, output_csv: Path) -> int:
    """Export external_id, uuid, title, and publisher from JSON items into a CSV file."""
    with input_json.open("r", encoding="utf-8") as source_file:
        payload = json.load(source_file)

    items = payload.get("items", []) if isinstance(payload, dict) else []
    headers = ["external_id", "uuid", "title", "publisher"]
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
                    "uuid": item.get("uuid", ""),
                    "title": data.get("title", ""),
                    "publisher": data.get("publisher", ""),
                }
            )
            row_count += 1

    return row_count
