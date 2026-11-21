"""
SYNTHETIC TEST FIXTURES -- NOT H2-SimNet DATA, NOT RESEARCH RESULTS.

Deterministic toy generators used only by unit/integration tests. Every frame carries
``data_status = "SYNTHETIC"`` metadata so it cannot be mistaken for project data.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

DATA_STATUS = "SYNTHETIC"
CLASSES = ["NORMAL", "LEAK", "COMPRESSOR_FAULT", "COMPRESSOR_DELAY"]


def toy_scenario_frame(n_rows: int, label: str, onset_row: int | None, seed: int, channels=("PS1", "MFS1"),
                       level: float = 5.0) -> pd.DataFrame:
    """A toy sensor frame with row-level binary label columns in the H2-SimNet layout."""
    rng = np.random.default_rng(seed)
    t = np.arange(n_rows, dtype=float)
    df = pd.DataFrame({c: level + 0.01 * rng.standard_normal(n_rows) for c in channels})
    for col in ("label_anomaly", "Leak", "CompressorFault", "CompressorDelay"):
        df[col] = 0
    if label != "NORMAL" and onset_row is not None:
        active = t >= onset_row
        col = {"LEAK": "Leak", "COMPRESSOR_FAULT": "CompressorFault", "COMPRESSOR_DELAY": "CompressorDelay"}[label]
        df.loc[active, col] = 1
        df.loc[active, "label_anomaly"] = 1
        shift = {"LEAK": -0.5, "COMPRESSOR_FAULT": 0.4, "COMPRESSOR_DELAY": 0.2}[label]
        for i, c in enumerate(channels):
            df.loc[active, c] = df.loc[active, c] + shift * (1 + i) + 0.002 * (t[active] - onset_row)
    df.attrs["data_status"] = DATA_STATUS
    return df


def toy_feature_table(n_families_per_class: int = 3, scenarios_per_family: int = 2, windows_per_scenario: int = 8,
                      n_features: int = 4, separation: float = 3.0, seed: int = 7) -> pd.DataFrame:
    """Window-level feature table with known family/scenario structure."""
    rng = np.random.default_rng(seed)
    rows = []
    for ci, cls in enumerate(CLASSES):
        center = np.zeros(n_features)
        center[ci % n_features] = separation
        for f in range(n_families_per_class):
            fam_offset = 0.3 * rng.standard_normal(n_features)
            for s in range(scenarios_per_family):
                scen = f"SYN_{cls}_F{f}_S{s}"
                for w in range(windows_per_scenario):
                    x = center + fam_offset + 0.5 * rng.standard_normal(n_features)
                    rows.append({"window_id": f"{scen}_w{w:04d}", "Scenario_ID": scen,
                                 "Scenario_Family_ID": f"SYN_FAM_{cls}_{f}", "label_mapped": cls,
                                 **{f"X{j}__mean": x[j] for j in range(n_features)}})
    df = pd.DataFrame(rows)
    df.attrs["data_status"] = DATA_STATUS
    return df


def family_round_robin_folds(table: pd.DataFrame, n_folds: int = 3):
    """Outer folds holding out every n-th family of each class (family-disjoint)."""
    from h2prism.baseline import OuterFold
    fams = sorted(table["Scenario_Family_ID"].unique())
    by_cls = {}
    for fam in fams:
        cls = table.loc[table["Scenario_Family_ID"] == fam, "label_mapped"].iloc[0]
        by_cls.setdefault(cls, []).append(fam)
    folds = []
    for k in range(n_folds):
        test_fams = {f for lst in by_cls.values() for i, f in enumerate(lst) if i % n_folds == k}
        test_s = sorted(set(table.loc[table["Scenario_Family_ID"].isin(test_fams), "Scenario_ID"]))
        train_s = sorted(set(table.loc[~table["Scenario_Family_ID"].isin(test_fams), "Scenario_ID"]))
        folds.append(OuterFold(k + 1, train_s, test_s))
    return folds
