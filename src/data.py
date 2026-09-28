"""
Data Ingestion and Schema Standardization (Person 1: Ahmed).
Responsible for loading pipeline time-series data without altering original metadata,
validating schemas, and providing mock scenario data for development and testing.
"""

from pathlib import Path
from typing import Optional, Union, Dict, Any
import numpy as np
import pandas as pd


STANDARD_COLUMNS = [
    "timestamp",
    "scenario_id",
    "run_id",
    "p_upstream",     # Pressure station 1 (Pa or bar, documented in metadata)
    "p_downstream",   # Pressure station 2
    "m_inlet",        # Mass flow station 1 (kg/s)
    "m_outlet",       # Mass flow station 2 (kg/s)
    "label",          # Ground truth label (if available)
]


def load_scenario(
    file_path: Union[str, Path],
    expected_format: str = "csv"
) -> pd.DataFrame:
    """
    Load an individual scenario file from disk (CSV or Parquet) preserving all original fields.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Scenario file not found: {path}")

    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    elif path.suffix.lower() in [".parquet", ".pq"]:
        df = pd.read_parquet(path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")

    return df


def generate_mock_scenario(
    scenario_type: str = "normal",
    duration_s: float = 600.0,
    dt: float = 1.0,
    pipe_length_m: float = 10000.0,
    wave_speed_m_s: float = 1300.0,
    random_seed: int = 42
) -> pd.DataFrame:
    """
    Generate synthetic/mock pipeline segment data for testing and mock pipeline execution.
    Scenarios supported: 'normal', 'leak', 'operational_transient', 'sensor_fault', 'ambiguous'.
    """
    rng = np.random.default_rng(random_seed)
    n_steps = int(duration_s / dt)
    time = np.arange(n_steps, dtype=float) * dt

    # Base operating conditions
    base_p1 = 5.0e6  # 5 MPa inlet
    pressure_drop = 0.2e6  # 0.2 MPa nominal friction drop
    base_p2 = base_p1 - pressure_drop
    base_flow = 12.0  # 12 kg/s nominal hydrogen flow

    # Add background noise
    p1 = base_p1 + rng.normal(0, 500.0, size=n_steps)
    p2 = base_p2 + rng.normal(0, 500.0, size=n_steps)
    m1 = base_flow + rng.normal(0, 0.02, size=n_steps)
    m2 = base_flow + rng.normal(0, 0.02, size=n_steps)

    label = np.array(["NORMAL"] * n_steps, dtype=object)
    t_event = int(n_steps * 0.4)

    if scenario_type == "leak":
        leak_rate = 0.8  # kg/s (~6.7% leak)
        # Outlet flow drops by leak rate after acoustic propagation
        delay_steps = int((pipe_length_m * 0.5) / (wave_speed_m_s * dt))
        delay_steps = max(1, delay_steps)
        p1[t_event:] -= 0.05e6
        p2[t_event + delay_steps:] -= 0.08e6
        m2[t_event + delay_steps:] -= leak_rate
        label[t_event:] = "LEAK"

    elif scenario_type == "operational_transient":
        # Operational compression/valve ramp: both flows rise or fall with line-pack accumulation
        ramp_duration = int(30 / dt)
        ramp = np.linspace(0, 2.0, ramp_duration)
        ramp_end = min(t_event + ramp_duration, n_steps)
        m1[t_event:ramp_end] += ramp[:ramp_end - t_event]
        m1[ramp_end:] += 2.0

        # Downstream lags slightly due to inertia & line-pack
        lag = int(5 / dt)
        t_down = t_event + lag
        if t_down < n_steps:
            ramp_down_end = min(t_down + ramp_duration, n_steps)
            m2[t_down:ramp_down_end] += ramp[:ramp_down_end - t_down]
            m2[ramp_down_end:] += 2.0

        p1[t_event:] += 0.15e6
        p2[t_down:] += 0.12e6
        label[t_event:] = "OPERATIONAL_TRANSIENT"

    elif scenario_type == "sensor_fault":
        # Sudden bias in downstream pressure sensor without any flow imbalance or upstream signature
        p2[t_event:] -= 0.3e6
        label[t_event:] = "SENSOR_FAULT"

    elif scenario_type == "ambiguous":
        # Small leak near detectability limit combined with high noise
        p1[t_event:] -= rng.uniform(500, 2000, size=n_steps - t_event)
        p2[t_event:] -= rng.uniform(500, 2000, size=n_steps - t_event)
        m2[t_event:] -= 0.05  # within flow meter noise floor
        label[t_event:] = "AMBIGUOUS"

    df = pd.DataFrame({
        "timestamp": time,
        "scenario_id": f"mock_{scenario_type}_001",
        "run_id": "run_01",
        "p_upstream": p1,
        "p_downstream": p2,
        "m_inlet": m1,
        "m_outlet": m2,
        "label": label
    })
    return df
