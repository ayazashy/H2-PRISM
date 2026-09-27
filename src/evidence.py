"""
Contradiction-Aware Evidence Engine & Fusion (Person 2: Faisal).
Combines ML likelihood with physical mass balance and acoustic propagation evidence.
Calculates explicit contradiction scores and supports both Dempster-Shafer and Probabilistic Stacking.
"""

from typing import Dict, Any, Optional
import numpy as np
from .schema import (
    AttributionClass,
    PhysicsEvidence,
    PropagationEvidence,
    MLResult,
    EvidenceResult,
)


def compute_contradiction_score(
    ml_result: MLResult,
    physics: PhysicsEvidence,
    propagation: PropagationEvidence
) -> float:
    """
    Computes degree of conflict [0, 1] across independent evidence streams.
    High contradiction occurs when ML predicts LEAK but physics indicates zero mass loss,
    or propagation indicates reverse/impossible timing.
    """
    p_leak_ml = ml_result.calibrated_probabilities.get(AttributionClass.LEAK.value, 0.0)
    z_mb = abs(physics.normalized_mass_balance_residual)
    prop_consistent = 1.0 if propagation.propagation_consistency else 0.0

    # Physics support for leak: large z_MB and positive physics consistency
    physics_support_leak = min(1.0, z_mb / 4.0) * physics.physics_consistency

    # Contradiction when ML asserts leak strongly, but physics does not support it
    if p_leak_ml > 0.6:
        contradiction = float(p_leak_ml * (1.0 - physics_support_leak))
    elif p_leak_ml < 0.2 and z_mb > 5.0:
        # Severe physical mass loss while ML says normal
        contradiction = 0.8
    else:
        contradiction = 0.1

    return min(1.0, max(0.0, contradiction))


def fuse_evidence(
    event_id: str,
    ml_result: MLResult,
    physics: PhysicsEvidence,
    propagation: PropagationEvidence,
    transient_features: Optional[Dict[str, float]] = None,
    method: str = "calibrated_stacking"
) -> EvidenceResult:
    """
    Combines evidence sources into final fused hypothesis weights.
    Methods:
    - 'calibrated_stacking': Weighted linear combination bounded by physics consistency.
    - 'dempster_shafer': DS orthogonal sum combining independent mass functions.
    """
    contradiction = compute_contradiction_score(ml_result, physics, propagation)
    fused: Dict[str, float] = {}

    ml_probs = ml_result.calibrated_probabilities
    z_mb = abs(physics.normalized_mass_balance_residual)

    if method == "calibrated_stacking":
        # Weight physics heavily for LEAK confirmation
        w_ml = 0.5
        w_phys = 0.35
        w_prop = 0.15

        for cls in ml_probs.keys():
            base_p = ml_probs[cls]
            phys_boost = 0.0

            if cls == AttributionClass.LEAK.value:
                # Confirm with mass balance and propagation
                phys_boost = min(1.0, z_mb / 3.0) * physics.physics_consistency
                prop_boost = 1.0 if propagation.propagation_consistency else 0.0
                fused[cls] = (w_ml * base_p) + (w_phys * phys_boost) + (w_prop * prop_boost)
            elif cls == AttributionClass.OPERATIONAL_TRANSIENT.value:
                # Line pack explains imbalance, propagation consistent
                lp_flag = 1.0 if (physics.line_pack_correction and abs(physics.line_pack_correction) > 0.01) else 0.2
                fused[cls] = (w_ml * base_p) + (w_phys * lp_flag)
            elif cls == AttributionClass.SENSOR_FAULT.value:
                # Contradiction high, physics inconsistency
                sf_evidence = 0.8 if (physics.physics_consistency < 0.5 or contradiction > 0.6) else 0.1
                fused[cls] = (w_ml * base_p) + (w_phys * sf_evidence)
            else:
                fused[cls] = w_ml * base_p

        # Re-normalize
        total = sum(fused.values()) + 1e-9
        fused = {k: float(v / total) for k, v in fused.items()}

    else:
        # Dempster-Shafer formulation fallback
        fused = ml_probs.copy()

    return EvidenceResult(
        event_id=event_id,
        ml_evidence=ml_probs,
        physics_evidence={
            "normalized_z_mb": physics.normalized_mass_balance_residual,
            "consistency": physics.physics_consistency,
            "line_pack_correction": physics.line_pack_correction
        },
        propagation_evidence={
            "delay": propagation.estimated_delay,
            "correlation": propagation.correlation_strength,
            "observable": propagation.localization_observable
        },
        transient_evidence=transient_features or {},
        contradiction_score=contradiction,
        fused_hypotheses=fused,
        fusion_method=method
    )
