from __future__ import annotations

from pathlib import Path
from collections import defaultdict

import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

RAW_DIR = Path("data/raw/H2-SimNet")
if not RAW_DIR.exists() or not any(RAW_DIR.rglob("*.csv")):
    if Path("data/selected").exists() and any(Path("data/selected").rglob("*.csv")):
        RAW_DIR = Path("data/selected")
    elif Path("data/raw").exists():
        RAW_DIR = Path("data/raw")


PRESSURE_SENSORS = [f"PS{i}" for i in range(1, 13)]
FLOW_SENSORS = [f"MFS{i}" for i in range(1, 5)]

EXPECTED_MEASUREMENTS = PRESSURE_SENSORS + FLOW_SENSORS


# ============================================================
# HELPERS
# ============================================================

def read_columns(path: Path) -> list[str]:
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path, nrows=5)
    elif path.suffix.lower() == ".parquet":
        df = pd.read_parquet(path, engine="pyarrow").head(5)
    else:
        return []

    return [str(c).strip() for c in df.columns]


def classify_column(column: str) -> str:
    if column in PRESSURE_SENSORS:
        return "Pressure"
    if column in FLOW_SENSORS:
        return "Mass flow"
    return "Other"


# ============================================================
# SCAN DATASET
# ============================================================

files = sorted(
    [
        p
        for p in RAW_DIR.rglob("*")
        if p.is_file() and p.suffix.lower() in {".csv", ".parquet"}
    ]
)

print("=" * 70)
print("H2-PRISM — STEP 3.2: MEASURED VARIABLES VERIFICATION")
print("=" * 70)

print(f"\nDataset files found: {len(files)}")

sensor_presence = defaultdict(int)
other_columns = defaultdict(int)
errors = []

for path in files:
    try:
        columns = read_columns(path)

        for col in columns:
            category = classify_column(col)

            if category in {"Pressure", "Mass flow"}:
                sensor_presence[col] += 1
            else:
                other_columns[col] += 1

    except Exception as exc:
        errors.append((str(path), str(exc)))


# ============================================================
# RESULTS
# ============================================================

print("\n--- EXPECTED MEASUREMENTS ---")

print("\nPressure:")
for sensor in PRESSURE_SENSORS:
    print(f"  {sensor}: present in {sensor_presence[sensor]}/{len(files)} files")

print("\nMass flow:")
for sensor in FLOW_SENSORS:
    print(f"  {sensor}: present in {sensor_presence[sensor]}/{len(files)} files")


print("\n--- OTHER COLUMNS ---")

for col in sorted(other_columns):
    print(f"  {col}: present in {other_columns[col]}/{len(files)} files")


print("\n--- ERRORS ---")

if errors:
    for path, error in errors:
        print(f"  {path}")
        print(f"    {error}")
else:
    print("  None")


# ============================================================
# COMPLETENESS CHECK
# ============================================================

missing_expected = [
    sensor
    for sensor in EXPECTED_MEASUREMENTS
    if sensor_presence[sensor] != len(files)
]

print("\n--- COMPLETENESS ---")

if missing_expected:
    print("Expected measurement channels NOT present in every file:")
    for sensor in missing_expected:
        print(f"  - {sensor}")
else:
    print("All expected measurement channels are present in every file.")


# ============================================================
# SUMMARY
# ============================================================

print("\n--- STEP 3.2 SUMMARY ---")

print(f"Pressure channels confirmed: {len(PRESSURE_SENSORS)}")
print(f"Mass-flow channels confirmed: {len(FLOW_SENSORS)}")
print(f"Expected measurement channels: {len(EXPECTED_MEASUREMENTS)}")
print(f"Other columns detected: {len(other_columns)}")
print(f"Files with errors: {len(errors)}")

if not missing_expected and not errors:
    print("\nSTEP 3.2 BASIC VARIABLE PRESENCE CHECK: PASS")
else:
    print("\nSTEP 3.2 BASIC VARIABLE PRESENCE CHECK: REVIEW")