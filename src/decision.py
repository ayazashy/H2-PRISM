"""
Decision Gating & UNKNOWN Abstention Logic (Person 3: Yazan).
Gates attribution decisions behind independently evaluated observability and confidence thresholds.
Emits clear reasons whenever an event is abstained as UNKNOWN.
"""

from typing import List, Tuple, Optional
from .schema import (
    AttributionClass,
    ObservabilityResult,
    ObservabilityLevel,
    EvidenceResult,
    Decision,
    PhysicsEvidence,
    PropagationEvidence,
)


class DecisionEngine:
    """Enforces false-attribution-centered decision gating and UNKNOWN abstention."""

    def __init__(
        self,
        min_observability_threshold: float = 0.50,
        min_confidence_threshold: float = 0.55,
        min_probability_margin: float = 0.15,
        max_allowed_contradiction: float = 0.50,
    ):
        self.o_min = min_observability_threshold
        self.conf_min = min_confidence_threshold
        self.margin_min = min_probability_margin
        self.max_contradiction = max_allowed_contradiction

    def evaluate(
        self,
        event_id: str,
        scenario_id: str,
        timestamp: float,
        evidence: EvidenceResult,
        observability: ObservabilityResult,
        physics: PhysicsEvidence,
        propagation: PropagationEvidence,
    ) -> Decision:
        """
        Applies gating criteria. If any criterion fails, returns UNKNOWN with explicit reason.
        """
        fused = evidence.fused_hypotheses
        sorted_hypotheses = sorted(fused.items(), key=lambda x: x[1], reverse=True)
        top_cls_str, top_score = sorted_hypotheses[0]
        second_score = sorted_hypotheses[1][1] if len(sorted_hypotheses) > 1 else 0.0
        margin = top_score - second_score

        top_class = AttributionClass(top_cls_str) if top_cls_str in AttributionClass._value2member_map_ else AttributionClass.UNKNOWN

        supporting = []
        contradicting = []

        if top_class == AttributionClass.LEAK:
            supporting.append(f"Normalized mass balance z_MB={physics.normalized_mass_balance_residual:.2f}")
            if propagation.propagation_consistency:
                supporting.append(f"Acoustic propagation confirmed with lag={propagation.estimated_delay:.2f}s")
            if evidence.contradiction_score > self.max_contradiction:
                contradicting.append(f"High cross-stream contradiction={evidence.contradiction_score:.2f}")

        # Check Abstention Criteria
        abstention_reasons = []

        if observability.overall_observability < self.o_min:
            reasons = "; ".join(observability.failing_criteria)
            abstention_reasons.append(f"Insufficient observability ({observability.overall_observability:.2f} < {self.o_min}): {reasons}")

        if top_score < self.conf_min:
            abstention_reasons.append(f"Low confidence ({top_score:.2f} < {self.conf_min})")

        if margin < self.margin_min:
            abstention_reasons.append(f"Ambiguous top hypotheses: margin ({margin:.2f} < {self.margin_min})")

        if evidence.contradiction_score > self.max_contradiction:
            abstention_reasons.append(f"Severe evidence conflict ({evidence.contradiction_score:.2f} > {self.max_contradiction})")

        # Emit Decision
        if abstention_reasons:
            full_reason = " | ".join(abstention_reasons)
            return Decision(
                event_id=event_id,
                scenario_id=scenario_id,
                timestamp=timestamp,
                decision=AttributionClass.UNKNOWN,
                reason=full_reason,
                confidence=top_score,
                observability=observability,
                supporting_evidence=supporting,
                contradicting_evidence=contradicting,
                localization_interval=None,
                severity_estimate=None,
                is_abstained=True
            )

        # Confident Decision
        loc_interval = propagation.localization_interval if top_class == AttributionClass.LEAK else None
        severity = float(physics.mass_balance_residual) if top_class == AttributionClass.LEAK else None

        return Decision(
            event_id=event_id,
            scenario_id=scenario_id,
            timestamp=timestamp,
            decision=top_class,
            reason=f"Confident attribution to {top_class.value} with confidence={top_score:.2f}, margin={margin:.2f}",
            confidence=top_score,
            observability=observability,
            supporting_evidence=supporting,
            contradicting_evidence=contradicting,
            localization_interval=loc_interval,
            severity_estimate=severity,
            is_abstained=False
        )
