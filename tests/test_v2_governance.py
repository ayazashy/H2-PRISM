"""Governance invariants for the Distinguishability v2 research phase: nothing frozen changes, nothing is runnable."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import yaml

from h2prism.experiments import primary_protocol as pp

REPO = Path(__file__).resolve().parents[1]
V2 = REPO / "06_audit_preparation" / "protocol2" / "v2"


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def test_template_is_not_runnable(tmp_path):
    t = V2 / "V2_EXPERIMENT_TEMPLATE.yaml"
    cfg = yaml.safe_load(t.read_text(encoding="utf-8"))
    assert cfg["status"] == "V2_TEMPLATE_NOT_REGISTERED"
    assert cfg["base_arm"]["sha256"] == _sha(REPO / cfg["base_arm"]["file"])
    assert cfg["status"] not in {pp.REAL_STATUS, pp.DEV_ARM_STATUS, pp.SYNTH_STATUS}   # no runnable status
    for mode in ("develop", "preflight"):
        with pytest.raises((pp.AuthorizationError, pp.PreflightError, KeyError)):
            pp.run(t, REPO, tmp_path, tmp_path / "o", mode)


def test_v2_not_integrated_into_registered_runner_or_rc1():
    src = (REPO / "src" / "h2prism" / "experiments" / "primary_protocol.py").read_text(encoding="utf-8")
    assert "distinguishability_v2" not in src and "feature_representations" not in src
    rc = REPO / "06_audit_preparation" / "protocol2" / "release_candidate"
    assert (rc / "P2_0_RC1.sha256").read_text().split()[0] == _sha(rc / "P2_0_RC1.yaml")
    assert "distinguishability_v2" not in (rc / "P2_0_RC1.yaml").read_text(encoding="utf-8")


def test_v2_estimability_conclusion_is_recorded_not_relaxed():
    import json
    s = json.loads((REPO / "03_results" / "diagnostics" / "distinguishability_v2" / "V2_ESTIMABILITY.json").read_text())
    assert s["m"] == 2 and s["share_detectability_defined"] == 0.0
    assert set(s["share_window_fold_instances_by_margin_state"]) <= {"HYPOTHESIS_NOT_SUPPORTED", "UNTESTABLE_NO_ELIGIBLE_COMPETITOR"}
    e = json.loads((REPO / "03_results" / "diagnostics" / "distinguishability_v2" / "EH_REPRODUCTION.json").read_text())
    assert e["reproduction_matches_stored_E"] is True
