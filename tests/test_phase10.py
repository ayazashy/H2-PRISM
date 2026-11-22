import numpy as np
import pytest

from h2prism.phase10 import diagnostic_time_shift, exact_pairs, metrics, quality, solver_grid


def test_exact_decimal_and_binary64_are_separate():
    a = ["0", "0.80000000000000004", "4"]
    b = ["0.0", "0.8", "4.0", "5"]
    assert [x.tolist() for x in exact_pairs(a, b)] == [[0, 2], [0, 2]]
    assert [x.tolist() for x in exact_pairs(a, b, decimal=False)] == [[0, 1, 2], [0, 1, 2]]


@pytest.mark.parametrize("clock", [["0", "0"], ["1", "0"]])
def test_alignment_rejects_bad_timestamp_order(clock):
    for decimal in (False, True):
        with pytest.raises(ValueError):
            exact_pairs(clock, ["0", "1"], decimal=decimal)


def test_grid_pairing_accepts_binary_roundoff_only():
    assert solver_grid([0, 0.8, 1.6, 2.4], 0.8, 2.4) == pytest.approx(np.spacing(2.4))
    with pytest.raises(ValueError, match="beyond roundoff"):
        solver_grid([0, 0.81, 1.6, 2.4], 0.8, 2.4)
    with pytest.raises(ValueError, match="missing"):
        solver_grid([0, 0.8, 2.4], 0.8, 2.4)


def test_metrics_retain_missing_pairs_and_skip_undefined_relative_scale():
    result = metrics([1, 5, np.nan, np.inf], [0, 0, 0, 0], [0, 4, 8, 12])
    assert result["matched_samples"] == 4
    assert result["finite_pairs"] == 2
    assert result["mae"] == 3
    assert result["rmse"] == pytest.approx(np.sqrt(13))
    assert result["max_absolute"] == 5
    assert result["peak_time_s"] == 4
    assert result["relative_rmse_reference_rms"] is None


def test_capture_quality_flags_nonmonotone_duplicates_and_invalid_values():
    record = quality([0, 1, 1, np.nan], [2, -3, np.nan, np.inf])
    assert record["duplicates"] == 1
    assert record["invalid_timestamps"] == 1
    assert not record["strictly_increasing"]
    assert record["nan_or_missing"] == record["infinite"] == 1
    assert record["negative"] == record["positive"] == 1
    assert record["last_s"] is None
    with pytest.raises(ValueError, match="scalar samples"):
        quality([0, 1], [[1], [2]])

def test_diagnostic_shift_recovers_lead_on_shared_interior_support():
    time = np.arange(10)
    result = diagnostic_time_shift(time, time * 3, time[1:-1], time[1:-1] * 3 + 1.8, 0.8)
    assert result["shift_s"] == pytest.approx(0.6, abs=1e-5)
    assert result["rmse_zero_shift"] == pytest.approx(1.8)
    assert result["rmse_fitted_shift"] < 1e-5
    with pytest.raises(ValueError, match="extrapolate"):
        diagnostic_time_shift(time, time, time, time, 0.8)
