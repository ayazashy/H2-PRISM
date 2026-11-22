"""H1 evidence analysis for H2-PRISM (additive, read-only on every frozen artifact).

What it does
  H1-01  re-reads the registered RQ1 result (R2, run key a10530f1fcf2...) and checks its status;
  H1-02  recomputes attainable specific coverage per outer fold from the frozen window-level predictions;
  H1-04  re-runs the registered rank-matched exact-count selection (PA-1 tie key) on the fixed exploratory grid
         0.05-0.25 that the R2 diagnostics already used, and verifies every count against the frozen outputs;
  H1-05  decomposes each selection by (a) source-model attribution status of the run (forensic audit, D1 pending),
         (b) independent units (Scenario_Family_ID and scenario ancestor), and compares the full evidence policy
         with plain confidence abstention without the evidence guard;
  H1-03  D(x) redundancy: correctness AUROC of every registered score, development ablation summary;
  RQ3    three-outcome validity of the registered 0.60 decisions (folds where it is attainable);
  H1-06  library-completeness risk of formal D(Y) on the Center conditional-bound grid (672 cells).

Nothing frozen is written. No model is trained or refit; no threshold, target or label is changed.
All outputs are EXPLORATORY_POST_HOC (the evaluation windows were inspected in R2) except the verification rows.

Usage (repository root):
  python 03_results/integrated_validation_v1/h1_validation/scripts/h1_analysis.py \
      --r2-run <path to the frozen R2 run directory holding predictions.parquet and decisions.parquet>
The R2 parquet files are not tracked (data policy); their SHA-256 must equal the values pinned in
03_results/diagnostics/PRIMARY_a10530f1fcf2/DIAGNOSTICS_MANIFEST.json, otherwise the script refuses to run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

H1 = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "src"))
from h2prism.experiments import primary_protocol as pp  # noqa: E402
from h2prism.uncertainty import paired_stratified_bootstrap  # noqa: E402

CONFIG = REPO / "06_audit_preparation/FINAL_EXPERIMENT_CONFIG.yaml"
R2 = REPO / "03_results/primary_protocol/PRIMARY"
DIAG = REPO / "03_results/diagnostics/PRIMARY_a10530f1fcf2"
FOR = REPO / "03_results/diagnostics/forensics"
ABL = REPO / "03_results/ablation/ARM_SUMMARY.csv"
DY = REPO / "03_results/validation/center_evidence_enhancement/analysis/dy_decisions.json"
GRID = (0.05, 0.10, 0.15, 0.20, 0.25)  # fixed by tools/experiments/diagnose_primary_run.py before this analysis
CLASSES = ["NORMAL", "LEAK", "COMPRESSOR_FAULT", "COMPRESSOR_DELAY"]
TAG = "EXPLORATORY_POST_HOC"
GUARDED = list(pp.METHODS)
BASELINE = "confidence_no_evidence_guard"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write(df, name, status=TAG):
    out = H1 / "analysis"
    out.mkdir(parents=True, exist_ok=True)
    df = df.copy()
    if status:
        df["analysis_status"] = status
    df.to_csv(out / name, index=False, lineterminator="\n", float_format="%.10g")
    return df


def ancestor(sid: str) -> str:
    """Scenario template shared across topologies: strip the topology token."""
    return re.sub(r"(?i)(^CS_(CENTER|DOWNSTREAM|UPSTREAM)_)|(_?GEST_(CENTER|DOWN|UP)$)", "", sid)


def auroc(score, correct):
    s, c = np.asarray(score, float), np.asarray(correct, bool)
    if c.all() or (~c).all():
        return np.nan
    r = pd.Series(s).rank(method="average").to_numpy()
    n1, n0 = c.sum(), (~c).sum()
    return float((r[c].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def load(run: Path):
    man = json.loads((DIAG / "DIAGNOSTICS_MANIFEST.json").read_text(encoding="utf-8"))
    got = {"predictions": sha(run / "predictions.parquet"), "decisions": sha(run / "decisions.parquet")}
    if got["predictions"] != man["source_predictions_sha256"] or got["decisions"] != man["source_decisions_sha256"]:
        raise SystemExit(f"REFUSED: R2 parquet hashes differ from the pinned diagnostics manifest: {got}")
    rman = json.loads((R2 / "run_manifest.json").read_text(encoding="utf-8"))
    if rman["status"] != "COMPLETED" or rman["config_sha256"] != sha(CONFIG):
        raise SystemExit("REFUSED: R2 manifest is not COMPLETED from the pinned config")
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    preds = pd.read_parquet(run / "predictions.parquet").reset_index(drop=True)
    dec = pd.read_parquet(run / "decisions.parquet")
    att = pd.read_csv(FOR / "source_model_attribution.csv")
    disputed = set(att.loc[~att.consistent.astype(bool), "Scenario_ID"])
    preds["y_hat"] = np.array(CLASSES, dtype=object)[preds[[f"p_cal_{c}" for c in CLASSES]].to_numpy(float).argmax(1)]
    preds["correct"] = preds.y_hat == preds.y_true
    preds["ancestor"] = preds.Scenario_ID.map(ancestor)
    preds["attribution_disputed"] = preds.Scenario_ID.isin(disputed)
    src = {"r2_predictions.parquet": got["predictions"], "r2_decisions.parquet": got["decisions"],
           "FINAL_EXPERIMENT_CONFIG.yaml": sha(CONFIG), "source_model_attribution.csv": sha(FOR / "source_model_attribution.csv"),
           "ARM_SUMMARY.csv": sha(ABL), "dy_decisions.json": sha(DY), "r2_run_key": rman.get("run_key", "")}
    return cfg, preds, dec, src


def select(pf, meth, c, pol, salt, guard=True):
    av = pp._available(np.zeros(len(pf)), pf.support_flags.fillna(""), pol) if guard else np.ones(len(pf), bool)
    sc = pf[f"score_{meth}"].to_numpy(float)
    mask, _ = pp.exact_count_selection(sc, av & np.isfinite(sc), pf.window_id.to_numpy(), c, salt)
    return mask


def selections(preds, cfg, c):
    pol, salt = pp._policies(cfg)["primary"], str(pp._matched_cfg(cfg)["tie_break_salt"])
    out = {}
    for meth in GUARDED + [BASELINE]:
        m = np.zeros(len(preds), bool)
        for f, pf in preds.groupby("fold"):
            mk = select(pf, "confidence" if meth == BASELINE else meth, c, pol, salt, guard=meth != BASELINE)
            if mk is None:
                return None
            m[pf.index[mk]] = True
        out[meth] = m
    return out


# ----------------------------------------------------------------------------- H1-01 / H1-02
def registered(preds, cfg):
    rq1 = pd.read_csv(R2 / "rq1.csv")
    prim = rq1[(rq1.comparison_role == "PRIMARY") & (rq1.variant == "primary")]
    reasons = pd.read_csv(DIAG / "rq1_pooled_reasons.csv")
    t = prim.merge(reasons[["comparison_b", "variant", "target", "mode", "reason_code", "non_estimable_folds",
                            "implementation_error_found"]],
                   on=["comparison_b", "variant", "target", "mode"], how="left")
    assert (t.status == "NOT_ESTIMABLE_UNDER_PRIMARY_PROTOCOL").all(), "registered RQ1 status changed"
    write(t, "h1_01_registered_rq1.csv", status="REGISTERED_RESULT_REREAD")
    est = pd.read_csv(R2 / "estimability.csv")
    bind = pd.read_csv(DIAG / "rq1_binding_constraints.csv")
    rows = []
    for v, pol in pp._policies(cfg).items():
        for f, pf in preds.groupby("fold"):
            av = pp._available(np.zeros(len(pf)), pf.support_flags.fillna(""), pol)
            rep = float(est[(est.fold == f) & (est.variant == v)].test_max_attainable_coverage.iloc[0])
            dev = bind[(bind.fold == f) & (bind.variant == v) & (bind["mode"] == "threshold_transfer")].dev_max_attainable_coverage
            row = {"variant": v, "fold": f, "held_out_topology": pf.topology.iloc[0], "n_windows": len(pf),
                   "n_eligible_specific": int(av.sum()), "max_attainable_coverage": float(av.mean()),
                   "reported_max_attainable_coverage": rep, "match": abs(rep - av.mean()) < 1e-9,
                   "dev_max_attainable_coverage": float(dev.iloc[0]) if len(dev) else np.nan,
                   "n_runs": pf.Scenario_ID.nunique(), "n_families": pf.Scenario_Family_ID.nunique(),
                   "n_ancestors": pf.ancestor.nunique(), "n_errors_classifier": int((~pf.correct).sum()),
                   "n_errors_in_disputed_runs": int((~pf.correct & pf.attribution_disputed).sum()),
                   "n_windows_disputed_runs": int(pf.attribution_disputed.sum())}
            for tg in (0.6, 0.8, 0.9):
                row[f"target_{tg:.2f}_attainable"] = bool(np.ceil(tg * len(pf) - 1e-9) <= av.sum())
            for c in CLASSES:
                row[f"eligible_share_{c}"] = float(av[pf.y_true.to_numpy() == c].mean()) if (pf.y_true == c).any() else np.nan
            rows.append(row)
    F = pd.DataFrame(rows)
    assert F.match.all(), "attainable coverage does not reproduce"
    write(F, "h1_02_fold_feasibility.csv", status="RECOMPUTED_VERIFIED")
    iu = pd.read_csv(FOR / "independence_units.csv").set_index("y_true")
    chk = preds.groupby("y_true").agg(runs=("Scenario_ID", "nunique"), families=("Scenario_Family_ID", "nunique"),
                                      ancestors=("ancestor", "nunique"), windows=("window_id", "size"))
    chk = chk.join(iu, rsuffix="_forensic")
    write(chk.reset_index(), "h1_02_independence_units_check.csv", status="RECOMPUTED_VERIFIED")
    return F, chk


# ----------------------------------------------------------------------------- H1-04 / H1-05
def bootstrap_units(preds, a, b, unit):
    yh, yt = preds.y_hat.to_numpy(), preds.y_true.to_numpy()
    rows = []
    for u, idx in preds.groupby(unit).indices.items():
        sa, sb = a[idx], b[idx]
        rows.append({"unit": u, "stratum": preds.topology.iloc[idx[0]] if unit == "Scenario_Family_ID" else "all",
                     "num_a": int((yh[idx][sa] != yt[idx][sa]).sum()), "den_a": int(sa.sum()),
                     "num_b": int((yh[idx][sb] != yt[idx][sb]).sum()), "den_b": int(sb.sum())})
    return pd.DataFrame(rows)


def exploratory(preds, cfg):
    u = cfg["evaluation"]["uncertainty"]
    curve = pd.read_csv(R2 / "risk_coverage_curve.csv")
    curve = curve[(curve.variant == "primary") & (curve["mode"] == "rank_matched")]
    shared = pd.read_csv(DIAG / "exploratory_shared_coverage.csv")
    shared = shared[shared.variant == "primary"]
    guard = pd.read_csv(DIAG / "exploratory_guard_effect.csv")
    overlap = pd.read_csv(DIAG / "dx_selection_overlap.csv")
    yh, yt = preds.y_hat.to_numpy(), preds.y_true.to_numpy()
    err = yh != yt
    disp = preds.attribution_disputed.to_numpy()
    sel_rows, cmp_rows, ver = [], [], []
    for c in GRID:
        S = selections(preds, cfg, c)
        for meth, m in S.items():
            for scope, idx in [("pooled", np.arange(len(preds)))] + list(preds.groupby("topology").indices.items()):
                mm = np.zeros(len(preds), bool)
                mm[idx] = m[idx]
                n, e = int(mm.sum()), int((mm & err).sum())
                sel_rows.append({"coverage": c, "method": meth, "scope": scope, "n_selected": n, "n_errors": e,
                                 "selective_risk": e / n if n else np.nan,
                                 "n_selected_undisputed": int((mm & ~disp).sum()),
                                 "n_errors_undisputed": int((mm & err & ~disp).sum()),
                                 "n_errors_disputed": int((mm & err & disp).sum()),
                                 "families_with_selected_error": int(preds.Scenario_Family_ID[mm & err].nunique()),
                                 "ancestors_with_selected_error": int(preds.ancestor[mm & err].nunique()),
                                 "families_selected": int(preds.Scenario_Family_ID[mm].nunique())})
                if meth in GUARDED:
                    r = curve[(curve.method == meth) & (curve.scope == scope) & np.isclose(curve.coverage_requested, c)]
                    ver.append({"item": f"risk_coverage_curve[{meth}|{scope}|{c}]", "reported": float(r.n_errors.iloc[0]),
                                "recomputed": e, "match": int(r.n_errors.iloc[0]) == e and int(r.n_specific.iloc[0]) == n})
                elif scope == "pooled":
                    g = guard[(guard.method == "confidence") & (~guard.support_guard) & np.isclose(guard.coverage, c)]
                    ver.append({"item": f"guard_effect[confidence_no_guard|{c}]", "reported": float(g.selective_risk.iloc[0]),
                                "recomputed": e / n, "match": abs(float(g.selective_risk.iloc[0]) - e / n) < 1e-9})
        a = S["s_C"]
        for mb in [m for m in GUARDED if m != "s_C"] + [BASELINE]:
            b = S[mb]
            fam = paired_stratified_bootstrap(bootstrap_units(preds, a, b, "Scenario_Family_ID"), int(u["n_boot"]), int(u["seed"]))
            anc = paired_stratified_bootstrap(bootstrap_units(preds, a, b, "ancestor"), int(u["n_boot"]), int(u["seed"]))
            ua, ub = a & ~disp, b & ~disp
            row = {"coverage": c, "method_a": "s_C", "method_b": mb, "n_selected_each": int(a.sum()),
                   "risk_a": fam["estimate_a"], "risk_b": fam["estimate_b"], "delta_R": fam["difference"],
                   "family_ci_low": fam["ci_low"], "family_ci_high": fam["ci_high"], "n_families": fam["n_units"],
                   "ancestor_ci_low": anc["ci_low"], "ancestor_ci_high": anc["ci_high"], "n_ancestors": anc["n_units"],
                   "ancestor_se": np.nan, "n_only_a": int((a & ~b).sum()), "errors_only_a": int((a & ~b & err).sum()),
                   "n_only_b": int((b & ~a).sum()), "errors_only_b": int((b & ~a & err).sum()),
                   "families_discordant_errors": int(preds.Scenario_Family_ID[((a & ~b) | (b & ~a)) & err].nunique()),
                   "ancestors_discordant_errors": int(preds.ancestor[((a & ~b) | (b & ~a)) & err].nunique()),
                   "n_selected_undisputed_a": int(ua.sum()), "n_errors_undisputed_a": int((ua & err).sum()),
                   "n_selected_undisputed_b": int(ub.sum()), "n_errors_undisputed_b": int((ub & err).sum())}
            # standard error of the ancestor-level bootstrap (planning input only)
            ud = bootstrap_units(preds, a, b, "ancestor")
            rng = np.random.default_rng(int(u["seed"]))
            reps = []
            for _ in range(int(u["n_boot"])):
                i = rng.integers(0, len(ud), len(ud))
                da, db = ud.den_a.to_numpy()[i].sum(), ud.den_b.to_numpy()[i].sum()
                if da and db:
                    reps.append(ud.num_a.to_numpy()[i].sum() / da - ud.num_b.to_numpy()[i].sum() / db)
            row["ancestor_se"] = float(np.std(reps, ddof=1))
            cmp_rows.append(row)
            if mb in GUARDED:
                s = shared[(shared.comparison_b == mb) & np.isclose(shared.coverage, c)].iloc[0]
                ok = all(abs(float(s[k]) - row[k2]) < 1e-9 for k, k2 in
                         [("difference", "delta_R"), ("ci_low", "family_ci_low"), ("ci_high", "family_ci_high")])
                ver.append({"item": f"shared_coverage_bootstrap[s_C-{mb}|{c}]", "reported": float(s.ci_high),
                            "recomputed": row["family_ci_high"], "match": ok})
            if mb == "s_C_minus_D":
                o = overlap[(overlap.scope == "pooled") & np.isclose(overlap.coverage, c)].iloc[0]
                ok = (int(o.errors_only_s_C) == row["errors_only_a"] and int(o.errors_only_s_C_minus_D) == row["errors_only_b"])
                ver.append({"item": f"selection_overlap[{c}]", "reported": int(o.errors_only_s_C_minus_D),
                            "recomputed": row["errors_only_b"], "match": ok})
    V = pd.DataFrame(ver)
    assert V.match.all(), V[~V.match]
    write(pd.DataFrame(sel_rows), "h1_04_selection_by_method.csv")
    write(pd.DataFrame(cmp_rows), "h1_05_paired_comparisons.csv")
    return pd.DataFrame(sel_rows), pd.DataFrame(cmp_rows), V


def error_capture(preds, cfg, sel):
    """Where do classifier errors go: blocked by evidence flags, rejected by the score, or issued as SPECIFIC?"""
    pol = pp._policies(cfg)["primary"]
    av = np.zeros(len(preds), bool)
    for f, pf in preds.groupby("fold"):
        av[pf.index] = pp._available(np.zeros(len(pf)), pf.support_flags.fillna(""), pol)
    err = ~preds.correct.to_numpy()
    rows = []
    for scope, idx in [("pooled", np.arange(len(preds)))] + list(preds.groupby("topology").indices.items()):
        e, a = err[idx], av[idx]
        rows.append({"scope": scope, "n_windows": len(idx), "classifier_errors": int(e.sum()),
                     "base_error_rate": float(e.mean()), "eligible_windows": int(a.sum()),
                     "error_rate_eligible": float(e[a].mean()) if a.any() else np.nan,
                     "error_rate_blocked": float(e[~a].mean()) if (~a).any() else np.nan,
                     "errors_blocked_by_evidence_flags": int((e & ~a).sum()),
                     "share_errors_blocked": float((e & ~a).sum() / e.sum()) if e.sum() else np.nan,
                     "errors_in_disputed_runs": int((e & preds.attribution_disputed.to_numpy()[idx]).sum())})
    return write(pd.DataFrame(rows), "h1_05_error_capture.csv")


# ----------------------------------------------------------------------------- H1-03 redundancy
def redundancy(preds, cfg):
    pol = pp._policies(cfg)["primary"]
    assoc = pd.read_csv(DIAG / "dx_association.csv")
    rows, ver = [], []
    for t, pf in preds.groupby("topology"):
        av = pp._available(np.zeros(len(pf)), pf.support_flags.fillna(""), pol)
        for scope, m in (("all_windows", np.ones(len(pf), bool)), ("guard_available", av)):
            g = pf[m]
            r = {"held_out_topology": t, "scope": scope, "n": len(g), "n_errors": int((~g.correct).sum()),
                 "spearman_D_confidence": g.D.corr(g.score_confidence, method="spearman"),
                 "spearman_s_C_s_C_minus_D": g.score_s_C.corr(g.score_s_C_minus_D, method="spearman")}
            for meth in GUARDED:
                r[f"auroc_correct_{meth}"] = auroc(g[f"score_{meth}"].fillna(-np.inf), g.correct)
            rows.append(r)
            a = assoc[(assoc.held_out_topology == t) & (assoc.scope == scope)].iloc[0]
            ver.append({"item": f"dx_association[{t}|{scope}]", "reported": a.spearman_D_confidence,
                        "recomputed": r["spearman_D_confidence"], "match": abs(a.spearman_D_confidence - r["spearman_D_confidence"]) < 1e-9})
    V = pd.DataFrame(ver)
    assert V.match.all(), V
    write(pd.DataFrame(rows), "h1_03_score_redundancy_test.csv")
    arm = pd.read_csv(ABL)
    keep = ["arm_id", "n_features", "dev_accuracy_mean", "dev_group_balanced_accuracy_mean", "dev_ece_mean",
            "min_auroc_confidence_over_dev_topologies", "min_auroc_D_only_over_dev_topologies",
            "share_errors_conf_ge_0_9", "share_flag_free_mean", "s_C_estimable_dev_topologies",
            "s_C_group_balanced_risk_mean", "s_C_minus_D_group_balanced_risk_mean", "confidence_group_balanced_risk_mean",
            "auroc_s_C_minus_auroc_s_C_minus_D_mean", "meta_model_undefined_folds", "min_auroc_E_over_dev_topologies",
            "share_E_undefined_mean", "evidence_status"]
    write(arm[keep], "h1_03_development_ablation.csv", status="EXPLORATORY_DEVELOPMENT_REREAD")
    return V


# ----------------------------------------------------------------------------- RQ3 validity
def three_outcome(preds, dec):
    d = dec[(dec.variant == "primary") & (dec.method == "s_C") & np.isclose(dec.target, 0.6) & (dec["mode"] == "rank_matched")]
    d = d.merge(preds[["window_id", "y_hat", "correct", "attribution_disputed", "Scenario_Family_ID"]], on="window_id",
                suffixes=("", "_p"))
    rows = []
    for (t, y), g in d.groupby(["topology", "y_true"]):
        sp, am, un = g[g.policy_outcome == "SPECIFIC"], g[g.policy_outcome == "AMBIGUITY_SET"], g[g.policy_outcome == "UNRESOLVED"]
        inc = am.apply(lambda r: r.y_true in str(r.ambiguity_set).split("|"), axis=1) if len(am) else pd.Series(dtype=bool)
        rc = un.reason_code.fillna("")
        rows.append({"held_out_topology": t, "true_class": y, "n": len(g), "n_families": g.Scenario_Family_ID.nunique(),
                     "specific": len(sp), "specific_wrong": int((sp.y_pred_specific != sp.y_true).sum()),
                     "ambiguity": len(am), "ambiguity_includes_true": int(inc.sum()) if len(am) else 0,
                     "ambiguity_mean_size": float(am.set_size.mean()) if len(am) else np.nan,
                     "unresolved": len(un),
                     "unresolved_flag_blocked": int(rc.str.contains("FLAG").sum()),
                     "unresolved_out_of_support": int(rc.str.contains("OUT_OF_SUPPORT").sum()),
                     "unresolved_score_below_threshold": int(rc.str.contains("SCORE_BELOW_THRESHOLD").sum()),
                     "classifier_error_rate_specific": float((~sp.correct).mean()) if len(sp) else np.nan,
                     "classifier_error_rate_unresolved": float((~un.correct).mean()) if len(un) else np.nan,
                     "classifier_errors_total": int((~g.correct).sum())})
    T = pd.DataFrame(rows)
    rq2 = pd.read_csv(R2 / "rq2.csv")
    rq2 = rq2[(rq2.variant == "primary") & np.isclose(rq2.target, 0.6)]
    agg = T.groupby("true_class")[["n", "specific", "ambiguity", "unresolved"]].sum()
    for _, r in rq2.iterrows():
        a = agg.loc[r["class"]]
        assert a.n == r.n and abs(a.specific / a.n - r.specific) < 1e-9, r["class"]
    return write(T, "h1_06_three_outcome_validity_r2.csv", status="REGISTERED_DECISIONS_DESCRIPTIVE")


# ----------------------------------------------------------------------------- H1-06 D(Y) library completeness
def dy_completeness():
    dy = json.loads(DY.read_text(encoding="utf-8"))
    rows = []
    for r in dy:
        dec = r["decision"]
        corr = (None if dec != "SPECIFIC" else r["selected"] == r["true_hypothesis"])
        rows.append({"universe": r["universe"], "group": r["group"], "clock_bound_s": r["clock_bound_s"],
                     "query": r["query"], "scenario": r["scenario"], "true_supported": r["true_supported"],
                     "decision": dec, "reason": r["reason"],
                     "specific_correct": corr is True, "specific_wrong": corr is False,
                     "true_retained": r["true_hypothesis"] in r["consistent"] or r["true_hypothesis"] in r["indeterminate"]})
    D = pd.DataFrame(rows)
    assert len(D) == 672
    s = D.groupby(["universe", "group", "clock_bound_s"]).agg(
        cells=("decision", "size"), specific=("decision", lambda x: int((x == "SPECIFIC").sum())),
        specific_correct=("specific_correct", "sum"), specific_wrong=("specific_wrong", "sum"),
        ambiguous=("decision", lambda x: int((x == "AMBIGUOUS").sum())),
        unresolved=("decision", lambda x: int((x == "UNRESOLVED").sum()))).reset_index()
    w = D[D.specific_wrong]
    assert (~w.true_supported).all(), "a wrong SPECIFIC occurred with a supported true hypothesis"
    by_support = D[D.decision == "SPECIFIC"].groupby(["universe", "true_supported"]).agg(
        specific=("decision", "size"), wrong=("specific_wrong", "sum")).reset_index()
    write(s, "h1_07_dy_library_completeness.csv", status="CONDITIONAL_HYPOTHETICAL_BOUNDS")
    write(by_support, "h1_07_dy_wrong_specific_by_support.csv", status="CONDITIONAL_HYPOTHETICAL_BOUNDS")
    return s, by_support


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--r2-run", type=Path, default=os.environ.get("H2PRISM_R2_RUN"))
    a = ap.parse_args()
    if a.r2_run is None:
        raise SystemExit("pass --r2-run or set H2PRISM_R2_RUN")
    cfg, preds, dec, src = load(Path(a.r2_run))
    F, chk = registered(preds, cfg)
    S, P, V1 = exploratory(preds, cfg)
    E = error_capture(preds, cfg, S)
    V2 = redundancy(preds, cfg)
    T = three_outcome(preds, dec)
    s, bs = dy_completeness()
    V = pd.concat([V1, V2], ignore_index=True)
    write(V, "h1_verification.csv", status="VERIFICATION")
    summary = {"sources_sha256": src, "verification_items": int(len(V)), "verification_all_match": bool(V.match.all()),
               "shared_attainable_coverage_primary": float(F[F.variant == "primary"].max_attainable_coverage.min()),
               "grid": list(GRID), "status": TAG,
               "classifier_errors_total": int((~preds.correct).sum()),
               "classifier_errors_disputed": int((~preds.correct & preds.attribution_disputed).sum())}
    (H1 / "analysis/h1_summary.json").write_text(json.dumps(summary, indent=2, default=float) + "\n", encoding="utf-8",
                                                 newline="\n")
    print(json.dumps(summary, indent=2, default=float))


if __name__ == "__main__":
    main()
