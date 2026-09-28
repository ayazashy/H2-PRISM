from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

DATASET_ROOT = Path("data/raw/H2-SimNet")


# ============================================================
# FILE DISCOVERY
# ============================================================

def discover_files() -> list[Path]:
    files = []

    for pattern in ("*.csv", "*.parquet"):
        files.extend(DATASET_ROOT.rglob(pattern))

    return sorted(files)


# ============================================================
# COLUMN READING
# ============================================================

def read_columns(path: Path) -> list[str]:
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path, nrows=1)

    elif path.suffix.lower() == ".parquet":
        df = pd.read_parquet(path)

    else:
        return []

    return [str(column) for column in df.columns]


# ============================================================
# SENSOR CLASSIFICATION
# ============================================================

def classify_sensor(column: str) -> str | None:
    name = column.upper()

    if name.startswith("PS") and name[2:].isdigit():
        return "pressure"

    if name.startswith("MFS") and name[3:].isdigit():
        return "mass_flow"

    if (
        "TEMP" in name
        or name.startswith("TS")
    ):
        return "temperature"

    return None


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    print("=" * 72)
    print("H2-PRISM — Step 3.1: Actual Sensor Verification")
    print("=" * 72)

    print(f"Dataset root: {DATASET_ROOT}")

    files = discover_files()

    print(f"Dataset files found: {len(files)}")
    print()

    sensor_files: dict[str, set[str]] = defaultdict(set)
    sensor_types: dict[str, str] = {}

    errors = []

    # --------------------------------------------------------
    # Scan every file
    # --------------------------------------------------------

    for index, path in enumerate(files, start=1):

        print(
            f"[{index:3d}/{len(files)}] "
            f"{path.relative_to(DATASET_ROOT)}"
        )

        try:
            columns = read_columns(path)

        except Exception as exc:
            errors.append(
                {
                    "file": str(path),
                    "error": str(exc),
                }
            )
            continue

        for column in columns:

            sensor_type = classify_sensor(column)

            if sensor_type is None:
                continue

            sensor_files[column].add(str(path))
            sensor_types[column] = sensor_type

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    pressure = sorted(
        sensor
        for sensor, sensor_type in sensor_types.items()
        if sensor_type == "pressure"
    )

    mass_flow = sorted(
        sensor
        for sensor, sensor_type in sensor_types.items()
        if sensor_type == "mass_flow"
    )

    temperature = sorted(
        sensor
        for sensor, sensor_type in sensor_types.items()
        if sensor_type == "temperature"
    )

    print()
    print("=" * 72)
    print("ACTUAL SENSOR CONFIGURATION")
    print("=" * 72)

    print()
    print(f"Pressure sensors: {len(pressure)}")

    for sensor in pressure:
        print(
            f"  {sensor:<6} "
            f"{len(sensor_files[sensor]):>3} files"
        )

    print()
    print(f"Mass-flow sensors: {len(mass_flow)}")

    for sensor in mass_flow:
        print(
            f"  {sensor:<6} "
            f"{len(sensor_files[sensor]):>3} files"
        )

    print()
    print(f"Temperature sensors: {len(temperature)}")

    if temperature:
        for sensor in temperature:
            print(
                f"  {sensor:<10} "
                f"{len(sensor_files[sensor]):>3} files"
            )
    else:
        print("  NONE")

    # --------------------------------------------------------
    # Errors
    # --------------------------------------------------------

    print()
    print("=" * 72)
    print("VERIFICATION STATUS")
    print("=" * 72)

    print()

    if errors:
        print(f"Files with errors: {len(errors)}")

        for error in errors:
            print(f"  {error['file']}")
            print(f"    {error['error']}")

    else:
        print("Files with errors: 0")

    print()

    print("Actual sensor families:")
    print(f"  Pressure   : {len(pressure)}")
    print(f"  Mass flow  : {len(mass_flow)}")
    print(f"  Temperature: {len(temperature)}")

    print()

    if pressure == [f"PS{i}" for i in range(1, 13)]:
        print("Pressure configuration: PS1–PS12 CONFIRMED")
    else:
        print("Pressure configuration: REVIEW")

    if mass_flow == [f"MFS{i}" for i in range(1, 5)]:
        print("Mass-flow configuration: MFS1–MFS4 CONFIRMED")
    else:
        print("Mass-flow configuration: REVIEW")

    if not temperature:
        print("Temperature sensors: NOT AVAILABLE")

    print()
    print("=" * 72)
    print("STEP 3.1 COMPLETE")
    print("=" * 72)


if __name__ == "__main__":
    main()