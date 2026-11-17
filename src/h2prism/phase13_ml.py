"""Retrospective release-label classification, grouped by known dependency components."""
import argparse
import json
from pathlib import Path
from types import SimpleNamespace

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, classification_report,
                             confusion_matrix, log_loss)

from .baseline import make_random_forest
from .data.loader import load_scenario
from .features import extract_features, model_feature_columns
from .secondary_baseline import make_logistic_regression
from .simnet_independence import build_graph
from .simnet_study import annotation, archive_path, catalog_tables

SEED = 42
SAMPLES = 5
FEATURES = ("mean", "std", "last_minus_first", "slope")
CLASSES = ("COMPRESSOR_DELAY", "COMPRESSOR_FAULT", "LEAK", "NORMAL")


def evaluation_metrics(truth, predicted, probabilities):
    support = {label: int((truth == label).sum()) for label in CLASSES}
    complete = all(support.values())
    return {
        "evaluated_scenarios": len(truth),
        "test_support": support,
        "restricted_accuracy": accuracy_score(truth, predicted),
        "criterion": "fraction of predictions matching archived labels in scored folds",
        "balanced_accuracy": balanced_accuracy_score(truth, predicted) if complete else None,
        "classification": classification_report(
            truth, predicted, labels=CLASSES, output_dict=True, zero_division=0
        ) if complete else None,
        "confusion": confusion_matrix(truth, predicted, labels=CLASSES).tolist(),
        "uncalibrated_log_loss": log_loss(truth, probabilities, labels=CLASSES),
    }


def main(output):
    manifest, _ = catalog_tables()
    graph = build_graph(manifest)
    family = {s: g for g, runs in graph["conservative_components"].items() for s in runs}
    windows = []
    excluded = {}
    for record in manifest.itertuples(index=False):
        key = record.Scenario_ID
        if record.eligible_primary != "True" or record.label_mapped not in CLASSES:
            excluded[key] = "manifest exclusion"
            continue
        frame = load_scenario(archive_path(record))
        labels, issues = annotation(frame, record)
        if issues:
            excluded[key] = list(issues)
            continue
        start = labels["onset_s"] if labels["onset_s"] is not None else 1000
        view = frame.loc[start:start+SAMPLES-1]
        if len(view) != SAMPLES or (labels["last_active_s"] is not None
                                    and view.index[-1] > labels["last_active_s"]):
            excluded[key] = "no complete within-event window"
            continue
        windows.append((record, view))
    channels = sorted(set.intersection(*(set(frame) for _, frame in windows)))
    channels = [c for c in channels if c.startswith(("PS", "MFS"))]
    if not channels:
        raise ValueError("No common telemetry")
    rows = []
    for record, frame in windows:
        key = record.Scenario_ID
        if not np.isfinite(frame[channels].to_numpy()).all():
            excluded[key] = "missing or nonfinite common telemetry"
            continue
        window = pd.DataFrame([dict(window_id=key, Scenario_ID=key, Scenario_Family_ID=family[key],
                                    label_mapped=record.label_mapped, start_row=0, end_row_exclusive=SAMPLES)])
        row = extract_features(frame, SimpleNamespace(t=frame.index), window, channels, FEATURES,
                               eligible_only=False)
        row["start_time"] = frame.index[0]
        rows.append(row)
    data = pd.concat(rows, ignore_index=True)
    columns = model_feature_columns(data)
    x, y = data[columns], data.label_mapped
    output.mkdir(parents=True)
    data.to_csv(output/"features.csv", index=False)
    models = {
        "logistic": make_logistic_regression({"C": 1}, SEED),
        "random_forest": make_random_forest({"n_estimators": 200, "min_samples_leaf": 2,
                                           "max_features": "sqrt"}, SEED),
    }
    results = {}
    for name, model in models.items():
        folds, predictions = [], []
        for group in sorted(data.Scenario_Family_ID.unique()):
            test = data.Scenario_Family_ID == group
            train = ~test
            if set(y[train]) != set(CLASSES):
                folds.append({"group": group, "train": int(train.sum()), "test": int(test.sum()),
                              "status": "skipped because at least one class is absent from training"})
                continue
            model.fit(x[train], y[train])
            proba = pd.DataFrame(model.predict_proba(x[test]), columns=model.classes_, index=x[test].index)
            pred = data.loc[test, ["Scenario_ID", "Scenario_Family_ID", "label_mapped"]].copy()
            pred["prediction"] = proba.idxmax(axis=1)
            predictions.append(pred.join(proba))
            folds.append({"group": group, "train": int(train.sum()), "test": int(test.sum()), "status":"scored"})
        table = pd.concat(predictions, ignore_index=True)
        table.to_csv(output/f"{name}_predictions.csv", index=False)
        truth, predicted = table.label_mapped, table.prediction
        results[name] = {"folds": folds, **evaluation_metrics(truth, predicted, table[list(CLASSES)])}
        model.fit(x, y)
        joblib.dump(model, output/f"{name}_full_archive.joblib")
    summary = {"scope": "exploratory archived annotation recognition; historically inspected, unknown ancestry possible",
               "scenario_count":len(data), "class_counts": y.value_counts().to_dict(),
               "dependency_graph_sha256":graph["sha256"], "excluded":excluded, "classes":CLASSES,
               "channel_names":channels, "features":columns, "seed":SEED, "window_samples":SAMPLES,
               "stride":None, "window_seconds_from_first_to_last":SAMPLES-1, "event_onset_supplied":True, "normal_anchor_s":1000, "random_forest_trees":200, "logistic_C":1, "model_runs":results,
               "calibration":"NOT_ESTABLISHED", "matched_coverage":"NOT_ESTABLISHED"}
    (output/"ml_results.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    main(parser.parse_args().output)
