#!/usr/bin/env python3
"""
Read-only root-cause diagnostic of development arm H_POSITION_MATCHED (EXPLORATORY_DIAGNOSTIC).

Inputs (never modified): H's stored development predictions (folds/fold_k/dev_oof.parquet, verified against the
hash list first), the candidate manifest v0.3, the position map v0.1 and the window feature table rebuilt with
the candidate settings (or a cached copy of exactly that table). No classifier, calibrator or meta-model is fitted;
nothing is tuned. Geometry uses the same standardisation and k as D(x) (training-topology mean/sd, k = 25).

Inner design reproduced from the runner: in outer fold k the two development topologies predict each other
(topology-held-out); the stored prediction for topology t comes from a model trained on the OTHER development
topology only.

Writes 03_results/diagnostics/arm_h_failures/:
  EVENT_OBSERVABILITY.csv     clean-signal difference of every event run to its own-model NORMAL run (noise-sigma units)
  LEAK_TO_NORMAL_TIME_PROFILE.csv  per 1000 s: classifier NORMAL calls vs clean-signal event visibility
  NORMAL_TRACE.csv            per fold x held-out topology: NORMAL predictions, confidence, D, training support
  NEAREST_CLASS_GEOMETRY.csv  per fold x held-out topology x true class: nearest training window by class
  NEIGHBOUR_COMPOSITION.csv   k=25 training neighbours of the held-out NORMAL / G5G6 error windows (class, scenario)
  SHIFT_VS_SEPARATION.csv     per canonical channel: cross-topology NORMAL shift vs within-topology NORMAL-LEAK gap
  LEAK_TO_NORMAL_TRACE.csv    the LEAK->NORMAL windows with time since onset and geometry
  DECISION_REPRODUCTION.csv   matched selection at the development target per method (validated against stored metrics)
  DX_DIAGNOSTIC.csv           correlation / saturation / conditional AUROC of D(x)
  SUMMARY.json
Usage: python tools/experiments/diagnose_h_failures.py [cached_feature_table.parquet]
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy.spatial.distance import cdist
from scipy.stats import spearmanr

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from h2prism.evaluation_metrics import auroc  # noqa: E402
from h2prism.experiments import primary_protocol as pp  # noqa: E402
from h2prism.independence import ancestor, independence_groups  # noqa: E402
from h2prism.position_map import apply_position_map, load_position_map  # noqa: E402

ARM = "H_POSITION_MATCHED"
RUN = REPO / "03_results" / "ablation_runs" / ARM
HASHES = REPO / "03_results" / "ablation_runs" / "logs" / "H_POSITION_MATCHED_65f05249dd12_OUTPUT_HASHES.sha256"
CFG = REPO / "06_audit_preparation" / "protocol2" / "arms" / f"{ARM}.yaml"
OUT = REPO / "03_results" / "diagnostics" / "arm_h_failures"
K = 25
TAU_CONF = 0.9


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def verify_inputs():
    for line in HASHES.read_text(encoding="utf-8").splitlines():
        h, name = line.split(maxsplit=1)
        if _sha(RUN / name.lstrip("*")) != h:
            raise SystemExit(f"stored H output changed: {name}")


def load():
    cfg = yaml.safe_load(CFG.read_text(encoding="utf-8"))
    cache = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if cache and cache.exists():
        ft = pd.read_parquet(cache)
    else:
        ft, _ = pp.build_features(cfg, REPO, REPO / "data" / "raw", cfg["dataset"]["realization_primary"])
    pm = load_position_map(REPO / cfg["features"]["position_map"]["file"], cfg["features"]["position_map"]["sha256"])
    ft = apply_position_map(ft, pm, cfg["features"]["statistics"])
    feats = [f"{c}__{s}" for c in cfg["features"]["channels"] for s in cfg["features"]["statistics"]]
    O = pd.concat([pd.read_parquet(f) for f in sorted(RUN.glob("folds/fold_*/dev_oof.parquet"))], ignore_index=True)
    man = pd.read_csv(REPO / cfg["dataset"]["manifest"]["file"])
    return cfg, ft, feats, O, man


def standardize(train: np.ndarray, *others):
    mu, sd = train.mean(0), train.std(0)
    sd = np.where(sd > 0, sd, 1.0)
    return [(x - mu) / sd for x in (train, *others)]


def nearest(Zq, Zr, chunk=2000):
    out = np.empty(len(Zq))
    for a in range(0, len(Zq), chunk):
        out[a:a + chunk] = cdist(Zq[a:a + chunk], Zr).min(1)
    return out


def observability(cfg, man) -> pd.DataFrame:
    """Signal-level check on the CLEAN realization (no noise): for every eligible event run, the difference to the
    NORMAL run of the SAME source model at identical timestamps, per canonical (position-matched) channel, in units
    of that channel's added-noise sigma (noise_added - clean of the NORMAL run). Before onset the difference measures
    operating-condition mismatch; after onset it measures how visible the event is to the sensors."""
    raw = REPO / "data" / "raw"
    pm = load_position_map(REPO / cfg["features"]["position_map"]["file"])
    src = {(r.canonical_channel, r.topology): r.source_channel for r in pm.itertuples()}
    chans = cfg["features"]["channels"]
    e = man[man.eligible_primary.astype(bool)]
    normal = e[e.label_mapped == "NORMAL"].set_index("topology_source_model")
    rows = []
    cache = {}
    zmax = {}  # per event run: max over channels of |z| at each timestamp (clean signals)

    def read(p):
        if p not in cache:
            cache[p] = pd.read_parquet(raw / p)
        return cache[p]

    for t, nrow in normal.iterrows():
        nc, nn = read(nrow.file_clean), read(nrow.file_noise_added)
        sig = {c: float((nn[src[(c, t)]] - nc[src[(c, t)]]).std()) for c in chans}
        for r in e[(e.topology_source_model == t) & (e.label_mapped != "NORMAL")].itertuples():
            ec = read(r.file_clean)
            idx = ec.index.intersection(nc.index)
            ev = ec.loc[idx, "label_anomaly"].to_numpy() == 1
            z = pd.DataFrame({c: (ec.loc[idx, src[(c, t)]] - nc.loc[idx, src[(c, t)]]).to_numpy() / sig[c] for c in chans})
            post, pre = z[ev].abs(), z[~ev].abs()
            zmax[r.Scenario_ID] = pd.Series(z.abs().max(axis=1).to_numpy(), index=idx).where(ev)
            top = post.median().sort_values(ascending=False)
            rows.append({"Scenario_ID": r.Scenario_ID, "source_model": t, "class": r.label_mapped,
                         "independence_group": r.independence_group, "n_event_rows": int(ev.sum()),
                         # original statistic (kept for reproducibility): maximum over all pre-event rows and channels.
                         # It is dominated by the start-up transient (t < ~500 s), where any two runs differ strongly.
                         "pre_event_max_abs_z": float(pre.max().max()) if len(pre) else np.nan,
                         # ADDITIONAL robust descriptive statistic: per-channel median over pre-event rows, max channel
                         "pre_event_median_abs_z_top_channel": float(pre.median().max()) if len(pre) else np.nan,
                         "pre_event_share_rows_any_channel_abs_z_gt_3": float((pre > 3).any(axis=1).mean()) if len(pre) else np.nan,
                         "event_median_abs_z_top_channel": float(top.iloc[0]), "event_top_channel": top.index[0],
                         "event_median_abs_z_second_channel": float(top.iloc[1]), "event_second_channel": top.index[1],
                         "event_share_rows_any_channel_abs_z_gt_3": float((post > 3).any(axis=1).mean()),
                         "event_share_rows_any_channel_abs_z_gt_1": float((post > 1).any(axis=1).mean())})
    return pd.DataFrame(rows).sort_values("event_median_abs_z_top_channel"), zmax


def main() -> int:
    verify_inputs()
    cfg, ft, feats, O, man = load()
    if set(O.window_id) - set(ft.window_id):
        raise SystemExit("dev_oof windows absent from the feature table: inputs are not the H inputs")
    ft = ft.set_index("window_id")
    grp = independence_groups(man.Scenario_ID, man.Scenario_Family_ID)
    onset = dict(zip(man.Scenario_ID, man.onset_s))
    OUT.mkdir(parents=True, exist_ok=True)
    trace, geom, comp, shift, l2n, dec, dx = [], [], [], [], [], [], []
    pol = pp._policies(cfg)["primary"]
    salt = str(pp._matched_cfg(cfg)["tie_break_salt"])
    stored = pd.read_csv(RUN / "DEV_DECISION_METRICS.csv")

    for (k, t), q in O.groupby(["fold", "topology"]):
        other = [x for x in O[O.fold == k].topology.unique() if x != t][0]
        tr = ft.loc[O[(O.fold == k) & (O.topology == other)].window_id]  # training data of the model that predicted t
        te = ft.loc[q.window_id]
        Ztr, Zte = standardize(tr[feats].to_numpy(float), te[feats].to_numpy(float))
        ytr, yte = tr.label_mapped.to_numpy(), te.label_mapped.to_numpy()

        # ---- training support of the model that predicted topology t
        sup = tr.groupby("label_mapped").agg(windows=("Scenario_ID", "size"), runs=("Scenario_ID", "nunique"))
        sup["independence_groups"] = tr.groupby("label_mapped").Scenario_ID.apply(lambda s: s.map(grp).nunique())
        n = q[q.label_mapped == "NORMAL"]
        trace.append({"fold": k, "heldout_topology": t, "training_topology": other,
                      "normal_windows": len(n), "normal_pred_LEAK": int((n.y_hat == "LEAK").sum()),
                      "normal_pred_other": int(((n.y_hat != "LEAK") & (n.y_hat != "NORMAL")).sum()),
                      "normal_recall": float((n.y_hat == "NORMAL").mean()),
                      "normal_conf_median": n.score_confidence.median(),
                      "normal_share_conf_ge_0_9": float((n.score_confidence >= TAU_CONF).mean()),
                      "normal_D_median": n.score_D_only.median(),
                      "normal_flag_free": float((n.support_flags.fillna("") == "").mean()),
                      **{f"train_{c}_{m}": int(sup.loc[c, m]) if c in sup.index else 0
                         for c in ("NORMAL", "LEAK", "COMPRESSOR_FAULT", "COMPRESSOR_DELAY")
                         for m in ("windows", "runs", "independence_groups")}})

        # ---- nearest training window per class (same standardisation as D(x))
        for cls in ("NORMAL", "LEAK"):
            m = yte == cls
            if not m.any():
                continue
            dN = nearest(Zte[m], Ztr[ytr == "NORMAL"])
            dL = nearest(Zte[m], Ztr[ytr == "LEAK"])
            geom.append({"fold": k, "heldout_topology": t, "true_class": cls, "n": int(m.sum()),
                         "median_nn_dist_train_NORMAL": float(np.median(dN)), "median_nn_dist_train_LEAK": float(np.median(dL)),
                         "share_nearer_to_LEAK": float((dL < dN).mean())})
            # reference scale: nearest-neighbour distance of a training window of the same class to its own run's windows
            same = Ztr[ytr == cls]
            dd = cdist(same[:: max(1, len(same) // 300)], same)
            dd[dd == 0] = np.inf
            geom[-1][f"median_nn_dist_within_training_{cls}"] = float(np.median(dd.min(1)))

        # ---- k=25 neighbour composition of held-out NORMAL windows and of LEAK->NORMAL windows
        sel_sets = {"NORMAL_true": (yte == "NORMAL"),
                    "LEAK_pred_NORMAL": (yte == "LEAK") & (q.y_hat.to_numpy() == "NORMAL")}
        for name, m in sel_sets.items():
            if not m.any():
                continue
            d = cdist(Zte[m], Ztr)
            nn = np.argsort(d, 1)[:, :K]
            cls_counts = pd.Series(ytr[nn.ravel()]).value_counts(normalize=True)
            scen = pd.Series(tr.Scenario_ID.to_numpy()[nn.ravel()]).value_counts(normalize=True).head(5)
            comp.append({"fold": k, "heldout_topology": t, "query_set": name, "n_query": int(m.sum()),
                         **{f"neighbour_share_{c}": float(cls_counts.get(c, 0.0)) for c in
                            ("NORMAL", "LEAK", "COMPRESSOR_FAULT", "COMPRESSOR_DELAY")},
                         "top_neighbour_scenarios": ";".join(f"{s}:{v:.3f}" for s, v in scen.items()),
                         "n_distinct_neighbour_ancestors": int(pd.Series(tr.Scenario_ID.to_numpy()[nn.ravel()]).map(ancestor).nunique()),
                         # per window: does the k-NN majority class disagree with the classifier label?
                         "share_windows_knn_majority_differs_from_classifier": float(np.mean(
                             [pd.Series(ytr[row]).value_counts().idxmax() != yh for row, yh in zip(nn, q.y_hat.to_numpy()[m])])),
                         "share_windows_knn_majority_is_true_class": float(np.mean(
                             [pd.Series(ytr[row]).value_counts().idxmax() == yt for row, yt in zip(nn, yte[m])]))})

        # ---- LEAK -> NORMAL windows
        m = (yte == "LEAK") & (q.y_hat.to_numpy() == "NORMAL")
        if m.any():
            dN = nearest(Zte[m], Ztr[ytr == "NORMAL"])
            dL = nearest(Zte[m], Ztr[ytr == "LEAK"])
            sub = q[m].assign(start_time=te.start_time.to_numpy()[m], nn_train_NORMAL=dN, nn_train_LEAK=dL)
            for sid, g in sub.groupby("Scenario_ID"):
                allw = q[q.Scenario_ID == sid]
                l2n.append({"fold": k, "heldout_topology": t, "Scenario_ID": sid, "independence_group": grp.get(sid),
                            "n_LEAK_to_NORMAL": len(g), "n_windows_of_run": len(allw),
                            "share_conf_ge_0_9": float((g.score_confidence >= TAU_CONF).mean()),
                            "onset_s": onset.get(sid), "start_time_min": g.start_time.min(), "start_time_max": g.start_time.max(),
                            "seconds_after_onset_min": g.start_time.min() - onset.get(sid, np.nan),
                            "seconds_after_onset_max": g.start_time.max() - onset.get(sid, np.nan),
                            "run_event_start_time_min": te.start_time[te.Scenario_ID == sid].min(),
                            "run_event_start_time_max": te.start_time[te.Scenario_ID == sid].max(),
                            "median_nn_dist_train_NORMAL": float(g.nn_train_NORMAL.median()), "median_nn_dist_train_LEAK": float(g.nn_train_LEAK.median()),
                            "share_nearer_to_train_NORMAL": float((g.nn_train_NORMAL < g.nn_train_LEAK).mean())})

        # ---- matched selection at the stored development target (reproduction, then comparison)
        st = stored[(stored.fold == k) & (stored.dev_topology == t) & (stored.status == "ESTIMABLE")]
        if len(st):
            target = float(st.target.iloc[0])
            av = pp._available(np.zeros(len(q)), q.support_flags.fillna("").to_numpy(), pol)
            masks = {}
            for meth in ("s_C", "s_C_minus_D", "confidence"):
                sc = q[f"score_{meth}"].to_numpy(float)
                mask, info = pp.exact_count_selection(sc, av & np.isfinite(sc), q.window_id.to_numpy(), target, salt)
                masks[meth] = mask
                wrong = mask & ~q.correct.to_numpy(bool)
                g = q.Scenario_ID.map(grp).to_numpy()
                per_g = pd.DataFrame({"g": g[mask], "w": wrong[mask]}).groupby("g").w.mean()
                s_row = st[st.method == meth].iloc[0]
                dec.append({"fold": k, "heldout_topology": t, "method": meth, "target": target,
                            "n_selected": int(mask.sum()), "n_wrong": int(wrong.sum()),
                            "stored_n_wrong_specific": int(s_row.n_wrong_specific),
                            "reproduced": int(wrong.sum()) == int(s_row.n_wrong_specific) and int(mask.sum()) == int(s_row.n_specific),
                            "groups_selected": int(per_g.size), "groups_with_any_error": int((per_g > 0).sum()),
                            "group_balanced_risk": float(per_g.mean()),
                            "stored_group_balanced_risk": float(s_row.group_balanced_selective_risk),
                            "NORMAL_group_selected_windows": int((mask & (q.label_mapped.to_numpy() == "NORMAL")).sum()),
                            "NORMAL_group_risk": float(per_g.get("IG_NORMAL_RUN_NORMALITY", np.nan)),
                            "risk_excluding_NORMAL_group": float(per_g.drop("IG_NORMAL_RUN_NORMALITY", errors="ignore").mean()),
                            "per_group_risk": ";".join(f"{a}:{b:.3f}" for a, b in per_g.items() if b > 0)})
            a, b = masks["s_C"], masks["s_C_minus_D"]
            ok = q.correct.to_numpy(bool)
            y = q.label_mapped.to_numpy()
            dx.append({"fold": k, "heldout_topology": t, "kind": "selection_change_s_C_vs_s_C_minus_D",
                       "jaccard_selected": float((a & b).sum() / (a | b).sum()),
                       "only_s_C": int((a & ~b).sum()), "only_s_C_minus_D": int((b & ~a).sum()),
                       "only_s_C_wrong": int((a & ~b & ~ok).sum()), "only_s_C_minus_D_wrong": int((b & ~a & ~ok).sum()),
                       "only_s_C_NORMAL": int((a & ~b & (y == "NORMAL")).sum()),
                       "only_s_C_minus_D_NORMAL": int((b & ~a & (y == "NORMAL")).sum())})

        # ---- D(x) relation to the other scores (no fitting)
        ok = q.correct.to_numpy(bool)
        D, C = q.score_D_only.to_numpy(float), q.score_confidence.to_numpy(float)
        hi = C >= np.quantile(C, 0.4)  # the confidence-top 60% (the region a 0.6 target selects from)
        dx.append({"fold": k, "heldout_topology": t, "kind": "score_relations",
                   "spearman_D_confidence": spearmanr(D, C).statistic,
                   "spearman_s_C_s_C_minus_D": spearmanr(q.score_s_C, q.score_s_C_minus_D, nan_policy="omit").statistic,
                   "spearman_s_C_D": spearmanr(q.score_s_C, D, nan_policy="omit").statistic,
                   "spearman_s_C_confidence": spearmanr(q.score_s_C, C, nan_policy="omit").statistic,
                   "D_saturation_share_at_1": float((D >= 1 - 1e-12).mean()),
                   "D_saturation_among_errors": float((D[~ok] >= 1 - 1e-12).mean()) if (~ok).any() else np.nan,
                   "auroc_D": auroc(D, ok), "auroc_confidence": auroc(C, ok),
                   "auroc_D_within_conf_top60": auroc(D[hi], ok[hi]),
                   "auroc_D_within_NORMAL_true": auroc(D[y == "NORMAL"], ok[y == "NORMAL"]) if (y == "NORMAL").any() else np.nan,
                   "auroc_D_excluding_NORMAL_true": auroc(D[y != "NORMAL"], ok[y != "NORMAL"]),
                   "share_errors_from_NORMAL": float(((y == "NORMAL") & ~ok).sum() / max((~ok).sum(), 1))})

    # ---- cross-topology NORMAL shift vs within-topology NORMAL-LEAK separation (window means, canonical channels)
    chans = cfg["features"]["channels"]
    for ch in chans:
        c = f"{ch}__mean"
        nm = ft[ft.label_mapped == "NORMAL"].groupby("topology")[c].agg(["mean", "std"])
        lk = ft[ft.label_mapped == "LEAK"].groupby("topology")[c].agg(["mean", "std"])
        sd = np.sqrt((nm["std"] ** 2).mean())  # within-NORMAL-run spread (noise + operating profile)
        row = {"channel": ch}
        for t in nm.index:
            row[f"NORMAL_mean_{t}"] = nm.loc[t, "mean"]
            row[f"LEAK_mean_{t}"] = lk.loc[t, "mean"]
            row[f"NORMAL_minus_LEAK_{t}_in_NORMAL_sd"] = (nm.loc[t, "mean"] - lk.loc[t, "mean"]) / sd if sd > 0 else np.nan
        row["max_cross_topology_NORMAL_shift_in_NORMAL_sd"] = (nm["mean"].max() - nm["mean"].min()) / sd if sd > 0 else np.nan
        row["within_NORMAL_run_sd"] = sd
        shift.append(row)

    obs, zmax = observability(cfg, man)
    # time profile of the runs with LEAK->NORMAL errors: is the event still visible in the clean signal when the
    # classifier says NORMAL? (bins of 1000 s of window start time; window = 60 s)
    prof = []
    for r in l2n:
        sid, k, t = r["Scenario_ID"], r["fold"], r["heldout_topology"]
        q = O[(O.fold == k) & (O.topology == t) & (O.Scenario_ID == sid)]
        st = ft.loc[q.window_id, "start_time"].to_numpy()
        zm = zmax[sid]
        win_z = np.array([np.nanmedian(zm.loc[a:a + 59].to_numpy()) for a in st])
        b = (st // 1000 * 1000).astype(int)
        for bb in sorted(set(b)):
            m = b == bb
            prof.append({"fold": k, "heldout_topology": t, "Scenario_ID": sid, "window_start_bin_s": bb,
                         "n_windows": int(m.sum()), "n_pred_NORMAL": int((q.y_hat.to_numpy()[m] == "NORMAL").sum()),
                         "n_pred_NORMAL_conf_ge_0_9": int(((q.y_hat.to_numpy()[m] == "NORMAL") &
                                                           (q.score_confidence.to_numpy()[m] >= TAU_CONF)).sum()),
                         "median_clean_event_visibility_max_channel_z": float(np.nanmedian(win_z[m]))})
    out = {"EVENT_OBSERVABILITY": obs.to_dict("records"), "LEAK_TO_NORMAL_TIME_PROFILE": prof, "NORMAL_TRACE": trace, "NEAREST_CLASS_GEOMETRY": geom, "NEIGHBOUR_COMPOSITION": comp,
           "SHIFT_VS_SEPARATION": shift, "LEAK_TO_NORMAL_TRACE": l2n, "DECISION_REPRODUCTION": dec, "DX_DIAGNOSTIC": dx}
    for name, rows in out.items():
        pd.DataFrame(rows).assign(evidence_status="EXPLORATORY_DIAGNOSTIC").to_csv(
            OUT / f"{name}.csv", index=False, lineterminator="\n", float_format="%.6g")
    D = pd.DataFrame(dec)
    summ = {"arm": ARM, "run_key": "65f05249dd12", "evidence_status": "EXPLORATORY_DIAGNOSTIC",
            "inputs_verified_against_hash_list": True, "model_fitted": False, "tuned": False,
            "decision_reproduction_all_match": bool(D.reproduced.all()) if len(D) else None,
            "per_class_probabilities_stored": False,
            "note": "per-class probabilities are not stored in dev_oof; probability analyses use stored confidence/margin only"}
    (OUT / "SUMMARY.json").write_text(json.dumps(summ, indent=2), encoding="utf-8")
    pd.set_option("display.width", 250, "display.max_columns", 50, "display.max_colwidth", 120)
    for name, rows in out.items():
        print("==", name)
        print(pd.DataFrame(rows).to_string(index=False))
    print(summ)
    return 0


if __name__ == "__main__":
    sys.exit(main())
