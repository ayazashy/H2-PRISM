from pathlib import Path

import numpy as np
import pytest

from h2prism.data.loader import RAW_DATASET_DIR
from h2prism.phase2 import MODEL, MODEL_DIR
from h2prism.phase11 import mass_integrals, model_diff


def test_step_integral_keeps_post_step_rate_out_of_previous_interval():
    t = np.arange(7, dtype=float)
    flow = np.where(t < 3, 2.0, 10.0)
    storage = 100 + 2 * np.minimum(t, 3) + 10 * np.maximum(0, t - 3)
    report = mass_integrals(t, flow, storage, 3)
    assert report.trapezoid_residual_kg.iloc[-1] == -4
    np.testing.assert_allclose(report.step_left_trapezoid_residual_kg, 0)
    np.testing.assert_allclose(report.step_split_simpson_residual_kg, 0)


@pytest.mark.parametrize("time,event", [(np.array([0, 1, 1]), 1), (np.arange(3), 0), (np.arange(3), 3)])
def test_invalid_integration_clock_or_event_fails(time, event):
    with pytest.raises(ValueError, match="clock or event"):
        mass_integrals(time, time, time, event)


def test_centre_leak_candidate_has_no_area_opening():
    normal = RAW_DATASET_DIR / MODEL_DIR / f"{MODEL}.slx"
    candidate = RAW_DATASET_DIR / Path("MATLAB_SIMSCAPE_Simulation/anomalous_scenarios/Anomalous_HNetwork_gest_center.slx")
    if not normal.exists() or not candidate.exists():
        pytest.skip("local archived SLX pair unavailable")
    result = model_diff(normal, candidate)
    assert result["status"] == "BLOCKED"
    assert result["added_connections"] == [("213#lconn:2", "563#rconn:1")]
    assert result["sid_563"]["initial_value"] == result["sid_563"]["final_value"] == "1e-10"
    assert result["sid_213"]["normal_area_m2"] == 0.001
    assert set(result["configuration_deltas"]) == {"FixedStep", "SolverName"}
