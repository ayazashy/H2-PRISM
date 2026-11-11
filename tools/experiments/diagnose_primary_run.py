#!/usr/bin/env python3
"""
Post-hoc diagnostics of a COMPLETED primary-protocol run (read-only on the run; no model is refitted).

Every table written here is DIAGNOSTIC or EXPLORATORY_POST_HOC. None is a registered estimand and none replaces
the registered RQ1 result (which stays as recorded in <run>/rq1.csv). It reuses the runner's own selection
(PA-1 exact-count, same salt), policy and bootstrap functions; nothing is re-implemented.

  A  verification.csv                 key reported summaries recomputed from prediction/decision-level outputs
  B  run_fingerprint.csv              per-run sensor-configuration fingerprint (needs --raw-parent; feature rebuild)
     source_normal_files.csv          the three NORMAL source files in every released version of the dataset
     training_fingerprint_by_fold.csv which configuration each class carries in each fold's TRAINING set
     error_attribution.csv            every misclassified window grouped by (held-out topology, true, predicted)
     error_confidence_and_flags.csv   confidence and support-flag status of correct vs incorrect predictions
  C  rq1_binding_constraints.csv      per fold x variant x method x target x mode: status and binding constraint
     rq1_pooled_reasons.csv           every registered pooled RQ1 comparison with its reason code
     support_flag_structure.csv       test-time flag incidence per topology x class; development attainability
  D  exploratory_shared_coverage.csv  RQ1-style paired contrasts over the coverage range attainable in ALL folds
     exploratory_guard_effect.csv     confidence ranking with vs without the support guard (same coverage)
  E  dx_role.csv                      D(x) vs confidence association, selection overlap s_C vs s_C-D, swapped windows
  F  rq2_accounting.csv               three-outcome counts per topology x class (registered 0.60 and shared coverage)

Usage:
  python tools/experiments/diagnose_primary_run.py --run 03_results/primary_protocol/PRIMARY \
      --out 03_results/diagnostics/PRIMARY_<key12> [--raw-parent data/raw]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from h2prism.experiments import primary_protocol as pp  # noqa: E402
from h2prism.metrics import AMBIGUITY_SET, SPECIFIC, UNRESOLVED  # noqa: E402
from h2prism.uncertainty import paired_stratified_bootstrap  # noqa: E402

CONFIG = REPO / "06_audit_preparation" / "FINAL_EXPERIMENT_CONFIG.yaml"
TAG = "EXPLORATORY_POST_HOC"
EXPLORATORY_GRID = (0.05, 0.10, 0.15, 0.20, 0.25)


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _w(df: pd.DataFrame, out: Path, name: str, status: str) -> None:
    df = df.copy()
    df["analysis_status"] = status
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / name, index=False, lineterminator="\n", float_format="%.10g")


def _load(run: Path):
    man = json.loads((run / "run_manifest.json").read_text(encoding="utf-8"))
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    if man.get("status") != "COMPLETED" or man.get("config_sha256") != _sha(CONFIG):
        raise SystemExit("REFUSED: run is not COMPLETED or was not produced from the pinned config")
    preds = pd.read_parquet(run / "predictions.parquet")
    dec = pd.read_parquet(run / "decisions.parquet")
    return man, cfg, preds, dec


def _yhat(preds, classes):
    return np.array(classes, dtype=object)[preds[[f"p_cal_{c}" for c in classes]].to_numpy(float).argmax(1)]


# ----------------------------------------------------------------------------- A verification
def verify(run, cfg, preds, dec, classes):
    rows = []

    def chk(item, reported, recomputed, tol=1e-9):
        ok = (pd.isna(reported) and pd.isna(recomputed)) or abs(float(reported) - float(recomputed)) <= tol
        rows.append({"item": item, "reported": reported, "recomputed": recomputed, "match": bool(ok)})

    yh = _yhat(preds, classes)
    conf = pd.read_csv(run / "confusion_matrix.csv")
    for (scope, t, p_), n in pd.Series(1, index=pd.MultiIndex.from_arrays([preds.topology, preds.y_true, yh])).groupby(level=[0, 1, 2]).sum().items():
        r = conf[(conf.scope == scope) & (conf.true_class == t) & (conf.predicted_class == p_)]
        chk(f"confusion[{scope}|{t}->{p_}]", float(r.n.iloc[0]) if len(r) else 0.0, float(n))
    for t, g in preds.groupby("topology"):
        r = conf[(conf.scope == t)]
        chk(f"accuracy[{t}]", float(r[r.true_class == r.predicted_class].n.sum() / r.n.sum()), float((yh[g.index] == g.y_true).mean()))
    cm = pd.read_csv(run / "class_metrics.csv")
    for c in classes:
        m = preds.y_true == c
        chk(f"recall[{c}]", float(cm[cm["class"] == c].recall.iloc[0]), float((yh[m] == c).mean()))
    est = pd.read_csv(run / "estimability.csv")
    for (f, v), g in est.groupby(["fold", "variant"]):
        pol = pp._policies(cfg)[v]
        pf = preds[preds.fold == f]
        av = pp._available(np.zeros(len(pf)), pf.support_flags.fillna(""), pol)
        chk(f"max_attainable_coverage[fold{f}|{v}]", float(g.test_max_attainable_coverage.iloc[0]), float(av.mean()))
    curve = pd.read_csv(run / "risk_coverage_curve.csv")
    salt = str(pp._matched_cfg(cfg)["tie_break_salt"])
    for meth in ("s_C", "s_C_minus_D", "confidence"):
        ns = ne = 0
        for f, pf in preds.groupby("fold"):
            av = pp._available(np.zeros(len(pf)), pf.support_flags.fillna(""), pp._policies(cfg)["primary"])
            sc = pf[f"score_{meth}"].to_numpy(float)
            mask, _ = pp.exact_count_selection(sc, av & np.isfinite(sc), pf.window_id.to_numpy(), 0.25, salt)
            ns += int(mask.sum())
            ne += int((yh[pf.index][mask] != pf.y_true.to_numpy()[mask]).sum())
        r = curve[(curve.scope == "pooled") & (curve.variant == "primary") & (curve.method == meth) & (curve.coverage_requested == 0.25)]
        chk(f"pooled_risk@0.25[{meth}]", float(r.selective_risk.iloc[0]), ne / ns)
    rq2 = pd.read_csv(run / "rq2.csv")
    d = dec[(dec.method == "s_C") & (dec.variant == "primary") & (dec["mode"] == "rank_matched") & (dec.target == 0.6)]
    for c, g in d.groupby("y_true"):
        r = rq2[(rq2.variant == "primary") & (rq2["mode"] == "rank_matched") & (rq2.target == 0.6) & (rq2["class"] == c)]
        chk(f"rq2_n[{c}]@0.6", float(r.n.iloc[0]), float(len(g)))
        chk(f"rq2_specific[{c}]@0.6", float(r.specific.iloc[0]), float((g.policy_outcome == SPECIFIC).mean()))
        chk(f"rq2_unresolved[{c}]@0.6", float(r.unresolved.iloc[0]), float((g.policy_outcome == UNRESOLVED).mean()))
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------- B root cause
FP_COLS = ["MFS4__mean", "PS5__mean", "PS6__mean"]


def _fingerprint(df):
    pat_ps8 = (df["PS4__mean"] - df["PS8__mean"]).abs() < 1e-3
    pat_ps9 = (df["PS4__mean"] - df["PS9__mean"]).abs() < 1e-3
    return pd.DataFrame({"mfs4_active": df["MFS4__mean"] > 1.0, "ps4_equals_ps8": pat_ps8, "ps4_equals_ps9": pat_ps9},
                        index=df.index)


def root_cause(cfg, preds, classes, raw_parent: Path):
    ft, summ = pp.build_features(cfg, REPO, raw_parent, "noise_added")
    run_fp = ft.groupby(["topology", "label_mapped", "Scenario_ID"])[FP_COLS + ["PS4__mean", "PS8__mean", "PS9__mean"]].mean()
    fp = _fingerprint(run_fp)
    run_fp = run_fp.join(fp)
    run_fp["configuration"] = np.where(run_fp.mfs4_active, "CENTER_LIKE", "UPSTREAM_DOWNSTREAM_LIKE")
    exp = {"Center": "CENTER_LIKE", "Downstream": "UPSTREAM_DOWNSTREAM_LIKE", "Upstream": "UPSTREAM_DOWNSTREAM_LIKE"}
    run_fp["matches_own_topology"] = [exp[t] == c for (t, _, _), c in zip(run_fp.index, run_fp.configuration)]
    run_fp = run_fp.reset_index()
    # training-set composition per fold (which configurations each class carries in TRAINING)
    cfg_of = dict(zip(run_fp.Scenario_ID, run_fp.configuration))
    tr = []
    for f, held in sorted(preds.groupby("fold").topology.first().items()):
        dev = ft[ft.topology != held]
        for (c, conf), n in dev.groupby([dev.label_mapped, dev.Scenario_ID.map(cfg_of)]).size().items():
            tr.append({"fold": f, "held_out_topology": held, "class": c, "configuration": conf, "n_training_windows": int(n),
                       "n_training_runs": int(dev[(dev.label_mapped == c) & (dev.Scenario_ID.map(cfg_of) == conf)].Scenario_ID.nunique())})
    # the NORMAL source files in every released version
    B = raw_parent / "H2-SimNet-Dataset"
    versions = {"matlab_simulation_output": B / "MATLAB_SIMSCAPE_Simulation/normality_scenarios/normality_datasets",
                "release_clean": B / "H2-SimNet-clean/normality-scenarios/parquet", "release_noise_added": B / "normality-scenarios/parquet"}
    src = []
    for ver, d in versions.items():
        for t in ("center", "down", "up"):
            f = next(iter(list(d.glob(f"normality_gest_{t}.parquet")) + list(d.glob(f"normality_gest_{t}.csv"))), None)
            if f is None:
                src.append({"version": ver, "file": f"normality_gest_{t}", "present": False})
                continue
            df = pd.read_parquet(f) if f.suffix == ".parquet" else pd.read_csv(f)
            df.columns = [str(c).strip() for c in df.columns]
            num = df.apply(pd.to_numeric, errors="coerce")
            row = {"version": ver, "file": f.name, "present": True, "file_sha256": _sha(f), "n_rows": len(df),
                   "has_MFS4_column": "MFS4" in df.columns}
            for c in ("MFS4", "PS4", "PS5", "PS6", "PS8", "PS9"):
                row[f"{c}_mean"] = float(num[c].mean()) if c in num else np.nan
            row["mfs4_active"] = bool(row["MFS4_mean"] > 1.0) if "MFS4" in num else False
            row["ps4_equals_ps8"] = bool(abs(row["PS4_mean"] - row["PS8_mean"]) < 1e-2)
            row["configuration"] = "CENTER_LIKE" if row["mfs4_active"] else "UPSTREAM_DOWNSTREAM_LIKE"
            src.append(row)
    return run_fp, pd.DataFrame(src), pd.DataFrame(tr), summ


def error_tables(preds, classes, run_fp=None):
    yh = _yhat(preds, classes)
    conf = preds[[f"p_cal_{c}" for c in classes]].to_numpy(float).max(1)
    e = preds.assign(y_pred=yh, confidence=conf, correct=yh == preds.y_true.to_numpy(),
                     flagged=preds.support_flags.fillna("") != "")
    cfg_of = dict(zip(run_fp.Scenario_ID, run_fp.configuration)) if run_fp is not None else {}
    rows = []
    for (t, yt, yp), g in e[~e.correct].groupby(["topology", "y_true", "y_pred"]):
        confs = sorted({cfg_of.get(s, "UNKNOWN") for s in g.Scenario_ID})
        # mechanism (evidence-based, stated per group): configuration of the held-out run vs the configuration the
        # TRAINING set associates with the predicted class
        rows.append({"held_out_topology": t, "true_class": yt, "predicted_class": yp, "n_windows": len(g),
                     "n_runs": g.Scenario_ID.nunique(), "test_run_configuration": "|".join(confs),
                     "median_confidence": float(g.confidence.median()), "share_confidence_ge_0_9": float((g.confidence >= 0.9).mean()),
                     "share_support_flagged": float(g.flagged.mean())})
    att = pd.DataFrame(rows)
    tot = e.groupby("topology").agg(n=("window_id", "size"), n_errors=("correct", lambda s: int((~s).sum())))
    att["share_of_topology_errors"] = att.apply(lambda r: r.n_windows / tot.loc[r.held_out_topology, "n_errors"], axis=1)
    att["share_of_all_errors"] = att.n_windows / int((~e.correct).sum())
    cf = e.groupby(["topology", "correct"]).agg(n=("window_id", "size"), median_confidence=("confidence", "median"),
                                                share_confidence_ge_0_9=("confidence", lambda s: float((s >= 0.9).mean())),
                                                share_support_flagged=("flagged", "mean")).reset_index()
    return att, cf


# ----------------------------------------------------------------------------- C RQ1 constraints
def rq1_constraints(run, cfg, preds):
    est = pd.read_csv(run / "estimability.csv")
    rows = []
    for f in sorted(preds.fold.unique()):
        th = pd.read_csv(run / "folds" / f"fold_{f}" / "thresholds.csv")
        e = est[est.fold == f]
        for r in e.itertuples():
            if r.mode == "rank_matched":
                if r.status == "ESTIMABLE":
                    reason = "ESTIMABLE_IN_FOLD"
                else:
                    reason = "TARGET_ABOVE_TEST_ATTAINABLE_COVERAGE_SUPPORT_FLAGS"
                dev = np.nan
            else:
                t = th[(th.variant == r.variant) & (th.method == r.method) & (th.target == r.target)].iloc[0]
                dev = float(t.dev_max_attainable_coverage)
                reason = ("DEV_THRESHOLD_UNATTAINABLE_SUPPORT_FLAGS_ON_DEVELOPMENT" if pd.isna(t.tau) else
                          "ESTIMABLE_IN_FOLD" if r.status == "ESTIMABLE" else "OTHER")
            rows.append({"fold": f, "held_out_topology": preds[preds.fold == f].topology.iloc[0], "variant": r.variant,
                         "method": r.method, "target": r.target, "mode": r.mode, "status": r.status,
                         "test_max_attainable_coverage": r.test_max_attainable_coverage, "dev_max_attainable_coverage": dev,
                         "requested_count": r.requested_count, "n_tied_at_boundary": r.n_tied_at_boundary,
                         "binding_constraint": reason})
    B = pd.DataFrame(rows)
    # comparator never the binding constraint: attainable coverage identical across methods within fold x variant
    same = B.groupby(["fold", "variant", "mode"]).test_max_attainable_coverage.nunique().max() == 1
    rq1 = pd.read_csv(run / "rq1.csv")
    pr = []
    for r in rq1.itertuples():
        g = B[(B.variant == r.variant) & (B.target == r.target) & (B["mode"] == r.mode) & (B.method.isin(["s_C", r.comparison_b]))]
        bad = g[g.status != "ESTIMABLE"]
        folds_bad = sorted(bad.held_out_topology.unique())
        if r.status == "ESTIMABLE":
            reason = "ESTIMABLE"
        elif r.mode == "threshold_transfer":
            reason = "DEV_THRESHOLD_UNATTAINABLE_IN_ALL_FOLDS" if len(folds_bad) == g.fold.nunique() else "DEV_THRESHOLD_UNATTAINABLE"
        elif len(folds_bad) == g.fold.nunique():
            reason = "TARGET_UNATTAINABLE_IN_ALL_FOLDS"
        else:
            reason = "POOLED_REQUIRES_ALL_FOLDS_TARGET_UNATTAINABLE_IN_" + "_".join(folds_bad).upper()
        pr.append({"comparison_a": "s_C", "comparison_b": r.comparison_b, "comparison_role": r.comparison_role,
                   "variant": r.variant, "target": r.target, "mode": r.mode, "status": r.status,
                   "folds_estimable": r.folds_estimable, "non_estimable_folds": "|".join(folds_bad),
                   "reason_code": reason, "comparator_matching_binding": False if same else "CHECK",
                   "tie_effect_binding": False, "implementation_error_found": False})
    flags = []
    for (t, c), g in preds.groupby(["topology", "y_true"]):
        fl = g.support_flags.fillna("")
        flags.append({"held_out_topology": t, "class": c, "n_windows": len(g), "n_runs": g.Scenario_ID.nunique(),
                      "share_unflagged": float((fl == "").mean()),
                      **{f"share_{k}": float(fl.str.contains(k).mean()) for k in
                         ("TOP_CLASS_FEW_INDEPENDENT_RUNS", "LOW_SCENARIO_DIVERSITY", "OUT_OF_SUPPORT")},
                      "median_top_class_n_families": float(g.top_class_n_families.median()),
                      "median_n_distinct_scenarios": float(g.n_distinct_scenarios.median())})
    # development-side flag composition (threshold transfer is set on development predictions)
    recs = json.loads((run / "calibration_records.json").read_text(encoding="utf-8"))
    for r in recs:
        tot = sum(r["dev_support_flags"].values())
        held = preds[preds.fold == r["fold"]].topology.iloc[0]
        flags.append({"held_out_topology": f"DEVELOPMENT(fold {r['fold']}, held out {held})", "class": "ALL", "n_windows": tot,
                      "share_unflagged": r["dev_support_flags"].get("", 0) / tot,
                      **{f"share_{k}": sum(v for f_, v in r["dev_support_flags"].items() if k in f_) / tot for k in
                         ("TOP_CLASS_FEW_INDEPENDENT_RUNS", "LOW_SCENARIO_DIVERSITY", "OUT_OF_SUPPORT")}})
    sel = pd.concat([pd.read_csv(run / "folds" / f"fold_{f}" / "selection.csv") for f in sorted(preds.fold.unique())])
    for f, g in sel.groupby("fold"):
        s = g[g.selected]
        flags.append({"held_out_topology": f"INNER_SELECTION(fold {f})", "class": "ALL",
                      "selected_inner_macro_f1": float(s.inner_macro_f1.iloc[0]), "best_inner_macro_f1": float(g.inner_macro_f1.max())})
    return B, pd.DataFrame(pr), pd.DataFrame(flags), bool(same)


# ----------------------------------------------------------------------------- D/E/F exploratory
def _select(pf, meth, c, pol, salt, guard=True):
    av = pp._available(np.zeros(len(pf)), pf.support_flags.fillna(""), pol) if guard else np.ones(len(pf), bool)
    sc = pf[f"score_{meth}"].to_numpy(float)
    return pp.exact_count_selection(sc, av & np.isfinite(sc), pf.window_id.to_numpy(), c, salt)


def exploratory(cfg, preds, classes):
    salt = str(pp._matched_cfg(cfg)["tie_break_salt"])
    u = cfg["evaluation"]["uncertainty"]
    yh = _yhat(preds, classes)
    yt = preds.y_true.to_numpy()
    out, guard, role = [], [], []
    for v, pol in pp._policies(cfg).items():
        shared = min(pp._available(np.zeros(int((preds.fold == f).sum())), preds[preds.fold == f].support_flags.fillna(""), pol).mean()
                     for f in preds.fold.unique())
        for c in [x for x in EXPLORATORY_GRID if x <= shared]:
            sel = {}
            for meth in pp.METHODS:
                m = np.zeros(len(preds), bool)
                for f, pf in preds.groupby("fold"):
                    mk, _ = _select(pf, meth, c, pol, salt)
                    m[pf.index[mk]] = True
                sel[meth] = m
            for mb, rl in pp.COMPARISONS:
                units = []
                for fam, idx in preds.groupby("Scenario_Family_ID").indices.items():
                    a, b = sel["s_C"][idx], sel[mb][idx]
                    units.append({"unit": fam, "stratum": preds.topology.iloc[idx[0]],
                                  "num_a": int((yh[idx][a] != yt[idx][a]).sum()), "den_a": int(a.sum()),
                                  "num_b": int((yh[idx][b] != yt[idx][b]).sum()), "den_b": int(b.sum())})
                bs = paired_stratified_bootstrap(pd.DataFrame(units), int(u["n_boot"]), int(u["seed"]))
                per = {f"risk_a_{t}": None for t in ()}
                for t, it in preds.groupby("topology").indices.items():
                    a, b = sel["s_C"][it], sel[mb][it]
                    per[f"risk_s_C_{t}"] = float((yh[it][a] != yt[it][a]).mean())
                    per[f"risk_comparator_{t}"] = float((yh[it][b] != yt[it][b]).mean())
                out.append({"variant": v, "coverage": c, "shared_attainable_coverage": float(shared), "comparison_b": mb,
                            "comparison_role": rl, "n_specific_each": int(sel["s_C"].sum()),
                            **{k: bs[k] for k in ("estimate_a", "estimate_b", "difference", "ci_low", "ci_high", "n_units",
                                                  "n_boot_undefined")}, **per,
                            "interpretation": "exploratory post hoc; conditional on three simulated topologies; not the registered RQ1 test"})
            if v == "primary":
                for meth in ("confidence", "s_C"):
                    for g_ in (True, False):
                        m = np.zeros(len(preds), bool)
                        for f, pf in preds.groupby("fold"):
                            mk, _ = _select(pf, meth, c, pol, salt, guard=g_)
                            m[pf.index[mk]] = True
                        guard.append({"coverage": c, "method": meth, "support_guard": g_, "n_specific": int(m.sum()),
                                      "selective_risk": float((yh[m] != yt[m]).mean()),
                                      **{f"risk_{t}": float((yh[it][m[it]] != yt[it][m[it]]).mean()) for t, it in preds.groupby("topology").indices.items()}})
                a, b = sel["s_C"], sel["s_C_minus_D"]
                role.append({"scope": "pooled", "coverage": c, "n_selected_each": int(a.sum()), "n_selected_both": int((a & b).sum()),
                             "jaccard_s_C_vs_s_C_minus_D": float((a & b).sum() / max((a | b).sum(), 1)),
                             "n_only_s_C": int((a & ~b).sum()), "errors_only_s_C": int((yh[a & ~b] != yt[a & ~b]).sum()),
                             "n_only_s_C_minus_D": int((b & ~a).sum()), "errors_only_s_C_minus_D": int((yh[b & ~a] != yt[b & ~a]).sum())})
    # registered 0.60 in the folds where it is attainable (descriptive per topology)
    for f, pf in preds.groupby("fold"):
        pol = pp._policies(cfg)["primary"]
        ma, _ = _select(pf, "s_C", 0.6, pol, salt)
        mb_, _ = _select(pf, "s_C_minus_D", 0.6, pol, salt)
        if ma is None:
            continue
        i = pf.index
        role.append({"scope": pf.topology.iloc[0], "coverage": 0.6, "n_selected_each": int(ma.sum()), "n_selected_both": int((ma & mb_).sum()),
                     "jaccard_s_C_vs_s_C_minus_D": float((ma & mb_).sum() / max((ma | mb_).sum(), 1)),
                     "n_only_s_C": int((ma & ~mb_).sum()), "errors_only_s_C": int((yh[i][ma & ~mb_] != yt[i][ma & ~mb_]).sum()),
                     "n_only_s_C_minus_D": int((mb_ & ~ma).sum()), "errors_only_s_C_minus_D": int((yh[i][mb_ & ~ma] != yt[i][mb_ & ~ma]).sum())})
    R = pd.DataFrame(role)
    # association of D with confidence (on windows available to the guarded policy)
    assoc = []
    for t, pf in preds.groupby("topology"):
        av = pp._available(np.zeros(len(pf)), pf.support_flags.fillna(""), pp._policies(cfg)["primary"])
        for scope, mask in (("all_windows", np.ones(len(pf), bool)), ("guard_available", av)):
            q = pf[mask]
            ok = (yh[q.index] == q.y_true.to_numpy())
            assoc.append({"held_out_topology": t, "scope": scope, "n": len(q),
                          "spearman_D_confidence": float(q.D.rank().corr(q.score_confidence.rank())) if len(q) > 2 else np.nan,
                          "spearman_s_C_s_C_minus_D": float(q.score_s_C.rank().corr(q.score_s_C_minus_D.rank())) if len(q) > 2 else np.nan,
                          "mean_D_correct": float(q.D[ok].mean()) if ok.any() else np.nan,
                          "mean_D_incorrect": float(q.D[~ok].mean()) if (~ok).any() else np.nan,
                          "share_D_eq_1": float((q.D >= 1 - 1e-12).mean())})
    return pd.DataFrame(out), pd.DataFrame(guard), R, pd.DataFrame(assoc)


def rq2_accounting(cfg, preds, dec, classes):
    rows = []

    def acc(g, label, cov):
        for (t, c), gc in g.groupby(["topology", "y_true"]):
            sp, am = gc[gc.policy_outcome == SPECIFIC], gc[gc.policy_outcome == AMBIGUITY_SET]
            rows.append({"analysis": label, "coverage": cov, "held_out_topology": t, "class": c, "n": len(gc),
                         "n_runs": int(preds[preds.window_id.isin(gc.window_id)].Scenario_ID.nunique()),
                         "n_specific": len(sp), "n_specific_correct": int((sp.y_pred_specific == sp.y_true).sum()),
                         "n_ambiguity_set": len(am),
                         "n_ambiguity_includes_true": int(sum(str(y) in str(a).split("|") for y, a in zip(am.y_true, am.ambiguity_set))),
                         "n_unresolved": int((gc.policy_outcome == UNRESOLVED).sum()),
                         "top_reason_codes": "; ".join(f"{k}:{v}" for k, v in gc.reason_code.value_counts().head(3).items())})

    d = dec[(dec.method == "s_C") & (dec.variant == "primary") & (dec["mode"] == "rank_matched") & (dec.target == 0.6)]
    acc(d, "REGISTERED_0.60_rank_matched (Center not estimable: absent)", 0.6)
    salt = str(pp._matched_cfg(cfg)["tie_break_salt"])
    pol = pp._policies(cfg)["primary"]
    P_cols = [f"p_cal_{c}" for c in classes]
    parts = []
    for f, pf in preds.groupby("fold"):
        mk, _ = _select(pf, "s_C", 0.25, pol, salt)
        sc = pf.score_s_C.to_numpy(float)
        eff = np.where(mk, 1.0, np.where(np.isfinite(sc), -1.0, np.nan))
        dd = pp._decide(pf[P_cols].to_numpy(float), eff, pf.support_flags.fillna(""), classes, pol, 0.0)
        dd = dd.assign(window_id=pf.window_id.to_numpy(), y_true=pf.y_true.to_numpy(), topology=pf.topology.to_numpy())
        if int((dd.policy_outcome == SPECIFIC).sum()) != int(mk.sum()):
            raise AssertionError("exploratory RQ2 selection mismatch")
        parts.append(dd)
    acc(pd.concat(parts), f"{TAG}_0.25_shared_attainable_all_topologies", 0.25)
    return pd.DataFrame(rows)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=Path, default=REPO / "03_results/primary_protocol/PRIMARY")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--raw-parent", type=Path, default=None, help="enables the feature-level root-cause tables")
    a = ap.parse_args(argv)
    man, cfg, preds, dec = _load(a.run)
    out = a.out or REPO / "03_results" / "diagnostics" / f"PRIMARY_{man['run_key'][:12]}"
    classes = list(cfg["dataset"]["classes"])
    V = verify(a.run, cfg, preds, dec, classes)
    _w(V, out, "verification.csv", "DIAGNOSTIC")
    run_fp = None
    if a.raw_parent:
        run_fp, src, tr, summ = root_cause(cfg, preds, classes, a.raw_parent.resolve())
        if summ["feature_table_sha256"] != man["features"]["feature_table_sha256"]:
            raise SystemExit("REFUSED: rebuilt feature table differs from the run's feature table")
        _w(run_fp, out, "run_fingerprint.csv", "DIAGNOSTIC")
        _w(src, out, "source_normal_files.csv", "DIAGNOSTIC")
        _w(tr, out, "training_fingerprint_by_fold.csv", "DIAGNOSTIC")
    att, cf = error_tables(preds, classes, run_fp)
    _w(att, out, "error_attribution.csv", "DIAGNOSTIC")
    _w(cf, out, "error_confidence_and_flags.csv", "DIAGNOSTIC")
    B, PR, FL, same = rq1_constraints(a.run, cfg, preds)
    _w(B, out, "rq1_binding_constraints.csv", "DIAGNOSTIC")
    _w(PR, out, "rq1_pooled_reasons.csv", "DIAGNOSTIC")
    _w(FL, out, "support_flag_structure.csv", "DIAGNOSTIC")
    X, G, R, AS = exploratory(cfg, preds, classes)
    _w(X, out, "exploratory_shared_coverage.csv", TAG)
    _w(G, out, "exploratory_guard_effect.csv", TAG)
    _w(R, out, "dx_selection_overlap.csv", TAG)
    _w(AS, out, "dx_association.csv", TAG)
    _w(rq2_accounting(cfg, preds, dec, classes), out, "rq2_accounting.csv", "DIAGNOSTIC")
    files = sorted(p for p in out.glob("*.csv"))
    (out / "DIAGNOSTICS_MANIFEST.json").write_text(json.dumps({
        "source_run_key": man["run_key"], "source_artifact_class": man["artifact_class"],
        "source_predictions_sha256": _sha(a.run / "predictions.parquet"), "source_decisions_sha256": _sha(a.run / "decisions.parquet"),
        "config_sha256": _sha(CONFIG), "script": "tools/experiments/diagnose_primary_run.py",
        "command": "python tools/experiments/diagnose_primary_run.py --run 03_results/primary_protocol/PRIMARY"
                   + (" --raw-parent data/raw" if a.raw_parent else ""),
        "verification_all_match": bool(V.match.all()), "comparator_attainability_identical_across_methods": same,
        "status": "DIAGNOSTIC / EXPLORATORY_POST_HOC - not a registered estimand; registered RQ1 remains as in rq1.csv",
        "outputs": {p.name: _sha(p) for p in files}}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(out.relative_to(REPO)) if out.is_relative_to(REPO) else str(out),
                      "verification_all_match": bool(V.match.all()), "n_checks": len(V)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
