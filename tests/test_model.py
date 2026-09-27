"""
Unit Tests for Feature Extraction, ML Model & Evidence Fusion (Person 2: Faisal).
"""

import pytest
import numpy as np
from src.schema import AttributionClass
from src.model import EventAttributionModel
from src.features import extract_window_features
from src.data import generate_mock_scenario


def test_feature_extraction_completeness():
    df = generate_mock_scenario(scenario_type="normal", duration_s=60.0)
    features = extract_window_features(df)
    assert "p_upstream_mean" in features
    assert "delta_p_mean" in features
    assert "delta_m_mean" in features


def test_model_cold_start_heuristic():
    model = EventAttributionModel()
    features = {"normalized_z_mb": 4.5, "p_drop_total": 5e4}
    res = model.predict_event("test_01", features)
    assert res.predicted_class == AttributionClass.LEAK
    assert res.confidence > 0.5
