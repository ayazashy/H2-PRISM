#!/usr/bin/env python3
"""
Build the CANDIDATE pre-experiment dataset package (CANDIDATE_NOT_APPROVED).

Read-only on data/raw. Writes only to --out. No model is trained.

Usage (repo root):
  python tools/dataset/build_pre_experiment_package.py --raw-parent data/raw \
      --out 06_audit_preparation/pre_experiment_review [--order sorted|reversed]

``--order reversed`` feeds the files in reverse order and with Windows separators; the
outputs must be byte-identical to the default run (cross-platform determinism check).
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from h2prism.dataset_manifest import (CLEAN, MISFILED, NOISY_VARIANT, RELEASE, SENSORS, SOLVER, STATUS,  # noqa: E402
                                      assign_scenarios, build_file_inventory, canonical_file,
                                      compare_realizations, discover_files, read_frame,
                                      shared_pre_event_rows, union_find, weak_strong_partner)
from h2prism.splits import inner_group_splits, validate_outer_folds  # noqa: E402

PRIMARY = ["NORMAL", "LEAK", "COMPRESSOR_FAULT", "COMPRESSOR_DELAY"]
MIN_DEPENDENT_ROWS = 400
FLOAT = "%.10g"
# Documented anomaly table of the dataset ReadME (REPORTED by the data publisher)
README_EVENTS = {
    "leakG3": ("G3 leak", 4000, "Steady State"), "leakG4": ("G4 leak", 2500, "Steady State"),
    "leakG5G6": ("G5+G6 overlapping leaks", 400, "Late Transient"),
    "brokenC1": ("C1 compressor fault", 25, "Initial Ramp-up"),
    "startdelayC1": ("C1 compressor start delay", 1000, "Initial Ramp-up"),
}


def readme_entry(run_stem: str):
    s = run_stem.replace("_weak", "").replace("_strong", "").replace("_overlapped", "")
    return README_EVENTS.get(s, ("not in ReadME anomaly table", None, "NOT_DOCUMENTED"))


def save(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, index=False, lineterminator="\n", float_format=FLOAT)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-parent", type=Path, default=Path("data/raw"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--order", choices=["sorted", "reversed"], default="sorted")
    a = ap.parse_args(argv)
    raw, out = a.raw_parent, a.out
    out.mkdir(parents=True, exist_ok=True)

    files = discover_files(raw)
    if a.order == "reversed":
        files = [f.replace("/", "\\") for f in reversed(files)]
    inv = assign_scenarios(build_file_inventory(raw, files))
    inv["status"] = STATUS
    save(inv, out / "CANDIDATE_FILE_INVENTORY.csv")
    frames = {}

    def F(f):
        if f not in frames:
            frames[f] = read_frame(raw / f)
        return frames[f]

    scen = sorted(inv["candidate_Scenario_ID"].unique())
    can = {s: {r: canonical_file(inv, s, r) for r in (CLEAN, RELEASE, NOISY_VARIANT, SOLVER)} for s in scen}

    # ---------------- realization relationships (same run, different realization)
    ev = []
    for s in scen:
        sub = inv[inv["candidate_Scenario_ID"] == s]
        # format twins inside one realization (CSV vs Parquet)
        for rt, g in sub.groupby("realization_type", sort=True):
            fs = sorted(g["file"])
            for x, y in itertools.combinations(fs, 2):
                c = compare_realizations(F(x), F(y))
                ev.append({"scenario_a": s, "scenario_b": s, "file_a": x, "file_b": y,
                           "relationship": "SAME_REALIZATION_FORMAT_TWIN" if c.get("numerically_equal_atol") else "SAME_REALIZATION_CONTENT_DIFFERS",
                           "method": "allclose(atol=1e-9) on sensor columns in canonical order", "tolerance": 1e-9,
                           "evidence": json.dumps(c, sort_keys=True), "confidence": "HIGH" if c.get("numerically_equal_atol") else "REVIEW",
                           "grouping": "same scenario", "handling": "use one file per realization (Parquet precedence)"})
        cl = can[s][CLEAN]
        for rt in (RELEASE, NOISY_VARIANT):
            other = can[s][rt]
            if cl and other:
                c = compare_realizations(F(cl), F(other))
                white = c.get("labels_identical") and abs(c.get("median_lag1_autocorr", 1)) < 0.05 and c.get("max_abs_mean_diff", 1) < 0.01
                ev.append({"scenario_a": s, "scenario_b": s, "file_a": cl, "file_b": other,
                           "relationship": "CLEAN_VS_NOISE_ADDED_SAME_RUN" if white else "CLEAN_VS_OTHER_UNEXPLAINED",
                           "method": "residual = other - clean: label identity, residual mean, lag-1 autocorrelation", "tolerance": "mean<0.01; |lag1|<0.05",
                           "evidence": json.dumps(c, sort_keys=True), "confidence": "HIGH" if white else "REVIEW",
                           "grouping": "same scenario; never count as independent evidence",
                           "handling": "choose ONE realization for modelling (Faisal)"})
        sol = can[s][SOLVER]
        if sol and cl:
            A, B = F(sol), F(cl)
            t = np.asarray(B.index, float) if B.index.name == "Timestamp" else np.arange(len(B), dtype=float)
            ok = t <= A["Timestamp"].max()
            per = {}
            for c in SENSORS:
                if c in A.columns:
                    rng = float(B[c].max() - B[c].min())
                    if rng > 1e-3:  # channels with no meaningful range cannot be compared relatively
                        per[c] = float(np.abs(np.interp(t[ok], A["Timestamp"], A[c]) - B[c].to_numpy()[ok]).max() / rng)
            rel_err = float(np.median(list(per.values()))) if per else float("nan")
            ev.append({"scenario_a": s, "scenario_b": s, "file_a": sol, "file_b": cl,
                       "relationship": "RAW_SOLVER_EXPORT_OF_SAME_RUN" if rel_err < 0.05 else "SOLVER_EXPORT_UNEXPLAINED",
                       "method": "linear interpolation of solver output to clean 1 s grid; per-channel max |diff| / channel range (channels with range>1e-3); median over channels",
                       "tolerance": 0.05, "evidence": json.dumps({"median_rel_err": rel_err, "per_channel": per}, sort_keys=True), "confidence": "MEDIUM",
                       "grouping": "same scenario", "handling": "not modelling input (variable step, missing PS11/PS12/MFS4, no labels)"})
        for _, m in sub[sub["realization_type"] == MISFILED].iterrows():
            ev.append({"scenario_a": s, "scenario_b": s, "file_a": m["file"], "file_b": m["scenario_resolution_evidence"].split(":", 1)[-1],
                       "relationship": "MISFILED_BYTE_IDENTICAL_COPY", "method": "SHA-256 equality", "tolerance": 0,
                       "evidence": m["scenario_resolution_evidence"], "confidence": "HIGH", "grouping": "same scenario",
                       "handling": "exclude copy; keep checksum record"})

    # ---------------- dependence between scenarios (clean realizations)
    clean_of = {s: can[s][CLEAN] for s in scen if can[s][CLEAN]}
    topo = {s: inv.loc[inv["candidate_Scenario_ID"] == s, "topology_from_path"].replace("UNLOCATED", np.nan).dropna().iloc[0]
            for s in scen}
    dep_edges, ext_edges = [], []
    for s1, s2 in itertools.combinations(sorted(clean_of), 2):
        cut, lead, dmax = shared_pre_event_rows(F(clean_of[s1]), F(clean_of[s2]))
        same_topo = topo[s1] == topo[s2]
        ws = weak_strong_partner(s1) == s2
        if ws:
            rel, grp, conf = "WEAK_STRONG_SAME_INJECTION", "dependent: same family (primary)", "HIGH (ReadME + shared rows)"
            dep_edges.append((s1, s2))
        elif lead >= MIN_DEPENDENT_ROWS:
            rel, grp, conf = "SHARED_IDENTICAL_TRAJECTORY", "dependent: same family (primary)", "HIGH"
            dep_edges.append((s1, s2))
        elif lead > 0:
            rel, grp, conf = "SHARED_SHORT_INITIAL_SEGMENT", "UNRESOLVED: merged only in extended view", "LOW"
            ext_edges.append((s1, s2))
        elif same_topo:
            rel, grp, conf = "SAME_TOPOLOGY_NO_SHARED_ROWS", "not merged (same network configuration; see conservative view)", "MEDIUM"
        else:
            rel, grp, conf = "CROSS_TOPOLOGY_NO_SHARED_ROWS", "independent runs (different withdrawal topology)", "MEDIUM"
        if rel in ("CROSS_TOPOLOGY_NO_SHARED_ROWS", "SAME_TOPOLOGY_NO_SHARED_ROWS"):
            continue  # summarised in counts below, not listed pairwise
        ev.append({"scenario_a": s1, "scenario_b": s2, "file_a": clean_of[s1], "file_b": clean_of[s2],
                   "relationship": rel, "method": "length of identical leading block of sensor rows before the earlier onset (clean realization)",
                   "tolerance": "exact equality", "evidence": json.dumps({"pre_event_rows": cut, "identical_leading_rows": lead, "max_abs_diff_pre_event": dmax}),
                   "confidence": conf, "grouping": grp, "handling": "keep together in every split" if grp.startswith("dependent") else "human review"})
    E = pd.DataFrame(ev)
    E.insert(0, "edge_id", [f"E{i:04d}" for i in range(len(E))])
    E["status"] = STATUS
    save(E, out / "FAMILY_RELATIONSHIP_EVIDENCE.csv")
    pairs = list(itertools.combinations(sorted(clean_of), 2))
    cross_total = sum(topo[x] != topo[y] for x, y in pairs)
    cross_shared = sum(1 for x, y in dep_edges + ext_edges if topo[x] != topo[y])

    # ---------------- families
    prim = union_find(scen, dep_edges)
    ext = union_find(scen, dep_edges + ext_edges)
    fam = pd.DataFrame({"Scenario_ID": scen})
    fam["topology"] = fam["Scenario_ID"].map(topo)
    fam["family_primary"] = fam["Scenario_ID"].map(lambda s: "FAM_P_" + prim[s][3:])
    fam["family_extended"] = fam["Scenario_ID"].map(lambda s: "FAM_E_" + ext[s][3:])
    fam["family_conservative"] = "FAM_C_" + fam["topology"].str.upper()
    edge_ids = {}
    for _, e in E.iterrows():
        for s in {e["scenario_a"], e["scenario_b"]}:
            if e["scenario_a"] != e["scenario_b"]:
                edge_ids.setdefault(s, []).append(e["edge_id"])
    fam["dependence_edges"] = fam["Scenario_ID"].map(lambda s: ";".join(edge_ids.get(s, [])))
    fam["family_primary_basis"] = np.where(fam["dependence_edges"] == "", "no evidenced dependence: singleton family",
                                           "union of WEAK_STRONG / SHARED_IDENTICAL_TRAJECTORY edges")
    assert fam.groupby("family_primary")["topology"].nunique().max() == 1
    assert fam.groupby("family_extended")["topology"].nunique().max() == 1

    # ---------------- scenario manifest with label / timing facts (clean canonical parquet)
    rows = []
    for s in scen:
        sub = inv[inv["candidate_Scenario_ID"] == s]
        src = can[s][CLEAN] or can[s][RELEASE]
        lab = inv.set_index("file").loc[src] if src else pd.Series(dtype=object)
        run_stem = sub["run_stem"].iloc[0] if (sub["topology_from_path"] != "UNLOCATED").any() else ""
        located = sub[sub["topology_from_path"] != "UNLOCATED"].iloc[0]
        types = [x for x in str(lab.get("event_types", "") or "").split(";") if x and x != "nan"]
        locs = str(lab.get("leak_locations", "") or "")
        incons = int(lab.get("rows_location_without_leak", 0) or 0) > 0
        multi = int(lab.get("rows_multiple_event_types", 0) or 0) > 0
        if incons:
            cls, why = "EXCLUDED_PENDING_REVIEW", "location label active while Leak=0 (annotation conflict)"
        elif not types:
            cls, why = "NORMAL", ""
        elif len(types) > 1 or multi:
            cls, why = "EXCLUDED_COMPOUND", "simultaneous different event types"
        else:
            cls, why = types[0], ("multi-location leak, single event type" if ";" in locs else "")
        fname_locs = "".join(re.findall(r"G(\d)", run_stem))
        file_locs = "".join(x.replace("G", "") for x in locs.split(";") if x and x != "nan")
        r_desc, r_t, r_phase = readme_entry(run_stem)
        onset = lab.get("label_anomaly__onset_s", np.nan)
        rows.append({
            "Scenario_ID": s, "topology": located["topology_from_path"], "segment_dir": located["segment_dir"],
            "run_stem": run_stem, "realizations": ";".join(sorted(sub["realization_type"].unique())),
            "n_files": len(sub), "canonical_clean_file": can[s][CLEAN] or "", "canonical_noise_added_file": can[s][RELEASE] or "",
            "noise_added_variant_file": can[s][NOISY_VARIANT] or "", "raw_solver_export_file": can[s][SOLVER] or "",
            "canonical_clean_sha256": inv.set_index("file").loc[can[s][CLEAN], "sha256"] if can[s][CLEAN] else "",
            "label_source_file": src or "", "raw_active_label_columns": lab.get("active_label_columns", ""),
            "event_types_rowlevel": ";".join(types), "leak_locations_rowlevel": locs if locs != "nan" else "",
            "filename_leak_locations": fname_locs, "filename_vs_label_locations": "MATCH" if fname_locs == file_locs or not fname_locs else f"MISMATCH(file:{fname_locs} labels:{file_locs})",
            "onset_s_verified": onset, "delay_last_active_s": lab.get("CompressorDelay__last_active_s", np.nan),
            "readme_event": r_desc, "readme_onset_s": r_t, "readme_phase": r_phase,
            "onset_vs_readme": "" if r_t is None or pd.isna(onset) else ("MATCH" if float(onset) == float(r_t) else f"DIFFERS(readme {r_t})"),
            "folder_segment_is_phase": "NO (folder name retained as segment_dir only; see LABEL_AND_TIMING_CORRECTIONS.md)",
            "rows_location_without_leak": lab.get("rows_location_without_leak", 0), "rows_multiple_event_types": lab.get("rows_multiple_event_types", 0),
            "candidate_primary_class": cls, "class_note": why, "eligible_primary_candidate": cls in PRIMARY, "status": STATUS,
        })
    man = pd.DataFrame(rows).merge(fam[["Scenario_ID", "family_primary", "family_extended", "family_conservative"]], on="Scenario_ID")
    save(man, out / "CANDIDATE_SCENARIO_MANIFEST.csv")
    save(fam.merge(man[["Scenario_ID", "candidate_primary_class"]], on="Scenario_ID").assign(status=STATUS), out / "CANDIDATE_FAMILY_MAP.csv")

    # ---------------- outer folds (leave-one-topology-out) and validation
    el = man[man["eligible_primary_candidate"]].sort_values("Scenario_ID")
    folds = []
    for k, test_t in enumerate(["Center", "Downstream", "Upstream"], start=1):
        for _, r in el.iterrows():
            folds.append({"outer_fold_id": k, "fold_name": f"LOTO_test_{test_t}", "split_role": "test" if r["topology"] == test_t else "train",
                          "Scenario_ID": r["Scenario_ID"], "target_class": r["candidate_primary_class"], "topology": r["topology"],
                          "family_primary": r["family_primary"], "family_extended": r["family_extended"],
                          "family_conservative": r["family_conservative"], "canonical_clean_file": r["canonical_clean_file"],
                          "canonical_noise_added_file": r["canonical_noise_added_file"], "status": STATUS})
    OF = pd.DataFrame(folds)
    save(OF, out / "CANDIDATE_OUTER_FOLDS.csv")
    # every file of every realization must sit on its scenario's side
    f_of = inv.groupby("candidate_Scenario_ID")["file"].apply(list).to_dict()
    sha_of = dict(zip(inv["file"], inv["sha256"]))
    long = OF.loc[OF.index.repeat(OF["Scenario_ID"].map(lambda s: len(f_of[s])))].copy()
    long["file"] = [f for s in OF["Scenario_ID"] for f in f_of[s]]
    eqv = {f: sha_of[f] for f in long["file"]}  # byte identity across scenarios
    vrows = []
    for view in ("family_primary", "family_extended", "family_conservative"):
        r = validate_outer_folds(long.rename(columns={view: "Scenario_Family_ID"}), required_train_classes=PRIMARY, equivalence=eqv)
        iss = r.issues_frame()
        iss = iss[iss["code"] != "MULTIPLE_FILES_PER_SCENARIO"]  # realizations of one run; one is chosen per experiment
        vrows.append(iss.assign(family_view=view))
        save(r.summary.assign(family_view=view), out / f"FOLD_SUMMARY_{view}.csv")
    V = pd.concat(vrows)
    save(V if len(V) else pd.DataFrame(columns=["fold", "severity", "code", "detail", "family_view"]), out / "CANDIDATE_FOLD_VALIDATION_ISSUES.csv")

    inner = []
    for k, d in OF.groupby("outer_fold_id"):
        tr = d[d["split_role"] == "train"].reset_index(drop=True)
        for scheme, groups, n in (("LOTO_within_train", tr["topology"], tr["topology"].nunique()),
                                  ("grouped_by_family_primary_k3", tr["family_primary"], 3)):
            sp, w = inner_group_splits(groups, tr["target_class"], n, required_classes=PRIMARY)
            for j, (ia, ib) in enumerate(sp):
                inner.append({"outer_fold_id": k, "scheme": scheme, "inner_split": j,
                              "train_scenarios": ";".join(tr.loc[ia, "Scenario_ID"]), "val_scenarios": ";".join(tr.loc[ib, "Scenario_ID"]),
                              "train_classes": ";".join(sorted(set(tr.loc[ia, "target_class"]))),
                              "val_class_counts": json.dumps(tr.loc[ib].groupby("target_class").size().to_dict(), sort_keys=True),
                              "train_missing_classes": ";".join(sorted(set(PRIMARY) - set(tr.loc[ia, "target_class"]))),
                              "feasible": not (set(PRIMARY) - set(tr.loc[ia, "target_class"])), "status": STATUS})
    save(pd.DataFrame(inner), out / "CANDIDATE_INNER_FOLDS.csv")

    counts = (el.groupby("candidate_primary_class").agg(independent_scenarios=("Scenario_ID", "nunique"),
              primary_families=("family_primary", "nunique"), extended_families=("family_extended", "nunique"),
              topologies=("topology", "nunique")).reset_index())
    per_topo = el.groupby(["topology", "candidate_primary_class"]).size().unstack(fill_value=0)
    save(counts, out / "CLASS_FAMILY_COUNTS.csv")
    save(per_topo.reset_index(), out / "CLASS_BY_TOPOLOGY.csv")
    meta = {"status": STATUS, "n_files": int(len(inv)), "n_scenarios": len(scen), "n_eligible": int(len(el)),
            "cross_topology_pairs": int(cross_total), "cross_topology_pairs_with_shared_rows": int(cross_shared),
            "dependent_edges": len(dep_edges), "short_segment_edges": len(ext_edges), "min_dependent_rows": MIN_DEPENDENT_ROWS,
            "validation_issue_rows": int(len(V)), "order": "deterministic"}
    # write bytes, not text: Path.write_text translates "\n" to the platform line separator
    # (CRLF on Windows), which made BUILD_SUMMARY.json/OUTPUT_HASHES.json platform-dependent
    (out / "BUILD_SUMMARY.json").write_bytes((json.dumps(meta, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob("*")) if p.suffix in (".csv", ".json") and p.name != "OUTPUT_HASHES.json"}
    (out / "OUTPUT_HASHES.json").write_bytes((json.dumps(hashes, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    print(json.dumps(meta, indent=2))
    print(counts.to_string())
    print(per_topo.to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
