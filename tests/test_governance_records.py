"""Directive records: referential integrity of register, matrix and status records; baseline register untouched."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "governance"))


def test_status_records_pass_integrity_checks():
    import build_execution_status as b
    assert b.main() == 0


def test_baseline_register_and_matrix_unchanged_since_ff11c87():
    for f in ("00_governance/MASTER_ISSUE_REGISTER.csv", "00_governance/EXECUTION_DEPENDENCY_MATRIX.csv"):
        r = subprocess.run(["git", "diff", "--quiet", "ff11c87", "--", f], cwd=ROOT)
        assert r.returncode == 0, f"{f} differs from the baseline"
