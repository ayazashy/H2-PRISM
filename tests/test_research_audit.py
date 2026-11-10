"""Fixture-based tests for the A12 read-only validators (tools/research_audit)."""

import hashlib
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "research_audit"))
import build_provenance_index as bpi  # noqa: E402
import validate_artifacts as va  # noqa: E402


def _write_spec(tmp, artifacts, extra=None):
    spec = {"artifacts": artifacts, **(extra or {})}
    p = tmp / "spec.yaml"
    p.write_text(yaml.safe_dump(spec), encoding="utf-8")
    return p


def _snapshot(d: Path):
    return {p: p.read_bytes() for p in d.rglob("*") if p.is_file()}


def test_correct_manifest_passes_and_inputs_untouched(tmp_path):
    (tmp_path / "data").mkdir()
    pd.DataFrame({"file": ["a", "b"], "Scenario_ID": ["S1", "S2"]}).to_csv(tmp_path / "data/m.csv", index=False)
    before = _snapshot(tmp_path / "data")
    spec = _write_spec(tmp_path, [{"path": "data/m.csv", "required_columns": ["file", "Scenario_ID"],
                                   "unique_key": "file", "non_null": ["Scenario_ID"]}])
    df = va.run(spec, tmp_path / "out", tmp_path)
    assert set(df["outcome"]) == {"PASS"}
    assert _snapshot(tmp_path / "data") == before


def test_missing_columns_duplicates_absent_and_hash(tmp_path):
    pd.DataFrame({"file": ["a", "a"], "status": ["VERIFIED", "COMPLETED"]}).to_csv(tmp_path / "m.csv", index=False)
    spec = _write_spec(tmp_path, [
        {"path": "m.csv", "required_columns": ["file", "Scenario_ID"], "unique_key": "file",
         "status_column": "status", "sha256": "0" * 64},
        {"path": "absent.csv"},
    ])
    df = va.run(spec, tmp_path / "out", tmp_path)
    outcomes = df.groupby("rule")["outcome"].first().to_dict()
    assert "FAIL" == outcomes["required_columns[spec]"]
    assert "FAIL" == outcomes["unique_key['file']"]
    assert "HASH_MISMATCH" == outcomes["sha256"]
    assert "UNSUPPORTED_STATUS" == outcomes["status_vocabulary[status]"]
    assert "MISSING_ARTIFACT" in set(df["outcome"])  # missing evidence distinct from FAIL
    assert (tmp_path / "out" / "ARTIFACT_VALIDATION_SUMMARY.md").exists()


def test_checksum_reconciliation(tmp_path):
    (tmp_path / "s").mkdir()
    (tmp_path / "s" / "x.parquet").write_bytes(b"abc")
    (tmp_path / "s" / "y.parquet").write_bytes(b"changed")
    h = hashlib.sha256(b"abc").hexdigest()
    h2 = hashlib.sha256(b"original").hexdigest()
    (tmp_path / "sums.sha256").write_text(f"{h}  raw/x.parquet\n{h2}  raw/y.parquet\n", encoding="utf-8")
    rows = pd.DataFrame(va.reconcile_checksums(tmp_path, "sums.sha256", "s/*.parquet")).set_index("artifact")
    assert rows.loc["s/x.parquet", "outcome"] == "PASS"
    assert rows.loc["s/y.parquet", "outcome"] == "FAIL"


def test_refuses_output_dir_containing_inputs(tmp_path):
    (tmp_path / "out").mkdir()
    pd.DataFrame({"a": [1]}).to_csv(tmp_path / "out" / "m.csv", index=False)
    spec = _write_spec(tmp_path, [{"path": "out/m.csv"}])
    with pytest.raises(SystemExit):
        va.run(spec, tmp_path / "out", tmp_path)


def test_provenance_index_never_backfills(tmp_path):
    (tmp_path / "r").mkdir()
    (tmp_path / "r" / "a.csv").write_text("x\n1\n", encoding="utf-8")
    (tmp_path / "r" / "b.csv").write_text("x\n2\n", encoding="utf-8")
    (tmp_path / "r" / "b.csv.provenance.json").write_text('{"seed": 7, "script": "run.py"}', encoding="utf-8")
    idx = bpi.build_index(tmp_path, ["r", "missing_dir"]).set_index("output_file")
    assert idx.loc["r/a.csv", "seed"] == "UNKNOWN" and idx.loc["r/a.csv", "config_hash"] == "UNKNOWN"
    assert idx.loc["r/b.csv", "seed"] == 7 and idx.loc["r/b.csv", "script"] == "run.py"
    assert idx.loc["missing_dir", "sha256"] == "MISSING"
    assert "r/b.csv.provenance.json" not in idx.index


def test_deterministic(tmp_path):
    pd.DataFrame({"file": ["a"]}).to_csv(tmp_path / "m.csv", index=False)
    spec = _write_spec(tmp_path, [{"path": "m.csv", "unique_key": "file"}])
    a = va.run(spec, tmp_path / "o1", tmp_path)
    b = va.run(spec, tmp_path / "o2", tmp_path)
    assert a.equals(b)
