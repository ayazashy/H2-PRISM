"""Extend the frozen Phase 13 release-label benchmark without changing its folds."""
import argparse
import hashlib
import json
import platform
import time
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from xgboost import XGBClassifier, __version__ as xgb_version

from .baseline import make_random_forest
from .phase13_ml import CLASSES, SEED
from .secondary_baseline import make_logistic_regression

LABELS = {name: code for code, name in enumerate(CLASSES)}
XGB_DEFAULT = dict(n_estimators=100, learning_rate=0.05, max_depth=2,
                   min_child_weight=2, reg_lambda=5)
XGB_ALTERNATE = dict(n_estimators=60, learning_rate=0.1, max_depth=3,
                     min_child_weight=1, reg_lambda=10)


def counts(labels):
    return {name: int((labels == name).sum()) for name in CLASSES}


def inner_validation_support(table):
    """Classes appearing in valid inner holdouts that retain all training classes."""
    labels = table.label_mapped
    groups = table.Scenario_Family_ID
    return sorted({label for group in groups.unique()
                   if set(labels[groups != group]) == set(CLASSES)
                   for label in labels[groups == group]})


def estimators(sensitivity=False):
    xgb = XGB_ALTERNATE if sensitivity else XGB_DEFAULT
    c = 0.1 if sensitivity else 1.0
    return {
        "logistic": make_logistic_regression({"C": 1}, SEED),
        "random_forest": make_random_forest(dict(n_estimators=200, min_samples_leaf=2,
                                                 max_features="sqrt"), SEED),
        "xgboost": Pipeline([("classifier", XGBClassifier(**xgb, objective="multi:softprob",
                                                           num_class=len(CLASSES), random_state=SEED,
                                                           n_jobs=1, tree_method="hist"))]),
        "linear_svm": Pipeline([("scale", StandardScaler()), ("classifier", SVC(
            kernel="linear", C=c, class_weight="balanced", random_state=SEED))]),
        "rbf_svm": Pipeline([("scale", StandardScaler()), ("classifier", SVC(
            kernel="rbf", C=c, gamma=0.01 if sensitivity else "scale",
            class_weight="balanced", random_state=SEED))]),
    }


def fit(model, name, data, cols):
    labels = data.label_mapped
    if set(labels) != set(CLASSES):
        raise ValueError("Frozen fold lacks the required training class support")
    model.fit(data[cols], labels.map(LABELS) if name == "xgboost" else labels)


def predict(model, name, data, cols):
    raw = model.predict(data[cols])
    return np.array(CLASSES)[raw.astype(int)] if name == "xgboost" else raw


def main(previous, output):
    meta = json.loads((previous / "ml_results.json").read_text(encoding="utf8"))
    data = pd.read_csv(previous / "features.csv", float_precision="round_trip")
    cols = meta["features"]
    groups = data.Scenario_Family_ID
    expected = meta["model_runs"]["logistic"]["folds"]
    if expected != meta["model_runs"]["random_forest"]["folds"] or not data.Scenario_ID.is_unique:
        raise ValueError("Frozen folds or scenario IDs disagree")
    fold_info = []
    for fold in expected:
        test = groups == fold["group"]
        train_labels, test_labels = data.label_mapped[~test], data.label_mapped[test]
        eligible = set(train_labels) == set(CLASSES)
        if ((len(train_labels), len(test_labels)) != (fold["train"], fold["test"])
                or eligible != (fold["status"] == "scored")):
            raise ValueError(f"Frozen split mismatch: {fold}")
        fold_info.append(dict(fold, train_classes=counts(train_labels), test_classes=counts(test_labels),
                              test_scenarios=data.Scenario_ID[test].tolist(),
                              inner_validation_classes=inner_validation_support(data[~test]) if eligible else []))
    if set(groups) != {f["group"] for f in fold_info}:
        raise ValueError("Frozen groups do not cover the feature table")
    scored = [f["group"] for f in fold_info if f["status"] == "scored"]
    if set(data.label_mapped[groups.isin(scored)]) != {"LEAK"}:
        raise ValueError("Benchmark is defined for the frozen LEAK-only test support")
    if any(set(f["inner_validation_classes"]) == set(CLASSES) for f in fold_info):
        raise ValueError("Unexpected nested tuning support in frozen protocol")
    variants = {"full": cols, "pressure": [c for c in cols if c.startswith("PS")],
                "flow": [c for c in cols if c.startswith("MFS")],
                "defaults_sensitivity": cols}
    rows = []
    for variant, columns in variants.items():
        alternate = variant == "defaults_sensitivity"
        for group in scored:
            test = groups == group
            for name, model in estimators(alternate).items():
                if alternate and name in ("logistic", "random_forest"):
                    continue
                start = time.perf_counter()
                fit(model, name, data[~test], columns)
                fit_ms = 1000 * (time.perf_counter() - start)
                start = time.perf_counter()
                predicted = predict(model, name, data[test], columns)
                predict_ms = 1000 * (time.perf_counter() - start)
                for scenario, observed in zip(data.Scenario_ID[test], predicted):
                    rows.append(dict(variant=variant, fold=group, model=name, Scenario_ID=scenario,
                                     truth="LEAK", prediction=observed, fit_ms=fit_ms,
                                     batch_predict_ms=predict_ms))
    table = pd.DataFrame(rows)
    for name in ("logistic", "random_forest"):
        frozen = pd.read_csv(previous / f"{name}_predictions.csv").set_index("Scenario_ID")
        fresh = table[(table.variant == "full") & (table.model == name)].set_index("Scenario_ID")
        if not fresh.prediction.sort_index().equals(frozen.prediction.sort_index()):
            raise ValueError(f"Previous predictions failed exact replay: {name}")
    table["hit"] = table.prediction == table.truth
    summary = table.groupby(["variant", "model"]).hit.agg(hits="sum", cases="size", recall="mean")
    perf = table.groupby(["variant", "model", "fold"]).agg(
        hits=("hit", "sum"), cases=("hit", "size"), recall=("hit", "mean"),
        fit_ms=("fit_ms", "first"), batch_predict_ms=("batch_predict_ms", "first"))
    output.mkdir(parents=True)
    table.to_csv(output / "predictions.csv", index=False)
    perf.to_csv(output / "fold_metrics.csv")
    summary.to_csv(output / "comparison.csv")
    full = table[table.variant == "full"]
    comparison = full.pivot(index=["fold", "Scenario_ID"], columns="model", values="prediction")
    comparison.to_csv(output / "scenario_comparison.csv")
    pd.crosstab(full.model, full.prediction).reindex(columns=CLASSES, fill_value=0).to_csv(output / "error_counts.csv")
    artifacts = {}
    for name, model in estimators().items():
        fit(model, name, data, cols)
        joblib.dump(model, output / f"{name}_archive.joblib")
        artifacts[name] = model.get_params(deep=True)
    inputs = ("features.csv", "ml_results.json", "logistic_predictions.csv", "random_forest_predictions.csv")
    report = dict(scope="exploratory LEAK recall; never multiclass accuracy", seed=SEED, folds=fold_info,
                  input_sha256={f: hashlib.sha256((previous / f).read_bytes()).hexdigest() for f in inputs},
                  versions=dict(python=platform.python_version(), sklearn=sklearn.__version__,
                                xgboost=xgb_version, numpy=np.__version__, pandas=pd.__version__),
                  classes=CLASSES, xgboost_label_codes=LABELS, features=variants,
                  model_settings=artifacts, alternate_xgboost=XGB_ALTERNATE,
                  alternate_svm=dict(C=0.1, rbf_gamma=0.01),
                  selection="Predefined settings; sensitivity variants are descriptive and do not replace defaults.",
                  benchmark=summary.reset_index().to_dict("records"),
                  formal={"consistency":"INDETERMINATE","decision":"UNRESOLVED","localization":"L0"},
                  unsupported=["four-class performance","calibration","selective risk","formal improvement"])
    (output / "benchmark.json").write_text(json.dumps(report, indent=2, default=str), encoding="utf8")
    ax = summary["recall"].unstack().loc[["full","pressure","flow"]].plot.bar(
        color=["#205573","#526d85","#41958d","#087d9e","#253c61"], figsize=(9, 4))
    ax.set_ylabel("Held-out LEAK recall (39 scenarios)")
    ax.set_xlabel("Feature subset")
    ax.set_ylim(0, 1.05)
    ax.tick_params(axis="x", rotation=0)
    ax.legend(fontsize=8, loc="lower right")
    plt.tight_layout()
    plt.savefig(output / "leak_recall.png", dpi=240)
    plt.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("previous", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    main(args.previous, args.output)
