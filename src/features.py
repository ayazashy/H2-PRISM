"""
Multi-Group Feature Engineering (Person 2: Faisal).
Extracts structured, interpretable features across:
- Group A: Raw signal levels
- Group B: Temporal derivatives and statistics
- Group C: Cross-station sensor relationships
- Group D: Physics residuals (from Person 1)
- Group E: Propagation indicators (from Person 1)
"""

from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
from .schema import PhysicsEvidence, PropagationEvidence


def extract_window_features(
    window_df: pd.DataFrame,
    physics: Optional[PhysicsEvidence] = None,
    propagation: Optional[PropagationEvidence] = None
) -> Dict[str, float]:
    """
    Extracts unified feature vector for classifier attribution.
    """
    features: Dict[str, float] = {}

    p_up = window_df["p_upstream"].to_numpy()
    p_down = window_df["p_downstream"].to_numpy()
    m_in = window_df["m_inlet"].to_numpy()
    m_out = window_df["m_outlet"].to_numpy()
    ts = window_df["timestamp"].to_numpy() if "timestamp" in window_df.columns else np.arange(len(p_up))
    dt = float(np.mean(np.diff(ts))) if len(ts) > 1 else 1.0

    # Group A — Raw Levels
    features["p_upstream_mean"] = float(np.mean(p_up))
    features["p_downstream_mean"] = float(np.mean(p_down))
    features["m_inlet_mean"] = float(np.mean(m_in))
    features["m_outlet_mean"] = float(np.mean(m_out))
    features["delta_p_mean"] = float(np.mean(p_up - p_down))
    features["delta_m_mean"] = float(np.mean(m_in - m_out))

    # Group B — Temporal Dynamics
    dp_dt = np.gradient(p_up, dt)
    dm_dt = np.gradient(m_in, dt)
    features["p_upstream_std"] = float(np.std(p_up))
    features["p_downstream_std"] = float(np.std(p_down))
    features["m_inlet_std"] = float(np.std(m_in))
    features["m_outlet_std"] = float(np.std(m_out))
    features["max_abs_dp_dt"] = float(np.max(np.abs(dp_dt)))
    features["max_abs_dm_dt"] = float(np.max(np.abs(dm_dt)))
    features["p_drop_total"] = float(p_up[0] - p_up[-1])
    features["m_imbalance_max"] = float(np.max(np.abs(m_in - m_out)))

    # Group C — Cross-Station Coupling
    std_p_up = np.std(p_up)
    std_p_down = np.std(p_down)
    if std_p_up > 1e-4 and std_p_down > 1e-4:
        features["cross_station_p_corr"] = float(np.corrcoef(p_up, p_down)[0, 1])
    else:
        features["cross_station_p_corr"] = 0.0

    std_m_in = np.std(m_in)
    std_m_out = np.std(m_out)
    if std_m_in > 1e-4 and std_m_out > 1e-4:
        features["cross_station_m_corr"] = float(np.corrcoef(m_in, m_out)[0, 1])
    else:
        features["cross_station_m_corr"] = 0.0

    # Group D — Physics Evidence (Person 1 integration)
    if physics is not None:
        features["mass_balance_residual"] = float(physics.mass_balance_residual)
        features["normalized_z_mb"] = float(physics.normalized_mass_balance_residual)
        features["physics_consistency"] = float(physics.physics_consistency)
        features["line_pack_correction"] = float(physics.line_pack_correction or 0.0)
        features["physics_valid"] = 1.0 if physics.physics_valid else 0.0
    else:
        features["mass_balance_residual"] = 0.0
        features["normalized_z_mb"] = 0.0
        features["physics_consistency"] = 0.0
        features["line_pack_correction"] = 0.0
        features["physics_valid"] = 0.0

    # Group E — Propagation Evidence (Person 1 integration)
    if propagation is not None:
        features["prop_estimated_delay"] = float(propagation.estimated_delay or 0.0)
        features["prop_correlation_strength"] = float(propagation.correlation_strength)
        features["propagation_consistency"] = 1.0 if propagation.propagation_consistency else 0.0
        features["localization_observable"] = 1.0 if propagation.localization_observable else 0.0
    else:
        features["prop_estimated_delay"] = 0.0
        features["prop_correlation_strength"] = 0.0
        features["propagation_consistency"] = 0.0
        features["localization_observable"] = 0.0

    return features
