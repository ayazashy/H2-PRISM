"""
Stage 1 Candidate Event Detector and Windowing (Person 3: Yazan).
Lightweight online trigger that scans rolling statistics and rate-of-change,
emitting EventCandidate objects and pre/post-event analysis windows.
"""

from typing import List, Optional
import numpy as np
import pandas as pd
from .schema import EventCandidate, EventStatus


class CandidateDetector:
    """Lightweight Stage 1 change-detection filter."""

    def __init__(
        self,
        window_size: int = 20,
        flow_imbalance_threshold_sigma: float = 3.0,
        pressure_rate_threshold_pa_s: float = 5000.0,
        pre_event_steps: int = 30,
        post_event_steps: int = 60
    ):
        self.window_size = window_size
        self.flow_threshold_sigma = flow_imbalance_threshold_sigma
        self.dp_threshold = pressure_rate_threshold_pa_s
        self.pre_event = pre_event_steps
        self.post_event = post_event_steps

    def scan_scenario(self, df: pd.DataFrame) -> List[EventCandidate]:
        """
        Scans time-series dataframe and returns detected candidate events.
        """
        candidates = []
        if len(df) < self.window_size * 2:
            return candidates

        ts = df["timestamp"].to_numpy() if "timestamp" in df.columns else np.arange(len(df))
        p_up = df["p_upstream"].to_numpy()
        m_in = df["m_inlet"].to_numpy()
        m_out = df["m_outlet"].to_numpy()

        dt = float(np.mean(np.diff(ts))) if len(ts) > 1 else 1.0

        # Uncorrected flow imbalance
        flow_imbalance = m_in - m_out
        baseline_flow_mean = float(np.mean(flow_imbalance[:self.window_size]))
        baseline_flow_std = float(np.std(flow_imbalance[:self.window_size])) + 1e-3

        # Pressure rate of change dP/dt
        dp_dt = np.abs(np.gradient(p_up, dt))

        # Online scan for threshold exceedance
        in_candidate = False
        last_event_step = -999

        for step in range(self.window_size, len(df) - 5):
            if step - last_event_step < self.post_event:
                continue

            current_imbalance_dev = abs(flow_imbalance[step] - baseline_flow_mean)
            current_dp = dp_dt[step]

            flow_score = current_imbalance_dev / baseline_flow_std
            dp_score = current_dp / self.dp_threshold

            if flow_score > self.flow_threshold_sigma or dp_score > 1.0:
                # Trigger candidate
                event_id = f"evt_{df['scenario_id'].iloc[step] if 'scenario_id' in df else 's0'}_{step}"
                w_start = float(ts[max(0, step - self.pre_event)])
                w_end = float(ts[min(len(df) - 1, step + self.post_event)])

                cand = EventCandidate(
                    event_id=event_id,
                    scenario_id=str(df["scenario_id"].iloc[step]) if "scenario_id" in df else "mock_001",
                    run_id=str(df["run_id"].iloc[step]) if "run_id" in df else "run_01",
                    t0=float(ts[step]),
                    window_start=w_start,
                    window_end=w_end,
                    detection_metric=max(flow_score, dp_score),
                    detection_threshold=self.flow_threshold_sigma,
                    status=EventStatus.CANDIDATE,
                    notes=f"Triggered by flow_score={flow_score:.2f}, dp_score={dp_score:.2f}"
                )
                candidates.append(cand)
                last_event_step = step

        return candidates

    def extract_event_window(self, df: pd.DataFrame, candidate: EventCandidate) -> pd.DataFrame:
        """
        Extracts the sub-dataframe corresponding to candidate [window_start, window_end].
        Ensures strict boundary containment without cross-scenario leakage.
        """
        mask = (df["timestamp"] >= candidate.window_start) & (df["timestamp"] <= candidate.window_end)
        return df.loc[mask].copy().reset_index(drop=True)
