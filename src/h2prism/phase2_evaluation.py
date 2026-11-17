"""Family-level accounting for eligible, independently labeled diagnostic cases."""
from collections import Counter
from dataclasses import dataclass
from typing import Optional

from .certified_evidence import DiagnosticDecision, DecisionStatus


@dataclass(frozen=True)
class EvaluationCase:
    family: str
    domain: str
    decision: DiagnosticDecision
    ground_truth: Optional[str]
    truth_verified: bool
    eligible: bool
    certificate_replayed: Optional[bool] = None
    runtime_s: Optional[float] = None


def summarize(cases: tuple[EvaluationCase, ...]) -> dict:
    eligible = [case for case in cases if case.eligible]
    families = {case.family for case in eligible}
    if "" in families or len(families) != len(eligible):
        raise ValueError("Submit exactly one predeclared decision per independent family")
    if len({case.domain for case in eligible}) > 1:
        raise ValueError("Separate evaluation by evidence domain")
    specific = [case for case in eligible if case.decision.status is DecisionStatus.SPECIFIC]
    verified = all(case.truth_verified and case.ground_truth for case in eligible)
    statuses = Counter(case.decision.status.value for case in eligible)
    results = [result for case in eligible for result in case.decision.certificate.results]
    hypotheses = Counter(result.status.value for result in results)
    n = len(eligible)
    return {
        "eligible_families": n,
        "specific_count": len(specific),
        "specific_coverage": len(specific) / n if n else None,
        "selective_risk": (
            sum(case.decision.hypothesis != case.ground_truth for case in specific) / len(specific)
            if specific and verified else None
        ),
        "decision_rates": {status.value: statuses[status.value] / n if n else None for status in DecisionStatus},
        "hypothesis_rates": {key: hypotheses[key] / len(results) if results else None
                             for key in ("FEASIBLE", "EXCLUDED", "INDETERMINATE")},
        "true_hypothesis_exclusions": sum(case.ground_truth in case.decision.certificate.excluded
                                         for case in eligible) if n and verified else None,
        "candidate_set_sizes": [len(case.decision.certificate.feasible) +
                                len(case.decision.certificate.indeterminate) for case in eligible],
        "solver_timeouts": sum(result.reason == "SOLVER_TIMEOUT" for result in results),
        "evidence_failures": sum(bool(case.decision.certificate.measurement_issues) for case in eligible),
        "certificate_replay_results": [case.certificate_replayed for case in eligible],
        "runtimes_s": [case.runtime_s for case in eligible],
    }
