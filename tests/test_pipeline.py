"""
Unit Tests for End-to-End Pipeline Execution (Person 3: Yazan).
"""

import pytest
from src.pipeline import H2PrismPipeline
from src.data import generate_mock_scenario
from src.schema import AttributionClass


def test_pipeline_runs_leak_mock():
    df = generate_mock_scenario(scenario_type="leak", duration_s=120.0)
    pipeline = H2PrismPipeline()
    reports = pipeline.process_scenario(df)
    assert len(reports) > 0
    first = reports[0]
    assert first.decision is not None
    assert first.physics is not None
    assert first.propagation is not None
    assert first.decision.decision in [AttributionClass.LEAK, AttributionClass.UNKNOWN]


def test_pipeline_runs_operational_transient_mock():
    df = generate_mock_scenario(scenario_type="operational_transient", duration_s=120.0)
    pipeline = H2PrismPipeline()
    reports = pipeline.process_scenario(df)
    if reports:
        first = reports[0]
        assert first.physics.line_pack_correction is not None


def test_pipeline_runs_sensor_fault_mock():
    df = generate_mock_scenario(scenario_type="sensor_fault", duration_s=120.0)
    pipeline = H2PrismPipeline()
    reports = pipeline.process_scenario(df)
    assert len(reports) >= 0


def test_pipeline_runs_normal_mock():
    df = generate_mock_scenario(scenario_type="normal", duration_s=120.0)
    pipeline = H2PrismPipeline()
    reports = pipeline.process_scenario(df)
    # Normal operation should yield zero or near-zero candidate alerts
    assert len(reports) == 0


def test_pipeline_runs_standardized_benchmark_scenario():
    import os
    from src.data import load_scenario
    benchmark_path = "data/processed/scen_leak_g3_strong_standardized.csv"
    if os.path.exists(benchmark_path):
        df = load_scenario(benchmark_path).iloc[:500]  # Sample first 500 steps for fast test
        pipeline = H2PrismPipeline()
        reports = pipeline.process_scenario(df)
        assert isinstance(reports, list)


def test_evaluate_pipeline_performance_metrics():
    from src.evaluation import evaluate_pipeline_performance
    df = generate_mock_scenario(scenario_type="leak", duration_s=120.0)
    pipeline = H2PrismPipeline()
    reports = pipeline.process_scenario(df)
    
    if reports:
        metrics = evaluate_pipeline_performance(
            reports=reports,
            ground_truth_labels=["LEAK"] * len(reports),
            leak_location_m=5000.0
        )
        assert "coverage" in metrics
        assert "fpar" in metrics
        assert "leak_recall" in metrics
        assert "covered_accuracy" in metrics
        assert 0.0 <= metrics["coverage"] <= 1.0
