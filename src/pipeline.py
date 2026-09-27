"""
End-to-End H2-PRISM Pipeline Orchestrator (Person 3: Yazan).
Connects Person 1 (Data, QC, Physics, Propagation), Person 2 (Features, XGBoost, Evidence Fusion),
and Person 3 (Observability, Decision Gating, Reporting).
"""

from typing import List, Optional
import pandas as pd

from .schema import (
    EventCandidate,
    PhysicsEvidence,
    PropagationEvidence,
    MLResult,
    EvidenceResult,
    ObservabilityResult,
    Decision,
    StructuredEventReport,
)
from .quality import QualityController
from .detector import CandidateDetector
from .physics import compute_mass_balance_residual
from .propagation import estimate_propagation_delay
from .features import extract_window_features
from .fingerprint import extract_transient_fingerprint
from .model import EventAttributionModel
from .evidence import fuse_evidence
from .observability import compute_observability
from .decision import DecisionEngine


class H2PrismPipeline:
    """Master orchestrator for the H2-PRISM framework."""

    def __init__(
        self,
        pipe_length_m: float = 10000.0,
        pipe_diameter_m: float = 0.4,
        hydrogen_wave_speed_m_s: float = 1300.0,
        attribution_model: Optional[EventAttributionModel] = None,
        enable_line_pack: bool = True,
        fusion_method: str = "calibrated_stacking"
    ):
        self.pipe_length_m = pipe_length_m
        self.pipe_diameter_m = pipe_diameter_m
        self.wave_speed = hydrogen_wave_speed_m_s
        self.enable_line_pack = enable_line_pack
        self.fusion_method = fusion_method

        # Component modules
        self.qc = QualityController()
        self.detector = CandidateDetector()
        self.model = attribution_model or EventAttributionModel()
        self.decision_engine = DecisionEngine()

    def process_scenario(self, df: pd.DataFrame) -> List[StructuredEventReport]:
        """
        Executes end-to-end processing of a single continuous scenario.
        Returns a structured report for each detected candidate event.
        """
        reports: List[StructuredEventReport] = []

        # 1. Quality Control & Synchronization
        qc_result = self.qc.inspect_dataframe(df)

        # 2. Stage 1 Candidate Event Detection
        candidates = self.detector.scan_scenario(df)
        if not candidates:
            return reports

        dt = float(df["timestamp"].diff().mean()) if "timestamp" in df and len(df) > 1 else 1.0

        for candidate in candidates:
            # Extract isolated event window
            window_df = self.detector.extract_event_window(df, candidate)
            if len(window_df) < 5:
                continue

            # 3. Physics Consistency (Person 1)
            physics = compute_mass_balance_residual(
                window_df=window_df,
                pipe_length_m=self.pipe_length_m,
                pipe_diameter_m=self.pipe_diameter_m,
                enable_line_pack=self.enable_line_pack
            )

            # 4. Propagation Delay & Conditional Localization (Person 1)
            propagation = estimate_propagation_delay(
                window_df=window_df,
                pipe_length_m=self.pipe_length_m,
                hydrogen_wave_speed_m_s=self.wave_speed
            )

            # 5. Transient-Physics Fingerprint (Candidate Layer - Person 2)
            fingerprint = extract_transient_fingerprint(
                signal=window_df["p_upstream"].to_numpy(),
                sampling_rate_hz=1.0 / dt
            )

            # 6. Feature Extraction (Person 2)
            features = extract_window_features(
                window_df=window_df,
                physics=physics,
                propagation=propagation
            )
            features.update(fingerprint)

            # 7. AI Event Attribution Likelihood (Person 2)
            ml_result = self.model.predict_event(candidate.event_id, features)

            # 8. Evidence Fusion & Contradiction Analysis (Person 2)
            evidence = fuse_evidence(
                event_id=candidate.event_id,
                ml_result=ml_result,
                physics=physics,
                propagation=propagation,
                transient_features=fingerprint,
                method=self.fusion_method
            )

            # 9. Independent 3-Axis Observability Assessment (Person 3)
            observability = compute_observability(
                event_id=candidate.event_id,
                data_qc_summary=qc_result,
                physics=physics,
                propagation=propagation,
                evidence=evidence,
                pipe_length_m=self.pipe_length_m,
                sampling_dt_s=dt,
                hydrogen_wave_speed_m_s=self.wave_speed
            )

            # 10. Gated Decision & UNKNOWN Abstention (Person 3)
            decision = self.decision_engine.evaluate(
                event_id=candidate.event_id,
                scenario_id=candidate.scenario_id,
                timestamp=candidate.t0,
                evidence=evidence,
                observability=observability,
                physics=physics,
                propagation=propagation
            )

            report = StructuredEventReport(
                event_id=candidate.event_id,
                scenario_id=candidate.scenario_id,
                run_id=candidate.run_id,
                timestamp=candidate.t0,
                candidate=candidate,
                physics=physics,
                propagation=propagation,
                ml=ml_result,
                evidence=evidence,
                decision=decision
            )
            reports.append(report)

        return reports
