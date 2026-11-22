"""Phase 7: final protocol configuration (structure, hashes, consistency). Trains nothing."""

import hashlib
from pathlib import Path

import pandas as pd
import pytest
import yaml

from h2prism.distinguishability import ALL_FLAGS, DConfig
from h2prism.features import FEATURE_FUNCTIONS
from h2prism.policy import PolicyConfig
from h2prism.windows import WindowConfig

ROOT = Path(__file__).resolve().parents[1]
F = ROOT / "06_audit_preparation" / "FINAL_EXPERIMENT_CONFIG.yaml"
C = ROOT / "06_audit_preparation" / "phase6_resolution" / "CANDIDATE_EVALUATION_CONFIG.yaml"
pytestmark = pytest.mark.skipif(not F.exists(), reason="final config absent")


@pytest.fixture(scope="module")
def cfg():
    return yaml.safe_load(F.read_text(encoding="utf-8"))


def test_status_and_no_fabricated_signoffs(cfg):
    assert cfg["status"] == "PROTOCOL_SELECTED_PENDING_EXECUTION"
    assert set(cfg["owner_signoffs"].values()) == {"NOT_RECORDED"}
    assert "PENDING_HUMAN_SIGNOFF" not in F.read_text(encoding="utf-8")  # no unresolved placeholders


def test_hashes(cfg):
    assert hashlib.sha256(C.read_bytes()).hexdigest() == cfg["derived_from"]["sha256"]
    for item in (cfg["dataset"]["manifest"], cfg["dataset"]["label_mapping"], cfg["splits"]["outer"],
                 cfg["splits"]["inner"], cfg["features"]["register"]):
        assert hashlib.sha256((ROOT / item["file"]).read_bytes()).hexdigest() == item["sha256"]


def test_matches_candidate_values_and_keeps_safeguard(cfg):
    cand = yaml.safe_load(C.read_text(encoding="utf-8"))
    for k in ("window_s", "stride_s", "min_samples", "pre_event_policy"):
        assert cfg["windows"][k] == cand["windows"][k]
    for k in ("k", "weighting", "prior_correction", "min_top_class_families"):
        assert cfg["distinguishability"][k] == cand["distinguishability"][k]
    assert cfg["thresholds"]["target_coverage_primary"] == cand["thresholds"]["target_coverage_primary"] == 0.80
    assert "TOP_CLASS_FEW_INDEPENDENT_RUNS" in cfg["policy_primary"]["specific_blocking_flags"]
    assert "TOP_CLASS_FEW_INDEPENDENT_RUNS" not in cfg["policy_sensitivity_warning_only"]["same_as_primary_except"]["specific_blocking_flags"]
    assert cfg["thresholds"]["source"] == "development" and "not_estimable" in cfg["evaluation"]["outcomes_accepted"]


def test_objects_and_manifest_consistency(cfg):
    w = cfg["windows"]
    WindowConfig(w["window_s"], w["stride_s"], w["min_samples"], w["label_mode"], w["pre_event_policy"])
    DConfig(**{k: v for k, v in cfg["distinguishability"].items() if k in DConfig.__dataclass_fields__})
    p = cfg["policy_primary"]
    PolicyConfig("final", 0.5, p["ambiguity_mass"], p["max_set_size"], p["singleton_handling"], cfg["thresholds"]["source"],
                 unresolved_flags=tuple(p["unresolved_flags"]), specific_blocking_flags=tuple(p["specific_blocking_flags"]))
    assert set(p["unresolved_flags"]) | set(p["specific_blocking_flags"]) <= set(ALL_FLAGS)
    assert set(cfg["features"]["statistics"]) <= set(FEATURE_FUNCTIONS)
    m = pd.read_csv(ROOT / cfg["dataset"]["manifest"]["file"])
    assert int(m.eligible_primary.sum()) == cfg["dataset"]["eligible_runs"] == 51
    folds = pd.read_csv(ROOT / cfg["splits"]["outer"]["file"])
    assert set(folds.Scenario_ID) == set(m.loc[m.eligible_primary, "Scenario_ID"])
