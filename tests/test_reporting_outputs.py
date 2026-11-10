"""Fixture-based tests for A13 reporting tools. All values below are ILLUSTRATIVE FIXTURES."""

import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "reporting"))
import build_research_figures as brf  # noqa: E402
import build_research_tables as brt  # noqa: E402
from _common import ReportingInputError  # noqa: E402


def _fixture(tmp, status_col=True):
    df = pd.DataFrame({"method": ["B", "B", "C", "C"], "coverage": [0.5, 1.0, 0.5, 1.0],
                       "selective_risk": [0.1, 0.2, 0.08, 0.2]})
    if status_col:
        df["data_status"] = "FIXTURE"
    (tmp / "res").mkdir(exist_ok=True)
    df.to_csv(tmp / "res" / "rc.csv", index=False)
    return df


def _cfg(tmp, evidence="VALIDATED", inp="res/rc.csv", **extra):
    cfg = {"dpi": 50, "fail_on_missing": True,
           "figures": [{"id": "f1", "kind": "risk_coverage", "input": inp, "evidence_status": evidence,
                        "source_experiment": "TEST", "caption": "fixture"}],
           "tables": [{"id": "t1", "input": inp, "columns": ["method", "coverage", "selective_risk"],
                       "evidence_status": evidence}]}
    cfg.update(extra)
    p = tmp / "cfg.yaml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return p


def test_fixture_data_never_routed_to_final(tmp_path):
    _fixture(tmp_path)
    man = brf.build(_cfg(tmp_path, "VALIDATED"), tmp_path / "out", tmp_path)
    assert set(man["status"]) == {"BUILT_ILLUSTRATIVE"}
    assert not (tmp_path / "out" / "final").exists()
    tman = brt.build(_cfg(tmp_path, "VALIDATED"), tmp_path / "tab", tmp_path)
    assert set(tman["status"]) == {"BUILT_ILLUSTRATIVE"}
    assert "ILLUSTRATIVE" in (tmp_path / "tab" / "illustrative" / "t1.md").read_text(encoding="utf-8")


def test_unvalidated_inputs_go_to_preliminary(tmp_path):
    _fixture(tmp_path, status_col=False)
    man = brf.build(_cfg(tmp_path, "PENDING"), tmp_path / "out", tmp_path)
    assert set(man["status"]) == {"BUILT_PRELIMINARY"}


def test_values_preserved_in_tables(tmp_path):
    df = _fixture(tmp_path, status_col=False)
    brt.build(_cfg(tmp_path, "FROZEN"), tmp_path / "tab", tmp_path)
    out = pd.read_csv(tmp_path / "tab" / "final" / "t1.csv")
    pd.testing.assert_frame_equal(out, df[["method", "coverage", "selective_risk"]])


def test_missing_evidence_fails_clearly(tmp_path):
    with pytest.raises(ReportingInputError, match="mandatory input missing"):
        brf.build(_cfg(tmp_path, inp="res/absent.csv"), tmp_path / "out", tmp_path)
    man = pd.read_csv(tmp_path / "out" / "FIGURE_BUILD_MANIFEST.csv")
    assert set(man["status"]) == {"NOT_BUILT_MISSING_EVIDENCE"}


def test_risk_without_coverage_rejected(tmp_path):
    (tmp_path / "res").mkdir()
    pd.DataFrame({"method": ["B"], "selective_risk": [0.1]}).to_csv(tmp_path / "res" / "rc.csv", index=False)
    with pytest.raises(ReportingInputError):
        brt.build(_cfg(tmp_path), tmp_path / "tab", tmp_path)


def test_figure_determinism_and_manifest_provenance(tmp_path):
    _fixture(tmp_path, status_col=False)
    m1 = brf.build(_cfg(tmp_path, "FROZEN"), tmp_path / "o1", tmp_path)
    m2 = brf.build(_cfg(tmp_path, "FROZEN"), tmp_path / "o2", tmp_path)
    assert m1["output_sha256"].tolist() == m2["output_sha256"].tolist()
    assert m1["input_sha256"].notna().all() and m1["config_sha256"].notna().all()
    assert set(m1["output_file"].str[-4:]) == {".png", ".svg"}
