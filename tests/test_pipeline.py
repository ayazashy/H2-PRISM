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
