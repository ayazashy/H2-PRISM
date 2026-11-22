"""Reproducible outer-fold experiments for the Faisal H2-PRISM workstream."""

import hashlib
import json
import subprocess
import sys
import time
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Dict, List, Mapping, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
)

from h2prism.evaluation import (
    TARGET_CLASSES,
    add_distinguishability_score,
    aligned_probabilities,
    apply_diagnostic_policy,
    compute_empirical_support,
    fit_baseline,
    fit_calibrator,
    inner_oof_predictions,
    load_outer_fold,
    probability_indicators,
    probability_metrics,
    threshold_for_coverage,
)
from h2prism.simnet_windows import build_window_dataset


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = WORKSPACE_ROOT / "configs" / "frozen_evaluation_config.yaml"
DEFAULT_OUTPUT_DIR = WORKSPACE_ROOT / "03_results"
CALIBRATION_METHODS = ("none", "sigmoid", "isotonic")
RUNTIME_PACKAGES = (
    "numpy",
    "pandas",
    "scipy",
    "pyarrow",
    "fastparquet",
    "PyYAML",
    "matplotlib",
    "seaborn",
    "PyWavelets",
    "scikit-learn",
    "joblib",
    "pytest",
)
SCORE_COLUMNS = {
    "B": "score_B",
    "C_minus_D": "score_C_minus_D",
    "C": "score_C",
    "B2": "score_B2",
    "B3": "score_B3",
    "D_only": "score_D_only",
}
SUPPORTED_CONFIG_VERSION = "1.0.2"


def _read_config(config_path: Path) -> Dict[str, object]:
    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    if not isinstance(config, dict):
        raise ValueError(f"Evaluation config must be a YAML mapping: {config_path}")
    required = {
        "config_version",
        "random_state",
        "window_size_samples",
        "stride_samples",
        "d_neighbors",
        "target_specific_coverage",
        "outer_folds",
        "bootstrap_replicates",
    }
    missing = required - set(config)

    expected_model = {
        "estimator": "RandomForestClassifier",
        "n_estimators": 300,
        "max_features": "sqrt",
        "min_samples_leaf": 2,
        "class_weight": "balanced_subsample",
        "family_balanced_sample_weight": True,
    }
    if config.get("model") != expected_model:
        raise ValueError("Model config does not match the implemented frozen baseline.")
    if config.get("calibration", {}).get("candidates") != list(CALIBRATION_METHODS):
        raise ValueError("Calibration candidates do not match the implementation.")
    if int(config.get("sampling_rate_hz", 0)) != 1:
        raise ValueError("The current window implementation requires the audited 1 Hz rate.")
    if not 0.0 < float(config["target_specific_coverage"]) <= 1.0:
        raise ValueError("target_specific_coverage must be in (0, 1].")
    if int(config["bootstrap_replicates"]) < 1:
        raise ValueError("bootstrap_replicates must be positive.")
    if not config["outer_folds"] or len(set(config["outer_folds"])) != len(
        config["outer_folds"]
    ):
        raise ValueError("outer_folds must be a non-empty list of unique fold IDs.")
    return config


def _window_data(records, config, fold_id: int):
    manifest, features = build_window_dataset(
        records,
        window_size=int(config["window_size_samples"]),
        stride=int(config["stride_samples"]),
    )
    manifest["outer_fold"] = fold_id
    features["outer_fold"] = fold_id
    features["topology"] = features["topology"].astype(str)
    return manifest, features


def _top_fraction(scores: Sequence[float], identifiers: Sequence[str], coverage: float):
    if not 0.0 < coverage <= 1.0:
        raise ValueError("Matched coverage must be in (0, 1].")
    values = np.asarray(scores, dtype=float)
    names = np.asarray(identifiers, dtype=str)
    if len(values) != len(names) or not len(values):
        raise ValueError("Matched-coverage evaluation requires non-empty aligned rows.")
    count = max(1, int(np.ceil(coverage * len(values))))
    order = np.lexsort((names, -values))
    selected = np.zeros(len(values), dtype=bool)
    selected[order[:count]] = True
    return selected


def _selective_metrics(
    labels: Sequence[str],
    predictions: Sequence[str],
    scores: Sequence[float],
    identifiers: Sequence[str],
    coverage: float,
) -> Dict[str, float]:
    accepted = _top_fraction(scores, identifiers, coverage)
    y = np.asarray(labels, dtype=str)
    pred = np.asarray(predictions, dtype=str)
    if not accepted.any():
        raise ValueError("Matched-coverage selection accepted no observations.")
    errors = pred != y
    return {
        "observations": int(len(y)),
        "accepted": int(accepted.sum()),
        "coverage": float(accepted.mean()),
        "selective_risk": float(errors[accepted].mean()),
        "accepted_errors": int(errors[accepted].sum()),
    }


def _oof_calibration_choice(oof: pd.DataFrame):
    labels = oof["label_mapped"].astype(str).to_numpy()
    raw = oof[[f"p_raw_{name}" for name in TARGET_CLASSES]].to_numpy(dtype=float)
    reports = []
    fitted = {}
    for method in CALIBRATION_METHODS:
        calibrator = fit_calibrator(method, raw, labels)
        calibrated = calibrator.transform(raw)
        metrics = probability_metrics(calibrated, labels)
        fitted[method] = calibrator
        reports.append(
            {
                "calibration_method": method,
                "development_log_loss": metrics["log_loss"],
                "development_brier": metrics["multiclass_brier"],
                "development_ece": metrics["ece"],
                "evaluation_data": "inner_grouped_oof_fit_and_selection",
                "selection_data": "inner_grouped_oof_only",
            }
        )
    selected = min(
        reports,
        key=lambda row: (
            row["development_log_loss"],
            CALIBRATION_METHODS.index(row["calibration_method"]),
        ),
    )["calibration_method"]
    return fitted[selected], selected, reports


def _family_sample_summary(predictions: pd.DataFrame, target_coverage: float):
    rows = []
    for (fold_id, family_id), family in predictions.groupby(
        ["outer_fold", "Scenario_Family_ID"], sort=True
    ):
        for method, score_column in SCORE_COLUMNS.items():
            metrics = _selective_metrics(
                family["y_true"],
                family["y_pred"],
                family[score_column],
                family["window_id"],
                target_coverage,
            )
            rows.append(
                {
                    "outer_fold": int(fold_id),
                    "Scenario_Family_ID": family_id,
                    "method": method,
                    "target_coverage": target_coverage,
                    **metrics,
                }
            )
    return rows


def _risk_results(predictions: pd.DataFrame, target_coverage: float):
    selective_rows = []
    curve_rows = []
    for fold_id, fold in predictions.groupby("outer_fold", sort=True):
        for method, score_column in SCORE_COLUMNS.items():
            matched = _selective_metrics(
                fold["y_true"],
                fold["y_pred"],
                fold[score_column],
                fold["window_id"],
                target_coverage,
            )
            selected = fold[f"threshold_{method}"].iloc[0]
            deployed = np.asarray(fold[score_column] >= selected)
            if not deployed.any():
                raise ValueError(
                    f"Development threshold for {method} accepted no outer-test "
                    f"windows in fold {fold_id}."
                )
            deployed_risk = float(
                (fold.loc[deployed, "y_true"] != fold.loc[deployed, "y_pred"]).mean()
            )
            selective_rows.append(
                {
                    "outer_fold": int(fold_id),
                    "method": method,
                    "target_coverage": target_coverage,
                    "matched_coverage": matched["coverage"],
                    "matched_selective_risk": matched["selective_risk"],
                    "matched_accepted": matched["accepted"],
                    "development_threshold": float(selected),
                    "development_threshold_test_coverage": float(deployed.mean()),
                    "development_threshold_test_selective_risk": deployed_risk,
                    "family_overlap_count": int(fold["family_overlap_count"].iloc[0]),
                    "evaluation_estimand": "cross_topology_transfer",
                }
            )
            for point in (0.25, 0.50, 0.75, target_coverage, 0.90, 1.0):
                metrics = _selective_metrics(
                    fold["y_true"],
                    fold["y_pred"],
                    fold[score_column],
                    fold["window_id"],
                    float(point),
                )
                curve_rows.append(
                    {
                        "outer_fold": int(fold_id),
                        "method": method,
                        "target_coverage": float(point),
                        "coverage": metrics["coverage"],
                        "selective_risk": metrics["selective_risk"],
                        "accepted": metrics["accepted"],
                    }
                )
    return selective_rows, curve_rows


def _family_risks(predictions: pd.DataFrame, coverage: float):
    rows = []
    for family_id, family in predictions.groupby("Scenario_Family_ID", sort=True):
        family_rows = {}
        for method, score_column in SCORE_COLUMNS.items():
            metrics = _selective_metrics(
                family["y_true"],
                family["y_pred"],
                family[score_column],
                family["window_id"],
                coverage,
            )
            family_rows[method] = metrics["selective_risk"]
            rows.append(
                {
                    "Scenario_Family_ID": family_id,
                    "method": method,
                    "target_coverage": coverage,
                    **metrics,
                }
            )
        rows.append(
            {
                "Scenario_Family_ID": family_id,
                "method": "C_minus_C_minus_D",
                "target_coverage": coverage,
                "risk_difference": family_rows["C"]
                - family_rows["C_minus_D"],
            }
        )
        rows.append(
            {
                "Scenario_Family_ID": family_id,
                "method": "C_minus_B",
                "target_coverage": coverage,
                "risk_difference": family_rows["C"] - family_rows["B"],
            }
        )
    return rows


def _cluster_statistics(family_rows, replicates: int, random_state: int):
    frame = pd.DataFrame(family_rows)
    differences = {}
    for comparison in ("C_minus_C_minus_D", "C_minus_B"):
        values = frame.loc[
            frame["method"] == comparison, "risk_difference"
        ].to_numpy(dtype=float)
        if not len(values):
            raise ValueError(f"No family-level results for {comparison}.")
        observed = float(values.mean())
        rng = np.random.default_rng(random_state)
        sampled_means = np.empty(replicates, dtype=float)
        for index in range(replicates):
            sampled_means[index] = rng.choice(values, size=len(values), replace=True).mean()
        lower, upper = np.quantile(sampled_means, [0.025, 0.975])
        sign_count = 1 << len(values)
        if len(values) <= 16:
            signs = np.asarray(
                [
                    [1.0 if mask & (1 << bit) else -1.0 for bit in range(len(values))]
                    for mask in range(sign_count)
                ],
                dtype=float,
            )
            permuted = np.abs((signs * values).mean(axis=1))
            p_value = float(np.count_nonzero(permuted >= abs(observed)) / len(permuted))
            permutation_method = "exact_family_sign_flip"
        else:
            signs = rng.choice((-1.0, 1.0), size=(10000, len(values)))
            permuted = np.abs((signs * values).mean(axis=1))
            p_value = float((np.count_nonzero(permuted >= abs(observed)) + 1) / 10001)
            permutation_method = "monte_carlo_family_sign_flip"
        differences[comparison] = {
            "comparison": comparison,
            "independent_units": len(values),
            "mean_family_risk_difference": observed,
            "bootstrap_ci_95_low": float(lower),
            "bootstrap_ci_95_high": float(upper),
            "two_sided_sign_flip_p": p_value,
            "permutation_method": permutation_method,
            "bootstrap_replicates": replicates,
            "interpretation": "negative favors method C",
        }
    return list(differences.values())


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=WORKSPACE_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    commit = result.stdout.strip()
    if len(commit) < 7:
        raise RuntimeError("Git did not return a valid commit hash.")
    return commit


def _write_provenance(config_path: Path, source_files: Sequence[Path], input_files: Sequence[Path], output_dir: Path):
    rows = [
        {
            "artifact_type": "config",
            "path": str(config_path.relative_to(WORKSPACE_ROOT)),
            "sha256": _hash_file(config_path),
        },
        {
            "artifact_type": "manifest",
            "path": str((WORKSPACE_ROOT / "01_dataset_audit" / "provisional" / "PROVISIONAL_DATA_FREEZE_MANIFEST.csv").relative_to(WORKSPACE_ROOT)),
            "sha256": _hash_file(WORKSPACE_ROOT / "01_dataset_audit" / "provisional" / "PROVISIONAL_DATA_FREEZE_MANIFEST.csv"),
        },
        {
            "artifact_type": "outer_folds",
            "path": str((WORKSPACE_ROOT / "01_dataset_audit" / "folds.csv").relative_to(WORKSPACE_ROOT)),
            "sha256": _hash_file(WORKSPACE_ROOT / "01_dataset_audit" / "folds.csv"),
        },
    ]
    for path in sorted(set(input_files)):
        rows.append(
            {
                "artifact_type": "input_parquet",
                "path": str(path.relative_to(WORKSPACE_ROOT)),
                "sha256": _hash_file(path),
            }
        )
    for path in sorted(set(source_files)):
        rows.append(
            {
                "artifact_type": "source",
                "path": str(path.relative_to(WORKSPACE_ROOT)),
                "sha256": _hash_file(path),
            }
        )
    for package in RUNTIME_PACKAGES:
        try:
            package_version = version(package)
        except PackageNotFoundError as error:
            raise RuntimeError(
                f"Required runtime package {package!r} has no installed version."
            ) from error
        rows.append(
            {
                "artifact_type": "runtime_dependency",
                "path": package,
                "sha256": "",
                "version": package_version,
            }
        )
    commit = _git_commit()
    provenance = pd.DataFrame(rows)
    if "version" not in provenance.columns:
        provenance["version"] = ""
    provenance["git_commit"] = commit
    provenance["python_version"] = sys.version.split()[0]
    provenance["generated_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    provenance.to_csv(output_dir / "RESULTS_PROVENANCE.csv", index=False)
    return provenance, commit


def _save_figures(predictions, curve_rows, output_dir: Path):
    figure_dir = output_dir / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)

    raw_cm = confusion_matrix(
        predictions["y_true"],
        predictions["y_pred_raw"],
        labels=list(TARGET_CLASSES),
    )
    fig, axis = plt.subplots(figsize=(7, 6))
    normalized = raw_cm / np.maximum(raw_cm.sum(axis=1, keepdims=True), 1)
    image = axis.imshow(normalized, cmap="Blues", vmin=0.0, vmax=1.0)
    axis.set_xticks(range(len(TARGET_CLASSES)), TARGET_CLASSES, rotation=30, ha="right")
    axis.set_yticks(range(len(TARGET_CLASSES)), TARGET_CLASSES)
    axis.set_xlabel("Predicted class")
    axis.set_ylabel("True class")
    axis.set_title("Outer-test confusion matrix (raw baseline)")
    for row in range(len(TARGET_CLASSES)):
        for column in range(len(TARGET_CLASSES)):
            axis.text(
                column,
                row,
                f"{normalized[row, column]:.1%}\n(n={raw_cm[row, column]})",
                ha="center",
                va="center",
                color="white" if normalized[row, column] > 0.5 else "black",
            )
    fig.colorbar(image, ax=axis, label="Row-normalized proportion")
    fig.tight_layout()
    fig.savefig(figure_dir / "fig3_confusion_matrix_stage2.png", dpi=300)
    plt.close(fig)

    curve = (
        pd.DataFrame(curve_rows)
        .groupby(["method", "target_coverage"], as_index=False)
        .agg(selective_risk=("selective_risk", "mean"))
    )
    fig, axis = plt.subplots(figsize=(7, 5))
    colors = {
        "C": "#1E3A8A",
        "C_minus_D": "#D97706",
        "B": "#6B7280",
        "B2": "#0284C7",
        "B3": "#7C3AED",
        "D_only": "#EC4899",
    }
    for method, group in curve.groupby("method", sort=False):
        axis.plot(
            group["target_coverage"],
            group["selective_risk"],
            "o-",
            color=colors[method],
            label=method,
        )
    axis.set_xlabel("Matched test coverage")
    axis.set_ylabel("Selective risk")
    axis.set_title("Outer-test selective risk at matched coverage")
    axis.set_ylim(0, 1)
    axis.legend()
    fig.tight_layout()
    fig.savefig(figure_dir / "fig4_risk_coverage_stage2.png", dpi=300)
    plt.close(fig)

    selected_probabilities = predictions[
        [f"p_calibrated_{name}" for name in TARGET_CLASSES]
    ].to_numpy(dtype=float)
    selected_metrics = probability_metrics(
        selected_probabilities, predictions["y_true"].astype(str).to_numpy()
    )
    confidences = selected_metrics["bin_confidences"]
    accuracies = selected_metrics["bin_accuracies"]
    counts = selected_metrics["bin_counts"]
    fig, (axis, count_axis) = plt.subplots(
        2, 1, figsize=(6, 7), gridspec_kw={"height_ratios": [3, 1]}, sharex=True
    )
    axis.plot([0, 1], [0, 1], "--", color="#6B7280", label="Ideal")
    nonempty_bins = np.asarray(counts) > 0
    axis.plot(
        np.asarray(confidences)[nonempty_bins],
        np.asarray(accuracies)[nonempty_bins],
        "o-",
        color="#1E3A8A",
        label="Outer-test",
    )
    axis.set_ylabel("Accuracy")
    methods = sorted(predictions["selected_calibration_method"].unique())
    axis.set_title(
        "Outer-test reliability diagram; selected method(s): " + ", ".join(methods)
    )
    axis.set_ylim(0, 1)
    axis.legend()
    count_axis.bar(np.linspace(0.05, 0.95, 10), counts, width=0.08, color="#6B7280")
    count_axis.set_xlabel("Mean confidence by bin")
    count_axis.set_ylabel("Count")
    fig.tight_layout()
    fig.savefig(figure_dir / "fig5_calibration_reliability_stage2.png", dpi=300)
    plt.close(fig)

    correct = predictions["y_pred_raw"] == predictions["y_true"]
    fig, axis = plt.subplots(figsize=(7, 5))
    axis.hist(
        predictions.loc[correct, "D"],
        bins=np.linspace(0, 1, 21),
        density=True,
        alpha=0.65,
        label="Correct raw predictions",
    )
    axis.hist(
        predictions.loc[~correct, "D"],
        bins=np.linspace(0, 1, 21),
        density=True,
        alpha=0.65,
        label="Incorrect raw predictions",
    )
    axis.set_xlabel("Family-excluded empirical support margin D(x)")
    axis.set_ylabel("Density")
    axis.set_title("Outer-test D(x) by raw prediction correctness")
    axis.legend()
    fig.tight_layout()
    fig.savefig(figure_dir / "fig6_distinguishability_stage2.png", dpi=300)
    plt.close(fig)


def run_experiments(
    config_path: Path = DEFAULT_CONFIG,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> Dict[str, Path]:
    """Run all frozen outer folds and write traceable research artifacts."""
    config = _read_config(config_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    fold_diagnostics = []
    calibration_rows = []
    baseline_rows = []
    selective_rows = []
    curve_rows = []
    family_rows = []
    policy_rows = []
    outer_predictions = []
    manifests = []
    feature_tables = []
    input_files: List[Path] = []
    source_files = [
        Path(__file__),
        Path(__file__).with_name("evaluation.py"),
        Path(__file__).with_name("simnet_windows.py"),
        WORKSPACE_ROOT / "scripts" / "run_experiments.py",
    ]
    for fold_id in config["outer_folds"]:
        train_records, test_records, diagnostics = load_outer_fold(
            int(fold_id)
        )
        fold_diagnostics.append(diagnostics)
        for metadata, _ in train_records + test_records:
            input_files.append(
                WORKSPACE_ROOT / "data" / "raw" / str(metadata["file"])
            )
        train_manifest, train_features = _window_data(
            train_records, config, int(fold_id)
        )
        test_manifest, test_features = _window_data(
            test_records, config, int(fold_id)
        )
        train_manifest["split_role"] = "train"
        test_manifest["split_role"] = "test"
        train_features["split_role"] = "train"
        test_features["split_role"] = "test"
        manifests.extend((train_manifest, test_manifest))
        feature_tables.extend((train_features, test_features))

        missing_train = set(TARGET_CLASSES) - set(
            train_features["label_mapped"].astype(str).unique()
        )
        missing_test = set(TARGET_CLASSES) - set(
            test_features["label_mapped"].astype(str).unique()
        )
        if missing_train or missing_test:
            raise ValueError(
                f"Fold {fold_id} eligible windows lack classes: "
                f"train={sorted(missing_train)}, test={sorted(missing_test)}."
            )

        oof = inner_oof_predictions(
            train_features,
            random_state=int(config["random_state"]),
            k=int(config["d_neighbors"]),
        )
        calibrator, selected_method, fold_calibration = _oof_calibration_choice(oof)
        for row in fold_calibration:
            row["outer_fold"] = int(fold_id)
            row["selected_for_fold"] = row["calibration_method"] == selected_method
            calibration_rows.append(row)

        model = fit_baseline(
            train_features,
            random_state=int(config["random_state"]) + int(fold_id),
        )
        raw_probabilities = aligned_probabilities(model, test_features)
        calibrated_probabilities = calibrator.transform(raw_probabilities)
        support = compute_empirical_support(
            test_features,
            train_features,
            k=int(config["d_neighbors"]),
        )
        indicators = add_distinguishability_score(
            probability_indicators(calibrated_probabilities),
            support,
        )
        oof_raw = oof[[f"p_raw_{name}" for name in TARGET_CLASSES]].to_numpy(
            dtype=float
        )
        oof_calibrated = calibrator.transform(oof_raw)
        oof_indicators = add_distinguishability_score(
            probability_indicators(oof_calibrated), oof
        )
        target_coverage = float(config["target_specific_coverage"])
        policy_threshold = threshold_for_coverage(
            oof_indicators["score_C"], target_coverage
        )
        policy = apply_diagnostic_policy(
            calibrated_probabilities,
            support,
            indicators["score_C"],
            specific_threshold=policy_threshold,
            ambiguity_delta=float(config["policy"]["ambiguity_delta"]),
            max_candidates=int(config["policy"]["max_candidates"]),
            minimum_confidence_for_ambiguity=float(
                config["policy"]["minimum_confidence_for_ambiguity"]
            ),
            minimum_support_for_ambiguity=float(
                config["policy"]["minimum_support_for_ambiguity"]
            ),
        )

        raw_predictions = np.asarray(TARGET_CLASSES)[raw_probabilities.argmax(axis=1)]
        calibrated_predictions = np.asarray(TARGET_CLASSES)[
            calibrated_probabilities.argmax(axis=1)
        ]
        y_true = test_features["label_mapped"].astype(str).to_numpy()
        baseline_rows.append(
            {
                "outer_fold": int(fold_id),
                "scenarios_train": diagnostics["train_scenarios"],
                "scenarios_test": diagnostics["test_scenarios"],
                "windows_train": len(train_features),
                "windows_test": len(test_features),
                "raw_accuracy": float(accuracy_score(y_true, raw_predictions)),
                "raw_macro_f1": float(
                    f1_score(y_true, raw_predictions, labels=list(TARGET_CLASSES), average="macro", zero_division=0)
                ),
                "raw_balanced_accuracy": float(
                    balanced_accuracy_score(y_true, raw_predictions)
                ),
                "calibrated_accuracy": float(
                    accuracy_score(y_true, calibrated_predictions)
                ),
                "calibration_method_selected_on": "inner_grouped_oof_only",
                "selected_calibration_method": selected_method,
                "train_test_family_overlap_count": diagnostics[
                    "family_overlap_count"
                ],
                "evaluation_estimand": "cross_topology_transfer",
            }
        )

        for method in CALIBRATION_METHODS:
            method_calibrator = fit_calibrator(
                method,
                oof_raw,
                oof["label_mapped"].astype(str).to_numpy(),
            )
            method_probabilities = method_calibrator.transform(raw_probabilities)
            metrics = probability_metrics(method_probabilities, y_true)
            calibration_rows.append(
                {
                    "outer_fold": int(fold_id),
                    "calibration_method": method,
                    "selected_for_fold": method == selected_method,
                    "evaluation_data": "outer_test",
                    "selection_data": "inner_grouped_oof_only",
                    "outer_log_loss": metrics["log_loss"],
                    "outer_brier": metrics["multiclass_brier"],
                    "outer_ece": metrics["ece"],
                    "bin_counts": json.dumps(metrics["bin_counts"]),
                    "bin_confidences": json.dumps(metrics["bin_confidences"]),
                    "bin_accuracies": json.dumps(metrics["bin_accuracies"]),
                }
            )

        fold_output = test_features[
            [
                "window_id",
                "Scenario_ID",
                "Scenario_Family_ID",
                "topology",
                "outer_fold",
            ]
        ].copy()
        fold_output["y_true"] = y_true
        fold_output["y_pred_raw"] = raw_predictions
        fold_output["y_pred"] = calibrated_predictions
        fold_output["selected_calibration_method"] = selected_method
        for index, class_name in enumerate(TARGET_CLASSES):
            fold_output[f"p_raw_{class_name}"] = raw_probabilities[:, index]
            fold_output[f"p_calibrated_{class_name}"] = calibrated_probabilities[
                :, index
            ]
        for column in support.columns:
            fold_output[column] = support[column].to_numpy()
        for column in indicators.columns:
            fold_output[column] = indicators[column].to_numpy()
        fold_output["specific_threshold"] = policy_threshold
        for method in SCORE_COLUMNS:
            fold_output[f"threshold_{method}"] = threshold_for_coverage(
                oof_indicators[SCORE_COLUMNS[method]], target_coverage
            )
        for column in policy.columns:
            fold_output[column] = policy[column].to_numpy()
        fold_output["family_overlap_count"] = diagnostics["family_overlap_count"]
        outer_predictions.append(fold_output)

        for outcome, group in policy.groupby("policy_outcome", sort=True):
            policy_rows.append(
                {
                    "outer_fold": int(fold_id),
                    "policy_outcome": outcome,
                    "windows": len(group),
                    "fraction_of_test_windows": len(group) / len(policy),
                    "evaluation_estimand": "cross_topology_transfer",
                }
            )

    predictions = pd.concat(outer_predictions, ignore_index=True)
    selective_rows, curve_rows = _risk_results(
        predictions, float(config["target_specific_coverage"])
    )
    family_rows = _family_sample_summary(
        predictions, float(config["target_specific_coverage"])
    )
    family_risk_rows = _family_risks(
        predictions, float(config["target_specific_coverage"])
    )
    statistical_rows = _cluster_statistics(
        family_risk_rows,
        replicates=int(config["bootstrap_replicates"]),
        random_state=int(config["random_state"]),
    )

    manifest_table = pd.concat(manifests, ignore_index=True)
    feature_table = pd.concat(feature_tables, ignore_index=True)
    fold_report = pd.DataFrame(fold_diagnostics)
    baseline_table = pd.DataFrame(baseline_rows)
    calibration_table = pd.DataFrame(calibration_rows)
    selective_table = pd.DataFrame(selective_rows)
    curve_table = pd.DataFrame(curve_rows)
    family_table = pd.DataFrame(family_rows)
    policy_table = pd.DataFrame(policy_rows)
    statistics_table = pd.DataFrame(statistical_rows)
    ablation_table = selective_table[
        [
            "outer_fold",
            "method",
            "target_coverage",
            "matched_coverage",
            "matched_selective_risk",
            "development_threshold_test_coverage",
            "development_threshold_test_selective_risk",
        ]
    ].copy()

    artifacts = {
        "FOLD_VALIDATION_REPORT.csv": fold_report,
        "WINDOW_MANIFEST.csv": manifest_table,
        "FEATURE_TABLE.csv": feature_table,
        "BASELINE_RESULTS.csv": baseline_table,
        "CALIBRATION_RESULTS.csv": calibration_table,
        "OUTER_PREDICTIONS.csv": predictions,
        "SELECTIVE_EVALUATION_RESULTS.csv": selective_table,
        "RISK_COVERAGE_CURVES.csv": curve_table,
        "PER_FAMILY_RESULTS.csv": family_table,
        "POLICY_OUTCOMES.csv": policy_table,
        "ABLATION_RESULTS.csv": ablation_table,
        "STATISTICAL_VALIDATION.csv": statistics_table,
    }
    for filename, frame in artifacts.items():
        frame.to_csv(output_dir / filename, index=False)
    _save_figures(predictions, curve_rows, output_dir)
    provenance, commit = _write_provenance(
        config_path,
        source_files,
        input_files,
        output_dir,
    )
    report_path = output_dir / "MAIN_EXPERIMENT_REPORT.md"
    _write_main_report(
        report_path,
        config,
        baseline_table,
        selective_table,
        calibration_table,
        statistics_table,
        policy_table,
        fold_report,
        commit,
        provenance,
    )
    return {name: output_dir / name for name in artifacts} | {
        "MAIN_EXPERIMENT_REPORT.md": report_path,
        "RESULTS_PROVENANCE.csv": output_dir / "RESULTS_PROVENANCE.csv",
    }


def _write_main_report(
    output_path: Path,
    config: Mapping[str, object],
    baseline: pd.DataFrame,
    selective: pd.DataFrame,
    calibration: pd.DataFrame,
    statistics: pd.DataFrame,
    policy: pd.DataFrame,
    folds: pd.DataFrame,
    commit: str,
    provenance: pd.DataFrame,
):
    overall = (
        selective.groupby("method", sort=True)
        .agg(
            folds=("outer_fold", "nunique"),
            mean_matched_coverage=("matched_coverage", "mean"),
            mean_matched_risk=("matched_selective_risk", "mean"),
            mean_deployed_coverage=("development_threshold_test_coverage", "mean"),
            mean_deployed_risk=("development_threshold_test_selective_risk", "mean"),
        )
        .reset_index()
    )
    unknown_training_topology_note = ""
    if any("Unknown" in topologies for topologies in folds["train_topologies"]):
        unknown_training_topology_note = (
            " The supplied folds also retain a scenario whose topology is "
            "recorded as `Unknown` in each training split; it is not assigned "
            "to an outer test topology. Inner validation uses two GroupKFold "
            "partitions over the three training topology values, so it does "
            "not leave each topology group out independently."
        )
    single_family_classes = sorted(
        {
            class_name
            for classes in folds["single_family_classes"]
            for class_name in str(classes).split(";")
            if class_name
        }
    )
    family_feasibility_note = ""
    if single_family_classes:
        family_feasibility_note = (
            " Strict family-disjoint four-class evaluation is not feasible "
            "with the current dataset because only one family is available "
            f"for: {', '.join(single_family_classes)}."
        )
    report = f"""# H2-PRISM Frozen Outer-Fold Experiment Report

**Status:** Empirical results generated from the frozen configuration; interpret only under the limitations below.
**Config:** `{config['config_version']}` (`configs/frozen_evaluation_config.yaml`)
**Git commit:** `{commit}`
**Independent uncertainty unit:** `Scenario_Family_ID` for family-level summaries and resampling.

## Evaluation estimand and family-overlap limitation

The configured outer folds hold out one network topology at a time. This tests
**cross-topology transfer**. The audited fold assignments reuse some
`Scenario_Family_ID` values across train and test because those families have
members at multiple topologies. The results therefore **must not** be described
as unseen-family generalization or as independent held-family validation. The
exact overlap is recorded in `FOLD_VALIDATION_REPORT.csv`. The D(x) reference
set excludes the entire query family, even when that family is represented in
outer training data. The evaluation population is conditional on the audited
normal/event intervals used to define eligible windows; this experiment is not
an end-to-end prospective event-onset detector. The data are simulated
hydrogen-blend results, not evidence of field performance or pure-hydrogen
operation.{unknown_training_topology_note}
{family_feasibility_note}

## Frozen pipeline

- Non-overlapping {config['window_size_samples']}-sample windows at 1 Hz; only
  windows wholly inside annotated event intervals are used for abnormal runs.
- Normal baseline files provide baseline windows. Pre-event, post-event,
  boundary-crossing, and excluded compound windows remain accounted for in
  `WINDOW_MANIFEST.csv` and are excluded from model fitting.
- Inputs are pressure/flow window summaries only; phase, topology, time,
  labels, and identifiers are not model features.
- One canonical Parquet per `Scenario_ID`; model fitting weights windows so
  each family has equal total weight.
- A fixed random forest baseline, inner topology-grouped OOF calibration
  selection, family-excluded nearest-neighbor support (`k={config['d_neighbors']}`),
  and a development-only specific-diagnosis threshold.
- All performance rows report the held-out topology transfer estimand.

## Baseline and matched-coverage comparison

```
{overall.to_string(index=False)}
```

`SELECTIVE_EVALUATION_RESULTS.csv` includes each fold, the test-score-ranked
matched-coverage risk, and the separately reported risk/coverage obtained by
applying the threshold selected from development OOF data. Matched-coverage
ranking uses only model scores to choose accepted test rows; labels are used
only to calculate test risk.

## Calibration and three-outcome policy

Calibration methods are fitted and selected using inner grouped OOF data only;
outer-test calibration metrics are in `CALIBRATION_RESULTS.csv`. Calibration
selection on the same development OOF predictions used to fit each
classwise calibrator is a development selection procedure, not an independent
calibration validation set.

Outcome counts and fractions are in `POLICY_OUTCOMES.csv`. Ambiguity sets are
truncated to at most {config['policy']['max_candidates']} classes according to
the frozen policy; `candidate_count`, truncation flags, and reason codes are
saved per outer prediction.

## Family-level uncertainty and ablation

```
{statistics.to_string(index=False)}
```

The intervals resample independent family-level risk differences, not windows.
The paired sign-flip p-values use family-level risk differences and should be
treated as limited-sample exploratory inference; the number of independent
families is reported in `STATISTICAL_VALIDATION.csv`. Negative risk differences
favor C. Retain null, negative, and inconclusive findings.

## Reproducibility artifacts

The run generated `{len(provenance)}` SHA-256 provenance entries in
`RESULTS_PROVENANCE.csv`, including the frozen config, manifest, fold table,
input Parquet files, and source modules. `FEATURE_TABLE.csv`,
`OUTER_PREDICTIONS.csv`, per-fold results, per-family results, and generated
Stage 2 figures contain the auditable intermediate and final outputs.

This empirical `D(x)` is a data-dependent class-support statistic. It is not a
claim of physical identifiability, physical localization, field validation,
or hydrogen-purity outside the audited H2-SimNet benchmark.
"""
    output_path.write_text(report, encoding="utf-8")
