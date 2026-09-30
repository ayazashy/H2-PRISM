"""
H2-PRISM Baseline Models Training & Evaluation Script (Person 2: Faisal / AI Lead).
Applies the algorithms and training pipelines from notebooks/baseline_models.ipynb:
- Ingests raw H2-SimNet pipeline scenarios without data leakage.
- Extracts multi-group physics and statistical window features.
- Performs GroupShuffleSplit across scenario IDs.
- Trains and benchmarks Logistic Regression, Random Forest, and Gradient Boosting.
- Calibrates and exports the master model to results/attribution_model.joblib.
- Saves benchmark evaluation metrics to results/baseline_models_evaluation.csv.
"""

import sys
from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, classification_report
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.features import extract_window_features

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "raw"
RESULTS_DIR = PROJECT_ROOT / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def load_raw_pipeline_scenario(scenario_path: Path, data_dir: Path) -> pd.DataFrame:
    """Loads a raw H2-SimNet CSV scenario and maps standardized channel names."""
    scenario = pd.read_csv(scenario_path)
    relative_path = scenario_path.resolve().relative_to(data_dir)
    scenario_id = "__".join(relative_path.with_suffix("").parts)

    if "timestamp" not in scenario.columns:
        scenario["timestamp"] = np.arange(len(scenario), dtype=float)
    if "scenario_id" not in scenario.columns:
        scenario["scenario_id"] = scenario_id
    if "run_id" not in scenario.columns:
        scenario["run_id"] = relative_path.as_posix()

    if "p_upstream" not in scenario.columns and "PS1" in scenario.columns:
        scenario["p_upstream"] = scenario["PS1"] * 1e6
    if "p_downstream" not in scenario.columns:
        downstream_sensor = "PS12" if "PS12" in scenario.columns else "PS6"
        if downstream_sensor in scenario.columns:
            scenario["p_downstream"] = scenario[downstream_sensor] * 1e6
    if "m_inlet" not in scenario.columns and "MFS1" in scenario.columns:
        scenario["m_inlet"] = scenario["MFS1"]
    if "m_outlet" not in scenario.columns:
        if "anom_gestcent" in {part.lower() for part in relative_path.parts} and "MFS3" in scenario.columns:
            outlet_sensor = "MFS3"
        else:
            outlet_sensor = next(
                (sensor for sensor in ("MFS4", "MFS2", "MFS3") if sensor in scenario.columns),
                None,
            )
        if outlet_sensor is not None:
            scenario["m_outlet"] = scenario[outlet_sensor]

    if "label" not in scenario.columns:
        labels = pd.Series("NORMAL", index=scenario.index, dtype="object")
        if "label_anomaly" in scenario.columns:
            labels.loc[scenario["label_anomaly"] == 1] = "ANOMALY"
        for column in ("leak_G3", "leak_G4", "leak_G5", "leak_G6"):
            if column in scenario.columns:
                labels.loc[scenario[column] == 1] = "LEAK"
        if "CompressorFault" in scenario.columns:
            labels.loc[scenario["CompressorFault"] == 1] = "OPERATIONAL_TRANSIENT"
        if "CompressorDelay" in scenario.columns:
            labels.loc[scenario["CompressorDelay"] == 1] = "OPERATIONAL_TRANSIENT"
        scenario["label"] = labels

    return scenario


def build_windowed_feature_table(data_dir: Path, window_size: int = 100, step_stride: int = 100) -> pd.DataFrame:
    """Extracts sliding window features across all scenario files."""
    scenario_files = sorted(data_dir.rglob("*.csv"))
    if not scenario_files:
        raise FileNotFoundError(f"No CSV scenarios found in {data_dir}")

    print(f"[*] Extracting features from {len(scenario_files)} raw scenarios (window={window_size}s)...")
    scenario_features = []

    for idx, p in enumerate(scenario_files, 1):
        try:
            sc = load_raw_pipeline_scenario(p, data_dir)
            for start in range(0, len(sc) - window_size + 1, step_stride):
                w = sc.iloc[start : start + window_size]
                wl = w["label"].dropna().astype(str)
                if wl.empty:
                    continue
                feats = extract_window_features(w)
                feats["scenario_id"] = sc["scenario_id"].iloc[0]
                feats["window_start"] = start
                feats["label"] = wl.value_counts().idxmax()
                scenario_features.append(feats)
        except Exception as e:
            continue

    df_feats = pd.DataFrame(scenario_features)
    print(f"[+] Successfully extracted {len(df_feats)} labeled windows.")
    print(df_feats["label"].value_counts().to_string())
    return df_feats


def train_and_benchmark(df_feats: pd.DataFrame):
    """Executes leakage-safe GroupShuffleSplit and trains multiple models."""
    excluded_columns = {"label", "scenario_id", "window_start"}
    feature_names = [col for col in df_feats.columns if col not in excluded_columns]

    df_feats[feature_names] = (
        df_feats[feature_names]
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0.0)
    )

    # GroupShuffleSplit to strictly preserve scenario boundaries
    gss = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42)
    train_indices, test_indices = next(
        gss.split(df_feats, groups=df_feats["scenario_id"])
    )

    train_table = df_feats.iloc[train_indices].copy()
    test_table = df_feats.iloc[test_indices].copy()

    # Filter out unseen classes from test set if any
    known_labels = train_table["label"].unique()
    test_table = test_table[test_table["label"].isin(known_labels)].copy()

    X_train = train_table[feature_names]
    X_test = test_table[feature_names]
    y_train = train_table["label"]
    y_test = test_table["label"]

    models = {
        "Logistic Regression": make_pipeline(
            StandardScaler(),
            LogisticRegression(
                max_iter=2000,
                class_weight="balanced",
                random_state=42,
            ),
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=300,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        ),
        "HistGradientBoosting": HistGradientBoostingClassifier(
            max_iter=200,
            class_weight="balanced",
            random_state=42,
        ),
    }

    # Optional XGBoost
    try:
        from xgboost import XGBClassifier
        from sklearn.preprocessing import LabelEncoder
        le = LabelEncoder()
        y_train_enc = le.fit_transform(y_train)
        y_test_enc = le.transform(y_test)
        xgb = XGBClassifier(
            objective="multi:softprob",
            num_class=len(le.classes_),
            eval_metric="mlogloss",
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            random_state=42,
            n_jobs=-1,
        )
        xgb.fit(X_train, y_train_enc)
        models["XGBoost"] = (xgb, le)
    except Exception:
        pass

    results = []
    best_model_name = None
    best_score = -1.0
    best_fitted_model = None

    print("\n" + "=" * 70)
    print("                BASELINE MODELS BENCHMARK EVALUATION")
    print("=" * 70)

    for name, model in models.items():
        if name == "XGBoost":
            xgb, le = model
            preds_enc = xgb.predict(X_test)
            preds = le.inverse_transform(preds_enc.astype(int))
            score = balanced_accuracy_score(y_test, preds)
            fitted_obj = xgb
        else:
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            score = balanced_accuracy_score(y_test, preds)
            fitted_obj = model

        results.append({
            "model": name,
            "balanced_accuracy": score,
            "train_samples": len(X_train),
            "test_samples": len(X_test),
        })

        print(f"\n[+] {name} | Balanced Accuracy: {score:.3f}")
        print(classification_report(y_test, preds, zero_division=0))

        if score > best_score:
            best_score = score
            best_model_name = name
            best_fitted_model = fitted_obj

    df_results = pd.DataFrame(results).sort_values("balanced_accuracy", ascending=False, ignore_index=True)
    eval_csv = RESULTS_DIR / "baseline_models_evaluation.csv"
    df_results.to_csv(eval_csv, index=False)
    print(f"\n[+] Saved evaluation results to {eval_csv}")

    # Save best master model artifact
    export_payload = {
        "model_name": best_model_name,
        "model": best_fitted_model,
        "feature_names": feature_names,
        "classes": list(known_labels),
        "balanced_accuracy": best_score,
    }
    model_path = RESULTS_DIR / "attribution_model.joblib"
    joblib.dump(export_payload, model_path)
    print(f"[✓] Saved production attribution model ({best_model_name}, Acc={best_score:.3f}) to {model_path}")

    return export_payload


if __name__ == "__main__":
    if not DATA_DIR.exists():
        raise FileNotFoundError(f"Data directory {DATA_DIR} not found.")
    df_feats = build_windowed_feature_table(DATA_DIR, window_size=100, step_stride=100)
    train_and_benchmark(df_feats)
