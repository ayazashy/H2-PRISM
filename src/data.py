"""
H2-PRISM Data Loading and Schema Standardization.

Step 5:
- Load raw scenario files without modifying source data.
- Preserve native H2-SimNet variable names and metadata.
- Provide a standardized long-form representation where supported.
- Do not silently infer physical station ordering or upstream/downstream roles.
- Keep generate_mock_scenario() for existing development/tests.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

import numpy as np
import pandas as pd


# ============================================================
# STANDARD SCHEMA
# ============================================================

STANDARD_COLUMNS = [
    "timestamp",
    "scenario_id",
    "run_id",
    "station_id",
    "sensor_id",
    "variable",
    "value",
    "unit",
    "label",
    "operational_phase",
    "anomaly_type",
    "localization",
]


# ============================================================
# H2-SimNet NATIVE MEASUREMENT CHANNELS
# ============================================================

PRESSURE_SENSORS = [f"PS{i}" for i in range(1, 13)]
MASS_FLOW_SENSORS = [f"MFS{i}" for i in range(1, 5)]

MEASUREMENT_COLUMNS = PRESSURE_SENSORS + MASS_FLOW_SENSORS


# ============================================================
# NATIVE ANOMALY / GROUND-TRUTH COLUMNS
# ============================================================

ANOMALY_COLUMNS = [
    "label_anomaly",
    "Leak",
    "CompressorFault",
    "CompressorDelay",
]


LOCALIZATION_COLUMNS = [
    "leak_G3",
    "leak_G4",
    "leak_G5",
    "leak_G6",
]


# ============================================================
# RAW DATA LOADING
# ============================================================

def load_scenario(
    file_path: Union[str, Path],
    expected_format: str = "csv",
) -> pd.DataFrame:
    """
    Load a raw scenario file without modifying its native columns.

    Supported formats:
        - CSV
        - Parquet
        - PQ

    Important:
        This function does NOT rename PS1/MFS1/etc.
        It does NOT infer upstream/downstream station ordering.
        It does NOT modify or remove source columns.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Scenario file not found: {path}"
        )

    suffix = path.suffix.lower()

    if suffix == ".csv":
        df = pd.read_csv(path)

    elif suffix in {".parquet", ".pq"}:
        df = pd.read_parquet(path)

    else:
        raise ValueError(
            f"Unsupported file format: {path.suffix}"
        )

    return df


# ============================================================
# METADATA HELPERS
# ============================================================

def _infer_operational_phase(
    path: Path,
) -> Optional[str]:
    """
    Infer the H2-SimNet operational/scenario phase from the
    directory structure.

    These values describe dataset scenario context only.
    They are not interpreted as physical operating states beyond
    the documented folder naming.
    """
    parts = {
        part.lower()
        for part in path.parts
    }

    if "start_transient" in parts:
        return "start_transient"

    if "assestment_transient" in parts:
        return "assestment_transient"

    if "constant_segment" in parts:
        return "constant_segment"

    return None


def _infer_configuration(
    path: Path,
) -> Optional[str]:
    """
    Infer H2-SimNet network configuration from the filename/path
    when explicitly represented.

    Supported values:
        center
        down
        up

    These describe H2-SimNet operating configurations and are NOT
    treated as physical sensor locations.
    """
    parts = [
        part.lower()
        for part in path.parts
    ]

    name = path.name.lower()

    # Explicit configuration names in filename.
    for configuration in (
        "center",
        "down",
        "up",
    ):
        if configuration in name:
            return configuration

    # H2-SimNet directory naming conventions.
    if "anom_gestcent" in parts:
        return "center"

    if "anom_gestdown" in parts:
        return "down"

    if "anom_gestup" in parts:
        return "up"

    return None


def _build_run_id(
    path: Path,
) -> str:
    """
    Build a deterministic run identifier from the source path.

    The original source path is preserved separately in
    source_file.
    """
    relative = str(path).replace("\\", "/")
    return relative


# ============================================================
# TIMESTAMP HANDLING
# ============================================================

def _prepare_timestamp(
    df: pd.DataFrame,
    sampling_interval_s: float = 1.0,
) -> tuple[pd.Series, bool]:
    """
    Preserve an explicit source timestamp when available.

    If the source has no timestamp column, construct a derived
    time axis using the documented sampling interval.

    Returns:
        timestamp
        timestamp_is_derived
    """
    timestamp_candidates = [
        column
        for column in df.columns
        if str(column).lower()
        in {
            "timestamp",
            "time",
            "datetime",
        }
    ]

    if timestamp_candidates:
        source_column = timestamp_candidates[0]

        return (
            df[source_column].copy(),
            False,
        )

    timestamp = pd.Series(
        np.arange(
            len(df),
            dtype=float,
        ) * sampling_interval_s,
        index=df.index,
        name="timestamp",
    )

    return (
        timestamp,
        True,
    )


# ============================================================
# STANDARDIZATION
# ============================================================

def standardize_scenario(
    file_path: Union[str, Path],
    sampling_interval_s: float = 1.0,
) -> pd.DataFrame:
    """
    Load and standardize one H2-SimNet scenario into long-form records.

    Each sensor measurement becomes one row with:

        timestamp
        scenario_id
        run_id
        station_id
        sensor_id
        variable
        value
        unit
        label
        operational_phase
        anomaly_type
        localization

    Native anomaly and source metadata are preserved in additional
    columns.

    Important:
        No physical station ordering is inferred.
        PS1 is not renamed to upstream.
        PS2 is not renamed to downstream.
        MFS1 is not renamed to inlet.
        MFS2 is not renamed to outlet.
    """
    path = Path(file_path)

    raw = load_scenario(path)

    timestamp, timestamp_is_derived = _prepare_timestamp(
        raw,
        sampling_interval_s=sampling_interval_s,
    )

    scenario_id = path.stem

    run_id = _build_run_id(path)

    operational_phase = _infer_operational_phase(path)

    configuration = _infer_configuration(path)

    records: list[dict] = []

    # --------------------------------------------------------
    # Native anomaly label
    # --------------------------------------------------------

    if "label_anomaly" in raw.columns:
        anomaly_label = raw["label_anomaly"]

    else:
        anomaly_label = pd.Series(
            [pd.NA] * len(raw),
            index=raw.index,
        )

    # --------------------------------------------------------
    # Native localization columns
    # --------------------------------------------------------

    localization_values = {}

    for column in LOCALIZATION_COLUMNS:
        if column in raw.columns:
            localization_values[column] = raw[column]

    # --------------------------------------------------------
    # Build active localization for every timestamp
    # --------------------------------------------------------

    active_localization = []

    for index in raw.index:

        active = [
            column
            for column, values in localization_values.items()
            if (
                pd.notna(values.loc[index])
                and values.loc[index] == 1
            )
        ]

        if active:
            active_localization.append(
                "|".join(active)
            )
        else:
            active_localization.append(
                pd.NA
            )

    # --------------------------------------------------------
    # Convert wide measurements to long-form records
    # --------------------------------------------------------

    for sensor_id in MEASUREMENT_COLUMNS:

        if sensor_id not in raw.columns:
            continue

        # Native measurement family.
        if sensor_id.startswith("PS"):
            variable = "PS"
            unit = "MPa"

        elif sensor_id.startswith("MFS"):
            variable = "MFS"
            unit = "kg/s"

        else:
            variable = sensor_id
            unit = pd.NA

        sensor_values = raw[sensor_id]

        for position, index in enumerate(raw.index):

            # ------------------------------------------------
            # Determine anomaly type from native labels only.
            # ------------------------------------------------

            if any(
                (
                    column in localization_values
                    and pd.notna(
                        localization_values[column].loc[index]
                    )
                    and localization_values[column].loc[index] == 1
                )
                for column in LOCALIZATION_COLUMNS
            ):
                anomaly_type = "LEAK"

            elif (
                "CompressorFault" in raw.columns
                and raw["CompressorFault"].loc[index] == 1
            ):
                anomaly_type = "COMPRESSOR_FAULT"

            elif (
                "CompressorDelay" in raw.columns
                and raw["CompressorDelay"].loc[index] == 1
            ):
                anomaly_type = "COMPRESSOR_DELAY"

            else:
                anomaly_type = pd.NA

            # ------------------------------------------------
            # Build standardized record.
            # ------------------------------------------------

            record = {
                "timestamp": timestamp.loc[index],

                "scenario_id": scenario_id,

                "run_id": run_id,

                # Physical station mapping is intentionally
                # unavailable/unverified in H2-SimNet.
                "station_id": pd.NA,

                # Preserve native sensor identity.
                "sensor_id": sensor_id,

                # Measurement family only.
                # Native sensor identity remains in sensor_id.
                "variable": variable,

                "value": sensor_values.loc[index],

                "unit": unit,

                # Native anomaly label.
                "label": anomaly_label.loc[index],

                "operational_phase": operational_phase,

                "anomaly_type": anomaly_type,

                # Component-level localization only.
                "localization": active_localization[position],

                # ------------------------------------------------
                # Source metadata
                # ------------------------------------------------

                "source_file": str(path),

                "source_format": (
                    path.suffix
                    .lower()
                    .lstrip(".")
                ),

                "configuration": configuration,

                "timestamp_is_derived": (
                    timestamp_is_derived
                ),

                # ------------------------------------------------
                # Preserve native ground-truth metadata
                # ------------------------------------------------

                "label_anomaly": (
                    raw["label_anomaly"].loc[index]
                    if "label_anomaly" in raw.columns
                    else pd.NA
                ),

                "Leak": (
                    raw["Leak"].loc[index]
                    if "Leak" in raw.columns
                    else pd.NA
                ),

                "CompressorFault": (
                    raw["CompressorFault"].loc[index]
                    if "CompressorFault" in raw.columns
                    else pd.NA
                ),

                "CompressorDelay": (
                    raw["CompressorDelay"].loc[index]
                    if "CompressorDelay" in raw.columns
                    else pd.NA
                ),

                "leak_G3": (
                    raw["leak_G3"].loc[index]
                    if "leak_G3" in raw.columns
                    else pd.NA
                ),

                "leak_G4": (
                    raw["leak_G4"].loc[index]
                    if "leak_G4" in raw.columns
                    else pd.NA
                ),

                "leak_G5": (
                    raw["leak_G5"].loc[index]
                    if "leak_G5" in raw.columns
                    else pd.NA
                ),

                "leak_G6": (
                    raw["leak_G6"].loc[index]
                    if "leak_G6" in raw.columns
                    else pd.NA
                ),
            }

            records.append(record)

    standardized = pd.DataFrame(
        records
    )

    return standardized


# ============================================================
# LEGACY MOCK SCENARIO GENERATOR
# ============================================================

def generate_mock_scenario(
    scenario_type: str = "normal",
    duration_s: float = 600.0,
    dt: float = 1.0,
    pipe_length_m: float = 10000.0,
    wave_speed_m_s: float = 1300.0,
    random_seed: int = 42,
) -> pd.DataFrame:
    """
    Generate synthetic/mock pipeline segment data for testing
    and mock pipeline execution.

    This legacy development interface is intentionally retained
    because existing physics/features/model/pipeline tests depend
    on its wide-form columns.

    Scenarios:
        normal
        leak
        operational_transient
        sensor_fault
        ambiguous

    Important:
        This mock schema is separate from the native H2-SimNet
        standardization layer.
    """
    rng = np.random.default_rng(
        random_seed
    )

    # --------------------------------------------------------
    # Build the actual time vector first.
    #
    # This guarantees that every generated signal has exactly
    # the same number of samples, including large dt values.
    # --------------------------------------------------------

    time = np.arange(
        0,
        duration_s,
        dt,
    )

    n_steps = len(time)

    # --------------------------------------------------------
    # Base operating conditions
    # --------------------------------------------------------

    base_p1 = 5.0e6

    pressure_drop = 0.2e6

    base_p2 = (
        base_p1
        - pressure_drop
    )

    base_flow = 12.0

    # --------------------------------------------------------
    # Base signals
    # --------------------------------------------------------

    p1 = (
        base_p1
        + rng.normal(
            0,
            500.0,
            size=n_steps,
        )
    )

    p2 = (
        base_p2
        + rng.normal(
            0,
            500.0,
            size=n_steps,
        )
    )

    m1 = (
        base_flow
        + rng.normal(
            0,
            0.02,
            size=n_steps,
        )
    )

    m2 = (
        base_flow
        + rng.normal(
            0,
            0.02,
            size=n_steps,
        )
    )

    label = np.array(
        ["NORMAL"] * n_steps,
        dtype=object,
    )

    t_event = int(
        n_steps * 0.4
    )

    # ========================================================
    # LEAK
    # ========================================================

    if scenario_type == "leak":

        leak_rate = 0.8

        delay_steps = int(
            (
                pipe_length_m * 0.5
            )
            / (
                wave_speed_m_s * dt
            )
        )

        delay_steps = max(
            1,
            delay_steps,
        )

        p1[t_event:] -= 0.05e6

        if (
            t_event + delay_steps
            < n_steps
        ):
            p2[
                t_event + delay_steps:
            ] -= 0.08e6

            m2[
                t_event + delay_steps:
            ] -= leak_rate

        label[
            t_event:
        ] = "LEAK"

    # ========================================================
    # OPERATIONAL TRANSIENT
    # ========================================================

    elif scenario_type == "operational_transient":

        ramp_duration = max(
            1,
            int(30 / dt),
        )

        ramp = np.linspace(
            0,
            2.0,
            ramp_duration,
        )

        ramp_end = min(
            t_event + ramp_duration,
            n_steps,
        )

        m1[
            t_event:ramp_end
        ] += ramp[
            : ramp_end - t_event
        ]

        m1[
            ramp_end:
        ] += 2.0

        lag = int(
            5 / dt
        )

        t_down = (
            t_event
            + lag
        )

        if t_down < n_steps:

            ramp_down_end = min(
                t_down + ramp_duration,
                n_steps,
            )

            m2[
                t_down:ramp_down_end
            ] += ramp[
                : ramp_down_end - t_down
            ]

            m2[
                ramp_down_end:
            ] += 2.0

            p2[
                t_down:
            ] += 0.12e6

        p1[
            t_event:
        ] += 0.15e6

        label[
            t_event:
        ] = "OPERATIONAL_TRANSIENT"

    # ========================================================
    # SENSOR FAULT
    # ========================================================

    elif scenario_type == "sensor_fault":

        p2[
            t_event:
        ] -= 0.3e6

        label[
            t_event:
        ] = "SENSOR_FAULT"

    # ========================================================
    # AMBIGUOUS
    # ========================================================

    elif scenario_type == "ambiguous":

        p1[
            t_event:
        ] -= rng.uniform(
            500,
            2000,
            size=n_steps - t_event,
        )

        p2[
            t_event:
        ] -= rng.uniform(
            500,
            2000,
            size=n_steps - t_event,
        )

        m2[
            t_event:
        ] -= 0.05

        label[
            t_event:
        ] = "AMBIGUOUS"

    # ========================================================
    # RETURN LEGACY WIDE-FORM DATAFRAME
    # ========================================================

    df = pd.DataFrame(
        {
            "timestamp": time,

            "scenario_id":
                f"mock_{scenario_type}_001",

            "run_id":
                "run_01",

            "p_upstream": p1,

            "p_downstream": p2,

            "m_inlet": m1,

            "m_outlet": m2,

            "label": label,
        }
    )

    return df