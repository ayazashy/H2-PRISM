"""Focused tests for the Center evidence enhancement (synthetic fixtures; no captures needed)."""
import os
import subprocess
from pathlib import Path

import numpy as np
import pytest

from h2prism import center_enhancement as ce
from h2prism.certified_evidence import ConsistencyStatus, DecisionStatus, HypothesisModel, diagnose

T = 400
A = 100
NAMES = ("PS1", "PS2", "MFS1")
KINDS = ("pressure", "pressure", "mass_flow")


def bump(scale_p, scale_f, delay=0):
    """Smooth synthetic residual starting at the anchor (+delay samples)."""
    x = np.zeros((T, 3))
    k = np.arange(T) - A - delay
    ramp = np.clip(k / 20.0, 0, 1)
    x[:, 0] = scale_p * ramp
    x[:, 1] = 0.5 * scale_p * ramp
    x[:, 2] = scale_f * ramp
    return x


def synthetic():
    templates = {"NORMAL_ZERO": (np.zeros((T, 3)), A), "NORMAL_TRANSIENT": (np.zeros((T, 3)), A),
                 "SID213": (bump(1e-3, 0.7), A), "ALT": (bump(1e-3, 0.7005), A),
                 "SID312": (bump(1.2e-3, 0.0), A), "SID215": (bump(5e-3, 3e-4), A),
                 "PRESSURE": (bump(0.17, 0.08), A), "TIMING": (bump(0.15, 0.1, delay=5), A)}
    queries = {k: (templates[k][0], A) for k in ("SID213", "SID312", "SID215", "PRESSURE", "TIMING", "ALT")}
    queries["NOMINAL"] = (np.zeros((T, 3)), A)
    queries["QUIET"] = (np.zeros((T, 3)), A)
    return ce.CenterData(np.arange(T) * 0.2, NAMES, KINDS, templates, queries, np.ones(3), {}, {})


@pytest.fixture(autouse=True)
def three_channel_sid(monkeypatch):
    monkeypatch.setattr(ce, "SID", {"PS1": "50", "PS2": "51", "MFS1": "311"})


def test_self_template_exclusion_uses_primary_capture():
    assert ce.excluded_templates("SID213", ["SID213", "SID312", "ALT"]) == ["SID213"]
    assert ce.excluded_templates("ALT", ["SID213", "ALT"]) == ["ALT"]
    assert ce.excluded_templates("QUIET", ["NORMAL_ZERO", "NORMAL_TRANSIENT"]) == ["NORMAL_ZERO"]
    # A shared nominal control is a disclosed dependence, not the query's primary capture.
    assert ce.excluded_templates("SID312", ["NORMAL_TRANSIENT"]) == []


def test_tie_handling_and_mechanism_collapse():
    assert ce.tied(0.1, 0.1 + 1e-15) and not ce.tied(0.1, 0.1001)
    rows = [dict(candidate="SID213", rms=0.2), dict(candidate="SID312", rms=0.1),
            dict(candidate="NORMAL_ZERO", rms=0.15)]
    best = ce.collapse_ranks(rows, ce.REGISTRY)
    assert [r["mechanism"] for r in best] == ["CONTROLLED_WITHDRAWAL", "NORMAL_OPERATION"]
    assert best[0]["candidate"] == "SID312"


def test_channel_groups_and_invalid_group():
    d = synthetic()
    assert list(ce.group_index(d, "pressure")) == [0, 1]
    assert list(ce.group_index(d, "flow")) == [2]
    assert list(ce.group_index(d, "omit_MFS1")) == [0, 1]
    with pytest.raises(ValueError):
        ce.group_index(d, "omit_MFS9")


def test_location_unsupported_without_independent_template():
    d = synthetic()
    r = ce.location_ranking(d, "SID312", "loto")
    assert r["status"] == "UNSUPPORTED" and r["true_rank"] is None
    r = ce.location_ranking(d, "SID213", "loto_replicate")
    assert r["status"] == "CORRECT" and "SID213" in r["site_scores"]
    assert r["candidate_templates"].count("SID213") == 0      # own template removed; ALT stands in


def _decide(d, query, eps_p, eps_f, universe="restricted", bound=1.0, group="all"):
    return ce.dy_decision(d, query, group, {"pressure": eps_p, "mass_flow": eps_f}, bound, universe)


def test_adapter_exclusion_feasibility_and_units():
    d = synthetic()
    tight = _decide(d, "SID213", 1e-9, 1e-9)
    assert tight["decision"] == "UNRESOLVED" and tight["reason"] == "MODEL_MISMATCH"
    window = _decide(d, "SID213", 1e-4, 1e-2)
    assert window["decision"] == "SPECIFIC" and window["selected"] == "WITHDRAWAL_SID213"
    # pressure and flow bounds are separate: a loose pressure bound alone cannot rescue a flow mismatch
    assert _decide(d, "SID213", 1.0, 1e-9)["decision"] == "UNRESOLVED"


def test_clock_shift_set_controls_feasibility():
    d = synthetic()
    # TIMING template lags its query by 5 samples = 1 s only when the query uses the PRESSURE-like shape
    shifted = dict(d.templates)
    shifted["TIMING"] = (bump(1e-3, 0.7, delay=5), A)
    d2 = ce.CenterData(d.clock, d.names, d.kinds, shifted, d.queries, d.scale, {}, {})
    idx = ce.group_index(d2, "all")
    with_shift = ce.thresholds(d2, "SID213", "COMMAND_ISSUANCE_SHIFT_SID59", "all", 1.0)
    no_shift = ce.thresholds(d2, "SID213", "COMMAND_ISSUANCE_SHIFT_SID59", "all", 0.0)
    assert with_shift["mass_flow"]["F"] < no_shift["mass_flow"]["F"]
    assert with_shift["mass_flow"]["E"] <= no_shift["mass_flow"]["E"]
    assert len(idx) == 3


def test_invalid_uncertainty_is_rejected_by_frozen_engine():
    d = synthetic()
    idx = ce.group_index(d, "all")
    bad = ce.measurement(d, "SID213", idx, {"pressure": -1.0, "mass_flow": 0.1})
    models = ce.dy_models(d, "SID213", idx, {"pressure": 0.0, "mass_flow": 0.0}, 1.0, "restricted")
    decision = diagnose(bad, models)
    assert decision.status is DecisionStatus.UNRESOLVED and decision.reason == "INVALID_MEASUREMENT"
    assert "INVALID_UNCERTAINTY" in decision.certificate.measurement_issues


def test_full_universe_never_decides_restricted_can():
    d = synthetic()
    full = _decide(d, "SID213", 1e-4, 1e-2, "full")
    rest = _decide(d, "SID213", 1e-4, 1e-2, "restricted")
    assert full["decision"] == "UNRESOLVED" and full["reason"] == "INDETERMINATE_HYPOTHESES"
    assert set(ce.DY_UNMODELLED) <= set(full["indeterminate"])
    assert rest["decision"] == "SPECIFIC"
    # unrepresented true mechanism: restricted universe may pick a wrong hypothesis
    wrong = _decide(d, "SID215", 1e-2, 1e-3, "restricted")
    assert wrong["true_supported"] is False
    assert wrong["selected"] != wrong["true_hypothesis"]


def test_closed_form_thresholds_match_engine_and_split_invariance():
    d = synthetic()
    t = ce.thresholds(d, "SID213", "WITHDRAWAL_SID312", "flow", 1.0)
    e = float(t["mass_flow"]["E"])
    below = _decide(d, "SID213", 1.0, e * (1 - 1e-6), group="flow")
    above = _decide(d, "SID213", 1.0, e * (1 + 1e-6), group="flow")
    assert "WITHDRAWAL_SID312" in below["excluded"] and "WITHDRAWAL_SID312" not in above["excluded"]
    a = ce.dy_decision(d, "SID213", "all", {"pressure": 1e-4, "mass_flow": 1e-2}, 1.0, "restricted", 0.5)
    b = ce.dy_decision(d, "SID213", "all", {"pressure": 1e-4, "mass_flow": 1e-2}, 1.0, "restricted", 1.0)
    assert (a["decision"], a["excluded"]) == (b["decision"], b["excluded"])


def test_adapter_result_passes_engine_validation():
    d = synthetic()
    idx = ce.group_index(d, "all")
    m = ce.measurement(d, "SID213", idx, {"pressure": 5e-5, "mass_flow": 5e-3})
    models = ce.dy_models(d, "SID213", idx, {"pressure": 5e-5, "mass_flow": 5e-3}, 1.0, "restricted")
    cert = diagnose(m, models).certificate
    # the engine downgrades any malformed adapter result to INVALID_ADAPTER_RESULT
    assert all(r.reason != "INVALID_ADAPTER_RESULT" for r in cert.results)
    assert any(r.status is ConsistencyStatus.EXCLUDED and r.separation is not None for r in cert.results)


def test_frozen_center_artifacts_unchanged():
    root = Path(__file__).resolve().parents[1]
    frozen = ["03_results/validation/publication_final_v1", "03_results/validation/baseline_freeze_v1",
              "03_results/validation/final_research", "03_results/validation/mechanism_screen_v1",
              "src/h2prism/certified_evidence.py", "src/h2prism/nres.py", "src/h2prism/mechanism_screen.py"]
    try:
        out = subprocess.run(["git", "diff", "--name-only", "h2prism-center-baseline-v1", "--", *frozen],
                             cwd=root, capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("git or baseline tag unavailable")
    assert out.strip() == ""


@pytest.mark.skipif(not os.environ.get("H2PRISM_CENTER_WORKSPACE"), reason="Center capture workspace not configured")
def test_real_captures_reproduce_frozen_margin_deterministically():
    d = ce.load(Path(os.environ["H2PRISM_CENTER_WORKSPACE"]))
    a = ce.recognition(d, "ALT", "frozen")
    b = ce.recognition(d, "ALT", "frozen")
    assert a["margin"] == b["margin"]
    assert abs(a["margin"] - 0.0283582) < 5e-7
