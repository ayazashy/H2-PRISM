"""
H2-PRISM: A Physics-Anchored, Observability-Gated Framework for Event Attribution in Hydrogen Pipelines.
"""

from .schema import (
    EventStatus,
    AttributionClass,
    QualityFlag,
    ObservabilityLevel,
    EventCandidate,
    PhysicsEvidence,
    PropagationEvidence,
    MLResult,
    EvidenceResult,
    ObservabilityResult,
    Decision,
    StructuredEventReport,
)

from .pipeline import H2PrismPipeline
from .detector import CandidateDetector
from .decision import DecisionEngine
from .observability import compute_observability
from .evaluation import evaluate_pipeline_performance

__all__ = [
    "EventStatus",
    "AttributionClass",
    "QualityFlag",
    "ObservabilityLevel",
    "EventCandidate",
    "PhysicsEvidence",
    "PropagationEvidence",
    "MLResult",
    "EvidenceResult",
    "ObservabilityResult",
    "Decision",
    "StructuredEventReport",
    "H2PrismPipeline",
    "CandidateDetector",
    "DecisionEngine",
    "compute_observability",
    "evaluate_pipeline_performance",
]
