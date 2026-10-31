
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
folder = ROOT / "preprocessing"
folder.mkdir(exist_ok=True)

code = r'''
from pathlib import Path
import pandas as pd
import json

ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "data" / "it_support_tickets_v2.csv"
OUTPUT = ROOT / "data" / "it_support_tickets_cleaned.csv"
REPORT = ROOT / "data" / "data_quality_report.csv"
SUMMARY = ROOT / "data" / "data_quality_summary.json"

if not INPUT.exists():
    raise FileNotFoundError(f"Dataset not found: {INPUT}")

print("Loading original dataset...")
df = pd.read_csv(INPUT)

original_rows = len(df)
original_columns = len(df.columns)

# Record initial data quality
missing_before = df.isna().sum()
duplicate_rows_before = int(df.duplicated().sum())

if "ticket_id" in df.columns:
    duplicate_ids = int(df["ticket_id"].duplicated().sum())
else:
    duplicate_ids = None

# Check required columns
required = ["ticket_id", "ticket_text", "category"]
missing_columns = [c for c in required if c not in df.columns]

if missing_columns:
    raise ValueError(f"Missing required columns: {missing_columns}")

# Normalize text fields without changing their meaning
text_columns = [
    "ticket_id", "subject", "description", "ticket_text",
    "category", "subcategory", "priority", "impact",
    "urgency", "status", "channel", "assigned_group",
    "resolution_summary"
]

for column in text_columns:
    if column in df.columns:
        df[column] = df[column].apply(
            lambda x: " ".join(x.split()) if isinstance(x, str) else x
        )

# Remove records only when essential classification fields are missing
before_required_filter = len(df)

df = df.dropna(subset=["ticket_id", "ticket_text", "category"]).copy()
df = df[
    df["ticket_id"].astype(str).str.strip().ne("")
    & df["ticket_text"].astype(str).str.strip().ne("")
    & df["category"].astype(str).str.strip().ne("")
].copy()

removed_required = before_required_filter - len(df)

# Do not silently discard duplicate ticket IDs
if df["ticket_id"].duplicated().any():
    duplicates = df.loc[
        df["ticket_id"].duplicated(keep=False), "ticket_id"
    ].tolist()
    raise ValueError(
        f"Duplicate ticket IDs found. Review these IDs: {duplicates[:20]}"
    )

# Parse date fields. Invalid dates become missing, not fabricated dates.
date_invalid_counts = {}

for column in ["created_at", "resolved_at"]:
    if column in df.columns:
        original_nonmissing = df[column].notna()
        parsed = pd.to_datetime(df[column], errors="coerce")
        date_invalid_counts[column] = int(
            (original_nonmissing & parsed.isna()).sum()
        )
        df[column] = parsed

# Convert numeric columns safely. Invalid values become missing.
numeric_invalid_counts = {}

numeric_columns = [
    "first_response_minutes",
    "resolution_minutes",
    "reopen_count",
    "sla_target_minutes"
]

for column in numeric_columns:
    if column in df.columns:
        original_nonmissing = df[column].notna()
        converted = pd.to_numeric(df[column], errors="coerce")

        numeric_invalid_counts[column] = int(
            (original_nonmissing & converted.isna()).sum()
        )

        df[column] = converted

# Normalize SLA boolean values without guessing unknown values.
if "sla_breached" in df.columns:
    bool_map = {
        "true": True, "1": True, "yes": True,
        "false": False, "0": False, "no": False
    }

    def convert_boolean(value):
        if pd.isna(value):
            return None
        if isinstance(value, bool):
            return value
        return bool_map.get(str(value).strip().lower())

    df["sla_breached"] = df["sla_breached"].apply(convert_boolean)

# Save cleaned data separately. Original CSV remains unchanged.
df.to_csv(OUTPUT, index=False)

# Build a column-level data quality report.
report_rows = []

for column in df.columns:
    report_rows.append({
        "column": column,
        "missing_before": int(missing_before.get(column, 0)),
        "missing_after": int(df[column].isna().sum()),
        "data_type_after": str(df[column].dtype)
    })

report_df = pd.DataFrame(report_rows)
report_df.to_csv(REPORT, index=False)

summary = {
    "input_file": INPUT.name,
    "output_file": OUTPUT.name,
    "original_rows": original_rows,
    "cleaned_rows": len(df),
    "columns": original_columns,
    "rows_removed_for_missing_required_fields": removed_required,
    "duplicate_rows_before": duplicate_rows_before,
    "duplicate_ticket_ids_before": duplicate_ids,
    "missing_values_before": {
        k: int(v) for k, v in missing_before.items() if v > 0
    },
    "missing_values_after": {
        k: int(v) for k, v in df.isna().sum().items() if v > 0
    },
    "invalid_dates_converted_to_missing": date_invalid_counts,
    "invalid_numbers_converted_to_missing": numeric_invalid_counts,
    "note": (
        "Missing resolution fields were preserved. "
        "No missing values were filled with invented values."
    )
}

with open(SUMMARY, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=4, default=str)

print("\n========== DATA QUALITY SUMMARY ==========")
print("Original rows:", original_rows)
print("Cleaned rows:", len(df))
print("Columns:", len(df.columns))
print("Rows removed for missing required fields:", removed_required)
print("Duplicate rows before cleaning:", duplicate_rows_before)
print("Duplicate ticket IDs before cleaning:", duplicate_ids)

print("\nMissing values after cleaning:")
print(df.isna().sum()[df.isna().sum() > 0])

print("\nCategory distribution:")
print(df["category"].value_counts())

print("\nSaved files:")
print(OUTPUT)
print(REPORT)
print(SUMMARY)

print("\nPREPROCESSING COMPLETED")
'''

target = folder / "clean_data.py"
target.write_text(code.strip() + "\n", encoding="utf-8")

print("Created:", target)
print("\nRunning preprocessing...\n")

subprocess.run([sys.executable, str(target)], check=True)
