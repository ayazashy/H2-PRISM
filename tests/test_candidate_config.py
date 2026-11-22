"""Validation of the Phase-6 candidate evaluation configuration (structure, hashes, constructibility).
Reads only saved artifacts; trains nothing."""

import hashlib
from pathlib import Path

import pandas as pd
import pytest
import yaml

from h2prism.distinguishability import ALL_FLAGS, DConfig
from h2prism.feature_table import REALIZATION_COLUMNS
from h2prism.features import FEATURE_FUNCTIONS
from h2prism.policy import PolicyConfig
from h2prism.windows import WindowConfig

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "06_audit_preparation" / "phase6_resolution" / "CANDIDATE_EVALUATION_CONFIG.yaml"
pytestmark = pytest.mark.skipif(not CFG.exists(), reason="candidate config not present")


@pytest.fixture(scope="module")
def cfg():
    return yaml.safe_load(CFG.read_text(encoding="utf-8"))


def _walk(d, out):
    if isinstance(d, dict):
        if "decision" in d:
            out.append(d)
        for v in d.values():
            _walk(v, out)
    elif isinstance(d, list):
        for v in d:
            _walk(v, out)
    return out


def test_never_marked_frozen_or_approved(cfg):
    assert cfg["status"] == "PROVISIONALLY_SELECTED" and cfg["signoff"] == "PENDING_HUMAN_SIGNOFF"
    blocks = _walk(cfg, [])
    assert len(blocks) >= 15 and all(b.get("signoff") == "PENDING_HUMAN_SIGNOFF" for b in blocks)
    assert "FROZEN" not in CFG.read_text(encoding="utf-8").replace("NOT FROZEN", "").replace("frozen_evaluation_config", "")


def test_pinned_artifact_hashes_match(cfg):
    for item in (cfg["dataset"]["manifest"], cfg["dataset"]["label_mapping"], cfg["splits"]["outer"],
                 cfg["splits"]["inner"], cfg["features"]["register"]):
        assert hashlib.sha256((ROOT / item["file"]).read_bytes()).hexdigest() == item["sha256"], item["file"]


def test_objects_constructible_from_config(cfg):
    w = cfg["windows"]
    WindowConfig(w["window_s"], w["stride_s"], w["min_samples"], w["label_mode"], w["pre_event_policy"])
    d = {k: v for k, v in cfg["distinguishability"].items() if k in DConfig.__dataclass_fields__}
    DConfig(**d)
    p = cfg["policy"]
    PolicyConfig(config_id="candidate", tau_accept=0.5, ambiguity_mass=p["ambiguity_mass"], max_set_size=p["max_set_size"],
                 singleton_handling=p["singleton_handling"], threshold_source=cfg["thresholds"]["source"],
                 unresolved_flags=tuple(p["unresolved_flags"]), specific_blocking_flags=tuple(p["specific_blocking_flags"]))
    assert set(p["unresolved_flags"]) | set(p["specific_blocking_flags"]) <= set(ALL_FLAGS)
    assert set(cfg["features"]["statistics"]) <= set(FEATURE_FUNCTIONS)
    assert cfg["dataset"]["realization"]["value"] in REALIZATION_COLUMNS
    assert cfg["dataset"]["realization"]["pooling"] == "forbidden"


def test_manifest_v02_consistent_with_config(cfg):
    m = pd.read_csv(ROOT / cfg["dataset"]["manifest"]["file"])
    assert set(m.status) == {"PROVISIONALLY_SELECTED_PENDING_YAZAN_SIGNOFF"}
    assert cfg["dataset"]["family_column"]["value"] in m.columns
    el = m[m.eligible_primary]
    assert set(el.label_mapped) == set(cfg["dataset"]["classes"])
    assert len(el) == 51 and el.Scenario_Family_ID.nunique() == 39
    assert (m.loc[~m.eligible_primary, "exclusion_reason"].str.len() > 0).all()
    assert el.groupby("Scenario_Family_ID").topology.nunique().max() == 1  # families nest in topology
    folds = pd.read_csv(ROOT / cfg["splits"]["outer"]["file"])
    assert set(folds.Scenario_ID) == set(el.Scenario_ID)
