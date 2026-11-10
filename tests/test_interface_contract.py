"""configs/interface_contracts.yaml v2 must describe exactly what the implemented pipeline reads and writes."""

import json
import re
from pathlib import Path

import pandas as pd
import pytest
import yaml

from h2prism import features as F
from h2prism.experiments import primary_protocol as pp
from h2prism.experiments.synthetic_protocol_fixture import make_fixture
from h2prism.feature_table import build_feature_table, normalize_manifest_columns
from h2prism.windows import WindowConfig

ROOT = Path(__file__).resolve().parents[1]
C = yaml.safe_load((ROOT / "configs" / "interface_contracts.yaml").read_text(encoding="utf-8"))["contracts"]
FINAL = yaml.safe_load((ROOT / "06_audit_preparation" / "FINAL_EXPERIMENT_CONFIG.yaml").read_text(encoding="utf-8"))


def _names(cols):
    return [c["name"] if isinstance(c, dict) else c for c in cols]


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    d = tmp_path_factory.mktemp("contract")
    fx = make_fixture(d / "fx")
    pp.run(fx["config"], fx["root"], fx["raw"], d / "out", "synthetic")
    return fx, d / "out"


def test_manifest_v02_satisfies_contract():
    m = pd.read_csv(ROOT / C["manifest_schema"]["file"])
    req = _names(C["manifest_schema"]["required_columns"])
    assert set(req) <= set(m.columns)
    assert m.Scenario_ID.is_unique and m.eligible_primary.dtype == bool
    el = m[m.eligible_primary]
    assert set(el.label_mapped) == set(C["manifest_schema"]["required_columns"][3]["enum_when_eligible"])
    assert (m.loc[~m.eligible_primary, "exclusion_reason"].fillna("").str.len() > 0).all()
    assert C["manifest_schema"]["file"] == FINAL["dataset"]["manifest"]["file"]
    normalize_manifest_columns(m)  # internal aliasing documented in the contract works


def test_window_manifest_and_feature_table_match_contract(run):
    fx, _ = run
    cfg = yaml.safe_load(fx["config"].read_text())
    w = cfg["windows"]
    out = build_feature_table(normalize_manifest_columns(pd.read_csv(fx["manifest"])), fx["raw"], "noise_added",
                              cfg["dataset"]["family_column"],
                              WindowConfig(w["window_s"], w["stride_s"], w["min_samples"], w["label_mode"], w["pre_event_policy"]),
                              cfg["features"]["statistics"])
    wm = out["window_manifest"]
    assert list(wm.columns) == _names(C["window_manifest_schema"]["required_columns"])
    assert set(wm.boundary_status) <= set(C["window_manifest_schema"]["required_columns"][13]["enum"])
    assert wm.window_id.is_unique and all(re.fullmatch(r".+_w\d{4}", x) for x in wm.window_id)
    ft = out["features"]
    meta = [c for c in ft.columns if "__" not in c]
    assert meta == C["feature_table_schema"]["metadata_columns"]
    pat = re.compile(C["feature_table_schema"]["feature_name_pattern"])
    feats = [c for c in ft.columns if "__" in c]
    assert all(pat.fullmatch(c) for c in feats) and len(feats) == C["feature_table_schema"]["n_features"]


def test_metadata_and_provenance_columns_can_never_be_features():
    for col in C["feature_table_schema"]["metadata_columns"] + C["feature_table_schema"]["runner_added_metadata"]:
        assert col in F.METADATA_COLUMNS, col
        with pytest.raises(ValueError):
            F.assert_no_metadata_features([col])
    df = pd.DataFrame({c: [0] for c in F.METADATA_COLUMNS} | {"PS1__mean": [1.0]})
    assert F.model_feature_columns(df) == ["PS1__mean"]


def test_runner_outputs_match_contract(run):
    _, out = run
    pred = pd.read_csv(out / "folds" / "fold_1" / "predictions.csv")
    classes = ["NORMAL", "LEAK", "COMPRESSOR_FAULT", "COMPRESSOR_DELAY"]
    req = [c for c in C["prediction_table_schema"]["required_columns"] if "<class>" not in c]
    req += [f"p_raw_{c}" for c in classes] + [f"p_cal_{c}" for c in classes]
    assert set(req) == set(pred.columns)
    idx = json.loads((out / "folds" / "fold_1" / "decision_index.json").read_text())
    f = next(r["decisions_file"] for r in idx if r["status"] == "ESTIMABLE")
    dec = pd.read_csv(out / "folds" / "fold_1" / f)
    assert list(dec.columns) == C["decision_table_schema"]["required_columns"]
    agg = C["aggregate_outputs"]
    for name in ("coverage_risk.csv", "estimability.csv", "rq1.csv", "rq2.csv", "tie_sensitivity.csv"):
        assert set(pd.read_csv(out / name).columns) == set(agg[name]), name
    th = pd.read_csv(out / "folds" / "fold_1" / "thresholds.csv")
    assert set(th.columns) == set(agg["thresholds.csv (per fold)"])
    man = json.loads((out / "run_manifest.json").read_text())
    assert set(agg["run_manifest.json"]) <= set(man)
    assert man["artifact_class"] in agg["artifact_class_enum"]
    assert {"manifest", "outer_folds"} <= set(man["input_sha256"])  # config.provenance.required: manifest/folds hashes
    for name in ("estimability.csv", "rq1.csv"):
        assert set(pd.read_csv(out / name).status) <= set(agg["status_enum"])


def test_contract_version_and_config_compatibility():
    meta = yaml.safe_load((ROOT / "configs" / "interface_contracts.yaml").read_text(encoding="utf-8"))["metadata"]
    assert meta["version"] == "2.0.0" and meta["owner_acceptance"] == "NOT_RECORDED"
    assert FINAL["version"].startswith("final-protocol-1.1") and "matched_coverage" in FINAL["thresholds"]
