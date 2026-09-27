"""
Physics-Anchored Consistency and Mass-Balance Engine (Person 1: Ahmed).
Implements real-gas hydrogen density, line-pack corrected mass conservation,
and cross-sensor consistency residuals.
"""

from typing import List, Optional, Tuple
import numpy as np
import pandas as pd
from .schema import PhysicsEvidence

# Physical Constants for Hydrogen (H2)
M_H2 = 2.01588e-3     # kg/mol (Molar mass of H2)
R_GAS = 8.314462618   # J / (mol * K) (Universal gas constant)
NOMINAL_TEMP_K = 293.15  # 20 C (Documented default when temperature sensor is unmetered)


def hydrogen_density_real_gas(
    p_pa: float,
    t_k: float = NOMINAL_TEMP_K,
    z_factor: Optional[float] = None
) -> Tuple[float, float, str]:
    """
    Computes hydrogen density using real-gas relation:
    rho = (P * M_H2) / (Z * R * T)
    Returns (density_kg_m3, z_factor_used, assumption_note).
    """
    if z_factor is None:
        # Standard Peng-Robinson or empirical linear expansion for H2 up to 10 MPa
        # Z ~ 1 + (0.0006 * P_bar) at ~293K
        p_bar = p_pa / 1.0e5
        z_factor = 1.0 + (0.00058 * p_bar)
        note = "Z approximated from empirical H2 compressibility equation of state."
    else:
        note = f"Z explicitly specified as {z_factor}."

    density = (p_pa * M_H2) / (z_factor * R_GAS * t_k)
    return density, z_factor, note


def compute_line_pack_mass(
    p_upstream: float,
    p_downstream: float,
    length_m: float = 10000.0,
    diameter_m: float = 0.4,
    t_k: float = NOMINAL_TEMP_K
) -> Tuple[float, str]:
    """
    Estimates mass stored in segment (line-pack) M_line = A * L * rho_mean.
    """
    p_mean = (2.0 / 3.0) * (p_upstream + p_downstream - (p_upstream * p_downstream) / (p_upstream + p_downstream + 1e-6))
    rho_mean, _, _ = hydrogen_density_real_gas(p_mean, t_k)
    area = np.pi * (diameter_m / 2.0) ** 2
    mass = area * length_m * rho_mean
    assumption = f"Line-pack estimated using representative mean pressure formula, L={length_m}m, D={diameter_m}m."
    return mass, assumption


def compute_mass_balance_residual(
    window_df: pd.DataFrame,
    pipe_length_m: float = 10000.0,
    pipe_diameter_m: float = 0.4,
    enable_line_pack: bool = True,
    flow_sensor_uncertainty_kg_s: float = 0.05
) -> PhysicsEvidence:
    """
    Evaluates mass balance over an event window:
    m_loss = integral(m_in - m_out) dt - Delta M_line
    z_MB = m_loss / sigma_MB
    """
    event_id = str(window_df["scenario_id"].iloc[0]) if "scenario_id" in window_df else "unknown_event"
    scenario_id = event_id
    assumptions = []

    m_in = window_df["m_inlet"].to_numpy()
    m_out = window_df["m_outlet"].to_numpy()
    p_up = window_df["p_upstream"].to_numpy()
    p_down = window_df["p_downstream"].to_numpy()
    ts = window_df["timestamp"].to_numpy() if "timestamp" in window_df else np.arange(len(m_in))

    dt = np.mean(np.diff(ts)) if len(ts) > 1 else 1.0
    duration = ts[-1] - ts[0] if len(ts) > 1 else 1.0

    raw_imbalance = float(np.mean(m_in - m_out))
    p_diff = float(np.mean(p_up - p_down))
    flow_diff = raw_imbalance

    line_pack_delta = 0.0
    if enable_line_pack and len(window_df) >= 2:
        m_start, note1 = compute_line_pack_mass(p_up[0], p_down[0], pipe_length_m, pipe_diameter_m)
        m_end, _ = compute_line_pack_mass(p_up[-1], p_down[-1], pipe_length_m, pipe_diameter_m)
        line_pack_delta = (m_end - m_start) / max(duration, 1.0)
        assumptions.append(note1)
    else:
        assumptions.append("Line-pack correction disabled or unsupported by sampling window.")

    corrected_loss_rate = raw_imbalance - line_pack_delta

    # Total uncertainty: combination of inlet flow meter, outlet meter, and line-pack error
    sigma_flow = np.sqrt(2 * (flow_sensor_uncertainty_kg_s ** 2))
    sigma_line_pack = 0.03 * abs(line_pack_delta) if enable_line_pack else 0.01
    sigma_total = float(np.sqrt(sigma_flow ** 2 + sigma_line_pack ** 2))

    z_mb = float(corrected_loss_rate / (sigma_total + 1e-6))

    # Cross-sensor physics consistency score
    # In a leak: pressure drops upstream & downstream, m_inlet >= m_outlet
    # In a valve/transient: pressure and flow deviate in coupled direction
    physics_consistency = 1.0
    if abs(z_mb) > 3.0 and p_diff < 0:
        # Negative pressure difference with massive apparent leak -> contradiction / sensor issue
        physics_consistency = 0.3
        assumptions.append("Notice: Negative Delta P observed during mass loss, possible sensor bias.")

    return PhysicsEvidence(
        event_id=event_id,
        scenario_id=scenario_id,
        raw_imbalance=raw_imbalance,
        mass_balance_residual=float(corrected_loss_rate),
        normalized_mass_balance_residual=z_mb,
        pressure_difference=p_diff,
        flow_difference=flow_diff,
        line_pack_correction=float(line_pack_delta) if enable_line_pack else None,
        physics_consistency=physics_consistency,
        physics_valid=True,
        physics_assumptions=assumptions,
        uncertainty_sigma=sigma_total
    )
