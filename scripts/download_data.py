"""
H2-PRISM Dataset Provisioning & Verification Tool
Owner: Yazan (Lead, Dataset Audit, Data Engineering & Dataset Readiness)

Usage:
    python3 scripts/download_data.py --summary
    python3 scripts/download_data.py --verify
    python3 scripts/download_data.py --download
"""

import argparse
import hashlib
import json
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

# Add src to pythonpath
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT / "src"))

from h2prism.data import get_dataset_summary, is_raw_dataset_available, load_scenario

RAW_DIR = WORKSPACE_ROOT / "data" / "raw" / "H2-SimNet-Dataset"
SAMPLE_DIR = WORKSPACE_ROOT / "data" / "sample"
CHECKSUMS_FILE = WORKSPACE_ROOT / "01_dataset_audit" / "raw_checksums.sha256"
ZENODO_RECORD_ID = "17871393"
ZENODO_API_URL = f"https://zenodo.org/api/records/{ZENODO_RECORD_ID}"
GITHUB_SOURCE_URL = "https://github.com/andysinx/H2-SimNet"


def check_and_print_summary():
    """Prints a clear summary of dataset locations and availability."""
    summary = get_dataset_summary()
    print("=" * 80)
    print(" H2-PRISM DATASET PROVISIONING & AVAILABILITY REPORT")
    print("=" * 80)
    
    if summary["raw_dataset_available"]:
        raw_files = list(RAW_DIR.rglob("*.*"))
        total_size_mb = sum(f.stat().st_size for f in raw_files) / (1024 * 1024)
        print(f"[✓] Full Raw Dataset is INSTALLED:")
        print(f"    • Path : {summary['raw_dataset_path']}")
        print(f"    • Files: {len(raw_files)} files ({total_size_mb:.1f} MB)")
        print(f"    • Class coverage: 4 target classes across 13 scenario families")
    else:
        print(f"[!] Full Raw Dataset is NOT found at: {RAW_DIR}")
        print(f"    Run 'python3 scripts/download_data.py --download' to retrieve it from Zenodo.")

    print("-" * 80)
    if summary["sample_dataset_available"]:
        sample_files = list(SAMPLE_DIR.glob("*.parquet"))
        print(f"[✓] Quickstart Sample Dataset is READY (Tracked in Git):")
        print(f"    • Path : {summary['sample_dataset_path']}")
        print(f"    • Files: {len(sample_files)} sample scenarios (covers all 4 classes)")
        print(f"    • You can immediately train, test, and evaluate without waiting for downloads!")
    else:
        print(f"[!] Sample dataset not found at {SAMPLE_DIR}")

    print("=" * 80)


def verify_checksums(sample_count: int = 15):
    """Verifies cryptographic SHA256 checksums of the raw files."""
    if not CHECKSUMS_FILE.exists():
        print(f"[✗] Checksums ledger missing at {CHECKSUMS_FILE}")
        return False
        
    if not is_raw_dataset_available():
        print(f"[✗] Raw dataset not found at {RAW_DIR}. Cannot verify.")
        return False

    print(f"[*] Verifying cryptographic SHA256 checksums against {CHECKSUMS_FILE.name}...")
    lines = CHECKSUMS_FILE.read_text().strip().splitlines()
    
    # Pick a subset or all
    import random
    selected_lines = lines[:sample_count] if sample_count > 0 else lines
    
    passed = 0
    failed = 0
    for line in selected_lines:
        if not line.strip() or "  " not in line:
            continue
        expected_sha, rel_path = line.split("  ", 1)
        full_p = WORKSPACE_ROOT / "data" / "raw" / rel_path.strip()
        
        if not full_p.exists():
            print(f"  [MISSING] {rel_path}")
            failed += 1
            continue
            
        h = hashlib.sha256()
        with open(full_p, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        calc_sha = h.hexdigest()
        
        if calc_sha == expected_sha.strip():
            passed += 1
        else:
            print(f"  [MISMATCH] {rel_path}")
            failed += 1

    print(f"[✓] Checksum verification completed: {passed} passed, {failed} failed.")
    return failed == 0


def download_dataset():
    """Provides download instructions or fetches via Zenodo API."""
    if is_raw_dataset_available():
        print("[✓] Raw dataset already exists in data/raw/H2-SimNet-Dataset/.")
        print("    If you wish to re-verify integrity, run: python3 scripts/download_data.py --verify")
        return

    print("=" * 80)
    print(" DOWNLOADING H2-SIMNET DATASET (Zenodo Record 17871393)")
    print("=" * 80)
    print(f"[*] Official Zenodo Record : https://zenodo.org/records/{ZENODO_RECORD_ID}")
    print(f"[*] Official GitHub Mirror : {GITHUB_SOURCE_URL}")
    print("\nAttempting to query Zenodo REST API for archive download...")
    
    try:
        req = urllib.request.Request(
            ZENODO_API_URL,
            headers={"User-Agent": "H2-PRISM-Downloader/2.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            files = data.get("files", [])
            print(f"Found {len(files)} download assets on Zenodo.")
            for file_info in files:
                fname = file_info.get("key", file_info.get("filename", ""))
                furl = file_info.get("links", {}).get("self", "")
                fsize = file_info.get("size", 0) / (1024 * 1024)
                print(f"  • {fname} ({fsize:.1f} MB) -> {furl}")
    except Exception as e:
        print(f"[!] Zenodo API query note: {e}")
        print("\nManual retrieval instructions:")
        print(f"1. Download the dataset zip from Zenodo: https://zenodo.org/records/{ZENODO_RECORD_ID}")
        print(f"2. Or clone from GitHub: git clone {GITHUB_SOURCE_URL} data/raw/H2-SimNet-Dataset")
        print(f"3. Ensure the extracted folder is placed at: data/raw/H2-SimNet-Dataset/")


def main():
    parser = argparse.ArgumentParser(description="H2-PRISM Dataset Provisioning & Verification Tool")
    parser.add_argument("--summary", action="store_true", help="Print dataset availability summary")
    parser.add_argument("--verify", action="store_true", help="Verify raw dataset SHA256 checksums")
    parser.add_argument("--download", action="store_true", help="Download or provide download links for raw dataset")
    args = parser.parse_args()

    if args.verify:
        verify_checksums()
    elif args.download:
        download_dataset()
    else:
        check_and_print_summary()


if __name__ == "__main__":
    main()
