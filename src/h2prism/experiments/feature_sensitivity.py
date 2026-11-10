"""
H2-PRISM controlled feature-representation sensitivity (Task A15 -- Ahmed).

STATUS: IMPLEMENTED + TESTED (synthetic). SECONDARY / EXPLORATORY by definition:
no arm result may be used to choose the primary feature set (A15 step 14).

Arms are prespecified in configs/feature_sensitivity.yaml and resolved against the
verified feature table by *rules*, never by outer-test performance:
  * ``all``                -> every model feature column
  * ``offset_invariant``   -> statistics invariant to a constant per-channel offset
                              (std, range, last_minus_first, slope, mean_abs_diff);
                              the delta/trend arm motivated by the absolute-pressure
                              fingerprinting risk (Faisal F3, Yazan Y3)
  * explicit ``statistics`` / ``channels`` lists
Every arm runs through the SAME grouped runner (baseline.run_grouped_evaluation) with
the same folds and eligible rows; learning transforms are refit inside training folds.
Infeasible arms are reported with a reason, never silently dropped.
"""

from __future__ import annotations

import hashlib
import json
from typing import Dict, List, Optional, Sequence

import pandas as pd

from ..baseline import EstimatorFactory, GroupedRunConfig, OuterFold, run_grouped_evaluation
from ..features import OFFSET_INVARIANT_FEATURES, model_feature_columns


def resolve_arm(table: pd.DataFrame, arm: Dict[str, object]) -> List[str]:
    cols = model_feature_columns(table)
    rule = arm.get("rule", "explicit")
    if rule == "all":
        chosen = cols
    elif rule == "offset_invariant":
        chosen = [c for c in cols if c.split("__")[-1] in OFFSET_INVARIANT_FEATURES]
    elif rule == "explicit":
        stats = set(arm.get("statistics", [])) or None
        chans = set(arm.get("channels", [])) or None
        chosen = [c for c in cols
                  if (stats is None or c.split("__")[-1] in stats)
                  and (chans is None or c.split("__")[0] in chans)]
    else:
        raise ValueError(f"unknown arm rule '{rule}'")
    return chosen  # order follows the feature table (deterministic)


def feature_set_hash(cols: Sequence[str]) -> str:
    return hashlib.sha256("\n".join(cols).encode("utf-8")).hexdigest()[:16]


def run_sensitivity(table: pd.DataFrame, outer_folds: Sequence[OuterFold], arms: Sequence[Dict[str, object]],
                    factory: EstimatorFactory, base_config: GroupedRunConfig,
                    min_features: int = 1) -> Dict[str, pd.DataFrame]:
    manifest, results, preds = [], [], []
    for arm in arms:
        name = str(arm["name"])
        try:
            cols = resolve_arm(table, arm)
        except ValueError as exc:
            manifest.append({"arm": name, "status": "NOT_SUPPORTED", "reason": str(exc), "n_features": 0,
                             "feature_set_hash": None, "features": ""})
            continue
        if len(cols) < min_features:
            manifest.append({"arm": name, "status": "NOT_SUPPORTED", "reason": "no features resolved",
                             "n_features": 0, "feature_set_hash": None, "features": ""})
            continue
        cfg = GroupedRunConfig(**{**base_config.__dict__, "model_name": f"{base_config.model_name}__{name}",
                                  "run_status": "EXPLORATORY_SECONDARY"})
        out = run_grouped_evaluation(table, cols, outer_folds, factory, cfg)
        p = out["predictions"].copy()
        p["arm"] = name
        preds.append(p)
        for (fold, fam), d in p.groupby(["outer_fold", cfg.independence_col]):
            results.append({"arm": name, "outer_fold": fold, cfg.independence_col: fam,
                            "n_windows": len(d), "n_scenarios": d["Scenario_ID"].nunique(),
                            "accuracy": float((d["y_true"] == d["y_pred"]).mean())})
        manifest.append({"arm": name, "status": "EXECUTED_EXPLORATORY", "reason": "",
                         "n_features": len(cols), "feature_set_hash": feature_set_hash(cols),
                         "features": json.dumps(cols)})
    return {"arm_manifest": pd.DataFrame(manifest),
            "family_results": pd.DataFrame(results),
            "predictions": pd.concat(preds, ignore_index=True) if preds else pd.DataFrame()}
