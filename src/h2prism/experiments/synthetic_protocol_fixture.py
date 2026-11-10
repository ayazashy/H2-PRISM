"""
SYNTHETIC PROTOCOL FIXTURE - NOT H2-SimNet DATA, NOT RESEARCH RESULTS.

Builds a small deterministic dataset with the same layout as the real candidate package
(raw-like Parquet per run in two realizations, a manifest in the v0.2 schema, leave-one-topology-out
folds, and a config in the FINAL_EXPERIMENT_CONFIG structure with status SYNTHETIC_TEST_CONFIG) so
that tools/experiments/run_primary_protocol.py can be exercised end to end.

Structure per topology (3 topologies): NORMAL 1 run, LEAK 4 runs (one weak/strong family + 2 single
runs), COMPRESSOR_FAULT 2 runs (one weak/strong family), COMPRESSOR_DELAY 1 run whose label stops
before the end (post-event rows). Thin classes therefore have one reference family per topology,
which exercises the D(x) support safeguard and unattainable coverage targets.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd
import yaml

SENS = [f"PS{i}" for i in range(1, 13)] + [f"MFS{i}" for i in range(1, 5)]
LAB = ["label_anomaly", "Leak", "CompressorFault", "CompressorDelay", "leak_G3", "leak_G4", "leak_G5", "leak_G6"]
TOPOS = ["TA", "TB", "TC"]
SHIFT = {"NORMAL": 0.0, "LEAK": -0.6, "COMPRESSOR_FAULT": 0.5, "COMPRESSOR_DELAY": 0.25}
N_ROWS = 300


def _run(cls: str, topo_i: int, run_seed: int, family_offset: float, noisy: bool) -> pd.DataFrame:
    base_rng = np.random.default_rng(run_seed)
    t = np.arange(N_ROWS, dtype=float)
    X = 5.0 + 0.3 * topo_i + family_offset + 0.02 * base_rng.standard_normal((N_ROWS, len(SENS)))
    df = pd.DataFrame(X, columns=SENS)
    for c in LAB:
        df[c] = 0
    if cls != "NORMAL":
        active = t < 120 if cls == "COMPRESSOR_DELAY" else np.ones(N_ROWS, bool)
        col = {"LEAK": "Leak", "COMPRESSOR_FAULT": "CompressorFault", "COMPRESSOR_DELAY": "CompressorDelay"}[cls]
        df.loc[active, [col, "label_anomaly"]] = 1
        if cls == "LEAK":
            df.loc[active, "leak_G4"] = 1
        df.loc[active, SENS] = df.loc[active, SENS] + SHIFT[cls] * np.linspace(1, 1.5, len(SENS))
    if noisy:
        df[SENS] = df[SENS] + 0.01 * np.random.default_rng(run_seed + 10_000).standard_normal((N_ROWS, len(SENS)))
    df.index = pd.Index(t, name="Timestamp")
    return df


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def make_fixture(root: Path, seed: int = 0) -> Dict[str, Path]:
    root = Path(root)
    raw = root / "raw"
    rows, k = [], 0
    for ti, topo in enumerate(TOPOS):
        plan = [("NORMAL", f"N", 0.0), ("LEAK", "L1", 0.05), ("LEAK", "L1", 0.05), ("LEAK", "L2", -0.05),
                ("LEAK", "L3", 0.1), ("COMPRESSOR_FAULT", "F1", 0.0), ("COMPRESSOR_FAULT", "F1", 0.0),
                ("COMPRESSOR_DELAY", "D1", 0.0)]
        for j, (cls, fam, off) in enumerate(plan):
            k += 1
            sid = f"SYN_{topo}_{cls}_{j}"
            files = {}
            for real, noisy in (("clean", False), ("noise_added", True)):
                p = raw / real / f"{sid}.parquet"
                p.parent.mkdir(parents=True, exist_ok=True)
                _run(cls, ti, seed * 1000 + k, off, noisy).to_parquet(p)
                files[real] = p
            rows.append({"Scenario_ID": sid, "Scenario_Family_ID": f"SYN_FAM_{topo}_{fam}", "topology": topo,
                         "run_stem": sid, "raw_label_columns": "", "label_mapped": cls, "eligible_primary": True,
                         "exclusion_reason": "", "file_noise_added": files["noise_added"].relative_to(raw).as_posix(),
                         "sha256_noise_added": _sha(files["noise_added"]),
                         "file_clean": files["clean"].relative_to(raw).as_posix(), "sha256_clean": _sha(files["clean"]),
                         "family_extended_sensitivity": f"SYN_FAM_{topo}_{fam}", "family_conservative_sensitivity": topo,
                         "manifest_version": "synthetic", "status": "SYNTHETIC_TEST"})
    # one ineligible run (excluded with reason) to exercise the exclusion path
    rows.append({**rows[1], "Scenario_ID": "SYN_TA_EXCLUDED", "eligible_primary": False,
                 "label_mapped": "EXCLUDED_COMPOUND", "exclusion_reason": "synthetic compound exclusion"})
    man = pd.DataFrame(rows).sort_values("Scenario_ID")
    man_p = root / "manifest.csv"
    man_p.write_bytes(man.to_csv(index=False, lineterminator="\n").encode("utf-8"))
    el = man[man.eligible_primary]
    folds = []
    for fk, test_t in enumerate(TOPOS, start=1):
        for _, r in el.iterrows():
            folds.append({"outer_fold_id": fk, "split_role": "test" if r.topology == test_t else "train",
                          "Scenario_ID": r.Scenario_ID, "target_class": r.label_mapped, "topology": r.topology,
                          "family_primary": r.Scenario_Family_ID})
    folds_p = root / "folds.csv"
    folds_p.write_bytes(pd.DataFrame(folds).to_csv(index=False, lineterminator="\n").encode("utf-8"))
    cfg = {
        "status": "SYNTHETIC_TEST_CONFIG", "version": "synthetic-1",
        "dataset": {"manifest": {"file": "manifest.csv", "sha256": _sha(man_p)}, "family_column": "Scenario_Family_ID",
                    "realization_primary": "noise_added", "realization_secondary": "clean",
                    "classes": ["NORMAL", "LEAK", "COMPRESSOR_FAULT", "COMPRESSOR_DELAY"], "eligible_runs": int(len(el))},
        "splits": {"outer": {"file": "folds.csv", "sha256": _sha(folds_p), "design": "leave_one_topology_out"},
                   "inner": {"scheme": "LOTO_within_train"}},
        "windows": {"window_s": 60, "stride_s": 30, "min_samples": 60, "label_mode": "row_level", "pre_event_policy": "exclude"},
        "features": {"statistics": ["mean", "std", "min", "max", "range", "last_minus_first", "slope", "mean_abs_diff"]},
        "model": {"primary": "random_forest", "grid": {"n_estimators": [15], "min_samples_leaf": [1], "max_features": ["sqrt", 0.3]}},
        "calibration": {"candidates": ["none", "sigmoid"], "criterion": "log_loss",
                        "feasibility_rule": {"min_groups_per_class": 2}},
        "distinguishability": {"k": 5, "weighting": "uniform", "prior_correction": False, "exclude_query_family": True,
                               "min_class_reference": 3, "min_distinct_scenarios": 2, "low_support_min_top_count": 2,
                               "min_top_class_families": 2, "out_of_support_quantile": 0.99},
        "combined_scores": {"fit": {"C": 1.0}},
        "policy_primary": {"ambiguity_mass": 0.9, "max_set_size": 2, "singleton_handling": "unresolved",
                           "unresolved_flags": ["OUT_OF_SUPPORT", "INVALID_FEATURES", "NO_REFERENCE"],
                           "specific_blocking_flags": ["LOW_SCENARIO_DIVERSITY", "TOP_CLASS_FEW_INDEPENDENT_RUNS"]},
        "policy_sensitivity_warning_only": {"same_as_primary_except": {"specific_blocking_flags": ["LOW_SCENARIO_DIVERSITY"]}},
        "thresholds": {"source": "development", "target_coverage_primary": 0.80, "target_coverage_secondary": [0.30, 0.90]},
        "evaluation": {"uncertainty": {"n_boot": 200, "seed": 7}},
        "seeds": {"global": 11},
    }
    cfg_p = root / "config.yaml"
    cfg_p.write_bytes(yaml.safe_dump(cfg, sort_keys=True).encode("utf-8"))
    return {"root": root, "raw": raw, "manifest": man_p, "folds": folds_p, "config": cfg_p}
