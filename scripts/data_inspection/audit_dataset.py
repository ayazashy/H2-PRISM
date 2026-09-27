"""
Forensic Dataset Audit Script (Ahmed Plan Day 1 / Materials Lead).
Scans data/raw/H2-SimNet/ and outputs:
- AUDIT.md
- results/data_audit.csv
- results/dataset_truth_table.md
"""

from pathlib import Path
import sys
import pandas as pd


def audit_raw_dataset(raw_dir: Path = Path("data/raw/H2-SimNet")):
    print(f"Scanning raw dataset in: {raw_dir}")
    if not raw_dir.exists():
        print(f"Directory {raw_dir} does not exist yet. Please place downloaded files there.")
        return

    files = list(raw_dir.glob("*.*"))
    print(f"Found {len(files)} files.")
    # Audit logic to be executed when raw dataset files are present.


if __name__ == "__main__":
    audit_raw_dataset()
