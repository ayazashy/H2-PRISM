#!/usr/bin/env python3
"""
Root-cause diagnostic for the OUT_OF_SUPPORT rate of the down source model (EXPLORATORY_DIAGNOSTIC).

What it does (no classifier is fitted, no class is predicted, no performance is scored):
  1. Builds the window feature table once with the candidate protocol 2.0 settings (manifest v0.3 source-model
     topology, noise_added realization) -- the same table the ablation arms used.
  2. Per source model, the mean of each channel's window means (descriptive), and, for every channel name, the
     standardized mean difference of the down model vs center/up.
  3. Recomputes ONLY the unsupervised support geometry used by the OUT_OF_SUPPORT flag (k-NN mean distance in
     reference-standardized feature space vs the reference's leave-one-family-out 99th percentile) for every ordered
     pair (reference model -> query model), under three channel representations:
       NAME_MATCHED_13     PS1-PS10, MFS1-MFS3 by release column name (arms C/G1)
       POSITION_MATCHED_12 the 12 sensor blocks present in all three diagrams (SENSOR_CORRESPONDENCE.csv); down-model
                           columns are read under the name that the down model logs for that block
       SHARED_NODE_<n>     only the blocks whose node neighbourhood is identical in all three diagrams
  4. Per channel group, the share of the query-to-reference distance that each channel contributes.
The position mapping comes from the diagrams alone (tools/dataset/trace_slx_sensors.py); signal values never choose it.

Writes 03_results/diagnostics/out_of_support/{CHANNEL_SHIFT.csv, SUPPORT_BY_REPRESENTATION.csv,
DISTANCE_CONTRIBUTION.csv, DEV_OOS_BY_FOLD.csv, SUMMARY.json}.
Usage: python tools/experiments/diagnose_out_of_support.py [cached_feature_table.parquet]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from h2prism.distinguishability import EmpiricalSupport  # noqa: E402
from h2prism.experiments import primary_protocol as pp  # noqa: E402

CFG = REPO / "06_audit_preparation" / "protocol2" / "CANDIDATE_PROTOCOL_2_0.yaml"
CORR = REPO / "03_results" / "diagnostics" / "sensor_correspondence" / "SENSOR_CORRESPONDENCE.csv"
OUT = REPO / "03_results" / "diagnostics" / "out_of_support"
RUNS = REPO / "03_results" / "ablation_runs"
STATS = ["mean", "std", "min", "max", "range", "last_minus_first", "slope", "mean_abs_diff"]
MODEL_OF = {"Center": "center", "Downstream": "down", "Upstream": "up"}
NAME13 = [f"PS{i}" for i in range(1, 11)] + ["MFS1", "MFS2", "MFS3"]


def position_maps(corr: pd.DataFrame):
    """canonical block -> {model: column name}, for blocks logged in all three models."""
    c = corr[corr.logged.astype(bool)].copy()
    c["sensor_block_sid"] = c.sensor_block_sid.astype(int)
    blocks = {}
    for sid, g in c.groupby("sensor_block_sid"):
        if set(g.model) == {"center", "down", "up"}:
            blocks[sid] = dict(zip(g.model, g.sensor_id))
    shared_node = set()
    for sid, m in blocks.items():
        rows = c[c.sensor_block_sid == sid]
        if rows.physical_node_adjacent_components.nunique() == 1:
            shared_node.add(sid)
    return blocks, shared_node


def remapped(ft: pd.DataFrame, blocks: dict, keep: set) -> tuple[pd.DataFrame, list]:
    """Feature matrix with one column group per canonical block; each row reads its own model's column name."""
    model = ft.topology.map(MODEL_OF)
    cols = {}
    for sid in sorted(keep):
        for st in STATS:
            v = np.full(len(ft), np.nan)
            for mdl, name in blocks[sid].items():
                m = (model == mdl).to_numpy()
                v[m] = ft.loc[m, f"{name}__{st}"].to_numpy(float)
            cols[f"B{sid}__{st}"] = v
    X = pd.DataFrame(cols, index=ft.index)
    return X, list(X.columns)


def support_from(cfg, ft, X, feats, ref_model):
    """One reference model: threshold from its own leave-one-family-out distances (exactly as
    EmpiricalSupport.fit_out_of_support_threshold), then the share above it for every query model."""
    topo = ft.topology.map(MODEL_OF)
    R = ft[topo == ref_model]
    Xr = X.loc[R.index, feats].to_numpy(float)
    es = EmpiricalSupport(pp._dconfig(cfg)).fit(Xr, R.label_mapped, R.Scenario_Family_ID, R.Scenario_ID,
                                               cfg["dataset"]["classes"])
    lofo = es.development_support()["mean_neighbor_distance"].astype(float)
    thr = float(np.quantile(lofo.dropna().to_numpy(), cfg["distinguishability"]["out_of_support_quantile"]))
    out = {}
    for q_model in ("center", "down", "up"):
        Q = ft[topo == q_model]
        if q_model == ref_model:
            d = lofo
        else:
            d = es.compute(X.loc[Q.index, feats].to_numpy(float),
                           query_families=Q.Scenario_Family_ID.to_numpy())["mean_neighbor_distance"].astype(float)
        Zq = (X.loc[Q.index, feats].to_numpy(float) - es.mu_) / es.sigma_  # descriptive per-channel contribution
        contrib = pd.Series((Zq ** 2).mean(axis=0), index=feats)
        out[q_model] = ({"threshold": thr, "share_out_of_support": float((d > thr).mean()),
                         "median_mean_knn_distance": float(d.median()), "n_query": int(len(d))}, contrib)
    return out


def main() -> int:
    cfg = yaml.safe_load(CFG.read_text(encoding="utf-8"))
    corr = pd.read_csv(CORR)
    blocks, shared = position_maps(corr)
    cache = Path(sys.argv[1]) if len(sys.argv) > 1 else None  # optional cached feature table (same config) to save time
    if cache and cache.exists():
        ft = pd.read_parquet(cache)
    else:
        ft, _ = pp.build_features(cfg, REPO, REPO / "data" / "raw", cfg["dataset"]["realization_primary"])
    model = ft.topology.map(MODEL_OF)
    OUT.mkdir(parents=True, exist_ok=True)

    # 2. channel shift by name (descriptive)
    rows = []
    for ch in sorted({c.rsplit("__", 1)[0] for c in ft.columns if c.endswith("__mean")}):
        col = f"{ch}__mean"
        r = {"channel_name": ch}
        for m in ("center", "down", "up"):
            r[f"{m}_mean_of_window_means"] = float(ft.loc[model == m, col].mean())
        cu = ft.loc[model != "down", col]
        dn = ft.loc[model == "down", col]
        pooled = np.sqrt((cu.var() + dn.var()) / 2)
        r["std_mean_diff_down_vs_center_up"] = float((dn.mean() - cu.mean()) / pooled) if pooled > 0 else np.nan
        r["evidence_status"] = "DESCRIPTIVE_NOT_USED_FOR_MAPPING"
        rows.append(r)
    pd.DataFrame(rows).to_csv(OUT / "CHANNEL_SHIFT.csv", index=False, lineterminator="\n", float_format="%.6g")

    # 3. support geometry under three representations
    reps = {}
    X13 = ft[[f"{n}__{s}" for n in NAME13 for s in STATS]]
    reps["NAME_MATCHED_13"] = (X13, list(X13.columns))
    reps["POSITION_MATCHED_12"] = remapped(ft, blocks, set(blocks))
    reps[f"SHARED_NODE_{len(shared)}"] = remapped(ft, blocks, shared)
    S, Cn = [], []
    for rep, (X, feats) in reps.items():
        for a in ("center", "down", "up"):
            for b, (s, contrib) in support_from(cfg, ft, X, feats, a).items():
                S.append({"representation": rep, "n_features": len(feats), "reference_model": a, "query_model": b, **s})
                ch = contrib.groupby(lambda c: c.rsplit("__", 1)[0]).sum()
                for k, v in (ch / ch.sum()).items():
                    Cn.append({"representation": rep, "reference_model": a, "query_model": b, "channel": k,
                               "share_of_squared_standardized_distance": float(v)})
    S = pd.DataFrame(S).assign(evidence_status="EXPLORATORY_DIAGNOSTIC")
    S.to_csv(OUT / "SUPPORT_BY_REPRESENTATION.csv", index=False, lineterminator="\n", float_format="%.6g")
    pd.DataFrame(Cn).to_csv(OUT / "DISTANCE_CONTRIBUTION.csv", index=False, lineterminator="\n", float_format="%.6g")

    # flag composition of the stored development predictions (existing outputs, no recomputation)
    D = []
    for arm in ("A_P11_DEV", "B_TOPOLOGY", "C_COMMON_SENSORS", "G1_DATA_CORRECTIONS"):
        for f in sorted((RUNS / arm).glob("folds/fold_*/dev_oof.parquet")):
            o = pd.read_parquet(f)
            for t, g in o.groupby("topology"):
                D.append({"arm_id": arm, "fold": int(g.fold.iloc[0]), "dev_topology": t, "n": len(g),
                          "share_out_of_support": float(g.support_flags.fillna("").str.contains("OUT_OF_SUPPORT").mean())})
    pd.DataFrame(D).to_csv(OUT / "DEV_OOS_BY_FOLD.csv", index=False, lineterminator="\n", float_format="%.6g")
    summ = {"evidence_status": "EXPLORATORY_DIAGNOSTIC", "classifier_fitted": False, "performance_scored": False,
            "position_mapping_source": "SENSOR_CORRESPONDENCE.csv (diagram identity only)",
            "blocks_in_all_models": {str(k): v for k, v in sorted(blocks.items())},
            "blocks_with_identical_node": sorted(int(x) for x in shared), "n_windows": int(len(ft))}
    (OUT / "SUMMARY.json").write_text(json.dumps(summ, indent=2), encoding="utf-8")
    pd.set_option("display.width", 250)
    print(S.pivot_table(index=["reference_model", "query_model"], columns="representation", values="share_out_of_support"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
