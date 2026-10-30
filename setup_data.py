#!/usr/bin/env python3
"""
H2-PRISM — 1-Click Dataset Setup & Provisioning
Run this script to automatically download, unpack, and verify the official H2-SimNet dataset:

    python3 setup_data.py

Source:
    https://zenodo.org/records/17871393/files/H2-SimNet-Dataset.zip?download=1
"""

import sys
from pathlib import Path

# Add scripts directory to path and invoke setup
scripts_dir = Path(__file__).resolve().parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from download_data import setup_dataset

if __name__ == "__main__":
    force_download = "--force" in sys.argv
    verify_only = "--verify" in sys.argv
    setup_dataset(force=force_download, verify_only=verify_only)
