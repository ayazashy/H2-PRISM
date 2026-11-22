"""Fold validation, baseline modeling, support statistics, and policy primitives."""

from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from sklearn.ensemble import RandomForestClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler

from h2prism.simnet_windows import TARGET_CLASSES, map_target_class


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = (
    WORKSPACE_ROOT
    / "01_dataset_audit"
    / "provisional"
    / "PROVISIONAL_DATA_FREEZE_MANIFEST.csv"
)
FOLDS_PATH = WORKSPACE_ROOT / "01_dataset_audit" / "folds.csv"
SENSOR_FEATURE_PREFIXES = ("PS", "MFS")


def _preferred_path(paths: Sequence[str]) -> str:
    parquet_paths = [path for path in paths if str(path).lower().endswith(".parquet")]
    if not parquet_paths:
        raise ValueError(f"No parquet source found for scenario paths: {paths}")
    cleaned = [path for path in parquet_paths if "H2-SimNet-clean" in str(path)]
    return sorted(cleaned or parquet_paths)[0]


def load_outer_fold(
    fold_id: int,
    folds_path: Path = FOLDS_PATH,
    manifest_path: Path = MANIFEST_PATH,
) -> Tuple[List[Tuple[pd.Series, pd.DataFrame]], List[Tuple[pd.Series, pd.DataFrame]], Dict[str, object]]:
    """Load one canonical Parquet per scenario and validate the frozen outer fold.

    The selected folds hold out a topology. Because a base family appears under
    multiple topologies, family overlap is returned as an explicit diagnostic;
    it is not misrepresented as unseen-family generalization.
    """
    folds = pd.read_csv(folds_path)
    if "outer_fold_id" not in folds or "split_role" not in folds:
        raise ValueError(f"Invalid outer-fold schema in {folds_path}.")
    current = folds[folds["outer_fold_id"] == fold_id].copy()
    if current.empty:
        available = sorted(int(value) for value in folds["outer_fold_id"].unique())
        raise ValueError(f"Fold {fold_id} is absent; available folds: {available}.")
    required = {
        "Scenario_ID",
        "Scenario_Family_ID",
        "file",
        "topology",
        "target_class",
    }
    missing_columns = required - set(current.columns)
    if missing_columns:
        raise ValueError(f"Fold table is missing required columns: {sorted(missing_columns)}")
    if current[list(required)].isna().any().any():
        raise ValueError("Fold table contains missing scenario identity or split metadata.")

    manifest = pd.read_csv(manifest_path)
    required_manifest = {
        "Scenario_ID",
        "file",
        "event_label_raw",
        "eligible_primary",
        "exclusion_reason",
        "event_onset_s",
        "event_offset_s",
        "phase",
        "topology",
    }
    missing_manifest = required_manifest - set(manifest.columns)
    if missing_manifest:
        raise ValueError(
            f"Provisional manifest is missing required columns: {sorted(missing_manifest)}"
        )
    manifest = manifest[manifest["file"].astype(str).str.lower().str.endswith(".parquet")]

    scenario_records: List[Tuple[pd.Series, pd.DataFrame]] = []
    seen_roles: Dict[str, str] = {}
    scenario_topologies: Dict[str, str] = {}
    for scenario_id, duplicate_rows in current.groupby("Scenario_ID", sort=True):
        for column in ("Scenario_Family_ID", "target_class", "topology", "split_role"):
            if duplicate_rows[column].astype(str).nunique() != 1:
                raise ValueError(
                    f"Scenario {scenario_id} has conflicting {column} values in fold {fold_id}."
                )
        role = str(duplicate_rows.iloc[0]["split_role"])
        if role not in {"train", "test"}:
            raise ValueError(f"Unsupported split_role {role!r} in fold {fold_id}.")
        seen_roles[str(scenario_id)] = role
        scenario_topologies[str(scenario_id)] = str(duplicate_rows.iloc[0]["topology"])
        paths = duplicate_rows["file"].astype(str).tolist()
        selected_path = _preferred_path(paths)
        matches = manifest[
            (manifest["Scenario_ID"].astype(str) == str(scenario_id))
            & (manifest["file"].astype(str) == selected_path)
        ]
        if matches.empty:
            matches = manifest[manifest["Scenario_ID"].astype(str) == str(scenario_id)]
        if matches.empty:
            raise FileNotFoundError(
                f"No provisional manifest row for scenario {scenario_id}."
            )
        for column in (
            "event_label_raw",
            "eligible_primary",
            "exclusion_reason",
            "event_onset_s",
            "event_offset_s",
            "topology",
        ):
            normalized = matches[column].map(
                lambda value: "<NA>" if pd.isna(value) else str(value).strip()
            )
            if normalized.nunique(dropna=False) != 1:
                raise ValueError(
                    f"Scenario {scenario_id} has conflicting provisional "
                    f"manifest values for {column!r}."
                )
        metadata = matches.sort_values("file").iloc[0].copy()
        fold_class = str(duplicate_rows.iloc[0]["target_class"])
        fold_family = str(duplicate_rows.iloc[0]["Scenario_Family_ID"])
        fold_topology = str(duplicate_rows.iloc[0]["topology"])
        if fold_class not in TARGET_CLASSES:
            raise ValueError(
                f"Scenario {scenario_id} has unsupported target class {fold_class!r}."
            )
        mapped_label = map_target_class(str(metadata["event_label_raw"]))
        if mapped_label != fold_class:
            raise ValueError(
                f"Scenario {scenario_id} fold class {fold_class!r} disagrees with "
                f"frozen manifest label {metadata['event_label_raw']!r} "
                f"(maps to {mapped_label!r})."
            )
        if str(metadata["topology"]) != fold_topology:
            raise ValueError(
                f"Scenario {scenario_id} fold topology {fold_topology!r} "
                f"disagrees with provisional manifest topology {metadata['topology']!r}."
            )
        manifest_family = metadata.get("Scenario_Family_ID")
        if pd.notna(manifest_family) and str(manifest_family) != fold_family:
            raise ValueError(
                f"Scenario {scenario_id} fold family {fold_family!r} disagrees "
                f"with provisional manifest family {manifest_family!r}."
            )
        if str(metadata["eligible_primary"]).strip().lower() not in {"true", "1"}:
            raise ValueError(
                f"Fold scenario {scenario_id} is not marked primary-eligible "
                "in the provisional manifest."
            )
        metadata["target_class"] = fold_class
        metadata["Scenario_Family_ID"] = fold_family
        metadata["file"] = selected_path
        raw_path = WORKSPACE_ROOT / "data" / "raw" / selected_path
        if not raw_path.is_file():
            raise FileNotFoundError(
                f"Fold scenario file does not exist: {raw_path}. "
                "Install the full benchmark before running experiments."
            )
        if raw_path.suffix.lower() != ".parquet":
            raise ValueError(f"Primary evaluation must use Parquet: {raw_path}")
        data = pd.read_parquet(raw_path)
        scenario_records.append((metadata, data))

    train_ids = {
        scenario_id for scenario_id, role in seen_roles.items() if role == "train"
    }
    test_ids = {
        scenario_id for scenario_id, role in seen_roles.items() if role == "test"
    }
    if not train_ids or not test_ids:
        raise ValueError(f"Fold {fold_id} has an empty train or test split.")
    if train_ids & test_ids:
        raise ValueError(f"Fold {fold_id} has scenario leakage.")

    train_topologies = {
        scenario_topologies[scenario_id] for scenario_id in train_ids
    }
    test_topologies = {
        scenario_topologies[scenario_id] for scenario_id in test_ids
    }
    if train_topologies & test_topologies:
        raise ValueError(f"Fold {fold_id} has topology leakage.")
    train_families = {
        str(metadata["Scenario_Family_ID"])
        for metadata, _ in scenario_records
        if seen_roles[str(metadata["Scenario_ID"])] == "train"
    }
    test_families = {
        str(metadata["Scenario_Family_ID"])
        for metadata, _ in scenario_records
        if seen_roles[str(metadata["Scenario_ID"])] == "test"
    }
    family_overlap = sorted(train_families & test_families)

    split_classes: Dict[str, List[str]] = {}
    for role, scenario_ids in (("train", train_ids), ("test", test_ids)):
        split_classes[role] = sorted(
            {
                str(metadata["target_class"])
                for metadata, _ in scenario_records
                if str(metadata["Scenario_ID"]) in scenario_ids
            }
        )
        missing_classes = set(TARGET_CLASSES) - set(split_classes[role])
        if missing_classes:
            raise ValueError(
                f"Fold {fold_id} {role} is missing target classes: "
                f"{sorted(missing_classes)}."
            )

    family_counts_by_class = {
        class_name: len(
            {
                str(metadata["Scenario_Family_ID"])
                for metadata, _ in scenario_records
                if str(metadata["target_class"]) == class_name
            }
        )
        for class_name in TARGET_CLASSES
    }
    single_family_classes = [
        class_name
        for class_name, family_count in family_counts_by_class.items()
        if family_count < 2
    ]
    train_records = [
        item
        for item in scenario_records
        if seen_roles[str(item[0]["Scenario_ID"])] == "train"
    ]
    test_records = [
        item
        for item in scenario_records
        if seen_roles[str(item[0]["Scenario_ID"])] == "test"
    ]
    diagnostics = {
        "outer_fold": fold_id,
        "train_scenarios": len(train_records),
        "test_scenarios": len(test_records),
        "train_topologies": sorted(train_topologies),
        "test_topologies": sorted(test_topologies),
        "train_families": len(train_families),
        "test_families": len(test_families),
        "family_overlap_count": len(family_overlap),
        "family_overlap": ";".join(family_overlap),
        "family_independent": not family_overlap,
        "family_counts_by_class": ";".join(
            f"{class_name}={family_counts_by_class[class_name]}"
            for class_name in TARGET_CLASSES
        ),
        "single_family_classes": ";".join(single_family_classes),
        "train_classes": ";".join(split_classes["train"]),
        "test_classes": ";".join(split_classes["test"]),
    }
    return train_records, test_records, diagnostics


def model_feature_columns(features: pd.DataFrame) -> List[str]:
    excluded = {
        "window_id",
        "Scenario_ID",
        "Scenario_Family_ID",
        "label_mapped",
        "outer_fold",
        "topology",
    }
    columns = [
        column
        for column in features.columns
        if column not in excluded
        and column.startswith(SENSOR_FEATURE_PREFIXES)
    ]
    if not columns:
        raise ValueError("No sensor-derived feature columns are available.")
    return columns


def _family_sample_weights(families: Sequence[str]) -> np.ndarray:
    values = np.asarray(families, dtype=str)
    unique, counts = np.unique(values, return_counts=True)
    count_by_family = dict(zip(unique, counts))
    weights = np.asarray([1.0 / count_by_family[value] for value in values])
    return weights / np.mean(weights)


def fit_baseline(
    features: pd.DataFrame,
    random_state: int = 2026,
) -> RandomForestClassifier:
    """Fit the frozen family-balanced random-forest baseline."""
    columns = model_feature_columns(features)
    labels = features["label_mapped"].astype(str)
    missing_classes = set(TARGET_CLASSES) - set(labels.unique())
    if missing_classes:
        raise ValueError(
            f"Training data lacks target classes: {sorted(missing_classes)}."
        )
    model = RandomForestClassifier(
        n_estimators=300,
        max_features="sqrt",
        min_samples_leaf=2,
        class_weight="balanced_subsample",
        random_state=random_state,
        n_jobs=-1,
    )
    model.fit(
        features[columns],
        labels,
        sample_weight=_family_sample_weights(
            features["Scenario_Family_ID"].astype(str).to_numpy()
        ),
    )
    return model


def aligned_probabilities(
    model: RandomForestClassifier,
    features: pd.DataFrame,
) -> np.ndarray:
    columns = model_feature_columns(features)
    raw = model.predict_proba(features[columns])
    aligned = np.zeros((len(features), len(TARGET_CLASSES)), dtype=float)
    class_index = {name: index for index, name in enumerate(TARGET_CLASSES)}
    for source_index, class_name in enumerate(model.classes_):
        aligned[:, class_index[str(class_name)]] = raw[:, source_index]
    if not np.isfinite(aligned).all() or np.any(aligned.sum(axis=1) <= 0):
        raise ValueError("Classifier returned invalid class probabilities.")
    return aligned / aligned.sum(axis=1, keepdims=True)


def compute_empirical_support(
    query_features: pd.DataFrame,
    reference_features: pd.DataFrame,
    k: int = 25,
) -> pd.DataFrame:
    """Compute family-excluded nearest-neighbor class support q and D.

    For each query family, both standardization and neighbor ranking use only
    references with that complete Scenario_Family_ID removed.
    """
    if k < 1:
        raise ValueError("k must be positive.")
    feature_columns = model_feature_columns(reference_features)
    if feature_columns != model_feature_columns(query_features):
        raise ValueError("Query and reference feature schemas differ.")
    ref_families = reference_features["Scenario_Family_ID"].astype(str).to_numpy()
    query_families = query_features["Scenario_Family_ID"].astype(str).to_numpy()
    if "window_id" not in reference_features or "window_id" not in query_features:
        raise ValueError("D(x) inputs must retain unique window_id values.")
    ref_window_ids = reference_features["window_id"].astype(str).to_numpy()
    query_window_ids = query_features["window_id"].astype(str).to_numpy()
    if len(np.unique(ref_window_ids)) != len(ref_window_ids):
        raise ValueError("D(x) reference window_id values must be unique.")
    if len(np.unique(query_window_ids)) != len(query_window_ids):
        raise ValueError("D(x) query window_id values must be unique.")
    if not ref_families.size:
        raise ValueError("The D(x) reference set is empty.")

    ref_values = reference_features[feature_columns].to_numpy(dtype=float)
    query_values = query_features[feature_columns].to_numpy(dtype=float)
    ref_labels = reference_features["label_mapped"].astype(str).to_numpy()
    rows: List[Dict[str, object]] = [{} for _ in range(len(query_values))]

    for query_family in np.unique(query_families):
        query_indices = np.flatnonzero(query_families == query_family)
        ref_indices = np.flatnonzero(ref_families != query_family)
        if not len(ref_indices):
            raise ValueError(
                "No D(x) references remain after excluding query family "
                f"{query_family!r}."
            )
        scaler = StandardScaler()
        ref_matrix = scaler.fit_transform(ref_values[ref_indices])
        query_matrix = scaler.transform(query_values[query_indices])
        neighbor_count = min(k, len(ref_indices))
        distance_block = cdist(
            query_matrix, ref_matrix, metric="euclidean"
        )
        for local_query_index, query_index in enumerate(query_indices):
            order = np.lexsort(
                (ref_window_ids[ref_indices], distance_block[local_query_index])
            )
            neighbor_indices = ref_indices[order[:neighbor_count]]
            neighbor_families = ref_families[neighbor_indices]
            unique_families, family_counts = np.unique(
                neighbor_families, return_counts=True
            )
            count_map = dict(zip(unique_families, family_counts))
            weights = np.asarray(
                [1.0 / count_map[family] for family in neighbor_families],
                dtype=float,
            )
            support = {class_name: 0.0 for class_name in TARGET_CLASSES}
            for label, weight in zip(ref_labels[neighbor_indices], weights):
                if label not in support:
                    raise ValueError(f"Unexpected reference label {label!r}.")
                support[label] += float(weight)
            total = sum(support.values())
            if total <= 0:
                raise ValueError("D(x) neighbors have no recognized class support.")
            q_values = {name: value / total for name, value in support.items()}
            sorted_q = sorted(q_values.values(), reverse=True)
            rows[query_index] = {
                **{f"q_{name}": q_values[name] for name in TARGET_CLASSES},
                "D": float(sorted_q[0] - sorted_q[1]),
                "support_n_neighbors": len(neighbor_indices),
                "support_n_families": len(np.unique(neighbor_families)),
                "support_missing_classes": ";".join(
                    name for name, value in q_values.items() if value == 0.0
                ),
                "query_family_excluded": True,
            }
    return pd.DataFrame(rows, index=query_features.index)


class _ClasswiseCalibrator:
    def __init__(self, method: str, classes: Sequence[str]):
        if method not in {"none", "sigmoid", "isotonic"}:
            raise ValueError(f"Unsupported calibration method: {method}")
        self.method = method
        self.classes = tuple(classes)
        self.models: List[object] = []

    def fit(self, probabilities: np.ndarray, labels: Sequence[str]):
        if probabilities.shape != (len(labels), len(self.classes)):
            raise ValueError("Calibration inputs have incompatible shapes.")
        labels = np.asarray(labels, dtype=str)
        self.models = []
        if self.method == "none":
            return self
        for index, class_name in enumerate(self.classes):
            binary_labels = (labels == class_name).astype(int)
            if np.unique(binary_labels).size != 2:
                raise ValueError(
                    f"Calibration development data lacks positive/negative "
                    f"examples for {class_name}."
                )
            scores = np.clip(probabilities[:, index], 1e-8, 1.0 - 1e-8)
            if self.method == "sigmoid":
                model = LogisticRegression(C=1e6, solver="lbfgs", max_iter=1000)
                model.fit(scores.reshape(-1, 1), binary_labels)
            else:
                model = IsotonicRegression(out_of_bounds="clip")
                model.fit(scores, binary_labels)
            self.models.append(model)
        return self

    def transform(self, probabilities: np.ndarray) -> np.ndarray:
        if self.method == "none":
            return probabilities.copy()
        if len(self.models) != len(self.classes):
            raise ValueError("Calibration model has not been fitted.")
        calibrated = np.zeros_like(probabilities, dtype=float)
        for index, model in enumerate(self.models):
            scores = np.clip(probabilities[:, index], 1e-8, 1.0 - 1e-8)
            if self.method == "sigmoid":
                calibrated[:, index] = model.predict_proba(
                    scores.reshape(-1, 1)
                )[:, 1]
            else:
                calibrated[:, index] = model.predict(scores)
        calibrated = np.clip(calibrated, 1e-8, None)
        totals = calibrated.sum(axis=1, keepdims=True)
        if not np.isfinite(calibrated).all() or np.any(totals <= 0):
            raise ValueError("Calibration produced invalid class probabilities.")
        return calibrated / totals


def fit_calibrator(
    method: str,
    probabilities: np.ndarray,
    labels: Sequence[str],
) -> _ClasswiseCalibrator:
    return _ClasswiseCalibrator(method, TARGET_CLASSES).fit(probabilities, labels)


def probability_metrics(
    probabilities: np.ndarray,
    labels: Sequence[str],
) -> Dict[str, float]:
    y = np.asarray(labels, dtype=str)
    class_to_index = {name: index for index, name in enumerate(TARGET_CLASSES)}
    if not set(y).issubset(class_to_index):
        raise ValueError("Probability metric received an unknown class label.")
    truth = np.zeros_like(probabilities, dtype=float)
    truth[np.arange(len(y)), [class_to_index[value] for value in y]] = 1.0
    clipped = np.clip(probabilities, 1e-12, 1.0)
    brier = float(np.mean(np.sum((truth - probabilities) ** 2, axis=1)))
    log_loss = float(-np.mean(np.log(clipped[np.arange(len(y)), truth.argmax(axis=1)])))
    confidence = probabilities.max(axis=1)
    correct = probabilities.argmax(axis=1) == truth.argmax(axis=1)
    edges = np.linspace(0.0, 1.0, 11)
    ece = 0.0
    bin_counts = []
    bin_confidences = []
    bin_accuracies = []
    for index in range(len(edges) - 1):
        if index == len(edges) - 2:
            mask = (confidence >= edges[index]) & (confidence <= edges[index + 1])
        else:
            mask = (confidence >= edges[index]) & (confidence < edges[index + 1])
        count = int(mask.sum())
        bin_counts.append(count)
        if count:
            mean_conf = float(confidence[mask].mean())
            accuracy = float(correct[mask].mean())
            ece += count / len(y) * abs(mean_conf - accuracy)
        else:
            mean_conf = float((edges[index] + edges[index + 1]) / 2.0)
            accuracy = 0.0
        bin_confidences.append(mean_conf)
        bin_accuracies.append(accuracy)
    return {
        "multiclass_brier": brier,
        "log_loss": log_loss,
        "ece": float(ece),
        "bin_counts": bin_counts,
        "bin_confidences": bin_confidences,
        "bin_accuracies": bin_accuracies,
    }


def inner_oof_predictions(
    features: pd.DataFrame,
    random_state: int,
    k: int,
) -> pd.DataFrame:
    """Generate development-only OOF probabilities and family-excluded D.

    Inner GroupKFold uses at most two folds and never splits a topology group.
    If the outer training split contains the audited Unknown topology value,
    those folds partition three topology groups rather than leaving each group
    out independently. Base-family overlap is retained and reported as a
    limitation, never represented as family-independent validation.
    """
    topologies = features["topology"].astype(str).to_numpy()
    unique_topologies = np.unique(topologies)
    if len(unique_topologies) < 2:
        raise ValueError("Inner grouped validation requires at least two topologies.")
    splitter = GroupKFold(n_splits=min(2, len(unique_topologies)))
    groups = topologies
    result = np.full((len(features), len(TARGET_CLASSES)), np.nan, dtype=float)
    support_frames: List[pd.DataFrame] = []
    for split_number, (train_idx, validation_idx) in enumerate(
        splitter.split(features, features["label_mapped"], groups), start=1
    ):
        train = features.iloc[train_idx]
        validation = features.iloc[validation_idx]
        missing = set(TARGET_CLASSES) - set(train["label_mapped"].astype(str).unique())
        if missing:
            raise ValueError(
                f"Inner split {split_number} lacks training classes {sorted(missing)}."
            )
        model = fit_baseline(train, random_state + split_number)
        result[validation_idx] = aligned_probabilities(model, validation)
        support_frames.append(
            compute_empirical_support(validation, train, k=k)
        )
    if not np.isfinite(result).all():
        raise ValueError("Inner OOF prediction matrix is incomplete.")
    support = pd.concat(support_frames).sort_index()
    if not support.index.equals(features.index):
        support = support.reindex(features.index)
    if support.isna().any().any():
        raise ValueError("Inner OOF D(x) support is incomplete.")
    output = features[
        [
            "window_id",
            "Scenario_ID",
            "Scenario_Family_ID",
            "label_mapped",
            "topology",
        ]
    ].copy()
    for index, class_name in enumerate(TARGET_CLASSES):
        output[f"p_raw_{class_name}"] = result[:, index]
    for column in support.columns:
        output[column] = support[column].to_numpy()
    return output


def probability_indicators(probabilities: np.ndarray) -> pd.DataFrame:
    sorted_probabilities = np.sort(probabilities, axis=1)
    confidence = sorted_probabilities[:, -1]
    margin = sorted_probabilities[:, -1] - sorted_probabilities[:, -2]
    entropy = -np.sum(
        probabilities * np.log(np.clip(probabilities, 1e-12, 1.0)), axis=1
    )
    normalized_entropy = entropy / np.log(len(TARGET_CLASSES))
    return pd.DataFrame(
        {
            "C": confidence,
            "M": margin,
            "H": normalized_entropy,
            "score_B": confidence,
            "score_B2": margin,
            "score_B3": 1.0 - normalized_entropy,
            "score_C_minus_D": (
                confidence + margin + (1.0 - normalized_entropy)
            )
            / 3.0,
            "score_C": (
                confidence + margin + (1.0 - normalized_entropy)
            )
            / 4.0,
        }
    )


def add_distinguishability_score(
    indicators: pd.DataFrame,
    support: pd.DataFrame,
) -> pd.DataFrame:
    result = indicators.copy()
    result["D"] = support["D"].to_numpy()
    result["score_D_only"] = result["D"]
    result["score_C"] = result["score_C"] + result["D"] / 4.0
    return result


def threshold_for_coverage(scores: Sequence[float], coverage: float) -> float:
    if not 0.0 < coverage <= 1.0:
        raise ValueError("Target coverage must be in (0, 1].")
    values = np.asarray(scores, dtype=float)
    if not len(values) or not np.isfinite(values).all():
        raise ValueError("Coverage threshold requires finite, non-empty scores.")
    n_accept = max(1, int(np.ceil(coverage * len(values))))
    return float(np.sort(values, kind="stable")[-n_accept])


def apply_diagnostic_policy(
    probabilities: np.ndarray,
    support: pd.DataFrame,
    combined_scores: Sequence[float],
    specific_threshold: float,
    ambiguity_delta: float = 0.15,
    max_candidates: int = 3,
    minimum_confidence_for_ambiguity: float = 0.40,
    minimum_support_for_ambiguity: float = 0.35,
) -> pd.DataFrame:
    """Apply the frozen three-outcome policy and return reasons/candidate sets."""
    if not 2 <= max_candidates <= len(TARGET_CLASSES):
        raise ValueError("max_candidates must be between 2 and the class count.")
    scores = np.asarray(combined_scores, dtype=float)
    if len(scores) != len(probabilities) or not np.isfinite(scores).all():
        raise ValueError("Policy score vector is invalid.")
    q = support[[f"q_{name}" for name in TARGET_CLASSES]].to_numpy(dtype=float)
    rows: List[Dict[str, object]] = []
    for index, probability in enumerate(probabilities):
        p_order = np.argsort(-probability, kind="stable")
        q_order = np.argsort(-q[index], kind="stable")
        candidates = {
            TARGET_CLASSES[class_index]
            for class_index in range(len(TARGET_CLASSES))
            if probability[class_index] >= probability.max() - ambiguity_delta
        }
        candidates.update(
            TARGET_CLASSES[class_index]
            for class_index in range(len(TARGET_CLASSES))
            if q[index, class_index] > 0.0
            and q[index, class_index] >= q[index].max() - ambiguity_delta
        )
        ranked_candidates = sorted(
            candidates,
            key=lambda class_name: (
                -(
                    probability[TARGET_CLASSES.index(class_name)]
                    + q[index, TARGET_CLASSES.index(class_name)]
                ),
                TARGET_CLASSES.index(class_name),
            ),
        )
        truncated = len(ranked_candidates) > max_candidates
        ranked_candidates = ranked_candidates[:max_candidates]
        if not ranked_candidates:
            ranked_candidates = [TARGET_CLASSES[int(p_order[0])]]
        confidence = float(probability.max())
        support_strength = float(q[index].max())
        if scores[index] >= specific_threshold and len(ranked_candidates) == 1:
            outcome = "SPECIFIC"
            reason = "SPECIFIC_THRESHOLD_AND_SINGLE_CANDIDATE"
            ambiguity_set = ""
        elif len(ranked_candidates) >= 2 and (
            confidence >= minimum_confidence_for_ambiguity
            or support_strength >= minimum_support_for_ambiguity
        ):
            outcome = "AMBIGUITY_SET"
            reason = (
                "CANDIDATE_SET_TRUNCATED"
                if truncated
                else "MULTIPLE_SUPPORTED_CANDIDATES"
            )
            ambiguity_set = ";".join(ranked_candidates)
        else:
            outcome = "UNRESOLVED"
            reason = "INSUFFICIENT_CONFIDENCE_AND_SUPPORT"
            ambiguity_set = ""
        rows.append(
            {
                "policy_outcome": outcome,
                "ambiguity_set": ambiguity_set,
                "reason_code": reason,
                "candidate_count": len(ranked_candidates),
                "candidates_truncated": bool(truncated),
                "specific_threshold": float(specific_threshold),
                "support_strength": support_strength,
                "support_missing_classes": support.iloc[index][
                    "support_missing_classes"
                ],
                "support_n_neighbors": int(
                    support.iloc[index]["support_n_neighbors"]
                ),
                "support_n_families": int(support.iloc[index]["support_n_families"]),
            }
        )
    return pd.DataFrame(rows, index=support.index)
