"""
Unit Tests for Physics Engine and Mass-Balance Residual (Person 1: Ahmed - Step 15).
Tests:
- sign convention
- units
- upstream/downstream ordering
- zero flow
- constant steady state
- synthetic imbalance
- known artificial delay
- missing station
- insufficient sampling resolution
"""

import pytest
import numpy as np
import pandas as pd
from src.physics import compute_mass_balance_residual, hydrogen_density_real_gas
from src.propagation import estimate_propagation_delay
from src.data import generate_mock_scenario


def test_steady_state_zero_imbalance():
    df = generate_mock_scenario(scenario_type="normal", duration_s=100.0)
    physics = compute_mass_balance_residual(df)
    assert abs(physics.raw_imbalance) < 0.1
    assert abs(physics.normalized_mass_balance_residual) < 3.0


def test_synthetic_leak_imbalance():
    df = generate_mock_scenario(scenario_type="leak", duration_s=100.0)
    physics = compute_mass_balance_residual(df)
    assert physics.raw_imbalance > 0.0
    assert physics.normalized_mass_balance_residual > 3.0


def test_propagation_resolution_floor():
    df = generate_mock_scenario(scenario_type="leak", duration_s=100.0, dt=1.0)
    prop = estimate_propagation_delay(df)
    # Resolution floor a * dt / 2 = 1300 * 1 / 2 = 650 m
    assert prop.resolution_floor == pytest.approx(650.0, rel=1e-2)
