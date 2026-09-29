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


def test_observability_adequate_under_nominal_conditions():
    df = generate_mock_scenario(scenario_type="leak", duration_s=100.0, dt=1.0)
    physics = compute_mass_balance_residual(df)
    prop = estimate_propagation_delay(df)
    ml_res = EventAttributionModel().predict_event("evt_02", {"normalized_z_mb": 5.0})
    ev = fuse_evidence("evt_02", ml_res, physics, prop)

    obs = compute_observability(
        event_id="evt_02",
        data_qc_summary={"data_adequacy_o_q": 1.0},
        physics=physics,
        propagation=prop,
        evidence=ev,
        sampling_dt_s=1.0
    )
    assert obs.overall_observability >= 0.7
    assert obs.observability_level == ObservabilityLevel.ADEQUATE


def test_decision_engine_abstains_on_insufficient_observability():
    engine = DecisionEngine(min_observability_threshold=0.60)
    df = generate_mock_scenario(scenario_type="leak", duration_s=100.0, dt=15.0)
    physics = compute_mass_balance_residual(df)
    prop = estimate_propagation_delay(df)
    ml_res = EventAttributionModel().predict_event("evt_03", {})
    ev = fuse_evidence("evt_03", ml_res, physics, prop)
    obs = compute_observability("evt_03", {"data_adequacy_o_q": 0.4}, physics, prop, ev, sampling_dt_s=15.0)

    decision = engine.evaluate(
        event_id="evt_03",
        scenario_id="mock_leak",
        timestamp=40.0,
        evidence=ev,
        observability=obs,
        physics=physics,
        propagation=prop
    )
    assert decision.is_abstained is True
    assert decision.decision == AttributionClass.UNKNOWN
    assert "Insufficient observability" in decision.reason


def test_decision_engine_abstains_on_low_confidence_or_margin():
    engine = DecisionEngine(min_confidence_threshold=0.60, min_probability_margin=0.20)
    df = generate_mock_scenario(scenario_type="normal", duration_s=100.0, dt=1.0)
    physics = compute_mass_balance_residual(df)
    prop = estimate_propagation_delay(df)
    ml_res = EventAttributionModel().predict_event("evt_04", {})
    # Mock ambiguous equal probabilities
    ev = fuse_evidence("evt_04", ml_res, physics, prop)
    ev.fused_hypotheses = {
        AttributionClass.LEAK.value: 0.35,
        AttributionClass.OPERATIONAL_TRANSIENT.value: 0.33,
        AttributionClass.SENSOR_FAULT.value: 0.16,
        AttributionClass.NORMAL.value: 0.16
    }
    obs = compute_observability("evt_04", {"data_adequacy_o_q": 1.0}, physics, prop, ev, sampling_dt_s=1.0)

    decision = engine.evaluate(
        event_id="evt_04",
        scenario_id="mock_ambiguous",
        timestamp=40.0,
        evidence=ev,
        observability=obs,
        physics=physics,
        propagation=prop
    )
    assert decision.is_abstained is True
    assert decision.decision == AttributionClass.UNKNOWN
    assert "Low confidence" in decision.reason or "Ambiguous" in decision.reason
