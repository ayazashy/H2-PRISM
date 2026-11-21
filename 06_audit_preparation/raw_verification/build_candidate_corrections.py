#!/usr/bin/env python3
"""
CANDIDATE dataset corrections for H2-PRISM. This is NOT an approved data freeze.

Yazan must review dataset definitions, Faisal must approve any evaluation design,
and Ahmed must review the scientific implications. Yazan's files in 01_dataset_audit/
are only read, never written. Raw data are only read.

Inputs: data/raw/H2-SimNet-Dataset (official Zenodo 10.5281/zenodo.17871393, V2),
        01_dataset_audit/{DATASET_SCENARIO_MAP,DUPLICATE_EXPORT_AUDIT}.csv,
        06_audit_preparation/raw_verification/{CROSS_TREE_COMPARISON,PRE_EVENT_SHARED_SEGMENTS}.csv
Outputs: 06_audit_preparation/candidate_corrections/*.csv

Usage (repo root): python 06_audit_preparation/raw_verification/build_candidate_corrections.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from h2prism.splits import content_equivalence_groups, inner_group_splits, validate_outer_folds  # noqa: E402

RAW = Path("data/raw")
AUD = Path("01_dataset_audit")
RV = Path("06_audit_preparation/raw_verification")
OUT = Path("06_audit_preparation/candidate_corrections")
STATUS = "CANDIDATE_NOT_APPROVED"
PRIMARY = ["NORMAL", "LEAK", "COMPRESSOR_FAULT", "COMPRESSOR_DELAY"]
TOPO = {"cent": "Center", "down": "Downstream", "up": "Upstream", "center": "Center"}
MIN_SHARED_ROWS = 400  # identical pre-event rows required to call two runs dependent (see report)


def tree_of(f: str) -> str:
    if "/H2-SimNet-clean/" in f:
        return "clean"
    if "/MATLAB_SIMSCAPE_Simulation/" in f:
        return "matlab_solver_export"
    return "noisy_release"


def parse(f: str):
    m = re.search(r"anom_gest(cent|down|up)/(\w+)/(\w+)\.(csv|parquet)$", f)
    if m:
        return TOPO[m.group(1)], m.group(2), m.group(3)
    m = re.search(r"normality_gest_(center|down|up)\.(csv|parquet)$", f)
    if m:
        return TOPO[m.group(1)], "normal_run", "normality"
    m = re.search(r"/(\w+)\.(csv|parquet)$", f)
    return "ROOT", "root", m.group(1)


def row_level_class(pq_path: Path):
    df = pd.read_parquet(pq_path)
    leak, cf, cd = (df[c].to_numpy() == 1 for c in ("Leak", "CompressorFault", "CompressorDelay"))
    loc = df[["leak_G3", "leak_G4", "leak_G5", "leak_G6"]].to_numpy() == 1
    types = set()
    if leak.any(): types.add("LEAK")
    if cf.any(): types.add("COMPRESSOR_FAULT")
    if cd.any(): types.add("COMPRESSOR_DELAY")
    locs = [g for g, on in zip(("G3", "G4", "G5", "G6"), loc.any(axis=0)) if on]
    inconsistent = bool((loc.any(axis=1) & ~leak).any())
    multi = bool(((leak.astype(int) + cf + cd) > 1).any())
    return types, locs, inconsistent, multi


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ymap = pd.read_csv(AUD / "DATASET_SCENARIO_MAP.csv")
    dup = pd.read_csv(AUD / "DUPLICATE_EXPORT_AUDIT.csv")
    eq = content_equivalence_groups(dup)
    xt = pd.read_csv(RV / "CROSS_TREE_COMPARISON.csv")
    pre = pd.read_csv(RV / "PRE_EVENT_SHARED_SEGMENTS.csv")

    # ---------------- 1. canonical inventory + candidate Scenario_IDs
    inv = ymap[["file", "Scenario_ID", "Scenario_Family_ID", "event_label_raw", "phase"]].rename(
        columns={"Scenario_ID": "yazan_Scenario_ID", "Scenario_Family_ID": "yazan_Scenario_Family_ID",
                 "event_label_raw": "yazan_event_label_raw", "phase": "yazan_phase"})
    inv["data_version"] = inv["file"].map(tree_of)
    parsed = inv["file"].map(parse)
    inv["topology"] = [p[0] for p in parsed]
    inv["segment_dir"] = [p[1] for p in parsed]
    stem = [p[2] for p in parsed]
    inv["noise_variant_of_stem"] = [s.replace("_noisy", "") if s.endswith("_noisy") else "" for s in stem]
    inv["run_stem"] = [s.replace("_noisy", "") for s in stem]

    # root-level leakG4 files: exact byte duplicate of the noisy Upstream/assestment_transient leakG4
    root_target = "H2-SimNet-Dataset/anomalous-scenarios/parquet/anom_gestup/assestment_transient/leakG4.parquet"
    is_root = inv["topology"] == "ROOT"
    for i in inv.index[is_root]:
        f = inv.at[i, "file"]
        if f in eq and root_target in eq and eq[f] == eq[root_target]:
            inv.at[i, "topology"], inv.at[i, "segment_dir"] = "Upstream", "assestment_transient"
            inv.at[i, "data_version"] = "noisy_release_misfiled_duplicate"
    inv["candidate_Scenario_ID"] = ("CS_" + inv["topology"].str.upper() + "_" + inv["segment_dir"].str.upper()
                                    + "_" + inv["run_stem"].str.upper())
    inv["content_group"] = inv["file"].map(lambda f: eq.get(f, f))

    # row-level label semantics from the clean parquet of each candidate scenario
    lab = {}
    for sid, d in inv.groupby("candidate_Scenario_ID"):
        cand = d[d["file"].str.endswith(".parquet") & d["data_version"].eq("clean")]["file"]
        if cand.empty:
            cand = d[d["file"].str.endswith(".parquet")]["file"]
        if cand.empty:
            lab[sid] = (set(), [], False, False)
            continue
        lab[sid] = row_level_class(RAW / sorted(cand)[0])
    inv["rowlevel_event_types"] = inv["candidate_Scenario_ID"].map(lambda s: ";".join(sorted(lab[s][0])) or "NONE")
    inv["rowlevel_leak_locations"] = inv["candidate_Scenario_ID"].map(lambda s: ";".join(lab[s][1]))
    inv["annotation_inconsistent_location_without_leak"] = inv["candidate_Scenario_ID"].map(lambda s: lab[s][2])
    inv["simultaneous_event_types"] = inv["candidate_Scenario_ID"].map(lambda s: lab[s][3])

    def primary(s):
        types, locs, incons, multi = lab[s]
        if incons:
            return "EXCLUDED_PENDING_REVIEW", "ANNOTATION_INCONSISTENT (location label active while Leak=0)"
        if not types:
            return "NORMAL", ""
        if len(types) > 1 or multi:
            return "EXCLUDED_COMPOUND", "simultaneous different event types (not mutually exclusive)"
        t = next(iter(types))
        note = "multi-location leak treated as LEAK (consistent rule; alternative: exclude all)" if len(locs) > 1 else ""
        return t, note
    pm = {s: primary(s) for s in lab}
    inv["candidate_primary_class"] = inv["candidate_Scenario_ID"].map(lambda s: pm[s][0])
    inv["candidate_class_note"] = inv["candidate_Scenario_ID"].map(lambda s: pm[s][1])
    inv["recommended_model_input"] = np.where(
        inv["data_version"].eq("matlab_solver_export"), "NO (different sampling 0.8/0.9 s, no labels, missing PS11/PS12/MFS4)",
        np.where(inv["file"].str.endswith(".csv"), "NO (numerically equivalent to Parquet in same tree; use Parquet)",
                 "CHOOSE ONE VERSION: clean OR noisy_release (Faisal decision)"))
    inv["status"] = STATUS

    # ---------------- 2. relationships (evidence-based edges between candidate scenarios)
    f2s = dict(zip(inv["file"], inv["candidate_Scenario_ID"]))
    edges = []
    for _, r in xt.iterrows():
        a, b = r["clean_file"], r["other_file"]
        same_sid = f2s.get(a) == f2s.get(b)
        if bool(r.get("labels_identical")) and float(r["max_abs_diff"]) > 0:
            edges.append((f2s.get(a), f2s.get(b), "CLEAN_VS_NOISY_VERSION_SAME_RUN",
                          f"labels identical; residual mean<= {r['mean_diff_max_abs_over_channels']:.2g}, lag1 autocorr {r['resid_lag1_autocorr_median']:.2g}",
                          "same scenario" if same_sid else "CHECK"))
    for _, r in pre.iterrows():
        a, b = f2s.get(r["file_a"]), f2s.get(r["file_b"])
        if a is None or b is None or a == b:
            continue
        if r["identical_pre_event"]:
            strong = r["rows_compared_pre_event"] >= MIN_SHARED_ROWS
            edges.append((a, b, "SHARED_IDENTICAL_PRE_EVENT_SEGMENT" if strong else "SHARED_SHORT_INITIAL_SEGMENT_UNRESOLVED",
                          f"{int(r['rows_compared_pre_event'])} identical pre-event rows (clean tree)",
                          "dependent: keep together" if strong else "human review (initial state only)"))
    for s in inv["candidate_Scenario_ID"].unique():
        m = re.match(r"(CS_\w+?_\w+?_)(\w+)_(WEAK|STRONG)$", s)
        if m:
            other = m.group(1) + m.group(2) + ("_STRONG" if m.group(3) == "WEAK" else "_WEAK")
            if other in set(inv["candidate_Scenario_ID"]) and s < other:
                edges.append((s, other, "WEAK_STRONG_VARIANT_SAME_CONFIG", "dataset ReadME: weak/strong intensities of one injection", "dependent: keep together"))
    for s in inv.loc[inv["noise_variant_of_stem"] != "", "candidate_Scenario_ID"].unique():
        pass  # noise variants already share the candidate_Scenario_ID (stem without _noisy)
    E = pd.DataFrame(edges, columns=["scenario_a", "scenario_b", "relationship", "evidence", "grouping_implication"]).drop_duplicates()
    E["status"] = STATUS
    E.to_csv(OUT / "CANDIDATE_SCENARIO_RELATIONSHIPS.csv", index=False, lineterminator="\n")

    # ---------------- 3. families: strict = within-topology components of dependent edges
    parent = {s: s for s in inv["candidate_Scenario_ID"].unique()}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for _, e in E[E["grouping_implication"].str.startswith("dependent")].iterrows():
        ra, rb = find(e["scenario_a"]), find(e["scenario_b"])
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)
    inv["candidate_family_strict"] = inv["candidate_Scenario_ID"].map(lambda s: "CF_" + find(s)[3:])
    inv["candidate_family_conservative"] = "CF_TOPOLOGY_" + inv["topology"].str.upper()
    cross = inv.groupby("candidate_family_strict")["topology"].nunique()
    assert (cross == 1).all(), "strict family spans topologies"
    inv.to_csv(OUT / "CANDIDATE_CANONICAL_INVENTORY_AND_SCENARIO_MAP.csv", index=False, lineterminator="\n")

    # ---------------- 4. candidate folds: leave-one-topology-out, one row per scenario
    sc = (inv[inv["file"].str.endswith(".parquet") & inv["data_version"].isin(["clean", "noisy_release"])]
          .pivot_table(index=["candidate_Scenario_ID", "topology", "candidate_primary_class",
                              "candidate_family_strict", "candidate_family_conservative"],
                       columns="data_version", values="file", aggfunc="first").reset_index())
    sc = sc.rename(columns={"clean": "file_clean_version", "noisy_release": "file_noisy_version"})
    elig = sc[sc["candidate_primary_class"].isin(PRIMARY)].copy()
    rows = []
    for k, test_topo in enumerate(["Downstream", "Center", "Upstream"], start=1):
        for _, r in elig.iterrows():
            rows.append({"outer_fold_id": k, "fold_name": f"LOTO_test_{test_topo}",
                         "split_role": "test" if r["topology"] == test_topo else "train",
                         "Scenario_ID": r["candidate_Scenario_ID"], "target_class": r["candidate_primary_class"],
                         "Scenario_Family_ID": r["candidate_family_strict"],
                         "Scenario_Family_ID_conservative": r["candidate_family_conservative"],
                         "topology": r["topology"], "file_clean_version": r["file_clean_version"],
                         "file_noisy_version": r["file_noisy_version"], "status": STATUS})
    folds = pd.DataFrame(rows)
    folds.to_csv(OUT / "CANDIDATE_FOLDS_LOTO.csv", index=False, lineterminator="\n")

    # ---------------- 5. validation of candidate folds (both family views, all file versions)
    long = pd.concat([folds.assign(file=folds["file_clean_version"]), folds.assign(file=folds["file_noisy_version"])])
    res = []
    for view in ("Scenario_Family_ID", "Scenario_Family_ID_conservative"):
        f = long.drop(columns=["Scenario_Family_ID"]).rename(columns={view: "Scenario_Family_ID"}) if view != "Scenario_Family_ID" else long
        # treat the clean/noisy versions as one scenario: collapse multi-file check by grouping on scenario
        r = validate_outer_folds(f, required_train_classes=PRIMARY, equivalence=eq)
        iss = r.issues_frame()
        iss = iss[iss["code"] != "MULTIPLE_FILES_PER_SCENARIO"]  # by design: two versions of ONE run, never both used
        iss["family_view"] = view
        res.append(iss)
        s = r.summary.copy(); s["family_view"] = view
        s.to_csv(OUT / f"CANDIDATE_FOLD_SUMMARY_{'strict' if view == 'Scenario_Family_ID' else 'conservative'}.csv",
                 index=False, lineterminator="\n")
    pd.concat(res).to_csv(OUT / "CANDIDATE_FOLD_VALIDATION_ISSUES.csv", index=False, lineterminator="\n")

    # ---------------- 6. inner development splits (leave-one-topology-out inside outer-train)
    inner = []
    for k, d in folds.groupby("outer_fold_id"):
        tr = d[d["split_role"] == "train"].reset_index(drop=True)
        splits, warns = inner_group_splits(tr["topology"], tr["target_class"], n_splits=tr["topology"].nunique(),
                                           required_classes=PRIMARY)
        for j, (a, b) in enumerate(splits):
            inner.append({"outer_fold_id": k, "inner_split": j,
                          "inner_train_topologies": ";".join(sorted(set(tr.loc[a, "topology"]))),
                          "inner_val_topologies": ";".join(sorted(set(tr.loc[b, "topology"]))),
                          "inner_train_classes": ";".join(sorted(set(tr.loc[a, "target_class"]))),
                          "inner_val_scenarios_per_class": tr.loc[b].groupby("target_class").size().to_dict(),
                          "warnings": " | ".join(warns), "status": STATUS})
    pd.DataFrame(inner).to_csv(OUT / "CANDIDATE_INNER_SPLITS.csv", index=False, lineterminator="\n")

    # ---------------- 7. counts for honest reporting
    cnt = (elig.groupby("candidate_primary_class")
           .agg(scenarios=("candidate_Scenario_ID", "nunique"), strict_families=("candidate_family_strict", "nunique"),
                topologies=("topology", "nunique")).reset_index())
    ex = sc[~sc["candidate_primary_class"].isin(PRIMARY)][["candidate_Scenario_ID", "candidate_primary_class"]]
    cnt.to_csv(OUT / "CANDIDATE_CLASS_FAMILY_COUNTS.csv", index=False, lineterminator="\n")
    ex.to_csv(OUT / "CANDIDATE_EXCLUSIONS.csv", index=False, lineterminator="\n")
    print(cnt.to_string()); print(ex.to_string())
    print("candidate scenarios:", sc.shape[0], "eligible:", elig.shape[0],
          "strict families:", elig["candidate_family_strict"].nunique())


if __name__ == "__main__":
    main()
