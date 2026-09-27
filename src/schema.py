"""
H2-PRISM Data Contracts & Result Schema
Defines the shared dataclasses connecting modules across Person 1, Person 2, and Person 3.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any


class EventStatus(str, Enum):
    NORMAL = "NORMAL"
    CANDIDATE = "CANDIDATE"


class AttributionClass(str, Enum):
    NORMAL = "NORMAL"
    LEAK = "LEAK"
    OPERATIONAL_TRANSIENT = "OPERATIONAL_TRANSIENT"
    SENSOR_FAULT = "SENSOR_FAULT"
    DATA_FAULT = "DATA_FAULT"
    UNKNOWN = "UNKNOWN"


class QualityFlag(str, Enum):
    GOOD = "GOOD"
    MISSING = "MISSING"
    DUPLICATE = "DUPLICATE"
    GAP = "GAP"
    STUCK = "STUCK"
    DISCONTINUITY = "DISCONTINUITY"
    INVALID = "INVALID"


class ObservabilityLevel(str, Enum):
    ADEQUATE = "ADEQUATE"
    LIMITED = "LIMITED"
    INSUFFICIENT = "INSUFFICIENT"


@dataclass
class EventCandidate:
    """Stage 1 lightweight trigger candidate."""
    event_id: str
    scenario_id: str
    run_id: str
    t0: float  # Onset timestamp / index
    window_start: float
    window_end: float
    detection_metric: float
    detection_threshold: float
    status: EventStatus = EventStatus.CANDIDATE
    notes: str = ""


@dataclass
class PhysicsEvidence:
    """Physics-anchored mass balance and line-pack evidence (Person 1 -> Person 2/3)."""
    event_id: str
    scenario_id: str
    raw_imbalance: float
    mass_balance_residual: float  # Uncorrected or line-pack corrected m_loss
    normalized_mass_balance_residual: float  # z_MB = m_loss / sigma_MB
    pressure_difference: float  # Upstream - downstream delta P
    flow_difference: float  # Inlet - outlet delta m_dot
    line_pack_correction: Optional[float] = None
    physics_consistency: float = 1.0  # [0, 1] consistency score
    physics_valid: bool = True
    physics_assumptions: List[str] = field(default_factory=list)
    uncertainty_sigma: float = 0.0


@dataclass
class PropagationEvidence:
    """Cross-station propagation and delay evidence (Person 1 -> Person 2/3)."""
    event_id: str
    scenario_id: str
    estimated_delay: Optional[float] = None  # Delta t_12
    correlation_strength: float = 0.0  # Peak cross-correlation value
    propagation_consistency: bool = False
    localization_interval: Optional[Tuple[float, float]] = None  # [x_min, x_max] in meters
    localization_observable: bool = False
    resolution_floor: float = 0.0  # Minimum resolvable distance = a * dt / 2
    abstention_reason: Optional[str] = None


@dataclass
class MLResult:
    """Machine learning likelihood and predictions (Person 2 -> Person 3)."""
    event_id: str
    predicted_class: AttributionClass
    probabilities: Dict[str, float]
    calibrated_probabilities: Dict[str, float]
    confidence: float
    probability_margin: float  # Margin between top and 2nd hypothesis
    feature_importance: Dict[str, float] = field(default_factory=dict)
    model_version: str = "xgboost_v1.0"


@dataclass
class EvidenceResult:
    """Contradiction-aware evidence aggregation (Person 2 -> Person 3)."""
    event_id: str
    ml_evidence: Dict[str, float]
    physics_evidence: Dict[str, Any]
    propagation_evidence: Dict[str, Any]
    transient_evidence: Dict[str, Any]
    contradiction_score: float  # [0, 1] Disagreement between ML and Physics/Propagation
    fused_hypotheses: Dict[str, float]
    fusion_method: str = "calibrated_stacking"  # or 'dempster_shafer'


@dataclass
class ObservabilityResult:
    """Independent 3-axis observability score (Person 3)."""
    event_id: str
    o_q: float  # Data quality / adequacy [0, 1]
    o_s: float  # Structural discriminability [0, 1]
    o_e: float  # Evidential discriminability [0, 1]
    overall_observability: float  # min(o_q, o_s, o_e)
    observability_level: ObservabilityLevel
    failing_criteria: List[str] = field(default_factory=list)


@dataclass
class Decision:
    """Final gated attribution decision or UNKNOWN abstention (Person 3)."""
    event_id: str
    scenario_id: str
    timestamp: float
    decision: AttributionClass
    reason: str
    confidence: float
    observability: ObservabilityResult
    supporting_evidence: List[str] = field(default_factory=list)
    contradicting_evidence: List[str] = field(default_factory=list)
    localization_interval: Optional[Tuple[float, float]] = None
    severity_estimate: Optional[float] = None
    is_abstained: bool = False


@dataclass
class StructuredEventReport:
    """End-to-end audit report for SCADA/Historian."""
    event_id: str
    scenario_id: str
    run_id: str
    timestamp: float
    candidate: EventCandidate
    physics: PhysicsEvidence
    propagation: PropagationEvidence
    ml: MLResult
    evidence: EvidenceResult
    decision: Decision
