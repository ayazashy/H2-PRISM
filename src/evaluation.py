"""
Performance Evaluation & Metrics Module (Person 3: Yazan).
Calculates joint performance metrics under conditional abstention:
- False Physical Attribution Rate (FPAR)
- Leak Recall & F1
- Decision Coverage & Accuracy on Covered Events
- Localization Accuracy and Observability Ratio
- Pipeline Inference Latency
"""

from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
import time
from .schema import StructuredEventReport, AttributionClass, Decision


def evaluate_pipeline_performance(
    reports: List[StructuredEventReport],
    ground_truth_labels: List[str],
    leak_location_m: Optional[float] = None
) -> Dict[str, Any]:
    """
    Evaluates a collection of event reports against ground-truth labels.
    Never reports FPAR or accuracy in isolation from decision coverage.
    """
    total_events = len(reports)
    if total_events == 0:
        return {
            "total_events": 0,
            "classified_events": 0,
            "abstained_events": 0,
            "coverage": 0.0,
            "fpar": 0.0,
            "leak_recall": 0.0,
            "covered_accuracy": 0.0,
            "localization_observable_ratio": 0.0,
            "mean_localization_error_m": None
        }

    decisions = [r.decision.decision for r in reports]
    is_abstained = [r.decision.is_abstained for r in reports]

    n_abstained = sum(is_abstained)
    n_classified = total_events - n_abstained
    coverage = n_classified / total_events if total_events > 0 else 0.0

    # Covered events evaluation
    correct_covered = 0
    non_leak_events = 0
    false_leak_attributions = 0
    true_leaks = 0
    detected_leaks = 0

    localization_errors = []
    loc_observable_count = 0

    for rep, gt_label in zip(reports, ground_truth_labels):
        pred = rep.decision.decision.value
        gt = gt_label.upper()

        if not rep.decision.is_abstained:
            if pred == gt or (gt.startswith("LEAK") and pred == "LEAK"):
                correct_covered += 1

        # False Physical Attribution Rate (FPAR):
        # Attributing an operational transient or sensor fault as a LEAK
        if gt != "LEAK" and not gt.startswith("LEAK"):
            non_leak_events += 1
            if pred == "LEAK":
                false_leak_attributions += 1

        # Leak Recall
        if gt == "LEAK" or gt.startswith("LEAK"):
            true_leaks += 1
            if pred == "LEAK":
                detected_leaks += 1

        # Localization Evaluation
        if rep.propagation.localization_observable and rep.propagation.localization_interval is not None:
            loc_observable_count += 1
            if leak_location_m is not None:
                x_min, x_max = rep.propagation.localization_interval
                x_center = (x_min + x_max) / 2.0
                err = abs(x_center - leak_location_m)
                localization_errors.append(err)

    covered_accuracy = correct_covered / n_classified if n_classified > 0 else 0.0
    fpar = false_leak_attributions / non_leak_events if non_leak_events > 0 else 0.0
    leak_recall = detected_leaks / true_leaks if true_leaks > 0 else 1.0
    loc_obs_ratio = loc_observable_count / total_events if total_events > 0 else 0.0
    mean_loc_err = float(np.mean(localization_errors)) if localization_errors else None

    return {
        "total_events": total_events,
        "classified_events": n_classified,
        "abstained_events": n_abstained,
        "coverage": round(coverage, 4),
        "covered_accuracy": round(covered_accuracy, 4),
        "fpar": round(fpar, 4),
        "leak_recall": round(leak_recall, 4),
        "localization_observable_ratio": round(loc_obs_ratio, 4),
        "mean_localization_error_m": round(mean_loc_err, 2) if mean_loc_err is not None else None
    }
