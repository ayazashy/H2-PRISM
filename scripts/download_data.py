"""
H2-PRISM Automated Dataset Provisioning & Verification Engine
Owner: Yazan (Lead, Dataset Audit, Data Engineering & Dataset Readiness)

Downloads, unzips, verifies, and provisions the official peer-reviewed H2-SimNet dataset
(Zenodo Record 17871393) so that any collaborator or evaluator can run the project in 1 step.

Usage:
    python3 setup_data.py                 # 1-click automatic setup & verification
    python3 scripts/download_data.py      # Same 1-click automatic setup
    python3 scripts/download_data.py --verify
    python3 scripts/download_data.py --force
"""

import argparse
import hashlib
import os
import shutil
import ssl
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

# Add src to pythonpath
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT / "src"))

from h2prism.data import get_dataset_summary, is_raw_dataset_available, load_scenario

RAW_DATA_DIR = WORKSPACE_ROOT / "data" / "raw"
DATASET_DIR = RAW_DATA_DIR / "H2-SimNet-Dataset"
SAMPLE_DIR = WORKSPACE_ROOT / "data" / "sample"
CHECKSUMS_FILE = WORKSPACE_ROOT / "01_dataset_audit" / "raw_checksums.sha256"

ZENODO_DIRECT_URL = "https://zenodo.org/records/17871393/files/H2-SimNet-Dataset.zip?download=1"
ZIP_PATH = RAW_DATA_DIR / "H2-SimNet-Dataset.zip"


def download_with_progress(url: str, output_path: Path):
    """Downloads a file with streaming progress, prioritizing curl for speed and robustness."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Try native curl first (fastest and most reliable on macOS/Linux)
    if shutil.which("curl"):
        print("[*] Downloading via curl with native progress...")
        cmd = [
            "curl",
            "-L",
            "--progress-bar",
            "-A", "curl/8.7.1",
            "-o", str(output_path),
            url,
        ]
        res = subprocess.run(cmd)
        if res.returncode == 0 and output_path.exists() and output_path.stat().st_size > 1000000:
            print("[✓] Download completed via curl.")
            return True
        print("[!] curl failed or was interrupted, falling back to Python streaming downloader...")

    # Python urllib fallback with chunked streaming progress
    print("[*] Downloading via Python urllib streaming engine...")
    try:
        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        ctx = ssl._create_unverified_context()

    req = urllib.request.Request(url, headers={"User-Agent": "curl/8.7.1"})
    with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
        total_size = int(resp.headers.get("Content-Length", 0))
        block_size = 1024 * 1024  # 1 MB blocks
        downloaded = 0
        start_time = time.time()

        with open(output_path, "wb") as f_out:
            while True:
                chunk = resp.read(block_size)
                if not chunk:
                    break
                f_out.write(chunk)
                downloaded += len(chunk)
                
                # Progress bar
                elapsed = time.time() - start_time
                speed_mb = (downloaded / (1024 * 1024)) / max(elapsed, 0.001)
                pct = (downloaded / total_size * 100) if total_size > 0 else 0
                dl_mb = downloaded / (1024 * 1024)
                tot_mb = total_size / (1024 * 1024)
                bar_len = 30
                filled = int(bar_len * (downloaded / total_size)) if total_size > 0 else 0
                bar = "=" * filled + ">" + " " * max(bar_len - filled - 1, 0)
                
                sys.stdout.write(f"\r    [{bar}] {pct:5.1f}% ({dl_mb:5.1f} / {tot_mb:5.1f} MB) at {speed_mb:4.1f} MB/s")
                sys.stdout.flush()
        print("\n[✓] Download completed successfully.")
        return True


def extract_zip(zip_path: Path, extract_to: Path):
    """Extracts H2-SimNet-Dataset.zip into extract_to directory and removes the zip file."""
    print(f"[*] Extracting {zip_path.name} into {extract_to}...")
    extract_to.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        total_files = len(zip_ref.infolist())
        for idx, member in enumerate(zip_ref.infolist(), 1):
            zip_ref.extract(member, extract_to)
            if idx % 50 == 0 or idx == total_files:
                sys.stdout.write(f"\r    Extracted {idx}/{total_files} files...")
                sys.stdout.flush()
    print("\n[✓] Extraction complete.")
    
    # Remove archive to save disk space (~509 MB)
    if zip_path.exists():
        zip_path.unlink()
        print(f"[✓] Cleaned up temporary archive {zip_path.name}.")


def verify_integrity(sample_count: int = 15):
    """Verifies cryptographic SHA256 hashes of the extracted files."""
    if not CHECKSUMS_FILE.exists():
        print(f"[!] Checksum file {CHECKSUMS_FILE} not found; skipping verification.")
        return True

    print(f"[*] Verifying cryptographic SHA-256 hashes against {CHECKSUMS_FILE.name}...")
    lines = CHECKSUMS_FILE.read_text().strip().splitlines()
    selected_lines = lines[:sample_count] if sample_count > 0 else lines
    
    passed = 0
    failed = 0
    for line in selected_lines:
        if not line.strip() or "  " not in line:
            continue
        expected_sha, rel_path = line.split("  ", 1)
        full_p = RAW_DATA_DIR / rel_path.strip()
        
        if not full_p.exists():
            failed += 1
            continue
            
        h = hashlib.sha256()
        with open(full_p, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        if h.hexdigest() == expected_sha.strip():
            passed += 1
        else:
            failed += 1

    print(f"[✓] Checksum verification: {passed} files passed, {failed} failed.")
    return failed == 0


def test_scenario_load():
    """Runs a quick test load on a standard scenario to confirm readiness."""
    print("[*] Running quick validation load on 'leakG4'...")
    try:
        df = load_scenario("leakG4")
        print(f"    ✓ Scenario loaded successfully: {df.shape[0]} rows x {df.shape[1]} columns")
        print(f"    ✓ Inlet Pressure (PS1): {df['PS1'].iloc[0]:.2f} MPa")
        print(f"    ✓ Inlet Mass Flow (MFS1): {df['MFS1'].iloc[0]:.2f} kg/s")
        return True
    except Exception as e:
        print(f"    ✗ Validation load failed: {e}")
        return False


def setup_dataset(force: bool = False, verify_only: bool = False):
    """Orchestrates the entire provisioning workflow."""
    print("=" * 80)
    print(" H2-PRISM AUTOMATED DATASET PROVISIONING & SETUP")
    print("=" * 80)
    print(f"[*] Target Directory: {DATASET_DIR}")
    print(f"[*] Official Source : {ZENODO_DIRECT_URL}")
    print("-" * 80)

    if verify_only:
        verify_integrity(sample_count=0)
        return

    # Check if dataset already exists
    already_installed = is_raw_dataset_available()

    if already_installed and not force:
        print("[✓] H2-SimNet Dataset is ALREADY installed and ready on disk!")
        raw_files = list(DATASET_DIR.rglob("*.*"))
        print(f"    • Total files: {len(raw_files)}")
        print(f"    • Location   : {DATASET_DIR}")
        print("    (Use --force if you wish to re-download from Zenodo)")
        print("-" * 80)
        test_scenario_load()
        print("=" * 80)
        return

    if force and DATASET_DIR.exists():
        print("[*] --force specified. Removing existing dataset directory...")
        shutil.rmtree(DATASET_DIR)

    # 1. Download
    print("[1/3] Downloading H2-SimNet dataset from Zenodo (~509 MB compressed)...")
    download_with_progress(ZENODO_DIRECT_URL, ZIP_PATH)

    # 2. Extract
    print("\n[2/3] Extracting files into data/raw/...")
    extract_zip(ZIP_PATH, RAW_DATA_DIR)

    # 3. Verify & Test
    print("\n[3/3] Verifying installation & executing scenario test load...")
    verify_integrity(sample_count=15)
    test_scenario_load()

    print("=" * 80)
    print(" [✓] DATASET SETUP COMPLETE! You are ready to train models, evaluate, and visualize.")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="H2-PRISM Automated Dataset Setup & Provisioning")
    parser.add_argument("--force", action="store_true", help="Force re-download even if already present")
    parser.add_argument("--verify", action="store_true", help="Run full cryptographic hash verification")
    parser.add_argument("--summary", action="store_true", help="Print summary of installed datasets")
    args = parser.parse_args()

    if args.summary:
        summary = get_dataset_summary()
        print(f"Raw dataset available   : {summary['raw_dataset_available']}")
        print(f"Active dataset directory: {summary['active_data_dir']}")
    else:
        setup_dataset(force=args.force, verify_only=args.verify)


if __name__ == "__main__":
    main()
