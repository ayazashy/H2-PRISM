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
        # Normalize ground truth category
        gt = str(gt_label).upper()
        gt_category = "UNKNOWN"
        if gt.startswith("LEAK"):
            gt_category = "LEAK"
        elif "TRANSIENT" in gt or "VALVE" in gt or "COMPRESSOR" in gt:
            gt_category = "TRANSIENT"
        elif "SENSOR" in gt or "FAULT" in gt or "DRIFT" in gt:
            gt_category = "FAULT"
        elif "UNKNOWN" in gt:
            gt_category = "UNKNOWN"

        pred_category = pred
        if pred in ("OPERATIONAL_TRANSIENT", "TRANSIENT"):
            pred_category = "TRANSIENT"
        elif pred in ("SENSOR_FAULT", "FAULT"):
            pred_category = "FAULT"

        if not rep.decision.is_abstained:
            if pred_category == gt_category:
                correct_covered += 1

        # False Physical Attribution Rate (FPAR):
        # Attributing an operational transient or sensor fault as a LEAK
        if gt_category != "LEAK":
            non_leak_events += 1
            if pred_category == "LEAK":
                false_leak_attributions += 1

        # Leak Recall
        if gt_category == "LEAK":
            true_leaks += 1
            if pred_category == "LEAK":
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


def evaluate_scenario_batch(pipeline, scenarios: List[pd.DataFrame]) -> Dict[str, Any]:
    """Processes a batch of scenario DataFrames and computes summary evaluation KPIs."""
    all_reports = []
    ground_truth = []
    for df in scenarios:
        reports = pipeline.process_scenario(df)
        for r in reports:
            t0, t1 = r.candidate.window_start, r.candidate.window_end
            if "timestamp" in df.columns:
                sub = df[(df["timestamp"] >= t0) & (df["timestamp"] <= t1)]
            else:
                sub = df
            
            if "label" in sub.columns and not sub["label"].empty:
                labels = sub["label"].tolist()
                non_normal = [l for l in labels if l != "NORMAL"]
                gt_label = non_normal[0] if non_normal else labels[0]
            elif "label" in df.columns:
                labels = df["label"].unique()
                non_normal = [l for l in labels if l != "NORMAL"]
                gt_label = non_normal[0] if non_normal else "NORMAL"
            else:
                gt_label = "NORMAL"

            all_reports.append(r)
            ground_truth.append(gt_label)
            
    if not all_reports:
        return {
            "total_events": 0,
            "classified_events": 0,
            "abstained_events": 0,
            "coverage": 1.0,
            "covered_accuracy": 1.0,
            "fpar": 0.0,
            "leak_recall": 1.0,
            "localization_observable_ratio": 1.0,
            "mean_localization_error_m": 0.0
        }
        
    return evaluate_pipeline_performance(all_reports, ground_truth)

