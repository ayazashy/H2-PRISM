from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .schema import QualityFlag


# ============================================================
# NATIVE H2-SimNet CONFIGURATION
# ============================================================

PRESSURE_CHANNELS = [f"PS{i}" for i in range(1, 13)]
FLOW_CHANNELS = [f"MFS{i}" for i in range(1, 5)]

NATIVE_MEASUREMENT_CHANNELS = (
    PRESSURE_CHANNELS + FLOW_CHANNELS
)

NATIVE_UNITS = {
    channel: "MPa"
    for channel in PRESSURE_CHANNELS
}

NATIVE_UNITS.update(
    {
        channel: "kg/s"
        for channel in FLOW_CHANNELS
    }
)


# Legacy wide-form channels used by the pipeline mock.
LEGACY_CHANNELS = [
    "p_upstream",
    "p_downstream",
    "m_inlet",
    "m_outlet",
]

LEGACY_UNITS = {
    "p_upstream": "Pa",
    "p_downstream": "Pa",
    "m_inlet": "kg/s",
    "m_outlet": "kg/s",
}


# ============================================================
# FLAG PRIORITY
# ============================================================

FLAG_PRIORITY = {
    QualityFlag.GOOD: 0,
    QualityFlag.GAP: 1,
    QualityFlag.DUPLICATE: 2,
    QualityFlag.STUCK: 3,
    QualityFlag.DISCONTINUITY: 4,
    QualityFlag.INVALID: 5,
    QualityFlag.MISSING: 6,
}


# ============================================================
# QUALITY CONTROLLER
# ============================================================

class QualityController:
    """
    Non-destructive quality-control system for H2-PRISM.

    The controller detects suspicious observations and assigns
    quality flags without deleting or modifying source data.
    """

    def __init__(
        self,
        min_sampling_interval: float = 0.01,
        max_sampling_interval: float = 10.0,
        expected_sampling_interval: float = 1.0,
        sampling_tolerance: float = 0.05,
        stuck_window_size: int = 15,
        discontinuity_threshold: Optional[float] = None,
        saturation_tolerance: float = 0.0,
        pressure_range_mpa: Tuple[float, float] = (
            0.0,
            np.inf,
        ),
        pressure_range_pa: Tuple[float, float] = (
            0.0,
            30.0e6,
        ),
        flow_range_kg_s: Tuple[float, float] = (
            0.0,
            np.inf,
        ),
        communication_gap_threshold: Optional[float] = None,
    ):
        self.min_dt = float(
            min_sampling_interval
        )
        self.max_dt = float(
            max_sampling_interval
        )

        self.expected_dt = float(
            expected_sampling_interval
        )

        self.sampling_tolerance = float(
            sampling_tolerance
        )

        self.stuck_window = int(
            stuck_window_size
        )

        self.discontinuity_threshold = (
            discontinuity_threshold
        )

        self.saturation_tolerance = float(
            saturation_tolerance
        )

        self.pressure_range_mpa = (
            pressure_range_mpa
        )

        self.pressure_range_pa = (
            pressure_range_pa
        )

        self.flow_range_kg_s = (
            flow_range_kg_s
        )

        if communication_gap_threshold is None:
            self.communication_gap_threshold = (
                self.max_dt
            )
        else:
            self.communication_gap_threshold = float(
                communication_gap_threshold
            )

    # ========================================================
    # CHANNEL DISCOVERY
    # ========================================================

    def _detect_measurement_channels(
        self,
        df: pd.DataFrame,
    ) -> List[str]:

        native = [
            channel
            for channel in NATIVE_MEASUREMENT_CHANNELS
            if channel in df.columns
        ]

        legacy = [
            channel
            for channel in LEGACY_CHANNELS
            if channel in df.columns
        ]

        return native + legacy

    # ========================================================
    # FLAG MANAGEMENT
    # ========================================================

    def _apply_flag(
        self,
        channel_flags: Dict[str, QualityFlag],
        channel: str,
        flag: QualityFlag,
    ) -> None:

        current = channel_flags.get(
            channel,
            QualityFlag.GOOD,
        )

        if (
            FLAG_PRIORITY.get(flag, 0)
            > FLAG_PRIORITY.get(current, 0)
        ):
            channel_flags[channel] = flag

    # ========================================================
    # TIMESTAMP CHECKS
    # ========================================================

    def _check_timestamps(
        self,
        df: pd.DataFrame,
    ) -> Dict[str, Any]:

        result = {
            "available": False,
            "duplicate_timestamps": False,
            "non_monotonic_timestamps": False,
            "non_positive_intervals": False,
            "timestamp_count": 0,
        }

        if "timestamp" not in df.columns:
            return result

        result["available"] = True

        ts = pd.to_numeric(
            df["timestamp"],
            errors="coerce",
        )

        result["timestamp_count"] = int(
            len(ts)
        )

        if ts.isna().any():
            result["non_monotonic_timestamps"] = True
            result["non_positive_intervals"] = True
            return result

        values = ts.to_numpy(
            dtype=float
        )

        if len(values) < 2:
            return result

        diffs = np.diff(values)

        result["duplicate_timestamps"] = bool(
            ts.duplicated().any()
        )

        result["non_positive_intervals"] = bool(
            np.any(diffs <= 0)
        )

        result["non_monotonic_timestamps"] = bool(
            np.any(diffs < 0)
        )

        return result

    # ========================================================
    # SAMPLING CHECKS
    # ========================================================

    def _check_sampling(
        self,
        df: pd.DataFrame,
    ) -> Dict[str, Any]:

        result = {
            "available": False,
            "irregular_sampling": False,
            "sampling_interval": None,
            "expected_sampling_interval": (
                self.expected_dt
            ),
            "off_expected_interval_count": 0,
            "minimum_interval": None,
            "maximum_interval": None,
        }

        if "timestamp" not in df.columns:
            return result

        ts = pd.to_numeric(
            df["timestamp"],
            errors="coerce",
        )

        if ts.isna().any() or len(ts) < 2:
            return result

        values = ts.to_numpy(
            dtype=float
        )

        diffs = np.diff(values)

        positive_diffs = diffs[
            diffs > 0
        ]

        if len(positive_diffs) == 0:
            return result

        result["available"] = True

        median_dt = float(
            np.median(positive_diffs)
        )

        result["sampling_interval"] = median_dt
        result["minimum_interval"] = float(
            np.min(positive_diffs)
        )
        result["maximum_interval"] = float(
            np.max(positive_diffs)
        )

        tolerance = (
            self.expected_dt
            * self.sampling_tolerance
        )

        off_expected = np.abs(
            positive_diffs
            - self.expected_dt
        ) > tolerance

        result[
            "off_expected_interval_count"
        ] = int(
            np.sum(off_expected)
        )

        result["irregular_sampling"] = bool(
            np.any(
                positive_diffs
                < self.min_dt
            )
            or np.any(
                positive_diffs
                > self.max_dt
            )
            or np.any(off_expected)
        )

        return result

    # ========================================================
    # NUMERIC RANGES
    # ========================================================

    def _get_channel_range(
        self,
        channel: str,
    ) -> Tuple[float, float]:

        if channel in PRESSURE_CHANNELS:
            return self.pressure_range_mpa

        if channel in FLOW_CHANNELS:
            return self.flow_range_kg_s

        if channel in (
            "p_upstream",
            "p_downstream",
        ):
            return self.pressure_range_pa

        if channel in (
            "m_inlet",
            "m_outlet",
        ):
            return self.flow_range_kg_s

        return (
            -np.inf,
            np.inf,
        )

    # ========================================================
    # NUMERIC VALUE CHECKS
    # ========================================================

    def _check_numeric_values(
        self,
        df: pd.DataFrame,
        channels: List[str],
    ) -> Dict[str, Any]:

        checks: Dict[str, Any] = {}

        for channel in channels:

            series = pd.to_numeric(
                df[channel],
                errors="coerce",
            )

            lower, upper = (
                self._get_channel_range(
                    channel
                )
            )

            missing_count = int(
                series.isna().sum()
            )

            finite_mask = np.isfinite(
                series.to_numpy(
                    dtype=float
                )
            )

            nonfinite_count = int(
                (~finite_mask).sum()
                - missing_count
            )

            out_of_range = (
                (series < lower)
                | (series > upper)
            )

            out_of_range = (
                out_of_range
                & series.notna()
            )

            out_of_range_count = int(
                out_of_range.sum()
            )

            checks[channel] = {
                "missing_count": (
                    missing_count
                ),
                "nonfinite_count": (
                    max(
                        nonfinite_count,
                        0,
                    )
                ),
                "out_of_range_count": (
                    out_of_range_count
                ),
                "range": (
                    float(lower),
                    float(upper),
                ),
            }

        return checks

    # ========================================================
    # STUCK / SATURATION / DISCONTINUITY
    # ========================================================

    def _is_stuck(
        self,
        values: np.ndarray,
    ) -> bool:

        if len(values) < self.stuck_window:
            return False

        numeric = pd.to_numeric(
            values,
            errors="coerce",
        )

        if np.isnan(numeric).any():
            return False

        differences = np.diff(
            numeric
        )

        run_length = 0

        for difference in differences:

            if difference == 0:
                run_length += 1

                if (
                    run_length
                    >= self.stuck_window - 1
                ):
                    return True
            else:
                run_length = 0

        return False

    def _check_sensor_behavior(
        self,
        df: pd.DataFrame,
        channels: List[str],
    ) -> Dict[str, Any]:

        checks: Dict[str, Any] = {}

        for channel in channels:

            values = pd.to_numeric(
                df[channel],
                errors="coerce",
            ).to_numpy(
                dtype=float
            )

            finite = values[
                np.isfinite(values)
            ]

            stuck_detected = self._is_stuck(
                finite
            )

            discontinuity_detected = False
            discontinuity_count = 0

            if (
                self.discontinuity_threshold
                is not None
                and len(values) >= 2
            ):

                diffs = np.abs(
                    np.diff(values)
                )

                mask = (
                    np.isfinite(diffs)
                    & (
                        diffs
                        > self.discontinuity_threshold
                    )
                )

                discontinuity_count = int(
                    np.sum(mask)
                )

                discontinuity_detected = (
                    discontinuity_count > 0
                )

            lower, upper = (
                self._get_channel_range(
                    channel
                )
            )

            saturation_detected = False
            saturation_count = 0

            if (
                self.saturation_tolerance
                >= 0
                and len(finite) > 0
            ):

                lower_sat = (
                    np.isclose(
                        finite,
                        lower,
                        atol=self.saturation_tolerance,
                    )
                    if np.isfinite(lower)
                    else np.zeros(
                        len(finite),
                        dtype=bool,
                    )
                )

                upper_sat = (
                    np.isclose(
                        finite,
                        upper,
                        atol=self.saturation_tolerance,
                    )
                    if np.isfinite(upper)
                    else np.zeros(
                        len(finite),
                        dtype=bool,
                    )
                )

                saturation_count = int(
                    np.sum(
                        lower_sat
                        | upper_sat
                    )
                )

                saturation_detected = (
                    saturation_count > 0
                )

            checks[channel] = {
                "stuck": {
                    "detected": bool(
                        stuck_detected
                    ),
                },
                "discontinuity": {
                    "detected": bool(
                        discontinuity_detected
                    ),
                    "count": (
                        discontinuity_count
                    ),
                },
                "saturation": {
                    "detected": bool(
                        saturation_detected
                    ),
                    "count": saturation_count,
                },
            }

        return checks

    # ========================================================
    # COMMUNICATION GAPS
    # ========================================================

    def _check_communication_gaps(
        self,
        df: pd.DataFrame,
        channels: List[str],
    ) -> Dict[str, Any]:

        checks: Dict[str, Any] = {}

        if "timestamp" not in df.columns:
            for channel in channels:
                checks[channel] = {
                    "detected": False,
                    "count": 0,
                }

            return checks

        ts = pd.to_numeric(
            df["timestamp"],
            errors="coerce",
        ).to_numpy(
            dtype=float
        )

        if len(ts) < 2:
            for channel in channels:
                checks[channel] = {
                    "detected": False,
                    "count": 0,
                }

            return checks

        diffs = np.diff(ts)

        gap_mask = (
            np.isfinite(diffs)
            & (
                diffs
                > self.communication_gap_threshold
            )
        )

        gap_count = int(
            np.sum(gap_mask)
        )

        for channel in channels:
            checks[channel] = {
                "detected": bool(
                    gap_count > 0
                ),
                "count": gap_count,
            }

        return checks

    # ========================================================
    # UNIT CHECKS
    # ========================================================

    def _check_units(
        self,
        df: pd.DataFrame,
        channels: List[str],
    ) -> Dict[str, Any]:

        channel_units: Dict[str, str] = {}

        for channel in channels:

            if channel in NATIVE_UNITS:
                channel_units[channel] = (
                    NATIVE_UNITS[channel]
                )

            elif channel in LEGACY_UNITS:
                channel_units[channel] = (
                    LEGACY_UNITS[channel]
                )

            else:
                channel_units[channel] = (
                    "UNKNOWN"
                )

        known_units = [
            unit
            for unit in channel_units.values()
            if unit != "UNKNOWN"
        ]

        inconsistent = False

        if (
            "unit" in df.columns
            and len(known_units) > 0
        ):

            declared = (
                df["unit"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

            inconsistent = any(
                unit not in known_units
                for unit in declared
            )

        return {
            "channel_units": channel_units,
            "inconsistent_units": bool(
                inconsistent
            ),
        }

    # ========================================================
    # STATION ORDERING
    # ========================================================

    def _check_station_ordering(
        self,
        df: pd.DataFrame,
    ) -> Dict[str, Any]:

        return {
            "verified": False,
            "status": "UNKNOWN",
            "reason": (
                "Physical station ordering is not "
                "verified by the native H2-SimNet "
                "measurement configuration."
            ),
        }

    # ========================================================
    # TIMESTAMP ALIGNMENT
    # ========================================================

    def _check_timestamp_alignment(
        self,
        df: pd.DataFrame,
        channels: List[str],
    ) -> Dict[str, Any]:

        if (
            "timestamp" in df.columns
            and len(channels) > 0
        ):

            return {
                "status": (
                    "ALIGNED_BY_SHARED_DATAFRAME_INDEX"
                ),
                "method": "wide_form_shared_timestamp",
            }

        return {
            "status": "NOT_AVAILABLE",
            "method": None,
        }

    # ========================================================
    # CHANNEL FLAG SUMMARY
    # ========================================================

    def _summarize_channel_flag(
        self,
        quality_flags: pd.DataFrame,
        channel: str,
    ) -> QualityFlag:

        values = quality_flags[
            channel
        ].tolist()

        if not values:
            return QualityFlag.GOOD

        best = QualityFlag.GOOD

        for value in values:

            if isinstance(
                value,
                QualityFlag,
            ):
                candidate = value

            else:
                try:
                    candidate = (
                        QualityFlag(
                            value
                        )
                    )
                except ValueError:
                    candidate = (
                        QualityFlag.INVALID
                    )

            if (
                FLAG_PRIORITY.get(
                    candidate,
                    0,
                )
                > FLAG_PRIORITY.get(
                    best,
                    0,
                )
            ):
                best = candidate

        return best

    # ========================================================
    # MAIN INSPECTION
    # ========================================================

    def inspect_dataframe(
        self,
        df: pd.DataFrame,
    ) -> Dict[str, Any]:

        if not isinstance(
            df,
            pd.DataFrame,
        ):
            raise TypeError(
                "inspect_dataframe expects a pandas DataFrame."
            )

        original_columns = list(
            df.columns
        )

        original_index = (
            df.index.copy()
        )

        measurement_channels = (
            self._detect_measurement_channels(
                df
            )
        )

        channel_flags = {
            channel: QualityFlag.GOOD
            for channel in measurement_channels
        }

        quality_flags = pd.DataFrame(
            QualityFlag.GOOD.value,
            index=df.index,
            columns=measurement_channels,
        )

        issues: List[str] = []

        # ----------------------------------------------------
        # TIMESTAMPS
        # ----------------------------------------------------

        timestamp_checks = (
            self._check_timestamps(df)
        )

        if (
            timestamp_checks[
                "duplicate_timestamps"
            ]
            or timestamp_checks[
                "non_positive_intervals"
            ]
        ):

            issues.append(
                "Duplicate or non-positive timestamp intervals detected."
            )

        if timestamp_checks[
            "non_monotonic_timestamps"
        ]:

            issues.append(
                "Non-monotonic timestamps detected."
            )

        # ----------------------------------------------------
        # SAMPLING
        # ----------------------------------------------------

        sampling_checks = (
            self._check_sampling(df)
        )

        if sampling_checks[
            "irregular_sampling"
        ]:

            issues.append(
                "Irregular sampling detected."
            )

        # ----------------------------------------------------
        # NUMERIC CHECKS
        # ----------------------------------------------------

        numeric_checks = (
            self._check_numeric_values(
                df,
                measurement_channels,
            )
        )

        for channel in measurement_channels:

            check = numeric_checks[
                channel
            ]

            if check[
                "missing_count"
            ] > 0:

                self._apply_flag(
                    channel_flags,
                    channel,
                    QualityFlag.MISSING,
                )

                quality_flags.loc[
                    df[channel].isna(),
                    channel,
                ] = (
                    QualityFlag.MISSING.value
                )

                issues.append(
                    f"{channel} contains missing values."
                )

            if (
                check[
                    "nonfinite_count"
                ]
                > 0
            ):

                self._apply_flag(
                    channel_flags,
                    channel,
                    QualityFlag.INVALID,
                )

                issues.append(
                    f"{channel} contains non-finite numeric values."
                )

            if (
                check[
                    "out_of_range_count"
                ]
                > 0
            ):

                self._apply_flag(
                    channel_flags,
                    channel,
                    QualityFlag.INVALID,
                )

                lower, upper = (
                    check["range"]
                )

                numeric_series = pd.to_numeric(
                    df[channel],
                    errors="coerce",
                )

                invalid_mask = (
                    (
                        numeric_series
                        < lower
                    )
                    | (
                        numeric_series
                        > upper
                    )
                )

                quality_flags.loc[
                    invalid_mask,
                    channel,
                ] = (
                    QualityFlag.INVALID.value
                )

                issues.append(
                    f"{channel} contains values outside its configured physical range."
                )

        # ----------------------------------------------------
        # SENSOR BEHAVIOR
        # ----------------------------------------------------

        sensor_checks = (
            self._check_sensor_behavior(
                df,
                measurement_channels,
            )
        )

        for channel in measurement_channels:

            behavior = sensor_checks[
                channel
            ]

            if behavior[
                "stuck"
            ]["detected"]:

                self._apply_flag(
                    channel_flags,
                    channel,
                    QualityFlag.STUCK,
                )

                quality_flags[
                    channel
                ] = quality_flags[
                    channel
                ].replace(
                    QualityFlag.GOOD.value,
                    QualityFlag.STUCK.value,
                )

                issues.append(
                    f"{channel} contains a long constant/stuck segment."
                )

            if behavior[
                "discontinuity"
            ]["detected"]:

                self._apply_flag(
                    channel_flags,
                    channel,
                    QualityFlag.DISCONTINUITY,
                )

                quality_flags[
                    channel
                ] = quality_flags[
                    channel
                ].replace(
                    QualityFlag.GOOD.value,
                    QualityFlag.DISCONTINUITY.value,
                )

                issues.append(
                    f"{channel} contains sudden discontinuities."
                )

            if behavior[
                "saturation"
            ]["detected"]:

                issues.append(
                    f"{channel} contains possible sensor saturation."
                )

        # ----------------------------------------------------
        # COMMUNICATION GAPS
        # ----------------------------------------------------

        communication_checks = (
            self._check_communication_gaps(
                df,
                measurement_channels,
            )
        )

        for channel in measurement_channels:

            if communication_checks[
                channel
            ]["detected"]:

                self._apply_flag(
                    channel_flags,
                    channel,
                    QualityFlag.GAP,
                )

                quality_flags[
                    channel
                ] = quality_flags[
                    channel
                ].replace(
                    QualityFlag.GOOD.value,
                    QualityFlag.GAP.value,
                )

                issues.append(
                    f"{channel} has one or more communication/sampling gaps."
                )

        # ----------------------------------------------------
        # UNIT CHECKS
        # ----------------------------------------------------

        unit_checks = (
            self._check_units(
                df,
                measurement_channels,
            )
        )

        if unit_checks[
            "inconsistent_units"
        ]:

            issues.append(
                "Inconsistent units detected."
            )

        # ----------------------------------------------------
        # STATION ORDERING
        # ----------------------------------------------------

        station_ordering = (
            self._check_station_ordering(
                df
            )
        )

        # ----------------------------------------------------
        # TIMESTAMP ALIGNMENT
        # ----------------------------------------------------

        timestamp_alignment = (
            self._check_timestamp_alignment(
                df,
                measurement_channels,
            )
        )

        # ----------------------------------------------------
        # DATA ADEQUACY
        # ----------------------------------------------------

        if measurement_channels:

            expected_native_channels = set(
                NATIVE_MEASUREMENT_CHANNELS
            )

            detected_native_channels = (
                set(measurement_channels)
                .intersection(
                    expected_native_channels
                )
            )

            native_channel_coverage = (
                len(
                    detected_native_channels
                )
                / len(
                    expected_native_channels
                )
            )

            data_adequacy_details = {
                "measurement_channel_count": int(
                    len(measurement_channels)
                ),
                "native_expected_channel_count": int(
                    len(expected_native_channels)
                ),
                "native_detected_channel_count": int(
                    len(detected_native_channels)
                ),
                "native_channel_coverage": float(
                    native_channel_coverage
                ),
            }

            data_adequacy_o_q = float(
                native_channel_coverage
            )

        else:

            data_adequacy_details = {
                "measurement_channel_count": 0,
                "native_expected_channel_count": int(
                    len(
                        NATIVE_MEASUREMENT_CHANNELS
                    )
                ),
                "native_detected_channel_count": 0,
                "native_channel_coverage": 0.0,
            }

            data_adequacy_o_q = 0.0

        # ----------------------------------------------------
        # SOURCE DATA INTEGRITY
        # ----------------------------------------------------

        data_was_modified = not (
            list(df.columns)
            == original_columns
            and df.index.equals(
                original_index
            )
        )

        # ----------------------------------------------------
        # ACCEPTABILITY
        # ----------------------------------------------------

        critical_flags = {
            QualityFlag.INVALID,
            QualityFlag.MISSING,
            QualityFlag.DISCONTINUITY,
        }

        critical_channel_count = sum(
            flag in critical_flags
            for flag in channel_flags.values()
        )

        if not channel_flags:

            is_acceptable = False

        else:

            quality_fraction = (
                1.0
                - (
                    critical_channel_count
                    / len(channel_flags)
                )
            )

            is_acceptable = bool(
                quality_fraction >= 0.75
            )

        # ----------------------------------------------------
        # FINAL RESULT
        # ----------------------------------------------------

        return {
            "measurement_channels": (
                measurement_channels
            ),
            "channel_flags": (
                channel_flags
            ),
            "quality_flags": (
                quality_flags
            ),
            "timestamp_checks": (
                timestamp_checks
            ),
            "sampling_checks": (
                sampling_checks
            ),
            "numeric_checks": (
                numeric_checks
            ),
            "sensor_checks": (
                sensor_checks
            ),
            "communication_checks": (
                communication_checks
            ),
            "unit_checks": (
                unit_checks
            ),
            "station_ordering": (
                station_ordering
            ),
            "timestamp_alignment": (
                timestamp_alignment
            ),
            "data_adequacy_o_q": (
                data_adequacy_o_q
            ),
            "data_adequacy_details": (
                data_adequacy_details
            ),
            "issues": issues,
            "is_acceptable": (
                is_acceptable
            ),
            "data_was_modified": (
                data_was_modified
            ),
            "native_units": (
                NATIVE_UNITS.copy()
            ),
        }