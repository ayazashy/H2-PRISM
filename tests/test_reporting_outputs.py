"""Fixture-based tests for A13 reporting tools. All values below are ILLUSTRATIVE FIXTURES."""

import sys
from pathlib import Path

import pandas as pd
import pytest
pytestmark = pytest.mark.slow   # X22: > ~10 s per test (durations profile 2026-11-13); runs in the full CI job
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
    # a YAML evidence_status never publishes: without a scoped approval record the table stays preliminary
    assert not (tmp_path / "tab" / "final").exists()
    out = pd.read_csv(tmp_path / "tab" / "preliminary" / "t1.csv")
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
    assert set(m1["output_file"].str[-4:]) == {".png", ".pdf", ".svg"}


def test_builders_consume_real_runner_outputs_and_quarantine_synthetic(tmp_path):
    """Integration: A13 builders read the runner's actual output schema (synthetic run -> illustrative only)."""
    import shutil
    from h2prism.experiments import primary_protocol as pp
    from h2prism.experiments.synthetic_protocol_fixture import make_fixture
    fx = make_fixture(tmp_path / "fx")
    pp.run(fx["config"], fx["root"], fx["raw"], tmp_path / "run", "synthetic")
    dst = tmp_path / "03_results" / "primary_protocol" / "PRIMARY"
    dst.mkdir(parents=True)
    for f in list((tmp_path / "run").glob("*.csv")) + list((tmp_path / "run").glob("*.parquet")) + [tmp_path / "run" / "run_manifest.json"]:
        shutil.copy(f, dst / f.name)
    import derive_decision_tables as ddt
    ddt.write(dst, tmp_path / "03_results" / "derived" / "PRIMARY")
    pp.run(fx["config"], fx["root"], fx["raw"], tmp_path / "03_results" / "primary_protocol" / "SENSITIVITY_k_10", "synthetic", sensitivity="k_10")
    import build_sensitivity_summary as bss
    runs = tmp_path / "03_results" / "primary_protocol"
    assert bss.main(["--runs", str(runs), "--out", str(runs / "SENSITIVITY_SUMMARY"), "--allow-synthetic"]) == 0
    cfg = ROOT / "configs" / "reporting_figures.yaml"
    fm = brf.build(cfg, tmp_path / "out_fig", tmp_path)
    tm = brt.build(cfg, tmp_path / "out_tab", tmp_path)
    assert set(fm.status) == {"BUILT_ILLUSTRATIVE"} and set(tm.status) == {"BUILT_ILLUSTRATIVE"}
    assert set(fm.figure_id) == {f["id"] for f in yaml.safe_load(cfg.read_text(encoding="utf-8"))["figures"]}
    assert not (tmp_path / "out_fig" / "final").exists() and not (tmp_path / "out_tab" / "final").exists()
    t = pd.read_csv(tmp_path / "out_tab" / "illustrative" / "T4_matched_coverage.csv")
    assert "target_coverage" in t.columns and set(t.method) >= {"s_C", "s_C_minus_D"}


def test_reporting_config_inputs_missing_before_execution(tmp_path):
    cfg = ROOT / "configs" / "reporting_figures.yaml"
    with pytest.raises(ReportingInputError, match="mandatory input missing"):  # a root without any recorded run
        brt.build(cfg, tmp_path / "o", tmp_path)
