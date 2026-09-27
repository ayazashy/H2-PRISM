"""
Independent 3-Axis Observability Assessment (Person 3: Yazan).
Evaluates whether sensor instrumentation and data quality structurally allow
discrimination, independent of classifier confidence.
O = min(O_Q, O_S, O_E)
"""

from typing import Dict, Any, List
from .schema import (
    ObservabilityResult,
    ObservabilityLevel,
    PhysicsEvidence,
    PropagationEvidence,
    EvidenceResult,
)


def compute_observability(
    event_id: str,
    data_qc_summary: Dict[str, Any],
    physics: PhysicsEvidence,
    propagation: PropagationEvidence,
    evidence: EvidenceResult,
    pipe_length_m: float = 10000.0,
    sampling_dt_s: float = 1.0,
    hydrogen_wave_speed_m_s: float = 1300.0,
) -> ObservabilityResult:
    """
    Computes 3-axis observability:
    1. O_Q (Data Quality Adequacy): Channel completeness and quality flags.
    2. O_S (Structural Discriminability): Ratio of propagation transit time to sampling interval.
    3. O_E (Evidential Discriminability): Availability of non-conflicted physics & propagation signals.
    """
    failing_criteria: List[str] = []

    # 1. O_Q: Data Quality
    o_q = float(data_qc_summary.get("data_adequacy_o_q", 1.0))
    if o_q < 0.7:
        failing_criteria.append(f"Data adequacy O_Q ({o_q:.2f}) below minimum threshold 0.70")

    # 2. O_S: Structural Discriminability
    # Acoustic transit time across segment tau_travel = L / a
    tau_travel = pipe_length_m / hydrogen_wave_speed_m_s
    # If sampling interval is larger than travel time, delay cannot be resolved
    ratio = tau_travel / max(sampling_dt_s, 1e-4)
    if ratio >= 2.0:
        o_s = 1.0
    elif ratio >= 1.0:
        o_s = 0.6
    else:
        o_s = 0.2
        failing_criteria.append(f"Structural resolution O_S ({o_s:.2f}) insufficient: sampling interval {sampling_dt_s}s exceeds acoustic transit time {tau_travel:.2f}s")

    # 3. O_E: Evidential Discriminability
    # Evaluates whether evidence items are above noise and non-contradictory
    contradiction = evidence.contradiction_score
    if contradiction > 0.6:
        o_e = 0.3
        failing_criteria.append(f"Severe evidential conflict (contradiction score={contradiction:.2f})")
    elif not physics.physics_valid:
        o_e = 0.4
        failing_criteria.append("Physics residual marked invalid due to numerical bounds.")
    else:
        o_e = 0.9

    overall_o = min(o_q, o_s, o_e)

    if overall_o >= 0.7:
        level = ObservabilityLevel.ADEQUATE
    elif overall_o >= 0.4:
        level = ObservabilityLevel.LIMITED
    else:
        level = ObservabilityLevel.INSUFFICIENT

    return ObservabilityResult(
        event_id=event_id,
        o_q=o_q,
        o_s=o_s,
        o_e=o_e,
        overall_observability=overall_o,
        observability_level=level,
        failing_criteria=failing_criteria
    )
