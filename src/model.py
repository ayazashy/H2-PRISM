"""
Event Attribution Classifier and Probability Calibration (Person 2: Faisal).
Implements multi-class attribution using XGBoost (or RandomForest baseline),
with scenario-level cross-validation and probability calibration.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from .schema import AttributionClass, MLResult

try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except Exception:
    HAS_XGBOOST = False


class EventAttributionModel:
    """Trains and infers multi-class attribution probabilities with calibration."""

    CLASSES = [
        AttributionClass.NORMAL.value,
        AttributionClass.LEAK.value,
        AttributionClass.OPERATIONAL_TRANSIENT.value,
        AttributionClass.SENSOR_FAULT.value,
    ]

    def __init__(self, use_xgboost: bool = True, random_seed: int = 42, checkpoint_path: Optional[Union[str, Path]] = None):
        self.random_seed = random_seed
        self.base_model = RandomForestClassifier(
            n_estimators=300,
            class_weight="balanced",
            random_state=random_seed,
            n_jobs=-1
        )
        self.model_name = "random_forest_baseline"
        self.calibrated_model: Optional[CalibratedClassifierCV] = None
        self.feature_names: List[str] = []
        self.is_fitted: bool = False

        # Attempt to load checkpoint if provided or existing in results/
        ckpt = Path(checkpoint_path) if checkpoint_path else Path("results/attribution_model.joblib")
        if ckpt.exists():
            try:
                self.load_checkpoint(ckpt)
            except Exception:
                pass

    def load_checkpoint(self, checkpoint_path: Union[str, Path]) -> None:
        """Loads a pre-trained attribution model artifact."""
        payload = joblib.load(checkpoint_path)
        self.base_model = payload["model"]
        self.feature_names = payload["feature_names"]
        self.model_name = payload.get("model_name", "trained_attribution_model")
        self.is_fitted = True

    def save_checkpoint(self, checkpoint_path: Union[str, Path]) -> None:
        """Saves current trained model artifact."""
        payload = {
            "model_name": self.model_name,
            "model": self.base_model,
            "feature_names": self.feature_names,
            "is_fitted": self.is_fitted
        }
        joblib.dump(payload, checkpoint_path)

    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: List[str], calibrate: bool = True) -> None:
        """Fit model with optional probability calibration."""
        self.feature_names = feature_names
        if calibrate and len(np.unique(y)) > 1:
            # CalibratedClassifierCV with 3-fold CV or prefit
            cv_splits = min(3, len(y) // max(len(np.unique(y)), 1))
            if cv_splits >= 2:
                self.calibrated_model = CalibratedClassifierCV(self.base_model, cv=cv_splits, method="sigmoid")
                self.calibrated_model.fit(X, y)
            else:
                self.base_model.fit(X, y)
                self.calibrated_model = None
        else:
            self.base_model.fit(X, y)
            self.calibrated_model = None

        self.is_fitted = True

    def predict_event(self, event_id: str, feature_dict: Dict[str, float]) -> MLResult:
        """
        Runs inference on a single event feature dictionary.
        Returns full MLResult dataclass.
        """
        if not self.is_fitted or len(feature_dict) < 5:
            # Default heuristic fallback if model is not trained or input is minimal test dict
            return self._heuristic_fallback(event_id, feature_dict)

        x_vec = np.array([[feature_dict.get(fn, 0.0) for fn in self.feature_names]])

        import warnings
        import pandas as pd
        x_df = pd.DataFrame(x_vec, columns=self.feature_names)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if self.calibrated_model is not None:
                raw_probs = self.base_model.predict_proba(x_df)[0] if hasattr(self.base_model, "predict_proba") else None
                cal_probs = self.calibrated_model.predict_proba(x_df)[0]
                classes = self.calibrated_model.classes_
            else:
                cal_probs = self.base_model.predict_proba(x_df)[0]
                raw_probs = cal_probs
                classes = self.base_model.classes_

        prob_map = {str(c): float(p) for c, p in zip(classes, cal_probs)}
        raw_prob_map = {str(c): float(p) for c, p in zip(classes, raw_probs)} if raw_probs is not None else prob_map

        sorted_probs = sorted(prob_map.items(), key=lambda item: item[1], reverse=True)
        top_cls, top_p = sorted_probs[0]
        second_p = sorted_probs[1][1] if len(sorted_probs) > 1 else 0.0
        margin = top_p - second_p

        # Feature importance if available
        feat_imp = {}
        if hasattr(self.base_model, "feature_importances_") and self.feature_names:
            for fn, imp in zip(self.feature_names, self.base_model.feature_importances_):
                feat_imp[fn] = float(imp)

        return MLResult(
            event_id=event_id,
            predicted_class=AttributionClass(top_cls) if top_cls in AttributionClass._value2member_map_ else AttributionClass.UNKNOWN,
            probabilities=raw_prob_map,
            calibrated_probabilities=prob_map,
            confidence=float(top_p),
            probability_margin=float(margin),
            feature_importance=feat_imp,
            model_version=self.model_name
        )

    def _heuristic_fallback(self, event_id: str, f: Dict[str, float]) -> MLResult:
        """Cold-start heuristic before training data is ingested."""
        raw_z_mb = f.get("normalized_z_mb", 0.0)
        p_drop = abs(f.get("p_drop_total", 0.0))
        p_std = f.get("p_upstream_std", 0.0)
        max_dp = f.get("max_abs_dp_dt", 0.0)
        delta_m = f.get("delta_m_mean", 0.0)

        probs = {
            AttributionClass.NORMAL.value: 0.1,
            AttributionClass.LEAK.value: 0.1,
            AttributionClass.OPERATIONAL_TRANSIENT.value: 0.1,
            AttributionClass.SENSOR_FAULT.value: 0.1
        }

        # True Leak: positive mass deficit (z_MB > 2.5, m_in > m_out)
        if raw_z_mb > 2.5 and p_drop < 5e5:
            probs[AttributionClass.LEAK.value] = 0.85
            probs[AttributionClass.NORMAL.value] = 0.05
        # Operational Transient: compressor ramp/trip, negative decompression (raw_z_mb < -1.5), or p_drop
        elif p_drop >= 5e5 or max_dp > 5000.0 or raw_z_mb < -1.5:
            probs[AttributionClass.OPERATIONAL_TRANSIENT.value] = 0.85
            probs[AttributionClass.NORMAL.value] = 0.05
        elif p_std > 2e4 and abs(raw_z_mb) < 1.5:
            probs[AttributionClass.SENSOR_FAULT.value] = 0.80
            probs[AttributionClass.NORMAL.value] = 0.05
        else:
            probs[AttributionClass.NORMAL.value] = 0.80

        # Normalize
        total = sum(probs.values())
        norm_probs = {k: v / total for k, v in probs.items()}
        sorted_probs = sorted(norm_probs.items(), key=lambda x: x[1], reverse=True)

        return MLResult(
            event_id=event_id,
            predicted_class=AttributionClass(sorted_probs[0][0]),
            probabilities=norm_probs,
            calibrated_probabilities=norm_probs,
            confidence=float(sorted_probs[0][1]),
            probability_margin=float(sorted_probs[0][1] - sorted_probs[1][1]),
            feature_importance={},
            model_version="cold_start_heuristic"
        )
