"""
Propagation Delay Estimation and Conditional Localization (Person 1: Ahmed).
Uses cross-correlation on upstream and downstream transients, determines physical plausibility,
and computes conditional localization intervals bounded by sampling rate resolution floors.
"""

from typing import Optional, Tuple
import numpy as np
import pandas as pd
from scipy.signal import correlate, correlation_lags
from .schema import PropagationEvidence


def estimate_propagation_delay(
    window_df: pd.DataFrame,
    pipe_length_m: float = 10000.0,
    hydrogen_wave_speed_m_s: float = 1300.0,
    min_correlation_threshold: float = 0.5
) -> PropagationEvidence:
    """
    Estimates time lag Delta t_12 via cross-correlation between upstream & downstream pressures.
    Derives conditional location interval x_hat +/- delta bounded by acoustic travel time.
    """
    event_id = str(window_df["scenario_id"].iloc[0]) if "scenario_id" in window_df else "unknown_event"
    scenario_id = event_id

    p_up = window_df["p_upstream"].to_numpy()
    p_down = window_df["p_downstream"].to_numpy()
    ts = window_df["timestamp"].to_numpy() if "timestamp" in window_df else np.arange(len(p_up))

    dt = float(np.mean(np.diff(ts))) if len(ts) > 1 else 1.0
    max_physical_lag_s = pipe_length_m / hydrogen_wave_speed_m_s
    resolution_floor = float(hydrogen_wave_speed_m_s * dt / 2.0)

    # Preprocess by removing mean and detrending
    s1 = p_up - np.mean(p_up)
    s2 = p_down - np.mean(p_down)

    std1 = np.std(s1)
    std2 = np.std(s2)

    # Check for flat / insufficient variance signals
    if std1 < 1e-4 or std2 < 1e-4:
        return PropagationEvidence(
            event_id=event_id,
            scenario_id=scenario_id,
            estimated_delay=None,
            correlation_strength=0.0,
            propagation_consistency=False,
            localization_interval=None,
            localization_observable=False,
            resolution_floor=resolution_floor,
            abstention_reason="Insufficient signal variance for cross-correlation."
        )

    # Standardized cross-correlation
    corr = correlate(s1, s2, mode="full") / (len(s1) * std1 * std2)
    lags = correlation_lags(len(s1), len(s2), mode="full")

    # Constrain lags to physical acoustic travel envelope
    max_lag_steps = int(np.ceil(max_physical_lag_s / dt)) + 2
    physical_mask = np.abs(lags * dt) <= (max_physical_lag_s * 1.5)

    if not np.any(physical_mask):
        return PropagationEvidence(
            event_id=event_id,
            scenario_id=scenario_id,
            estimated_delay=None,
            correlation_strength=0.0,
            propagation_consistency=False,
            localization_interval=None,
            localization_observable=False,
            resolution_floor=resolution_floor,
            abstention_reason="No lags within physical acoustic window."
        )

    valid_corr = corr[physical_mask]
    valid_lags = lags[physical_mask]

    peak_idx = int(np.argmax(valid_corr))
    peak_corr = float(valid_corr[peak_idx])
    best_lag_steps = valid_lags[peak_idx]
    delta_t_12 = float(best_lag_steps * dt)

    is_consistent = (peak_corr >= min_correlation_threshold) and (abs(delta_t_12) <= max_physical_lag_s)

    # Conditional localization:
    # x_hat = (L - a * Delta t_12) / 2
    # Bounded by resolution floor delta = a * dt / 2
    if is_consistent:
        x_hat = (pipe_length_m - hydrogen_wave_speed_m_s * delta_t_12) / 2.0
        x_min = max(0.0, x_hat - resolution_floor)
        x_max = min(pipe_length_m, x_hat + resolution_floor)
        loc_interval = (float(x_min), float(x_max))
        loc_observable = True
        abstention_reason = None
    else:
        loc_interval = None
        loc_observable = False
        abstention_reason = f"Peak correlation {peak_corr:.2f} below threshold or lag {delta_t_12:.2f}s unphysical."

    return PropagationEvidence(
        event_id=event_id,
        scenario_id=scenario_id,
        estimated_delay=delta_t_12,
        correlation_strength=peak_corr,
        propagation_consistency=is_consistent,
        localization_interval=loc_interval,
        localization_observable=loc_observable,
        resolution_floor=resolution_floor,
        abstention_reason=abstention_reason
    )
