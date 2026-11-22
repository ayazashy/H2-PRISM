#!/usr/bin/env python3
"""
Arm H NORMAL<->LEAK root cause, part 2: signal-level profiles, offsets vs signatures, distinguishability, and
errors grouped by independent scenario ancestor (EXPLORATORY_DIAGNOSTIC; read-only; no model is fitted).

Inputs (never modified): H's development predictions (verified against the H hash list), manifest v0.3, position map
v0.1, the raw CLEAN and NOISE_ADDED series of every eligible run, and the window feature table rebuilt with the
candidate settings (or a cached copy of exactly that table, passed as argv[1]). Each development prediction for
topology t comes from the classifier trained on the other development topology of its fold (see the runner).

Definitions (fixed here, before looking at results of this script):
  noise sigma (per model x canonical channel) = std(noise_added - clean) of that model's NORMAL run (per sample);
  window-mean noise sigma = noise sigma / sqrt(60) (white noise, 60 one-second samples per window);
  steady period = 1000 s <= t < 19000 s (excludes the start-up transient and the end-of-run decay);
  onset signature = mean over [onset+60, onset+660) minus mean over [onset-600, onset) of the event run (clean);
  diff to NORMAL = event run minus the SAME source model's NORMAL run at identical timestamps;
  "low-visibility" run = clean post-onset median |diff to NORMAL| < 2 noise sigma on every canonical channel
                         (read from EVENT_OBSERVABILITY.csv, produced by diagnose_h_failures.py).

Writes 03_results/diagnostics/arm_h_failures/:
  ONSET_PROFILE.csv, OFFSET_VS_SIGNATURE.csv, DISTINGUISHABILITY.csv, ERROR_BY_ANCESTOR.csv,
  ERROR_INDEPENDENT_SUMMARY.csv, ERROR_TAXONOMY.csv, STATEMENT_VERIFICATION.csv, SIGNALS_SUMMARY.json
Usage: python tools/experiments/diagnose_h_signals.py [cached_feature_table.parquet]
"""

from __future__ import annotations

import json
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy.spatial.distance import cdist

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tools" / "experiments"))

import diagnose_h_failures as hf  # noqa: E402  (reuses the hash check, loading and standardisation)
from h2prism.independence import ancestor  # noqa: E402
from h2prism.position_map import load_position_map  # noqa: E402

OUT = hf.OUT
RAW = REPO / "data" / "raw"
STEADY = (1000, 19000)
WIN = 60
LOW_VIS_Z = 2.0
K = hf.K


def _read(cache, p):
    if p not in cache:
        cache[p] = pd.read_parquet(RAW / p)
    return cache[p]


def signals(cfg, man):
    """Onset profiles (clean and noisy) and noise sigmas per model x canonical channel."""
    pm = load_position_map(REPO / cfg["features"]["position_map"]["file"])
    src = {(r.canonical_channel, r.topology): r.source_channel for r in pm.itertuples()}
    chans = cfg["features"]["channels"]
    e = man[man.eligible_primary.astype(bool)]
    normal = e[e.label_mapped == "NORMAL"].set_index("topology_source_model")
    cache, rows, sig = {}, [], {}
    for t, nrow in normal.iterrows():
        nc, nn = _read(cache, nrow.file_clean), _read(cache, nrow.file_noise_added)
        for c in chans:
            sig[(t, c)] = float((nn[src[(c, t)]] - nc[src[(c, t)]]).std())
    for r in e[e.label_mapped != "NORMAL"].itertuples():
        t = r.topology_source_model
        for real, col in (("clean", "file_clean"), ("noise_added", "file_noise_added")):
            ev, nr = _read(cache, getattr(r, col)), _read(cache, getattr(normal.loc[t], col))
            on = ev.index[ev.label_anomaly == 1]
            if not len(on):
                continue
            t0 = float(on[0])
            for c in chans:
                s = src[(c, t)]
                x, n = ev[s], nr[s]

                def seg(series, a, b):
                    v = series[(series.index >= a) & (series.index < b)]
                    return float(v.mean()) if len(v) else np.nan

                pre_a = max(0.0, t0 - 600)
                rows.append({"Scenario_ID": r.Scenario_ID, "independence_group": r.independence_group,
                             "ancestor": ancestor(r.Scenario_ID), "source_model": t, "class": r.label_mapped,
                             "realization": real, "channel": c, "source_column": s, "onset_s": t0,
                             "pre_window_s": t0 - pre_a,
                             "run_pre": seg(x, pre_a, t0), "run_onset": seg(x, t0 + 60, t0 + 660),
                             "run_post_steady": seg(x, max(t0 + 600, STEADY[0]), STEADY[1]),
                             "normal_pre": seg(n, pre_a, t0), "normal_post_steady": seg(n, max(t0 + 600, STEADY[0]), STEADY[1]),
                             "noise_sigma_sample": sig[(t, c)]})
    P = pd.DataFrame(rows)
    P["onset_signature"] = P.run_onset - P.run_pre
    P["diff_to_normal_pre"] = P.run_pre - P.normal_pre
    P["diff_to_normal_post"] = P.run_post_steady - P.normal_post_steady
    for k in ("onset_signature", "diff_to_normal_pre", "diff_to_normal_post"):
        P[f"{k}_in_window_sigma"] = P[k] / (P.noise_sigma_sample / np.sqrt(WIN))
    return P, sig, src, normal, cache


def normal_offsets(cfg, src, normal, cache):
    """Steady-state medians of each model's clean NORMAL run per canonical channel; pairwise cross-model offsets."""
    chans = cfg["features"]["channels"]
    med = {}
    for t, nrow in normal.iterrows():
        nc = _read(cache, nrow.file_clean)
        for c in chans:
            v = nc[src[(c, t)]]
            med[(t, c)] = float(v[(v.index >= STEADY[0]) & (v.index < STEADY[1])].median())
    rows = []
    for c in chans:
        pairs = {f"{a}-{b}": abs(med[(a, c)] - med[(b, c)]) for a, b in combinations(sorted(normal.index), 2)}
        rows.append({"channel": c, **{f"NORMAL_steady_median_{t}": med[(t, c)] for t in sorted(normal.index)},
                     **{f"offset_{k}": v for k, v in pairs.items()},
                     "offset_min": min(pairs.values()), "offset_max": max(pairs.values())})
    return pd.DataFrame(rows)


def window_means(series, start, end):
    v = series[(series.index >= start) & (series.index < end)]
    b = ((v.index - start) // 30).astype(int)
    # 60 s windows with a 30 s stride: mean of two consecutive 30 s blocks
    blk = v.groupby(b).mean()
    return pd.Series(((blk + blk.shift(-1)) / 2).dropna().to_numpy(), index=start + blk.index[:-1] * 30)


def distinguishability(cfg, man, P, src, normal, cache, sig, low_vis):
    """Noisy 60 s window means in the steady post-onset period: |difference| / window-mean noise sigma.
    within-model: low-visibility event run vs its own model's NORMAL run (same timestamps);
    cross-model:  NORMAL(model a) vs NORMAL(model b) (same timestamps);
    cross-model event: low-visibility event run of model a vs NORMAL of model b."""
    rows = []
    e = man.set_index("Scenario_ID")
    chans = ["PS4", "PS9", "PS3", "PS2", "PS1", "MFS1", "MFS3"]

    def stat(x, y, s):
        d = (x - y).dropna().abs() / (s / np.sqrt(WIN))
        return float(d.median()), float((d > 3).mean()), int(len(d))

    for sid in low_vis:
        r = e.loc[sid]
        t, t0 = r.topology_source_model, float(P[P.Scenario_ID == sid].onset_s.iloc[0])
        ev = _read(cache, r.file_noise_added)
        for other in sorted(normal.index):
            nr = _read(cache, normal.loc[other].file_noise_added)
            for c in chans:
                a = window_means(ev[src[(c, t)]], max(t0 + 600, STEADY[0]), STEADY[1])
                b = window_means(nr[src[(c, other)]], max(t0 + 600, STEADY[0]), STEADY[1])
                med, share, n = stat(a, b, sig[(t, c)])
                rows.append({"comparison": "event_vs_own_NORMAL" if other == t else "event_vs_other_model_NORMAL",
                             "a": sid, "a_model": t, "b": f"NORMAL_{other}", "b_model": other, "channel": c,
                             "median_abs_diff_in_window_sigma": med, "share_windows_abs_diff_gt_3": share, "n_windows": n})
    for a_m, b_m in combinations(sorted(normal.index), 2):
        na = _read(cache, normal.loc[a_m].file_noise_added)
        nb = _read(cache, normal.loc[b_m].file_noise_added)
        for c in chans:
            a = window_means(na[src[(c, a_m)]], *STEADY)
            b = window_means(nb[src[(c, b_m)]], *STEADY)
            med, share, n = stat(a, b, sig[(a_m, c)])
            rows.append({"comparison": "NORMAL_vs_NORMAL_cross_model", "a": f"NORMAL_{a_m}", "a_model": a_m,
                         "b": f"NORMAL_{b_m}", "b_model": b_m, "channel": c,
                         "median_abs_diff_in_window_sigma": med, "share_windows_abs_diff_gt_3": share, "n_windows": n})
    return pd.DataFrame(rows)


def errors_by_ancestor(cfg, ft, feats, O, man):
    """Every wrong development prediction of H, with its k=25 training-neighbour majority (same standardisation as
    D(x); training set = the other development topology of the fold). Aggregated by independence group and stem."""
    grp = dict(zip(man.Scenario_ID, man.independence_group))
    rows = []
    for (k, t), q in O.groupby(["fold", "topology"]):
        other = [x for x in O[O.fold == k].topology.unique() if x != t][0]
        tr = ft.loc[O[(O.fold == k) & (O.topology == other)].window_id]
        Ztr, Zq = hf.standardize(tr[feats].to_numpy(float), ft.loc[q.window_id, feats].to_numpy(float))
        ytr = tr.label_mapped.to_numpy()
        wrong = ~q.correct.to_numpy(bool)
        idx = np.flatnonzero(wrong)
        maj = np.empty(len(idx), dtype=object)
        for a in range(0, len(idx), 1500):
            nn = np.argsort(cdist(Zq[idx[a:a + 1500]], Ztr), 1)[:, :K]
            maj[a:a + 1500] = [pd.Series(ytr[row]).value_counts().idxmax() for row in nn]
        sub = q.iloc[idx].assign(knn_majority=maj, training_topology=other)
        rows.append(sub)
    E = pd.concat(rows, ignore_index=True)
    E["error_type"] = E.label_mapped + "->" + E.y_hat
    E["independence_group"] = E.Scenario_ID.map(grp)
    E["ancestor"] = E.Scenario_ID.map(ancestor)
    E["conf_ge_0_9"] = E.score_confidence >= hf.TAU_CONF
    E["knn_agrees_with"] = np.where(E.knn_majority == E.label_mapped, "true_class",
                                    np.where(E.knn_majority == E.y_hat, "classifier_label", "third_class"))
    by = E.groupby(["error_type", "independence_group", "ancestor"]).agg(
        window_fold_instances=("window_id", "size"), unique_windows=("window_id", "nunique"),
        runs=("Scenario_ID", "nunique"), folds=("fold", lambda s: ",".join(map(str, sorted(set(s))))),
        heldout_topologies=("topology", lambda s: ",".join(sorted(set(s)))),
        confident_instances=("conf_ge_0_9", "sum"),
        knn_majority_true_class=("knn_agrees_with", lambda s: float((s == "true_class").mean())),
        knn_majority_classifier_label=("knn_agrees_with", lambda s: float((s == "classifier_label").mean()))).reset_index()
    summ = E.groupby("error_type").agg(
        window_fold_instances=("window_id", "size"), unique_windows=("window_id", "nunique"),
        runs=("Scenario_ID", "nunique"), independence_groups=("independence_group", "nunique"),
        ancestors=("ancestor", "nunique"), confident_instances=("conf_ge_0_9", "sum"),
        confident_independence_groups=("independence_group", lambda s: s[E.loc[s.index, "conf_ge_0_9"]].nunique()),
        knn_majority_true_class=("knn_agrees_with", lambda s: float((s == "true_class").mean())),
        knn_majority_classifier_label=("knn_agrees_with", lambda s: float((s == "classifier_label").mean()))).reset_index()
    top = E.groupby(["error_type", "independence_group"]).size().groupby(level=0).apply(lambda s: s.max() / s.sum())
    summ["share_of_instances_in_largest_group"] = summ.error_type.map(top)
    return E, by.sort_values("window_fold_instances", ascending=False), summ.sort_values("window_fold_instances", ascending=False)


def main() -> int:
    hf.verify_inputs()
    cfg, ft, feats, O, man = hf.load()
    ft = ft.set_index("window_id")
    obs = pd.read_csv(OUT / "EVENT_OBSERVABILITY.csv")
    low = obs[obs.event_median_abs_z_top_channel < LOW_VIS_Z]
    low_vis = low.Scenario_ID.tolist()

    P, sig, src, normal, cache = signals(cfg, man)
    off = normal_offsets(cfg, src, normal, cache)
    # offsets vs signatures for the low-visibility runs on their two most affected channels (clean realization)
    rows = []
    for r in low.itertuples():
        for c in (r.event_top_channel, r.event_second_channel):
            p = P[(P.Scenario_ID == r.Scenario_ID) & (P.channel == c) & (P.realization == "clean")].iloc[0]
            o = off[off.channel == c].iloc[0]
            sigabs = abs(p.onset_signature)
            rows.append({"Scenario_ID": r.Scenario_ID, "independence_group": r.independence_group, "source_model": r.source_model,
                         "channel": c, "onset_signature_abs": sigabs, "diff_to_own_NORMAL_post_abs": abs(p.diff_to_normal_post),
                         "diff_to_own_NORMAL_pre_abs": abs(p.diff_to_normal_pre),
                         "cross_model_NORMAL_offset_min": o.offset_min, "cross_model_NORMAL_offset_max": o.offset_max,
                         "offset_min_over_signature": o.offset_min / sigabs if sigabs > 0 else np.nan,
                         "offset_max_over_signature": o.offset_max / sigabs if sigabs > 0 else np.nan,
                         "offset_min_over_diff_to_NORMAL_post": o.offset_min / abs(p.diff_to_normal_post) if p.diff_to_normal_post else np.nan})
    OS = pd.DataFrame(rows)
    DI = distinguishability(cfg, man, P, src, normal, cache, sig, low_vis)
    E, BY, SUMM = errors_by_ancestor(cfg, ft, feats, O, man)

    # ---- statement verification (numbers recomputed here; verdicts follow fixed rules stated in each row)
    offs = off.set_index("channel")
    OS_t = OS[OS.Scenario_ID.str.contains("TRANSIENT")]
    OS_c = OS[~OS.Scenario_ID.str.contains("TRANSIENT")]
    # clean-signal visibility at the windows the classifier called NORMAL (window-weighted over 1000 s bins)
    prof = pd.read_csv(OUT / "LEAK_TO_NORMAL_TIME_PROFILE.csv")
    prof = prof[prof.n_pred_NORMAL > 0]
    vis_at_err = {sid: float(np.average(g.median_clean_event_visibility_max_channel_z, weights=g.n_pred_NORMAL))
                  for sid, g in prof.groupby("Scenario_ID")}
    pc = P[P.realization == "clean"]
    pn = P[P.realization == "noise_added"]
    low_clean = pc[pc.Scenario_ID.isin(low_vis)]
    low_noisy = pn[pn.Scenario_ID.isin(low_vis)]
    vis = obs[obs.event_median_abs_z_top_channel >= LOW_VIS_Z]
    l2n_ids = E[E.error_type == "LEAK->NORMAL"].Scenario_ID.unique()
    st = [
        {"statement": "Eight weak/transient G4/G5 leak runs are ~0.4-1.2 noise sigma from their NORMAL references",
         "evidence": f"{len(low)} runs with clean post-onset median |diff| < {LOW_VIS_Z} sigma on every channel; top-channel "
                     f"medians {low.event_median_abs_z_top_channel.min():.2f}-{low.event_median_abs_z_top_channel.max():.2f} "
                     f"(per-sample noise sigma); names: {';'.join(sorted(low.Scenario_ID))}; independence groups: "
                     f"{low.independence_group.nunique()} ({';'.join(sorted(low.independence_group.unique()))})",
         "noisy_check": f"noisy steady-state window means vs own NORMAL: median |diff| on PS4 "
                        f"{DI[(DI.comparison == 'event_vs_own_NORMAL') & (DI.channel == 'PS4')].median_abs_diff_in_window_sigma.median():.2f} window-sigma",
         "verdict": "VERIFIED" if len(low) == 8 else "REVISED"},
        {"statement": "Cross-topology pressure offsets ~0.13-0.60 MPa, 10-40x the weak-leak signatures",
         "evidence": f"clean steady NORMAL offsets PS4 {offs.loc['PS4', 'offset_min']:.3f}-{offs.loc['PS4', 'offset_max']:.3f} MPa, "
                     f"PS9 {offs.loc['PS9', 'offset_min']:.3f}-{offs.loc['PS9', 'offset_max']:.3f} MPa. Constant-segment low-visibility runs "
                     f"(n={OS_c.Scenario_ID.nunique()}): onset signature {OS_c.onset_signature_abs.min():.3f}-"
                     f"{OS_c.onset_signature_abs.max():.3f} MPa, offset/signature {OS_c.offset_min_over_signature.min():.1f}-"
                     f"{OS_c.offset_max_over_signature.max():.1f}x. Transient runs (n={OS_t.Scenario_ID.nunique()}): brief onset drop "
                     f"{OS_t.onset_signature_abs.min():.2f}-{OS_t.onset_signature_abs.max():.2f} MPa that decays; steady post-onset "
                     f"difference to own NORMAL {OS_t.diff_to_own_NORMAL_post_abs.min():.5f}-{OS_t.diff_to_own_NORMAL_post_abs.max():.5f} MPa "
                     f"(offset/difference {OS_t.offset_min_over_diff_to_NORMAL_post.min():.0f}-{OS_t.offset_min_over_diff_to_NORMAL_post.max():.0f}x)",
         "noisy_check": "window-level noisy comparison in DISTINGUISHABILITY.csv",
         "verdict": (f"REVISED: offsets VERIFIED; ratio is {OS_c.offset_min_over_signature.min():.1f}-"
                     f"{OS_c.offset_max_over_signature.max():.1f}x for constant-segment weak leaks, not 10-40x; transient G4 runs "
                     "drop briefly and then settle much closer to their own NORMAL than the cross-model offset")},
        {"statement": "Weak-leak trajectories converge toward the model-specific NORMAL operating point after onset",
         "evidence": f"clean |diff to own NORMAL| on top channels: pre-onset median {OS.diff_to_own_NORMAL_pre_abs.median():.4f}, "
                     f"post-onset median {OS.diff_to_own_NORMAL_post_abs.median():.5f} (same units); "
                     f"post < pre in {(OS.diff_to_own_NORMAL_post_abs < OS.diff_to_own_NORMAL_pre_abs).sum()}/{len(OS)} run-channels",
         "noisy_check": f"noisy realization, same channels: post |diff| median "
                        f"{low_noisy.diff_to_normal_post.abs().median():.4f} vs pre {low_noisy.diff_to_normal_pre.abs().median():.4f}",
         "verdict": "VERIFIED" if (OS.diff_to_own_NORMAL_post_abs < OS.diff_to_own_NORMAL_pre_abs).all() else "PARTLY_VERIFIED"},
        {"statement": "G5/G6 and G5_STRONG show visible event signatures despite LEAK->NORMAL misclassification",
         "evidence": "; ".join(f"{s}: visibility at the windows predicted NORMAL {vis_at_err.get(s, np.nan):.1f} sigma "
                               f"(run-level event median {obs.set_index('Scenario_ID').loc[s, 'event_median_abs_z_top_channel']:.1f})"
                               for s in l2n_ids),
         "noisy_check": "per-1000 s profile in LEAK_TO_NORMAL_TIME_PROFILE.csv",
         "verdict": ("VERIFIED for G5G6_OVERLAPPED and G5_STRONG; the third LEAK->NORMAL run (transient G4, 5 windows) is visible "
                     "only early in its decaying transient, which is where its errors occur")
                    if all(vis_at_err.get(s, 0) >= LOW_VIS_Z for s in l2n_ids) else "PARTLY_VERIFIED"},
    ]

    # ---- taxonomy per (error type, run): mechanism from fixed rules (independence groups can mix weak and strong runs)
    tax = []
    run_vis = obs.set_index("Scenario_ID").event_median_abs_z_top_channel
    lowv_by_model = low.groupby("source_model").Scenario_ID.nunique().to_dict()
    lowv_windows = ft[ft.Scenario_ID.isin(low_vis)].groupby("topology").size().to_dict()
    BYR = E.groupby(["error_type", "independence_group", "Scenario_ID"]).agg(
        instances=("window_id", "size"), unique_windows=("window_id", "nunique"), confident=("conf_ge_0_9", "sum"),
        heldout=("topology", lambda x: ",".join(sorted(set(x)))),
        training=("training_topology", lambda x: ",".join(sorted(set(x)))),
        knn_true=("knn_agrees_with", lambda x: float((x == "true_class").mean())),
        knn_clf=("knn_agrees_with", lambda x: float((x == "classifier_label").mean()))).reset_index()
    for r in BYR.itertuples():
        true_cls = r.error_type.split("->")[0]
        v = vis_at_err.get(r.Scenario_ID, run_vis.get(r.Scenario_ID, np.nan))
        if true_cls == "NORMAL":
            mech = "PHYSICAL_OVERLAP + INSUFFICIENT_INDEPENDENT_NORMAL_SUPPORT + CROSS_MODEL_OPERATING_POINT_SHIFT"
            note = (f"training topology {r.training} holds 1 NORMAL run (665 windows) and low-visibility LEAK runs at the NORMAL "
                    f"operating point (runs per source model {lowv_by_model}; windows {lowv_windows}); "
                    f"k-NN majority = classifier label in {r.knn_clf:.3f} of windows")
        elif v < LOW_VIS_Z:
            mech, note = "LOW_VISIBILITY_EVENT", "event not distinguishable from own-model NORMAL at the error windows"
        elif r.knn_true >= 0.9:
            mech, note = "CLASSIFIER_FAILURE", (f"event visible ({v:.0f} sigma at the error windows); k-NN majority = true class "
                                                f"in {r.knn_true:.3f}; held-out {r.heldout}, trained on {r.training}")
        elif r.knn_clf >= 0.9:
            mech, note = "EVIDENCE_AGREES_WITH_WRONG_LABEL", (f"event visible ({v:.0f} sigma) but k-NN majority = classifier label "
                                                              f"in {r.knn_clf:.3f}: class overlap or insufficient class support")
        else:
            mech, note = "UNRESOLVED", "mixed evidence"
        tax.append({"error_type": r.error_type, "independence_group": r.independence_group, "Scenario_ID": r.Scenario_ID,
                    "ancestor": ancestor(r.Scenario_ID), "window_fold_instances": r.instances,
                    "unique_windows": r.unique_windows, "confident_instances": int(r.confident),
                    "heldout_topology": r.heldout, "training_topology": r.training,
                    "knn_majority_true_class": r.knn_true, "knn_majority_classifier_label": r.knn_clf,
                    "event_visibility_sigma": v, "mechanism": mech, "evidence": note})
    TAX = pd.DataFrame(tax).sort_values("window_fold_instances", ascending=False)

    for name, df in {"ONSET_PROFILE": P, "OFFSET_VS_SIGNATURE": OS, "NORMAL_STEADY_OFFSETS": off,
                     "DISTINGUISHABILITY": DI, "ERROR_BY_ANCESTOR": BY, "ERROR_INDEPENDENT_SUMMARY": SUMM,
                     "ERROR_TAXONOMY": TAX, "STATEMENT_VERIFICATION": pd.DataFrame(st)}.items():
        df.assign(evidence_status="EXPLORATORY_DIAGNOSTIC").to_csv(OUT / f"{name}.csv", index=False,
                                                                   lineterminator="\n", float_format="%.6g")
    (OUT / "SIGNALS_SUMMARY.json").write_text(json.dumps({
        "evidence_status": "EXPLORATORY_DIAGNOSTIC", "model_fitted": False, "inputs_verified_against_hash_list": True,
        "low_visibility_threshold_sigma": LOW_VIS_Z, "steady_period_s": STEADY, "window_s": WIN, "k": K,
        "n_error_window_fold_instances": int(len(E)), "n_error_unique_windows": int(E.window_id.nunique()),
        "note": "window-fold instances double-count windows that appear in two folds' development sets; "
                "independent units are independence groups"}, indent=2), encoding="utf-8")
    pd.set_option("display.width", 250, "display.max_colwidth", 200)
    for name, df in (("STATEMENTS", pd.DataFrame(st)), ("SUMMARY", SUMM), ("TAXONOMY", TAX), ("OFFSETS", OS)):
        print("==", name)
        print(df.to_string(index=False))
    print(DI.groupby(["comparison", "channel"])[["median_abs_diff_in_window_sigma", "share_windows_abs_diff_gt_3"]].median().round(2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
