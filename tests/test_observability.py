"""
Unit Tests for Observability Engine and Decision Gating (Person 3: Yazan).
"""

import pytest
from src.schema import ObservabilityLevel, AttributionClass
from src.observability import compute_observability
from src.decision import DecisionEngine
from src.data import generate_mock_scenario
from src.physics import compute_mass_balance_residual
from src.propagation import estimate_propagation_delay
from src.model import EventAttributionModel
from src.evidence import fuse_evidence


def test_observability_insufficient_on_bad_sampling():
    df = generate_mock_scenario(scenario_type="leak", duration_s=100.0, dt=15.0)  # dt=15s > tau=7.7s
    physics = compute_mass_balance_residual(df)
    prop = estimate_propagation_delay(df)
    ml_res = EventAttributionModel().predict_event("evt_01", {})
    ev = fuse_evidence("evt_01", ml_res, physics, prop)

    obs = compute_observability(
        event_id="evt_01",
        data_qc_summary={"data_adequacy_o_q": 1.0},
        physics=physics,
        propagation=prop,
        evidence=ev,
        sampling_dt_s=15.0
    )
    assert obs.observability_level == ObservabilityLevel.INSUFFICIENT
    assert any("Structural resolution" in c for c in obs.failing_criteria)
