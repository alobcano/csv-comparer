# CSV Row Comparator

This project compares two CSV files by using the first column as the row key and generates output CSV(s) based on the selected comparison mode.

## What It Does

- Uses the first column in each CSV as the comparison key
- Supports using a custom key column via `--key-column` for CSV comparison modes
- Supports comparison and extraction modes:
  - **new**: Finds rows in the second CSV that don't exist in the first CSV (default)
  - **deleted**: Finds rows in the first CSV that don't exist in the second CSV
  - **common**: Finds rows with matching keys in both CSVs (outputs in second CSV format)
  - **both**: Generates both new and deleted row files in a single run
  - **duplicates**: Finds rows with duplicate values in a specified column (default column: `S3_PATH`)
  - **json**: Exports `external_id`, `uuid`, `title`, and `publisher` from a JSON file with an `items` array
- Collects all key values from the reference CSV
- Scans rows and keeps those matching the selected mode
- Writes results to output CSV(s) with columns from the source CSV

## Requirements

- Python 3.10+
- No external packages

## Usage

Run from the project root:

```bash
# Default mode: find new rows (in updated but not in base)
python3 main.py base.csv updated.csv new_rows.csv

# Default mode with a custom key column
python3 main.py base.csv updated.csv new_rows.csv --key-column=AVAILABILITY_PK

# Find deleted rows (in base but not in updated)
python3 main.py base.csv updated.csv deleted_rows.csv --mode=deleted

# Find common rows (matching keys in both, using updated.csv format)
python3 main.py base.csv updated.csv common_rows.csv --mode=common

# Find both new and deleted rows in one run
python3 main.py base.csv updated.csv new_rows.csv --mode=both --output-deleted deleted_rows.csv

# Find rows with duplicate S3_PATH values
python3 main.py input.csv duplicated.csv --mode=duplicates

# Find rows with duplicate values in a custom column
python3 main.py output.csv duplicates.csv --mode=duplicates --column=external_id

# Export external_id, uuid, title, publisher from JSON
python3 main.py omnipubs.json output.csv --mode=json
```

### Arguments

- `base_csv`: First CSV file (baseline key values)
- `updated_csv`: Second CSV file (candidate rows)
- `output_csv`: Output CSV path (required for all modes)
  - For `--mode=new`: Contains rows that are in updated_csv but not in base_csv
  - For `--mode=deleted`: Contains rows that are in base_csv but not in updated_csv
  - For `--mode=common`: Contains rows with matching keys in both CSVs (using updated_csv format)
  - For `--mode=both`: Contains new rows

### Options

- `--mode {new,deleted,common,both,duplicates,json}`: Comparison mode (default: `new`)
  - `new`: Find rows in updated_csv not in base_csv
  - `deleted`: Find rows in base_csv not in updated_csv
  - `common`: Find rows with matching keys in both CSVs (uses updated_csv column format)
  - `both`: Find both new and deleted rows
  - `duplicates`: Find rows with duplicate values in a column (only `base_csv` and `output_csv` needed)
  - `json`: Export `external_id`, `uuid`, `title`, `publisher` from each object in `items` (only `base_csv` and `output_csv` needed)
- `--output-deleted PATH`: Path for deleted rows (required when using `--mode=both`)
- `--column NAME`: Column name to check for duplicates (only used with `--mode=duplicates`, default: `S3_PATH`)
- `--key-column NAME`: Column name to use as the comparison key for `new`, `deleted`, `common`, and `both` modes (default: first column)

## Examples

### Example 1: Find New Rows (Default)

Base CSV (`base.csv`):
```text
id,name
1,Alice
2,Bob
```

Updated CSV (`updated.csv`):
```text
id,name,email,phone
1,Alice,a@example.com,111
2,Bob,b@example.com,222
3,Carol,c@example.com,333
```

Run:
```bash
python3 main.py base.csv updated.csv new_rows.csv
```

Output (`new_rows.csv`):
```text
id,name,email,phone
3,Carol,c@example.com,333
```

### Example 2: Find Deleted Rows

Using the same files as above, run:
```bash
python3 main.py base.csv updated.csv deleted_rows.csv --mode=deleted
```

Output (`deleted_rows.csv`):
```text
id,name
```
(Empty, because no rows were deleted in this example)

### Example 3: Find Common Rows

Using the same files as above, run:
```bash
python3 main.py base.csv updated.csv common_rows.csv --mode=common
```

Output (`common_rows.csv`) - uses updated_csv format:
```text
id,name,email,phone
1,Alice,a@example.com,111
2,Bob,b@example.com,222
```

This is useful when:
- Base CSV has fewer columns than updated CSV
- You want to get all columns from the updated CSV for rows that exist in both files
- You need to track which rows were present and unchanged (by key) between versions

### Example 4: Find Both New and Deleted Rows in One Run

Run:
```bash
python3 main.py base.csv updated.csv new_rows.csv --mode=both --output-deleted deleted_rows.csv
```

This creates two files:
- `new_rows.csv`: Rows in updated_csv not in base_csv
- `deleted_rows.csv`: Rows in base_csv not in updated_csv
