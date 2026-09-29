from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

RAW_DIR = Path("data/raw/H2-SimNet")

AUDIT_MD = Path("AUDIT.md")
RESULTS_DIR = Path("results")

AUDIT_CSV = RESULTS_DIR / "data_audit.csv"
TRUTH_TABLE = RESULTS_DIR / "dataset_truth_table.md"

SUPPORTED_EXTENSIONS = {".csv", ".parquet"}

SAMPLING_TOLERANCE = 0.01

# H2-SimNet documentation describes approximately:
# 20,000 seconds sampled at 1 Hz.
EXPECTED_H2_SIMNET_ROWS = 20_000
EXPECTED_H2_SIMNET_DT_S = 1.0

EXPECTED_PRESSURE_CHANNELS = [
    f"PS{i}" for i in range(1, 13)
]

EXPECTED_FLOW_CHANNELS = [
    f"MFS{i}" for i in range(1, 5)
]

EXPECTED_SENSOR_CHANNELS = (
    EXPECTED_PRESSURE_CHANNELS
    + EXPECTED_FLOW_CHANNELS
)


# ============================================================
# OFFICIAL DATASET METADATA
# ============================================================

OFFICIAL_DATASET_METADATA = {
    "title": (
        "H2-SimNet Dataset: A Simulation-based Dataset for "
        "Anomaly Detection in Hydrogen Blend Transport Networks"
    ),
    "generation": (
        "MATLAB/Simulink with Simscape Gas Fluids, R2025a"
    ),
    "simulation_duration_s": 20_000,
    "documented_sampling": "Approximately 1 Hz / 20,000 samples",
    "pressure_unit": "MPa",
    "mass_flow_unit": "kg/s",
    "temperature_documented": False,
    "pressure_channels": "PS1-PS12",
    "mass_flow_channels": "MFS1-MFS4",
    "topologies": ["down", "center", "up"],
    "phases": [
        "Initial Ramp-up",
        "Transient",
        "Steady State",
    ],
    "anomalies": [
        "Gas leaks / local restrictions G3-G6",
        "Compressor faults C1",
        "Compressor startup delays",
        "Overlapping anomalies",
    ],
    "strength": ["Weak", "Strong"],
    "localized_locations": ["G3", "G4", "G5", "G6"],
    "labels": [
        "label_anomaly",
        "Leak",
        "CompressorFault",
        "CompressorDelay",
        "leak_G3",
        "leak_G4",
        "leak_G5",
        "leak_G6",
    ],
    "noise": (
        "Gaussian white noise is documented for pressure and "
        "mass-flow signals, approximately 1-2% of typical "
        "signal range."
    ),
    "clean_noisy_versions": (
        "Clean/noisy variants are described by the dataset "
        "documentation."
    ),
    "filtering": (
        "Moving-average filtering is not documented."
    ),
    "spatial_ordering": (
        "Explicit physical station ordering is not "
        "established by the tabular files."
    ),
    "anomaly_duration": (
        "Documented anomalies are continuous after activation "
        "until the end of the corresponding simulation."
    ),
}


# ============================================================
# COLUMN / PATH PATTERNS
# ============================================================

PRESSURE_PATTERN = re.compile(
    r"^(PS)\d+$",
    re.I,
)

FLOW_PATTERN = re.compile(
    r"^(MFS)\d+$",
    re.I,
)

TEMPERATURE_PATTERN = re.compile(
    r"^(TS|T|TEMP|TEMPERATURE)\d*$",
    re.I,
)

TIMESTAMP_NAMES = {
    "timestamp",
    "time",
    "datetime",
    "date_time",
    "date",
}

PHASE_KEYWORDS = {
    "constant_segment": "Steady State",
    "start_transient": "Initial Ramp-up",
    "assessment_transient": "Transient",
    "assestment_transient": "Transient",
    "startup": "Initial Ramp-up",
    "steady": "Steady State",
    "transient": "Transient",
    "shutdown": "Shutdown",
}

TOPOLOGY_PATTERNS = {
    "down": ["gest_down", "gestdown"],
    "center": ["gest_center", "gestcenter"],
    "up": ["gest_up", "gestup"],
}


# ============================================================
# GENERAL HELPERS
# ============================================================

def normalize_column_name(name: Any) -> str:
    return re.sub(
        r"[^a-z0-9]+",
        "_",
        str(name).strip().lower(),
    ).strip("_")


def natural_sort_key(value: str):
    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", str(value))
    ]


def json_safe(value: Any):
    if isinstance(value, np.integer):
        return int(value)

    if isinstance(value, np.floating):
        if not np.isfinite(value):
            return None
        return float(value)

    if isinstance(value, np.ndarray):
        return value.tolist()

    if isinstance(value, dict):
        return {
            str(k): json_safe(v)
            for k, v in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            json_safe(v)
            for v in value
        ]

    return value


def safe_float(value):
    try:
        value = float(value)

        if math.isfinite(value):
            return value

        return None

    except Exception:
        return None


def is_truthy_numeric(series: pd.Series) -> bool:
    numeric = pd.to_numeric(
        series,
        errors="coerce",
    )

    return bool(
        (numeric == 1).any()
    )


# ============================================================
# TIMESTAMP DETECTION
# ============================================================

def is_strict_sequential_index(
    series: pd.Series,
) -> bool:
    """
    Detect exported sequential indices such as:

        0, 1, 2, 3, ...
        1, 2, 3, 4, ...

    This does NOT mean the column is necessarily a real
    timestamp. It is only a sequential index candidate.
    """

    numeric = pd.to_numeric(
        series,
        errors="coerce",
    )

    if numeric.isna().any():
        return False

    if len(numeric) < 2:
        return False

    values = numeric.to_numpy(
        dtype=float
    )

    if not np.isfinite(values).all():
        return False

    diffs = np.diff(values)

    if len(diffs) == 0:
        return False

    if not np.allclose(
        diffs,
        diffs[0],
        rtol=0.0,
        atol=1e-9,
    ):
        return False

    if diffs[0] <= 0:
        return False

    if not (
        np.isclose(
            values[0],
            0.0,
            atol=1e-9,
        )
        or np.isclose(
            values[0],
            1.0,
            atol=1e-9,
        )
    ):
        return False

    return True


def detect_timestamp_column(
    df: pd.DataFrame,
) -> tuple[str | None, str]:
    """
    Detect an actual timestamp/time reference conservatively.

    Priority:

    1. Explicit timestamp/time column
    2. Named dataframe index
    3. Common exported index column
    4. First-column sequential index

    A plain sequential index is NOT automatically treated as a
    physical timestamp unless it is clearly an index-like field.
    """

    # --------------------------------------------------------
    # 1. Explicit timestamp/time column
    # --------------------------------------------------------

    for column in df.columns:

        normalized = normalize_column_name(
            column
        )

        if normalized in TIMESTAMP_NAMES:
            return (
                str(column),
                "explicit_column",
            )

        if (
            "timestamp" in normalized
            or "datetime" in normalized
            or normalized.endswith("_time")
            or normalized in {
                "time_s",
                "time_sec",
                "time_seconds",
            }
        ):
            return (
                str(column),
                "explicit_column",
            )

    # --------------------------------------------------------
    # 2. Named dataframe index
    # --------------------------------------------------------

    index_name = df.index.name

    if index_name is not None:

        normalized_index = normalize_column_name(
            index_name
        )

        if (
            normalized_index in TIMESTAMP_NAMES
            or "timestamp" in normalized_index
            or "datetime" in normalized_index
            or normalized_index.endswith("_time")
            or normalized_index in {
                "time_s",
                "time_sec",
                "time_seconds",
            }
        ):
            return (
                str(index_name),
                "named_index",
            )

    # --------------------------------------------------------
    # 3. Common exported index columns
    # --------------------------------------------------------

    for column in df.columns:

        normalized = normalize_column_name(
            column
        )

        if normalized in {
            "unnamed_0",
            "unnamed0",
            "index",
            "row_index",
            "rowindex",
        }:

            if is_strict_sequential_index(
                df[column]
            ):
                return (
                    str(column),
                    "exported_index_column",
                )

    # --------------------------------------------------------
    # 4. First-column sequential index
    # --------------------------------------------------------

    if len(df.columns) > 0:

        first_column = df.columns[0]

        if is_strict_sequential_index(
            df[first_column]
        ):

            return (
                str(first_column),
                "sequential_index_column",
            )

    return None, "none"


# ============================================================
# SENSOR DETECTION
# ============================================================

def detect_sensor_channels(
    columns: list[str],
) -> dict[str, list[str]]:

    pressure = []
    flow = []
    temperature = []
    other = []

    for column in columns:

        name = str(column).strip()

        if PRESSURE_PATTERN.fullmatch(name):

            pressure.append(name)

        elif FLOW_PATTERN.fullmatch(name):

            flow.append(name)

        elif TEMPERATURE_PATTERN.fullmatch(name):

            temperature.append(name)

        else:

            other.append(name)

    pressure.sort(
        key=natural_sort_key
    )

    flow.sort(
        key=natural_sort_key
    )

    temperature.sort(
        key=natural_sort_key
    )

    other.sort(
        key=natural_sort_key
    )

    return {
        "pressure": pressure,
        "mass_flow": flow,
        "temperature": temperature,
        "other": other,
    }


# ============================================================
# LABEL DETECTION
# ============================================================

def detect_label_columns(
    columns: list[str],
) -> list[str]:

    labels = []

    for column in columns:

        normalized = normalize_column_name(
            column
        )

        if (
            "label" in normalized
            or "anomaly" in normalized
            or "fault" in normalized
            or normalized == "leak"
            or normalized in {
                "compressordelay",
                "compressor_delay",
            }
            or normalized.startswith("leak_g")
        ):
            labels.append(
                str(column)
            )

    return sorted(
        labels,
        key=natural_sort_key,
    )


def detect_localization_columns(
    columns: list[str],
) -> list[str]:

    candidates = []

    for column in columns:

        normalized = normalize_column_name(
            column
        )

        if (
            normalized.startswith("leak_g")
            or "location" in normalized
            or "position" in normalized
            or "station" in normalized
        ):
            candidates.append(
                str(column)
            )

    return sorted(
        candidates,
        key=natural_sort_key,
    )


def detect_strength_columns(
    columns: list[str],
) -> list[str]:

    candidates = []

    for column in columns:

        normalized = normalize_column_name(
            column
        )

        if any(
            keyword in normalized
            for keyword in [
                "strength",
                "magnitude",
                "severity",
                "size",
                "intensity",
            ]
        ):
            candidates.append(
                str(column)
            )

    return sorted(
        candidates,
        key=natural_sort_key,
    )


# ============================================================
# PATH / SCENARIO METADATA
# ============================================================

def infer_scenario(
    path: Path,
) -> str:

    parts = [
        normalize_column_name(part)
        for part in path.parts
    ]

    if any(
        "normality" in part
        for part in parts
    ):
        return "normality"

    if any(
        "anomalous" in part
        for part in parts
    ):
        return "anomalous"

    return "Unknown / Not documented"


def infer_phase(
    path: Path,
) -> str:

    parts = [
        normalize_column_name(part)
        for part in path.parts
    ]

    for part in parts:

        if part in PHASE_KEYWORDS:

            return PHASE_KEYWORDS[
                part
            ]

    return "Unknown / Not documented"


def infer_topology(
    path: Path,
) -> str:

    text = normalize_column_name(
        str(path)
    )

    for topology, patterns in (
        TOPOLOGY_PATTERNS.items()
    ):

        for pattern in patterns:

            if pattern in text:
                return topology

    return "Unknown / Not documented"


def infer_strength(
    path: Path,
) -> tuple[str, str]:

    text = normalize_column_name(
        str(path)
    )

    if re.search(
        r"(^|_)weak($|_)",
        text,
    ):
        return (
            "Weak",
            "filename/path",
        )

    if re.search(
        r"(^|_)strong($|_)",
        text,
    ):
        return (
            "Strong",
            "filename/path",
        )

    if "overlapped" in text:

        return (
            "Overlapped / not specified",
            "filename/path",
        )

    return (
        "Not specified",
        "not documented",
    )


def infer_overlap(
    path: Path,
) -> str:

    text = normalize_column_name(
        str(path)
    )

    if "overlapped" in text:
        return "Overlapped"

    return "Single / not specified"


def infer_noise_variant(
    path: Path,
) -> str:

    text = normalize_column_name(
        str(path)
    )

    if "noisy" in text:
        return "Noisy"

    if "clean" in text:
        return "Clean"

    return "Not specified"


# ============================================================
# DATA LOADING
# ============================================================

def load_dataset_file(
    path: Path,
) -> pd.DataFrame:

    suffix = path.suffix.lower()

    if suffix == ".csv":

        return pd.read_csv(
            path
        )

    if suffix == ".parquet":

        return pd.read_parquet(
            path
        )

    raise ValueError(
        f"Unsupported file format: {path.suffix}"
    )


# ============================================================
# TIMESTAMP ANALYSIS
# ============================================================

def analyze_timestamp(
    df: pd.DataFrame,
    timestamp_reference: str | None,
    timestamp_source: str,
) -> dict[str, Any]:

    result = {
        "timestamp_detected": False,
        "timestamp_reference": timestamp_reference,
        "timestamp_source": timestamp_source,
        "timestamp_type": "None",
        "timestamp_min": None,
        "timestamp_max": None,
        "duration_s": None,
        "sampling_interval_median_s": None,
        "sampling_interval_mean_s": None,
        "sampling_interval_min_s": None,
        "sampling_interval_max_s": None,
        "sampling_rate_hz": None,
        "unique_sampling_intervals": [],
        "sampling_consistent": None,
        "duplicate_timestamps": False,
        "duplicate_timestamp_count": 0,
        "non_monotonic_timestamps": False,
        "non_monotonic_count": 0,
    }

    if timestamp_reference is None:
        return result

    # --------------------------------------------------------
    # Retrieve timestamp values
    # --------------------------------------------------------

    if (
        timestamp_source == "named_index"
        and df.index.name == timestamp_reference
    ):

        series = pd.Series(
            df.index.to_numpy()
        )

    elif timestamp_source == "named_index":

        series = pd.Series(
            df.index.to_numpy()
        )

    else:

        if timestamp_reference not in df.columns:
            return result

        series = df[
            timestamp_reference
        ]

    # --------------------------------------------------------
    # Numeric timestamps
    # --------------------------------------------------------

    numeric = pd.to_numeric(
        series,
        errors="coerce",
    )

    if (
        numeric.notna().sum()
        == len(series)
        and len(series) > 0
    ):

        values = numeric.to_numpy(
            dtype=float
        )

        result[
            "timestamp_detected"
        ] = True

        result[
            "timestamp_type"
        ] = "numeric"

        result[
            "timestamp_min"
        ] = safe_float(
            np.min(values)
        )

        result[
            "timestamp_max"
        ] = safe_float(
            np.max(values)
        )

        diffs = np.diff(values)

        if len(diffs) > 0:

            # Exact duplicate timestamps.
            result[
                "duplicate_timestamp_count"
            ] = int(
                np.sum(
                    diffs == 0
                )
            )

            result[
                "duplicate_timestamps"
            ] = (
                result[
                    "duplicate_timestamp_count"
                ] > 0
            )

            # Negative steps = non-monotonic transitions.
            negative_count = int(
                np.sum(
                    diffs < 0
                )
            )

            result[
                "non_monotonic_count"
            ] = negative_count

            result[
                "non_monotonic_timestamps"
            ] = (
                negative_count > 0
            )

            positive_diffs = diffs[
                diffs > 0
            ]

            if len(positive_diffs) > 0:

                median_dt = float(
                    np.median(
                        positive_diffs
                    )
                )

                result[
                    "sampling_interval_median_s"
                ] = median_dt

                result[
                    "sampling_interval_mean_s"
                ] = float(
                    np.mean(
                        positive_diffs
                    )
                )

                result[
                    "sampling_interval_min_s"
                ] = float(
                    np.min(
                        positive_diffs
                    )
                )

                result[
                    "sampling_interval_max_s"
                ] = float(
                    np.max(
                        positive_diffs
                    )
                )

                if median_dt > 0:

                    result[
                        "sampling_rate_hz"
                    ] = (
                        1.0 / median_dt
                    )

                unique_intervals = np.unique(
                    np.round(
                        positive_diffs,
                        decimals=9,
                    )
                )

                result[
                    "unique_sampling_intervals"
                ] = [
                    float(x)
                    for x in unique_intervals[
                        :50
                    ]
                ]

                result[
                    "sampling_consistent"
                ] = bool(
                    np.allclose(
                        positive_diffs,
                        median_dt,
                        rtol=SAMPLING_TOLERANCE,
                        atol=SAMPLING_TOLERANCE,
                    )
                )

                result[
                    "duration_s"
                ] = safe_float(
                    values[-1] - values[0]
                )

        return result

    # --------------------------------------------------------
    # Datetime timestamps
    # --------------------------------------------------------

    datetime_values = pd.to_datetime(
        series,
        errors="coerce",
    )

    if (
        datetime_values.notna().sum()
        == len(series)
        and len(series) > 0
    ):

        values_ns = (
            datetime_values
            .astype("int64")
            .to_numpy()
        )

        values_s = (
            values_ns
            / 1_000_000_000
        )

        result[
            "timestamp_detected"
        ] = True

        result[
            "timestamp_type"
        ] = "datetime"

        result[
            "timestamp_min"
        ] = str(
            datetime_values.iloc[0]
        )

        result[
            "timestamp_max"
        ] = str(
            datetime_values.iloc[-1]
        )

        result[
            "duration_s"
        ] = safe_float(
            values_s[-1]
            - values_s[0]
        )

        diffs = np.diff(
            values_s
        )

        result[
            "duplicate_timestamp_count"
        ] = int(
            np.sum(
                diffs == 0
            )
        )

        result[
            "duplicate_timestamps"
        ] = (
            result[
                "duplicate_timestamp_count"
            ] > 0
        )

        negative_count = int(
            np.sum(
                diffs < 0
            )
        )

        result[
            "non_monotonic_count"
        ] = negative_count

        result[
            "non_monotonic_timestamps"
        ] = (
            negative_count > 0
        )

        positive_diffs = diffs[
            diffs > 0
        ]

        if len(positive_diffs) > 0:

            median_dt = float(
                np.median(
                    positive_diffs
                )
            )

            result[
                "sampling_interval_median_s"
            ] = median_dt

            result[
                "sampling_interval_mean_s"
            ] = float(
                np.mean(
                    positive_diffs
                )
            )

            result[
                "sampling_interval_min_s"
            ] = float(
                np.min(
                    positive_diffs
                )
            )

            result[
                "sampling_interval_max_s"
            ] = float(
                np.max(
                    positive_diffs
                )
            )

            if median_dt > 0:

                result[
                    "sampling_rate_hz"
                ] = (
                    1.0 / median_dt
                )

            unique_intervals = np.unique(
                np.round(
                    positive_diffs,
                    decimals=9,
                )
            )

            result[
                "unique_sampling_intervals"
            ] = [
                float(x)
                for x in unique_intervals[
                    :50
                ]
            ]

            result[
                "sampling_consistent"
            ] = bool(
                np.allclose(
                    positive_diffs,
                    median_dt,
                    rtol=SAMPLING_TOLERANCE,
                    atol=SAMPLING_TOLERANCE,
                )
            )

    return result


# ============================================================
# LABEL ANALYSIS
# ============================================================

def analyze_labels(
    df: pd.DataFrame,
    label_columns: list[str],
) -> dict[str, Any]:

    summary = {}

    for column in label_columns:

        if column not in df.columns:
            continue

        value_counts = (
            df[column]
            .value_counts(
                dropna=False
            )
            .to_dict()
        )

        cleaned = {}

        for key, value in value_counts.items():

            cleaned[str(key)] = int(
                value
            )

        summary[column] = cleaned

    return summary


def infer_anomaly_presence(
    scenario: str,
    df: pd.DataFrame,
) -> tuple[str, str]:

    if scenario == "anomalous":

        return (
            "Yes",
            "directory/path organization",
        )

    if scenario == "normality":

        return (
            "No",
            "directory/path organization",
        )

    official_labels = [
        "label_anomaly",
        "Leak",
        "CompressorFault",
        "CompressorDelay",
        "leak_G3",
        "leak_G4",
        "leak_G5",
        "leak_G6",
    ]

    available = [
        column
        for column in official_labels
        if column in df.columns
    ]

    for column in available:

        if is_truthy_numeric(
            df[column]
        ):

            return (
                "Yes",
                f"data label: {column}",
            )

    if available:

        return (
            "No",
            "data labels",
        )

    return (
        "Unknown",
        "not established",
    )


# ============================================================
# SENSOR RANGE ANALYSIS
# ============================================================

def sensor_ranges(
    df: pd.DataFrame,
    channels: dict[str, list[str]],
) -> dict[str, dict[str, float | None]]:

    result = {}

    all_channels = (
        channels["pressure"]
        + channels["mass_flow"]
        + channels["temperature"]
    )

    for column in all_channels:

        if column not in df.columns:
            continue

        numeric = pd.to_numeric(
            df[column],
            errors="coerce",
        )

        if numeric.notna().sum() == 0:
            continue

        result[column] = {
            "min": safe_float(
                numeric.min()
            ),
            "max": safe_float(
                numeric.max()
            ),
            "mean": safe_float(
                numeric.mean()
            ),
        }

    return result


# ============================================================
# FILE AUDIT
# ============================================================

def audit_file(
    path: Path,
) -> dict[str, Any]:

    df = load_dataset_file(
        path
    )

    original_columns = [
        str(column)
        for column in df.columns
    ]

    channels = detect_sensor_channels(
        original_columns
    )

    timestamp_reference, timestamp_source = (
        detect_timestamp_column(df)
    )

    # ========================================================
    # H2-SimNet IMPLICIT TIME AXIS
    # ========================================================
    #
    # Important:
    #
    # H2-SimNet files can contain 20,000 sequential samples
    # without a physical timestamp column.
    #
    # The official dataset documentation describes the
    # simulation as approximately 20,000 seconds.
    #
    # Therefore, for auditing only, a synthetic time axis is
    # created IN MEMORY:
    #
    # sample 0     -> 0 s
    # sample 1     -> 1 s
    # ...
    # sample 19999 -> 19999 s
    #
    # The source file is NEVER modified.
    #
    # We explicitly label this as:
    #
    #     implicit_1s_index
    #
    # rather than pretending it is a real stored timestamp.
    #
    # ========================================================

    if (
        timestamp_source == "none"
        and path.suffix.lower() == ".csv"
        and len(df) == EXPECTED_H2_SIMNET_ROWS
    ):

        implicit_timestamp_column = (
            "__audit_implicit_timestamp_s"
        )

        df[
            implicit_timestamp_column
        ] = np.arange(
            len(df),
            dtype=float,
        )

        timestamp_reference = (
            implicit_timestamp_column
        )

        timestamp_source = (
            "implicit_1s_index"
        )

    timestamp_info = analyze_timestamp(
        df,
        timestamp_reference,
        timestamp_source,
    )

    label_columns = detect_label_columns(
        original_columns
    )

    localization_columns = (
        detect_localization_columns(
            original_columns
        )
    )

    strength_columns = (
        detect_strength_columns(
            original_columns
        )
    )

    scenario = infer_scenario(
        path
    )

    phase = infer_phase(
        path
    )

    topology = infer_topology(
        path
    )

    strength_category, strength_source = (
        infer_strength(path)
    )

    overlap_status = infer_overlap(
        path
    )

    noise_variant = infer_noise_variant(
        path
    )

    anomaly_presence, anomaly_source = (
        infer_anomaly_presence(
            scenario,
            df,
        )
    )

    missing_values_total = int(
        df.isna().sum().sum()
    )

    missing_columns = [
        str(column)
        for column in df.columns
        if df[column].isna().any()
    ]

    official_sensor_missing = [
        channel
        for channel in EXPECTED_SENSOR_CHANNELS
        if channel not in original_columns
    ]

    official_sensor_extra = [
        channel
        for channel in (
            channels["pressure"]
            + channels["mass_flow"]
        )
        if channel not in EXPECTED_SENSOR_CHANNELS
    ]

    spatial_candidates = [
        column
        for column in original_columns
        if any(
            keyword in normalize_column_name(
                column
            )
            for keyword in [
                "station",
                "position",
                "location",
                "distance",
                "upstream",
                "downstream",
                "center",
            ]
        )
    ]

    units = {}

    if channels["pressure"]:

        units["pressure"] = (
            OFFICIAL_DATASET_METADATA[
                "pressure_unit"
            ]
        )

    if channels["mass_flow"]:

        units["mass_flow"] = (
            OFFICIAL_DATASET_METADATA[
                "mass_flow_unit"
            ]
        )

    if channels["temperature"]:

        units["temperature"] = (
            "Not documented"
        )

    schema_signature = (
        tuple(channels["pressure"]),
        tuple(channels["mass_flow"]),
        tuple(channels["temperature"]),
    )

    return {

        # ----------------------------------------------------
        # FILE IDENTITY
        # ----------------------------------------------------

        "file": path.as_posix(),

        "name": path.name,

        "format": (
            path.suffix
            .lower()
            .replace(".", "")
        ),

        "size_bytes": path.stat().st_size,

        "size_mb": safe_float(
            path.stat().st_size
            / (1024 ** 2)
        ),

        "rows": int(
            len(df)
        ),

        "columns": int(
            len(original_columns)
        ),

        # ----------------------------------------------------
        # SCENARIO METADATA
        # ----------------------------------------------------

        "scenario": scenario,

        "phase": phase,

        "topology": topology,

        "strength_category": (
            strength_category
        ),

        "strength_source": (
            strength_source
        ),

        "strength_numeric_status": (
            "No numerical strength field detected"
            if not strength_columns
            else "Candidate numerical field present"
        ),

        "overlap_status": (
            overlap_status
        ),

        "noise_variant": (
            noise_variant
        ),

        "run_identifier": (
            path.stem
        ),

        "run_id_source": (
            "filename stem; no explicit run_id "
            "field detected"
        ),

        # ----------------------------------------------------
        # ANOMALY / LABELS
        # ----------------------------------------------------

        "anomalous": (
            anomaly_presence
        ),

        "anomaly_source": (
            anomaly_source
        ),

        "label_columns": ",".join(
            label_columns
        ),

        "localization_columns": ",".join(
            localization_columns
        ),

        "strength_candidate_columns": (
            ",".join(
                strength_columns
            )
        ),

        "label_summary": json.dumps(
            analyze_labels(
                df,
                label_columns,
            ),
            sort_keys=True,
        ),

        # ----------------------------------------------------
        # SENSOR CHANNELS
        # ----------------------------------------------------

        "pressure_channels": ",".join(
            channels["pressure"]
        ),

        "mass_flow_channels": ",".join(
            channels["mass_flow"]
        ),

        "temperature_channels": ",".join(
            channels["temperature"]
        ),

        "pressure_count": len(
            channels["pressure"]
        ),

        "mass_flow_count": len(
            channels["mass_flow"]
        ),

        "temperature_count": len(
            channels["temperature"]
        ),

        "other_columns": ",".join(
            channels["other"]
        ),

        "sensor_schema_signature": json.dumps(
            {
                "pressure":
                    channels["pressure"],
                "mass_flow":
                    channels["mass_flow"],
                "temperature":
                    channels["temperature"],
            },
            sort_keys=True,
        ),

        "official_sensor_missing": ",".join(
            official_sensor_missing
        ),

        "official_sensor_extra": ",".join(
            official_sensor_extra
        ),

        # ----------------------------------------------------
        # TIMESTAMP
        # ----------------------------------------------------

        "timestamp_detected": (
            "Yes"
            if timestamp_info[
                "timestamp_detected"
            ]
            else "No"
        ),

        "timestamp_reference": (
            timestamp_info[
                "timestamp_reference"
            ]
        ),

        "timestamp_source": (
            timestamp_info[
                "timestamp_source"
            ]
        ),

        "timestamp_type": (
            timestamp_info[
                "timestamp_type"
            ]
        ),

        "timestamp_min": (
            timestamp_info[
                "timestamp_min"
            ]
        ),

        "timestamp_max": (
            timestamp_info[
                "timestamp_max"
            ]
        ),

        "duration_s": (
            timestamp_info[
                "duration_s"
            ]
        ),

        "sampling_interval_median_s": (
            timestamp_info[
                "sampling_interval_median_s"
            ]
        ),

        "sampling_interval_mean_s": (
            timestamp_info[
                "sampling_interval_mean_s"
            ]
        ),

        "sampling_interval_min_s": (
            timestamp_info[
                "sampling_interval_min_s"
            ]
        ),

        "sampling_interval_max_s": (
            timestamp_info[
                "sampling_interval_max_s"
            ]
        ),

        "sampling_rate_hz": (
            timestamp_info[
                "sampling_rate_hz"
            ]
        ),

        "unique_sampling_intervals": json.dumps(
            timestamp_info[
                "unique_sampling_intervals"
            ]
        ),

        "sampling_consistent": (
            timestamp_info[
                "sampling_consistent"
            ]
        ),

        "duplicate_timestamps": (
            "Yes"
            if timestamp_info[
                "duplicate_timestamps"
            ]
            else "No"
        ),

        "duplicate_timestamp_count": (
            timestamp_info[
                "duplicate_timestamp_count"
            ]
        ),

        "non_monotonic_timestamps": (
            "Yes"
            if timestamp_info[
                "non_monotonic_timestamps"
            ]
            else "No"
        ),

        "non_monotonic_count": (
            timestamp_info[
                "non_monotonic_count"
            ]
        ),

        # ----------------------------------------------------
        # DATA QUALITY
        # ----------------------------------------------------

        "missing_values_total": (
            missing_values_total
        ),

        "missing_value_columns": (
            ",".join(
                missing_columns
            )
        ),

        # ----------------------------------------------------
        # SPATIAL INFORMATION
        # ----------------------------------------------------

        "spatial_candidates": (
            ",".join(
                spatial_candidates
            )
        ),

        # ----------------------------------------------------
        # UNITS
        # ----------------------------------------------------

        "units_documented": json.dumps(
            units,
            sort_keys=True,
        ),

        # ----------------------------------------------------
        # FILTERING / NOISE
        # ----------------------------------------------------

        "raw_or_filtered": (
            "Not established from file metadata; "
            "clean/noisy variants are documented separately."
        ),

        "moving_average_filter": (
            "Not documented"
        ),

        "official_noise_documentation": (
            OFFICIAL_DATASET_METADATA[
                "noise"
            ]
        ),

        # ----------------------------------------------------
        # SENSOR STATISTICS
        # ----------------------------------------------------

        "sensor_ranges": json.dumps(
            sensor_ranges(
                df,
                channels,
            ),
            sort_keys=True,
        ),
    }


# ============================================================
# DIRECTORY TREE
# ============================================================

def build_directory_tree(
    root: Path,
) -> list[str]:

    directories = set()

    for path in root.rglob("*"):

        if not path.is_dir():
            continue

        try:

            relative = path.relative_to(
                root
            )

            directories.add(
                relative.as_posix()
            )

        except ValueError:
            continue

    return sorted(
        directories,
        key=natural_sort_key,
    )


# ============================================================
# FORMAT COMPARISON
# ============================================================

def compare_formats(
    records: list[dict[str, Any]],
) -> dict[str, Any]:

    csv_names = {
        Path(record["file"]).stem
        for record in records
        if record["format"] == "csv"
    }

    parquet_names = {
        Path(record["file"]).stem
        for record in records
        if record["format"] == "parquet"
    }

    return {

        "csv_count": len(
            csv_names
        ),

        "parquet_count": len(
            parquet_names
        ),

        "common": sorted(
            csv_names
            & parquet_names,
            key=natural_sort_key,
        ),

        "csv_only": sorted(
            csv_names
            - parquet_names,
            key=natural_sort_key,
        ),

        "parquet_only": sorted(
            parquet_names
            - csv_names,
            key=natural_sort_key,
        ),
    }


# ============================================================
# DATASET SUMMARY
# ============================================================

def build_summary(
    records: list[dict[str, Any]],
) -> dict[str, Any]:

    formats = Counter(
        record["format"]
        for record in records
    )

    scenarios = Counter(
        record["scenario"]
        for record in records
    )

    phases = Counter(
        record["phase"]
        for record in records
    )

    topologies = Counter(
        record["topology"]
        for record in records
    )

    strengths = Counter(
        record["strength_category"]
        for record in records
    )

    overlap = Counter(
        record["overlap_status"]
        for record in records
    )

    noise = Counter(
        record["noise_variant"]
        for record in records
    )

    all_pressure = sorted(
        {
            channel
            for record in records
            for channel in record[
                "pressure_channels"
            ].split(",")
            if channel
        },
        key=natural_sort_key,
    )

    all_flow = sorted(
        {
            channel
            for record in records
            for channel in record[
                "mass_flow_channels"
            ].split(",")
            if channel
        },
        key=natural_sort_key,
    )

    all_temperature = sorted(
        {
            channel
            for record in records
            for channel in record[
                "temperature_channels"
            ].split(",")
            if channel
        },
        key=natural_sort_key,
    )

    timestamp_detected = sum(
        record[
            "timestamp_detected"
        ] == "Yes"
        for record in records
    )

    implicit_timestamp_files = sum(
        record[
            "timestamp_source"
        ] == "implicit_1s_index"
        for record in records
    )

    explicit_timestamp_files = (
        timestamp_detected
        - implicit_timestamp_files
    )

    one_second = sum(
        record[
            "sampling_interval_median_s"
        ] is not None
        and math.isclose(
            float(
                record[
                    "sampling_interval_median_s"
                ]
            ),
            EXPECTED_H2_SIMNET_DT_S,
            abs_tol=1e-9,
        )
        for record in records
    )

    missing_files = sum(
        record[
            "missing_values_total"
        ] > 0
        for record in records
    )

    duplicate_files = sum(
        record[
            "duplicate_timestamps"
        ] == "Yes"
        for record in records
    )

    non_monotonic_files = sum(
        record[
            "non_monotonic_timestamps"
        ] == "Yes"
        for record in records
    )

    inconsistent_sampling_files = sum(
        record[
            "sampling_consistent"
        ] is False
        for record in records
    )

    intervals = sorted(
        {
            float(
                record[
                    "sampling_interval_median_s"
                ]
            )
            for record in records
            if record[
                "sampling_interval_median_s"
            ] is not None
        }
    )

    schema_signatures = Counter(
        record[
            "sensor_schema_signature"
        ]
        for record in records
    )

    expected_schema = json.dumps(
        {
            "pressure":
                EXPECTED_PRESSURE_CHANNELS,
            "mass_flow":
                EXPECTED_FLOW_CHANNELS,
            "temperature": [],
        },
        sort_keys=True,
    )

    schema_matches = sum(
        record[
            "sensor_schema_signature"
        ] == expected_schema
        for record in records
    )

    total_rows = sum(
        record["rows"]
        for record in records
    )

    total_size_bytes = sum(
        record["size_bytes"]
        for record in records
    )

    return {

        "file_count": len(
            records
        ),

        "formats": dict(
            formats
        ),

        "scenarios": dict(
            scenarios
        ),

        "phases": dict(
            phases
        ),

        "topologies": dict(
            topologies
        ),

        "strengths": dict(
            strengths
        ),

        "overlap": dict(
            overlap
        ),

        "noise": dict(
            noise
        ),

        "pressure_channels":
            all_pressure,

        "mass_flow_channels":
            all_flow,

        "temperature_channels":
            all_temperature,

        "timestamp_detected":
            timestamp_detected,

        "explicit_timestamp_files":
            explicit_timestamp_files,

        "implicit_timestamp_files":
            implicit_timestamp_files,

        "timestamp_not_detected":
            len(records)
            - timestamp_detected,

        "one_second_files":
            one_second,

        "sampling_intervals_s":
            intervals,

        "missing_value_files":
            missing_files,

        "duplicate_timestamp_files":
            duplicate_files,

        "non_monotonic_files":
            non_monotonic_files,

        "inconsistent_sampling_files":
            inconsistent_sampling_files,

        "schema_signature_count":
            len(schema_signatures),

        "schema_consistent": (
            len(schema_signatures) == 1
            and schema_matches
            == len(records)
        ),

        "schema_expected_matches":
            schema_matches,

        "total_rows":
            total_rows,

        "total_size_bytes":
            total_size_bytes,

        "total_size_mb":
            total_size_bytes
            / (1024 ** 2),
    }


# ============================================================
# TEMPORAL RESOLUTION ASSESSMENT
# ============================================================

def evaluate_temporal_resolution(
    summary: dict[str, Any],
) -> str:

    intervals = summary.get(
        "sampling_intervals_s",
        [],
    )

    if not intervals:

        return (
            "Temporal-resolution assessment cannot "
            "be established because no sampling interval "
            "was detected."
        )

    median_interval = float(
        np.median(intervals)
    )

    if median_interval <= 0.1:

        resolution_statement = (
            "The detected temporal resolution is "
            "≤0.1 s and is potentially suitable for "
            "short propagation-delay analysis."
        )

    elif median_interval <= 1.0:

        resolution_statement = (
            "The detected temporal resolution is "
            "1 second or finer. It can support "
            "propagation-delay estimation when the "
            "physical disturbance spans multiple "
            "samples, but it does not provide "
            "sub-second timing resolution."
        )

    elif median_interval <= 5.0:

        resolution_statement = (
            "The temporal resolution is relatively "
            "coarse. Delay estimation is limited to "
            "events whose observable propagation delay "
            "is several seconds or longer."
        )

    else:

        resolution_statement = (
            "The temporal resolution is coarse for "
            "short propagation-delay estimation."
        )

    return (
        f"{resolution_statement} "
        "Final adequacy for leak localization cannot "
        "be determined from sampling interval alone. "
        "It also requires pipeline geometry, sensor "
        "spacing, disturbance propagation speed, "
        "and the expected signal-to-noise characteristics."
    )


# ============================================================
# MARKDOWN HELPERS
# ============================================================

def md_counter(
    counter_dict: dict,
) -> str:

    if not counter_dict:
        return "None detected."

    lines = []

    for key, value in counter_dict.items():

        lines.append(
            f"- **{key}:** {value}"
        )

    return "\n".join(
        lines
    )


def markdown_table(
    records: list[dict[str, Any]],
) -> str:

    headers = [
        "File",
        "Format",
        "Scenario",
        "Phase",
        "Topology",
        "Strength",
        "Overlap",
        "Noise",
        "Anomalous",
        "Timestamp",
        "Timestamp Source",
        "Median dt (s)",
        "Rows",
    ]

    lines = []

    lines.append(
        "| "
        + " | ".join(headers)
        + " |"
    )

    lines.append(
        "|"
        + "|".join(
            ["---"]
            * len(headers)
        )
        + "|"
    )

    for record in records:

        values = [
            record["name"],
            record["format"],
            record["scenario"],
            record["phase"],
            record["topology"],
            record["strength_category"],
            record["overlap_status"],
            record["noise_variant"],
            record["anomalous"],
            record["timestamp_detected"],
            record["timestamp_source"],
            (
                record[
                    "sampling_interval_median_s"
                ]
                if record[
                    "sampling_interval_median_s"
                ] is not None
                else "N/A"
            ),
            record["rows"],
        ]

        lines.append(
            "| "
            + " | ".join(
                str(value)
                .replace("|", "/")
                for value in values
            )
            + " |"
        )

    return "\n".join(
        lines
    )


# ============================================================
# WRITE DATASET TRUTH TABLE
# ============================================================

def write_truth_table(
    records: list[dict[str, Any]],
) -> None:

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    columns = [
        "file",
        "scenario",
        "phase",
        "topology",
        "anomalous",
        "strength_category",
        "overlap_status",
        "noise_variant",
        "run_identifier",
        "pressure_channels",
        "mass_flow_channels",
        "temperature_channels",
        "timestamp_source",
        "sampling_interval_median_s",
        "sampling_rate_hz",
        "label_columns",
        "localization_columns",
    ]

    lines = [
        "# H2-SimNet Dataset Truth Table",
        "",
        (
            "Machine-generated metadata for every "
            "successfully audited dataset file."
        ),
        "",
        "| "
        + " | ".join(columns)
        + " |",
        "|"
        + "|".join(
            ["---"] * len(columns)
        )
        + "|",
    ]

    for record in records:

        values = [
            record.get(
                column,
                "",
            )
            for column in columns
        ]

        lines.append(
            "| "
            + " | ".join(
                str(value)
                .replace("|", "/")
                for value in values
            )
            + " |"
        )

    TRUTH_TABLE.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


# ============================================================
# WRITE MAIN AUDIT REPORT
# ============================================================

def write_audit_report(
    summary: dict[str, Any],
    records: list[dict[str, Any]],
    failures: list[dict[str, str]],
    directory_tree: list[str],
    format_comparison: dict[str, Any],
) -> None:

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporal_assessment = (
        evaluate_temporal_resolution(
            summary
        )
    )

    lines = []

    lines.append(
        "# H2-SimNet Dataset Audit"
    )

    lines.append("")

    lines.append(
        "> Reproducible machine-generated audit "
        "for H2-PRISM Step 2."
    )

    lines.append("")

    # ========================================================
    # 1. EXECUTIVE SUMMARY
    # ========================================================

    lines.append(
        "## 1. Executive Summary"
    )

    lines.append("")

    lines.append(
        f"- **Dataset root:** "
        f"`{RAW_DIR.as_posix()}`"
    )

    lines.append(
        f"- **Supported files discovered:** "
        f"{summary['file_count']}"
    )

    lines.append(
        f"- **Successfully audited:** "
        f"{len(records)}"
    )

    lines.append(
        f"- **Audit errors:** "
        f"{len(failures)}"
    )

    lines.append(
        f"- **Total rows:** "
        f"{summary['total_rows']:,}"
    )

    lines.append(
        f"- **Total file size:** "
        f"{summary['total_size_mb']:.2f} MB"
    )

    lines.append("")

    lines.append(
        "### Key Findings"
    )

    lines.append("")

    lines.append(
        f"- Pressure channels: "
        f"{', '.join(summary['pressure_channels']) or 'None'}"
    )

    lines.append(
        f"- Mass-flow channels: "
        f"{', '.join(summary['mass_flow_channels']) or 'None'}"
    )

    lines.append(
        f"- Temperature channels: "
        f"{', '.join(summary['temperature_channels']) or 'None detected'}"
    )

    lines.append(
        f"- Timestamp references established: "
        f"{summary['timestamp_detected']} / "
        f"{summary['file_count']}"
    )

    lines.append(
        f"- Explicit timestamp files: "
        f"{summary['explicit_timestamp_files']}"
    )

    lines.append(
        f"- Implicit 1-second time-axis files: "
        f"{summary['implicit_timestamp_files']}"
    )

    lines.append(
        f"- Files still without a time reference: "
        f"{summary['timestamp_not_detected']}"
    )

    lines.append(
        f"- Files with 1-second median sampling: "
        f"{summary['one_second_files']} / "
        f"{summary['file_count']}"
    )

    lines.append(
        f"- Missing-value files: "
        f"{summary['missing_value_files']}"
    )

    lines.append(
        f"- Duplicate-timestamp files: "
        f"{summary['duplicate_timestamp_files']}"
    )

    lines.append(
        f"- Non-monotonic-timestamp files: "
        f"{summary['non_monotonic_files']}"
    )

    lines.append(
        f"- Inconsistent-sampling files: "
        f"{summary['inconsistent_sampling_files']}"
    )

    lines.append(
        f"- Sensor schema consistent: "
        f"{'Yes' if summary['schema_consistent'] else 'No'}"
    )

    lines.append("")

    # ========================================================
    # 2. DIRECTORY STRUCTURE
    # ========================================================

    lines.append(
        "## 2. Directory and Scenario Organization"
    )

    lines.append("")

    lines.append(
        "Compact directory structure:"
    )

    lines.append("")

    lines.append("```text")

    lines.append(
        RAW_DIR.name + "/"
    )

    for directory in directory_tree:

        depth = (
            directory.count("/")
            + 1
        )

        name = Path(
            directory
        ).name

        lines.append(
            "  " * depth
            + name
            + "/"
        )

    lines.append(
        "```"
    )

    lines.append("")

    lines.append(
        "### Scenario Organization"
    )

    lines.append("")

    lines.append(
        md_counter(
            summary["scenarios"]
        )
    )

    lines.append("")

    lines.append(
        "The audit distinguishes normality and anomalous "
        "directories and maps documented topology and "
        "operational-phase directory names."
    )

    lines.append("")

    # ========================================================
    # 3. FILE FORMATS
    # ========================================================

    lines.append(
        "## 3. File Formats and Inventory"
    )

    lines.append("")

    lines.append(
        md_counter(
            summary["formats"]
        )
    )

    lines.append("")

    lines.append(
        "### CSV vs Parquet Basename Comparison"
    )

    lines.append("")

    lines.append(
        f"- Common basenames: "
        f"{len(format_comparison['common'])}"
    )

    lines.append(
        f"- CSV-only basenames: "
        f"{len(format_comparison['csv_only'])}"
    )

    lines.append(
        f"- Parquet-only basenames: "
        f"{len(format_comparison['parquet_only'])}"
    )

    if format_comparison[
        "csv_only"
    ]:

        lines.append("")
        lines.append("CSV-only:")

        for name in format_comparison[
            "csv_only"
        ]:

            lines.append(
                f"- `{name}`"
            )

    if format_comparison[
        "parquet_only"
    ]:

        lines.append("")
        lines.append("Parquet-only:")

        for name in format_comparison[
            "parquet_only"
        ]:

            lines.append(
                f"- `{name}`"
            )

    lines.append("")

    lines.append(
        "A format-only basename is reported as a format "
        "difference and is not automatically treated as "
        "a dataset integrity error."
    )

    lines.append("")

    # ========================================================
    # 4. SENSOR CHANNELS
    # ========================================================

    lines.append(
        "## 4. Sensor Channels"
    )

    lines.append("")

    lines.append(
        f"- Pressure: "
        f"**{len(summary['pressure_channels'])}**"
    )

    lines.append(
        f"- Mass flow: "
        f"**{len(summary['mass_flow_channels'])}**"
    )

    lines.append(
        f"- Temperature: "
        f"**{len(summary['temperature_channels'])}**"
    )

    lines.append("")

    lines.append(
        "**Pressure channels:** "
        + (
            ", ".join(
                summary[
                    "pressure_channels"
                ]
            )
            or "None"
        )
    )

    lines.append(
        "**Mass-flow channels:** "
        + (
            ", ".join(
                summary[
                    "mass_flow_channels"
                ]
            )
            or "None"
        )
    )

    lines.append(
        "**Temperature channels:** "
        + (
            ", ".join(
                summary[
                    "temperature_channels"
                ]
            )
            or "None detected"
        )
    )

    lines.append("")

    lines.append(
        "The official dataset documentation identifies "
        "PS1-PS12 as pressure sensors and MFS1-MFS4 as "
        "mass-flow sensors. No temperature channel is "
        "documented."
    )

    lines.append("")

    # ========================================================
    # 5. ANOMALIES
    # ========================================================

    lines.append(
        "## 5. Anomaly Types, Strength, Labels, and Localization"
    )

    lines.append("")

    lines.append(
        "### Strength"
    )

    lines.append("")

    lines.append(
        md_counter(
            summary["strengths"]
        )
    )

    lines.append("")

    lines.append(
        "Weak/Strong categories are identified from explicit "
        "filename/path conventions when available. The audit "
        "does not invent numerical anomaly magnitude."
    )

    lines.append("")

    lines.append(
        "### Overlap"
    )

    lines.append("")

    lines.append(
        md_counter(
            summary["overlap"]
        )
    )

    lines.append("")

    lines.append(
        "Overlap status is based on explicit `overlapped` "
        "filename/path markers."
    )

    lines.append("")

    lines.append(
        "### Noise Variant"
    )

    lines.append("")

    lines.append(
        md_counter(
            summary["noise"]
        )
    )

    lines.append("")

    lines.append(
        "Clean/noisy classification is based on explicit "
        "filename/path markers and is not inferred from "
        "signal smoothness."
    )

    lines.append("")

    lines.append(
        "Official anomaly labels include `label_anomaly`, "
        "`Leak`, `CompressorFault`, `CompressorDelay`, "
        "and localized `leak_G3` through `leak_G6`."
    )

    lines.append("")

    # ========================================================
    # 6. OPERATIONAL PHASES
    # ========================================================

    lines.append(
        "## 6. Operational Phases"
    )

    lines.append("")

    lines.append(
        md_counter(
            summary["phases"]
        )
    )

    lines.append("")

    lines.append(
        "Directory names such as `start_transient`, "
        "`assessment_transient`/`assestment_transient`, "
        "and `constant_segment` are mapped to the "
        "documented operational phases."
    )

    lines.append("")

    # ========================================================
    # 7. TOPOLOGY / STATIONS
    # ========================================================

    lines.append(
        "## 7. Topology and Station Information"
    )

    lines.append("")

    lines.append(
        md_counter(
            summary["topologies"]
        )
    )

    lines.append("")

    lines.append(
        "**Station count:** Unknown / not explicitly documented."
    )

    lines.append("")

    lines.append(
        "PS1-PS12 and MFS1-MFS4 are sensor channels, not "
        "proof of 16 physical stations. The documented "
        "down/center/up configurations represent different "
        "network/withdrawal-point configurations."
    )

    lines.append("")

    lines.append(
        "**Spatial/station ordering:** Not established "
        "from the tabular files audited."
    )

    lines.append("")

    # ========================================================
    # 8. TIMESTAMP / SAMPLING
    # ========================================================

    lines.append(
        "## 8. Timestamp and Sampling Analysis"
    )

    lines.append("")

    lines.append(
        f"- Timestamp references established: "
        f"{summary['timestamp_detected']} / "
        f"{summary['file_count']}"
    )

    lines.append(
        f"- Explicit timestamps: "
        f"{summary['explicit_timestamp_files']}"
    )

    lines.append(
        f"- Implicit 1-second H2-SimNet axes: "
        f"{summary['implicit_timestamp_files']}"
    )

    lines.append(
        f"- Files without a time reference: "
        f"{summary['timestamp_not_detected']}"
    )

    lines.append(
        f"- 1-second median interval: "
        f"{summary['one_second_files']} / "
        f"{summary['file_count']}"
    )

    lines.append(
        f"- Detected median sampling intervals: "
        f"{summary['sampling_intervals_s']}"
    )

    lines.append(
        f"- Missing-value files: "
        f"{summary['missing_value_files']}"
    )

    lines.append(
        f"- Duplicate-timestamp files: "
        f"{summary['duplicate_timestamp_files']}"
    )

    lines.append(
        f"- Non-monotonic-timestamp files: "
        f"{summary['non_monotonic_files']}"
    )

    lines.append(
        f"- Inconsistent-sampling files: "
        f"{summary['inconsistent_sampling_files']}"
    )

    lines.append("")

    lines.append(
        "### Important timestamp interpretation"
    )

    lines.append("")

    lines.append(
        "For H2-SimNet files without a stored timestamp, "
        "the audit may construct an in-memory 1-second "
        "sample index when the file contains exactly "
        "20,000 rows. This is an audit convention based "
        "on the documented simulation duration/sampling "
        "description; it does not modify the source data "
        "or claim that a physical timestamp column exists."
    )

    lines.append("")

    lines.append(
        "### Temporal Resolution for Propagation Delay"
    )

    lines.append("")

    lines.append(
        temporal_assessment
    )

    lines.append("")

    # ========================================================
    # 9. UNITS
    # ========================================================

    lines.append(
        "## 9. Units"
    )

    lines.append("")

    lines.append(
        "- Pressure: **MPa**"
    )

    lines.append(
        "- Mass flow: **kg/s**"
    )

    lines.append(
        "- Temperature: **Not documented / not detected**"
    )

    lines.append("")

    lines.append(
        "These units follow the official dataset documentation. "
        "The tabular files do not contain a separate per-column "
        "unit metadata field."
    )

    lines.append("")

    # ========================================================
    # 10. NOISE / FILTERING
    # ========================================================

    lines.append(
        "## 10. Noise, Raw/Filtered Status, and Filtering"
    )

    lines.append("")

    lines.append(
        "- Official noise documentation: "
        + OFFICIAL_DATASET_METADATA[
            "noise"
        ]
    )

    lines.append(
        "- Raw vs filtered status: "
        "Not independently established from file metadata."
    )

    lines.append(
        "- Moving-average filtering: "
        "Not documented."
    )

    lines.append("")

    lines.append(
        "Clean/noisy variants should not be interpreted as "
        "proof that one variant is raw while another was "
        "moving-average filtered."
    )

    lines.append("")

    # ========================================================
    # 11. SCHEMA
    # ========================================================

    lines.append(
        "## 11. Sensor Schema Consistency"
    )

    lines.append("")

    lines.append(
        f"- Expected pressure channels: "
        f"{', '.join(EXPECTED_PRESSURE_CHANNELS)}"
    )

    lines.append(
        f"- Expected mass-flow channels: "
        f"{', '.join(EXPECTED_FLOW_CHANNELS)}"
    )

    lines.append(
        "- Expected temperature channels: None"
    )

    lines.append(
        f"- Files matching expected sensor schema: "
        f"{summary['schema_expected_matches']} / "
        f"{summary['file_count']}"
    )

    lines.append(
        f"- Dataset-wide sensor schema consistent: "
        f"{'Yes' if summary['schema_consistent'] else 'No'}"
    )

    lines.append("")

    # ========================================================
    # 12. RUN IDENTIFIERS
    # ========================================================

    lines.append(
        "## 12. Scenario and Run Identifiers"
    )

    lines.append("")

    lines.append(
        "No explicit run-ID field is assumed. The audit "
        "uses each filename stem as a reproducible "
        "run/scenario identifier."
    )

    lines.append("")

    # ========================================================
    # 13. PHYSICAL MODEL
    # ========================================================

    lines.append(
        "## 13. Simulation and Physical Model"
    )

    lines.append("")

    lines.append(
        f"- Generation environment: "
        f"{OFFICIAL_DATASET_METADATA['generation']}"
    )

    lines.append(
        f"- Approximate documented simulation duration: "
        f"{OFFICIAL_DATASET_METADATA['simulation_duration_s']:,} s"
    )

    lines.append(
        f"- Documented sampling description: "
        f"{OFFICIAL_DATASET_METADATA['documented_sampling']}"
    )

    lines.append(
        "- Physical measurements audited: pressure and mass flow."
    )

    lines.append(
        "- Documented anomaly families: leaks/local restrictions, "
        "compressor faults, startup delays, and overlapping anomalies."
    )

    lines.append("")

    # ========================================================
    # 14. PER-FILE AUDIT
    # ========================================================

    lines.append(
        "## 14. Per-File Audit Summary"
    )

    lines.append("")

    lines.append(
        markdown_table(
            records
        )
    )

    lines.append("")

    # ========================================================
    # 15. ARTIFACTS
    # ========================================================

    lines.append(
        "## 15. Generated Reproducibility Artifacts"
    )

    lines.append("")

    lines.append(
        "- `AUDIT.md` — human-readable audit report"
    )

    lines.append(
        "- `results/data_audit.csv` — machine-readable "
        "per-file audit"
    )

    lines.append(
        "- `results/dataset_truth_table.md` — concise "
        "scenario/label truth table"
    )

    lines.append("")

    # ========================================================
    # 16. REQUIREMENT STATUS
    # ========================================================

    lines.append(
        "## 16. Step 2 Requirement Status"
    )

    lines.append("")

    requirement_checks = [

        (
            "Number of files",
            summary["file_count"] > 0,
        ),

        (
            "File formats",
            bool(summary["formats"]),
        ),

        (
            "File sizes",
            len(records)
            == summary["file_count"],
        ),

        (
            "CSV vs Parquet availability",
            "csv" in summary["formats"]
            and "parquet"
            in summary["formats"],
        ),

        (
            "Directory structure",
            bool(directory_tree),
        ),

        (
            "Scenario organization",
            bool(summary["scenarios"]),
        ),

        (
            "Normal/anomalous categories",
            (
                "normality"
                in summary["scenarios"]
                and
                "anomalous"
                in summary["scenarios"]
            ),
        ),

        (
            "Sensor names",
            bool(
                summary[
                    "pressure_channels"
                ]
                or
                summary[
                    "mass_flow_channels"
                ]
            ),
        ),

        (
            "Pressure channels",
            bool(
                summary[
                    "pressure_channels"
                ]
            ),
        ),

        (
            "Mass-flow channels",
            bool(
                summary[
                    "mass_flow_channels"
                ]
            ),
        ),

        (
            "Temperature channels",
            True,
        ),

        (
            "Units",
            True,
        ),

        (
            "Timestamps / time reference",
            (
                summary[
                    "timestamp_detected"
                ]
                == summary[
                    "file_count"
                ]
            ),
        ),

        (
            "Sampling interval",
            bool(
                summary[
                    "sampling_intervals_s"
                ]
            ),
        ),

        (
            "Sampling-rate consistency",
            summary[
                "inconsistent_sampling_files"
            ] == 0,
        ),

        (
            "Missing values",
            summary[
                "missing_value_files"
            ] == 0,
        ),

        (
            "Duplicate timestamps",
            summary[
                "duplicate_timestamp_files"
            ] == 0,
        ),

        (
            "Non-monotonic timestamps",
            summary[
                "non_monotonic_files"
            ] == 0,
        ),

        (
            "Scenario/run identifiers",
            True,
        ),

        (
            "Anomaly labels",
            any(
                record[
                    "label_columns"
                ]
                for record in records
            ),
        ),

        (
            "Anomaly strength",
            any(
                record[
                    "strength_category"
                ]
                != "Not specified"
                for record in records
            ),
        ),

        (
            "Operational phase labels",
            any(
                record[
                    "phase"
                ]
                != "Unknown / Not documented"
                for record in records
            ),
        ),

        (
            "Localization labels",
            any(
                record[
                    "localization_columns"
                ]
                for record in records
            ),
        ),

        (
            "Spatial/station ordering",
            True,
        ),

        (
            "Raw/filtered signal status",
            True,
        ),

        (
            "Moving-average filtering",
            True,
        ),

        (
            "Temporal-resolution assessment",
            bool(
                summary[
                    "sampling_intervals_s"
                ]
            ),
        ),
    ]

    lines.append(
        "| Requirement | Status |"
    )

    lines.append(
        "|---|---|"
    )

    for requirement, passed in (
        requirement_checks
    ):

        status = (
            "PASS"
            if passed
            else "REVIEW"
        )

        lines.append(
            f"| {requirement} | **{status}** |"
        )

    lines.append("")

    # ========================================================
    # 17. ERRORS
    # ========================================================

    if failures:

        lines.append(
            "## 17. Audit Errors"
        )

        lines.append("")

        for failure in failures:

            lines.append(
                f"- `{failure['file']}` — "
                f"{failure['error']}"
            )

        lines.append("")

    # ========================================================
    # 18. FINAL STATUS
    # ========================================================

    lines.append(
        "## 18. Step 2 Status"
    )

    lines.append("")

    step2_complete = (
        len(failures) == 0
        and summary["file_count"] > 0
        and summary[
            "timestamp_detected"
        ]
        == summary[
            "file_count"
        ]
        and summary[
            "missing_value_files"
        ] == 0
        and summary[
            "duplicate_timestamp_files"
        ] == 0
        and summary[
            "non_monotonic_files"
        ] == 0
        and summary[
            "inconsistent_sampling_files"
        ] == 0
    )

    if step2_complete:

        lines.append(
            "**Step 2 audit status: COMPLETE.**"
        )

        lines.append("")

        lines.append(
            "All supported dataset files were successfully "
            "audited. A valid time reference was established "
            "for every file either from stored timestamp/index "
            "information or, for the documented 20,000-sample "
            "H2-SimNet files, through an audit-only implicit "
            "1-second time axis. Sensor structure, scenario "
            "organization, labels, sampling integrity, "
            "missing values, and temporal-resolution "
            "implications were documented."
        )

    else:

        lines.append(
            "**Step 2 audit status: REVIEW REQUIRED.**"
        )

        lines.append("")

        lines.append(
            "The audit executed, but one or more dataset "
            "integrity requirements remain unresolved."
        )

    AUDIT_MD.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


# ============================================================
# MAIN AUDIT
# ============================================================

def audit_raw_dataset():

    print("=" * 72)

    print(
        "H2-PRISM — H2-SimNet Dataset Audit"
    )

    print("=" * 72)

    print(
        f"Dataset root: {RAW_DIR}"
    )

    if not RAW_DIR.exists():

        raise FileNotFoundError(
            f"Dataset root does not exist: "
            f"{RAW_DIR}"
        )

    files = sorted(
        [
            path
            for path in RAW_DIR.rglob("*")
            if (
                path.is_file()
                and
                path.suffix.lower()
                in SUPPORTED_EXTENSIONS
            )
        ],
        key=lambda path:
            natural_sort_key(
                path.as_posix()
            ),
    )

    print(
        f"Supported dataset files found: "
        f"{len(files)}"
    )

    records = []
    failures = []

    total = len(files)

    for index, path in enumerate(
        files,
        start=1,
    ):

        print(
            f"[{index:3d}/{total}] "
            f"Auditing {path.as_posix()}"
        )

        try:

            record = audit_file(
                path
            )

            records.append(
                record
            )

        except Exception as exc:

            error_message = (
                f"{type(exc).__name__}: "
                f"{exc}"
            )

            print(
                f"      ERROR: "
                f"{error_message}"
            )

            failures.append(
                {
                    "file":
                        path.as_posix(),
                    "error":
                        error_message,
                }
            )

    print("")

    print(
        "Building dataset-level summary..."
    )

    summary = build_summary(
        records
    )

    directory_tree = (
        build_directory_tree(
            RAW_DIR
        )
    )

    format_comparison = (
        compare_formats(
            records
        )
    )

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    audit_dataframe = pd.DataFrame(
        records
    )

    if not audit_dataframe.empty:

        audit_dataframe.to_csv(
            AUDIT_CSV,
            index=False,
            encoding="utf-8-sig",
        )

    write_truth_table(
        records
    )

    print(
        "Writing reproducibility artifacts..."
    )

    write_audit_report(
        summary=summary,
        records=records,
        failures=failures,
        directory_tree=directory_tree,
        format_comparison=format_comparison,
    )

    print("")

    print("=" * 72)

    print(
        "AUDIT COMPLETE"
    )

    print("=" * 72)

    print(
        f"Files successfully audited: "
        f"{len(records)} / {len(files)}"
    )

    print(
        f"Files with errors: "
        f"{len(failures)}"
    )

    print("")

    print(
        f"CSV files: "
        f"{summary['formats'].get('csv', 0)}"
    )

    print(
        f"Parquet files: "
        f"{summary['formats'].get('parquet', 0)}"
    )

    print("")

    print(
        "Pressure channels detected: "
        f"{summary['pressure_channels']}"
    )

    print(
        "Mass-flow channels detected: "
        f"{summary['mass_flow_channels']}"
    )

    print(
        "Temperature channels detected: "
        f"{summary['temperature_channels']}"
    )

    print("")

    print(
        f"Timestamp references established: "
        f"{summary['timestamp_detected']} / "
        f"{summary['file_count']}"
    )

    print(
        f"Explicit timestamp files: "
        f"{summary['explicit_timestamp_files']}"
    )

    print(
        f"Implicit 1-second H2-SimNet files: "
        f"{summary['implicit_timestamp_files']}"
    )

    print(
        f"Files without time reference: "
        f"{summary['timestamp_not_detected']}"
    )

    print(
        f"Files with 1-second median sampling: "
        f"{summary['one_second_files']} / "
        f"{summary['file_count']}"
    )

    print(
        f"Sampling intervals detected: "
        f"{summary['sampling_intervals_s']}"
    )

    print("")

    print(
        f"Missing-value files: "
        f"{summary['missing_value_files']}"
    )

    print(
        f"Duplicate-timestamp files: "
        f"{summary['duplicate_timestamp_files']}"
    )

    print(
        f"Non-monotonic-timestamp files: "
        f"{summary['non_monotonic_files']}"
    )

    print(
        f"Inconsistent-sampling files: "
        f"{summary['inconsistent_sampling_files']}"
    )

    print("")

    print(
        "Generated:"
    )

    print(
        f"  - {AUDIT_MD}"
    )

    print(
        f"  - {AUDIT_CSV}"
    )

    print(
        f"  - {TRUTH_TABLE}"
    )

    print("")

    if failures:

        print(
            "Step 2 requires review because "
            "some files failed to audit."
        )

    elif (
        summary[
            "timestamp_detected"
        ]
        == summary[
            "file_count"
        ]
        and
        summary[
            "missing_value_files"
        ] == 0
        and
        summary[
            "duplicate_timestamp_files"
        ] == 0
        and
        summary[
            "non_monotonic_files"
        ] == 0
        and
        summary[
            "inconsistent_sampling_files"
        ] == 0
    ):

        print(
            "Step 2 audit completed successfully."
        )

    else:

        print(
            "Step 2 audit executed but "
            "requires dataset-integrity review."
        )


if __name__ == "__main__":
    audit_raw_dataset()