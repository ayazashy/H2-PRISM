"""
Data Quality Control and Flagging (Person 1: Ahmed).
Checks sensor health, missing data, stuck sensors, timestamp continuity, and physical range validity.
Flags observations without destructive deletions.
"""

from typing import Dict, List, Tuple, Any
import numpy as np
import pandas as pd
from .schema import QualityFlag


class QualityController:
    """Evaluates time-series data quality and generates structured flags and adequacy scores."""

    def __init__(
        self,
        min_sampling_interval: float = 0.01,
        max_sampling_interval: float = 10.0,
        stuck_window_size: int = 15,
        pressure_range_pa: Tuple[float, float] = (0.0, 30.0e6),  # 0 to 300 bar
        flow_range_kg_s: Tuple[float, float] = (0.0, 100.0),
    ):
        self.min_dt = min_sampling_interval
        self.max_dt = max_sampling_interval
        self.stuck_window = stuck_window_size
        self.p_min, self.p_max = pressure_range_pa
        self.m_min, self.m_max = flow_range_kg_s

    def inspect_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Runs comprehensive QC audit across all channels in the dataframe.
        Returns per-channel quality flags and an overall data adequacy score [0, 1].
        """
        issues = []
        flags = {col: QualityFlag.GOOD for col in df.columns}

        # 1. Timestamp checks
        if "timestamp" in df.columns:
            ts = df["timestamp"].to_numpy()
            diffs = np.diff(ts)

            if np.any(diffs <= 0):
                flags["timestamp"] = QualityFlag.INVALID
                issues.append("Non-monotonic or duplicate timestamps detected.")

            if np.any(diffs > self.max_dt):
                flags["timestamp"] = QualityFlag.GAP
                issues.append("Sampling gap exceeds maximum allowed threshold.")

        # 2. Channel range and NaN checks
        for col in ["p_upstream", "p_downstream"]:
            if col in df.columns:
                series = df[col]
                if series.isna().any():
                    flags[col] = QualityFlag.MISSING
                    issues.append(f"{col} contains missing values.")
                elif np.any(series < self.p_min) or np.any(series > self.p_max):
                    flags[col] = QualityFlag.INVALID
                    issues.append(f"{col} contains values outside physical pressure range.")
                elif self._is_stuck(series.to_numpy()):
                    flags[col] = QualityFlag.STUCK
                    issues.append(f"{col} has zero-variance stuck segments.")

        for col in ["m_inlet", "m_outlet"]:
            if col in df.columns:
                series = df[col]
                if series.isna().any():
                    flags[col] = QualityFlag.MISSING
                    issues.append(f"{col} contains missing values.")
                elif np.any(series < self.m_min) or np.any(series > self.m_max):
                    flags[col] = QualityFlag.INVALID
                    issues.append(f"{col} contains values outside physical flow range.")
                elif self._is_stuck(series.to_numpy()):
                    flags[col] = QualityFlag.STUCK
                    issues.append(f"{col} has zero-variance stuck segments.")

        # Compute adequacy score O_Q (fraction of channels that are GOOD)
        essential_channels = [c for c in ["p_upstream", "p_downstream", "m_inlet", "m_outlet"] if c in df.columns]
        good_count = sum(1 for c in essential_channels if flags[c] == QualityFlag.GOOD)
        o_q = (good_count / len(essential_channels)) if essential_channels else 0.0

        return {
            "channel_flags": flags,
            "data_adequacy_o_q": o_q,
            "issues": issues,
            "is_acceptable": o_q >= 0.75
        }

    def _is_stuck(self, array: np.ndarray) -> bool:
        if len(array) < self.stuck_window:
            return False
        # Rolling variance check
        rolling_diff = np.diff(array)
        for i in range(len(rolling_diff) - self.stuck_window):
            if np.all(rolling_diff[i:i + self.stuck_window] == 0):
                return True
        return False
