"""Regression test for L22: validation packages must not reuse the figure-system manifest file names.

tests/test_figure_system.py treats every 03_results/**/FIGURE_MANIFEST.csv and TABLE_MANIFEST.csv as a figure-system
manifest. Package-specific QA manifests therefore carry a prefix (Q1_, H1_, AV_, V2_). The renamed Q1 manifest must stay
byte-identical to the original recorded in MANIFEST_RENAME_RECORD.csv.
"""
import hashlib
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESERVED = {"FIGURE_MANIFEST.csv", "TABLE_MANIFEST.csv"}


def test_validation_packages_do_not_use_figure_system_manifest_names():
    hits = [p for d in (ROOT / "03_results").glob("integrated_validation_v*") for p in d.rglob("*") if p.name in RESERVED]
    assert not hits, hits


def test_q1_manifest_rename_preserved_bytes():
    qc = ROOT / "03_results/integrated_validation_v1/publication_q1/quality_control"
    rec = pd.read_csv(qc / "MANIFEST_RENAME_RECORD.csv").iloc[0]
    new = ROOT / rec.new_path
    assert new.exists() and not (ROOT / rec.old_path).exists()
    assert bool(rec.byte_identical) and rec.old_sha256 == rec.new_sha256
    assert hashlib.sha256(new.read_bytes()).hexdigest() == rec.new_sha256
    assert {"figure_id", "png_sha256", "svg_sha256", "qa_status"} <= set(pd.read_csv(new).columns)
