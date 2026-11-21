#!/usr/bin/env python3
"""
Phase 4 decision evidence (read-only; no model training, no outer-test labels used for any choice).

Outputs to 06_audit_preparation/phase4_approvals/evidence/:
  RELATIONSHIP_19_REVIEW.csv      individual review of the SHARED_SHORT_INITIAL_SEGMENT pairs
  INVENTORY_RECONCILIATION.csv    files -> realizations -> runs -> eligible runs -> classes
  WINDOW_OPTION_COMPARISON.csv    window/stride candidates: eligible windows per class, boundary losses
  EVENT_DURATIONS.csv             verified active-label durations per run
  INNER_FOLD_SUFFICIENCY.csv      runs/families/windows per class in every inner-train partition

Usage (repo root): python tools/dataset/phase4_decision_evidence.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from h2prism.io import SENSOR_CHANNELS, build_time_axis, find_invalid_intervals, read_table  # noqa: E402
from h2prism.windows import WindowConfig, generate_windows  # noqa: E402

PKG = ROOT / "06_audit_preparation" / "pre_experiment_review"
OUT = ROOT / "06_audit_preparation" / "phase4_approvals" / "evidence"
RAW = ROOT / "data" / "raw"
CLASSES = ["NORMAL", "LEAK", "COMPRESSOR_FAULT", "COMPRESSOR_DELAY"]
WINDOW_OPTIONS = [(30, 15), (60, 30), (60, 60), (120, 60), (300, 150)]


def save(df, name):
    df.to_csv(OUT / name, index=False, lineterminator="\n", float_format="%.6g")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    man = pd.read_csv(PKG / "CANDIDATE_SCENARIO_MANIFEST.csv").set_index("Scenario_ID")
    inv = pd.read_csv(PKG / "CANDIDATE_FILE_INVENTORY.csv")
    ev = pd.read_csv(PKG / "FAMILY_RELATIONSHIP_EVIDENCE.csv")
    fam = pd.read_csv(PKG / "CANDIDATE_FAMILY_MAP.csv").set_index("Scenario_ID")

    # ---------- 1. the 19 unresolved relationships
    rows = []
    for _, e in ev[ev.relationship == "SHARED_SHORT_INITIAL_SEGMENT"].iterrows():
        a, b = e.scenario_a, e.scenario_b
        d = json.loads(e.evidence)
        cut, lead = d["pre_event_rows"], d["identical_leading_rows"]
        A, B = man.loc[a], man.loc[b]
        same_primary = fam.loc[a, "family_primary"] == fam.loc[b, "family_primary"]
        if lead == cut and cut <= 25:
            kind, status = "IDENTICAL_UNTIL_EARLIEST_ONSET_25S", "PLAUSIBLE (shared start-up; first 25 s are pre-event in every run)"
        elif lead >= 0.95 * cut:
            kind, status = "NEAR_IDENTICAL_PRE_EVENT_TRAJECTORY", "PLAUSIBLE_DEPENDENT (diverges only in the last rows before onset)"
        else:
            kind, status = "PARTIAL_SHARED_START", "UNRESOLVED"
        rows.append({
            "edge_id": e.edge_id, "scenario_a": a, "scenario_b": b, "topology": A.topology,
            "segment_a": A.segment_dir, "segment_b": B.segment_dir, "run_a": A.run_stem, "run_b": B.run_stem,
            "class_a": A.candidate_primary_class, "class_b": B.candidate_primary_class,
            "cross_class": A.candidate_primary_class != B.candidate_primary_class,
            "onset_a_s": A.onset_s_verified, "onset_b_s": B.onset_s_verified,
            "pre_event_rows_compared": cut, "identical_leading_rows": lead,
            "max_abs_diff_pre_event": d["max_abs_diff_pre_event"],
            "already_same_primary_family": bool(same_primary), "relation_type": kind, "dependence_status": status,
            "effect_on_LOTO_outer_folds": "none (same topology, always same side)",
            "effect_on_inner_family_splits": "matters only for grouped_by_family_primary_k3 inner scheme",
            "recommendation": ("keep separate in primary map; merge in extended/conservative sensitivity view"
                               if kind == "IDENTICAL_UNTIL_EARLIEST_ONSET_25S" else
                               "treat as dependent for inner splits (merge) unless Yazan shows different configurations"),
        })
    save(pd.DataFrame(rows), "RELATIONSHIP_19_REVIEW.csv")

    # ---------- 2. inventory reconciliation
    rec = [("tabular files (CSV + Parquet)", len(inv), "CANDIDATE_FILE_INVENTORY.csv")]
    for rt, n in inv.realization_type.value_counts().sort_index().items():
        rec.append((f"  files of realization {rt}", int(n), "realization_type"))
    rec.append(("distinct simulated runs (candidate Scenario_IDs)", int(inv.candidate_Scenario_ID.nunique()), "candidate_Scenario_ID"))
    m = man.reset_index()
    for c, n in m.candidate_primary_class.value_counts().sort_index().items():
        rec.append((f"  runs with candidate class {c}", int(n), "CANDIDATE_SCENARIO_MANIFEST.csv"))
    rec.append(("eligible runs for the primary 4-class task", int(m.eligible_primary_candidate.sum()), "57 - 3 compound - 3 annotation conflict"))
    for v in ("family_primary", "family_extended", "family_conservative"):
        rec.append((f"families ({v}) over all 57 runs", int(m[v].nunique()), "CANDIDATE_FAMILY_MAP.csv"))
        rec.append((f"families ({v}) over the 51 eligible runs", int(m.loc[m.eligible_primary_candidate, v].nunique()), ""))
    save(pd.DataFrame(rec, columns=["quantity", "count", "source_or_rule"]), "INVENTORY_RECONCILIATION.csv")

    # ---------- 3. windows (clean canonical realization of every run; windowing only)
    el = m.copy()
    durations, wrows, wins_6030 = [], [], []
    for _, r in el.sort_values("Scenario_ID").iterrows():
        df = read_table(RAW / r.canonical_clean_file)
        ax = build_time_axis(df, time_col="Timestamp")
        inval = find_invalid_intervals(df, SENSOR_CHANNELS)
        act = {c: int((df[c] == 1).sum()) for c in ("Leak", "CompressorFault", "CompressorDelay", "label_anomaly")}
        durations.append({"Scenario_ID": r.Scenario_ID, "class": r.candidate_primary_class, "onset_s": r.onset_s_verified,
                          **{f"{k}_active_s": v for k, v in act.items()}, "run_length_s": len(df)})
        scen = {"file": r.canonical_clean_file, "Scenario_ID": r.Scenario_ID, "Scenario_Family_ID": r.family_primary,
                "label_raw": "", "label_mapped": r.candidate_primary_class, "phase": "n/a", "topology": r.topology,
                "eligible_primary": bool(r.eligible_primary_candidate)}
        for (w, s) in WINDOW_OPTIONS:
            for pol in ("exclude", "label_normal"):
                wm = generate_windows(df, ax, scen, WindowConfig(w, s, w, "row_level", pol), inval)
                e = wm[wm.eligible_primary]
                rec = {"Scenario_ID": r.Scenario_ID, "class": r.candidate_primary_class, "topology": r.topology,
                       "family_primary": r.family_primary, "window_s": w, "stride_s": s, "pre_event_policy": pol,
                       "windows_total": len(wm), "boundary_crossing": int((wm.boundary_status == "BOUNDARY_CROSSING").sum()),
                       "eligible_windows": len(e)}
                for c in CLASSES:
                    rec[f"eligible_{c}"] = int((e.label_mapped == c).sum())
                wrows.append(rec)
    save(pd.DataFrame(durations), "EVENT_DURATIONS.csv")
    W = pd.DataFrame(wrows)
    save(W, "WINDOW_OPTION_PER_RUN.csv")
    agg = (W[W.Scenario_ID.isin(el.loc[el.eligible_primary_candidate, "Scenario_ID"])]
           .groupby(["window_s", "stride_s", "pre_event_policy"])
           .agg(windows_total=("windows_total", "sum"), boundary_crossing=("boundary_crossing", "sum"),
                eligible=("eligible_windows", "sum"), **{f"eligible_{c}": (f"eligible_{c}", "sum") for c in CLASSES},
                **{f"runs_contributing_{c}": (f"eligible_{c}", lambda s: int((s > 0).sum())) for c in CLASSES})
           .reset_index())
    agg["overlap_fraction"] = 1 - agg["stride_s"] / agg["window_s"]
    save(agg, "WINDOW_OPTION_COMPARISON.csv")

    # ---------- 4. inner-fold sufficiency (LOTO_within_train and family k3), using the 60/30 'exclude' candidate
    folds = pd.read_csv(PKG / "CANDIDATE_OUTER_FOLDS.csv")
    inner = pd.read_csv(PKG / "CANDIDATE_INNER_FOLDS.csv")
    w6030 = W[(W.window_s == 60) & (W.stride_s == 30) & (W.pre_event_policy == "exclude")].set_index("Scenario_ID")
    out = []
    for _, r in inner.iterrows():
        tr = r.train_scenarios.split(";")
        va = r.val_scenarios.split(";")
        for c in CLASSES:
            trc = [s for s in tr if man.loc[s, "candidate_primary_class"] == c]
            vac = [s for s in va if man.loc[s, "candidate_primary_class"] == c]
            out.append({"outer_fold_id": r.outer_fold_id, "scheme": r.scheme, "inner_split": r.inner_split, "class": c,
                        "train_runs": len(trc), "train_families_primary": man.loc[trc, "family_primary"].nunique() if trc else 0,
                        "train_windows_60_30": int(w6030.loc[trc, f"eligible_{c}"].sum()) if trc else 0,
                        "val_runs": len(vac),
                        "D_k25_neighbourhood_can_span_>=2_runs": len(trc) >= 2,
                        "calibration_has_positives": len(trc) > 0 and len(vac) > 0})
    save(pd.DataFrame(out), "INNER_FOLD_SUFFICIENCY.csv")
    outer = []
    for k, d in folds.groupby("outer_fold_id"):
        tr = d[d.split_role == "train"]
        for c in CLASSES:
            s = tr[tr.target_class == c].Scenario_ID.tolist()
            outer.append({"outer_fold_id": k, "class": c, "outer_train_runs": len(s),
                          "outer_train_families_primary": tr[tr.target_class == c].family_primary.nunique(),
                          "outer_train_windows_60_30": int(w6030.loc[s, f"eligible_{c}"].sum())})
    save(pd.DataFrame(outer), "OUTER_TRAIN_REFERENCE_SUPPORT.csv")
    print(agg.to_string())


if __name__ == "__main__":
    main()
