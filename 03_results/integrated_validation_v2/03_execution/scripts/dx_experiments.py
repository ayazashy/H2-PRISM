"""Does D(x) add information beyond classifier confidence?  (H2, EXPLORATORY on inspected R2 windows + SYNTHETIC controls)

X1 conditional utility: within confidence strata, AUROC of D for correctness (eligible windows), per topology.
X2 incremental predictive utility: leave-one-TEMPLATE-out cross-validated logistic models of correctness:
   [logit conf], [logit conf, D], [logit conf, margin, -H], [logit conf, margin, -H, D]; out-of-fold log-loss and Brier.
   17 templates as groups; folds never share a template.  Fitted only on frozen scores; no classifier is refit.
X3 artifact test: AUROC of (1 - D) for membership in disputed-attribution runs vs for classifier error.
X4 registered k sensitivities (k = 10, 50) and clean realization: status re-read from SENSITIVITY_SUMMARY.
X5 SYNTHETIC controlled case (method check, not evidence about pipelines): two Gaussian classes with known overlap;
   (a) calibrated Bayes classifier -> D should add nothing; (b) overconfident classifier (temperature 0.2) and
   (c) classifier blind to one informative feature -> D computed on the full feature space can add information.
Usage: python dx_experiments.py --r2-run <frozen R2 run>
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

V2 = Path(__file__).resolve().parents[2]
REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "03_results/integrated_validation_v1/h1_validation/scripts"))
sys.path.insert(0, str(REPO / "src"))
import h1_analysis as h1  # noqa: E402
from h2prism.distinguishability import DConfig, EmpiricalSupport  # noqa: E402

OUT = V2 / "04_results/analysis"
SEED = 20261118


def auroc(s, y):
    s, y = np.asarray(s, float), np.asarray(y, bool)
    if y.all() or (~y).all():
        return np.nan
    r = pd.Series(s).rank().to_numpy()
    n1, n0 = y.sum(), (~y).sum()
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def logit(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def fit_lr(X, y, l2=1e-3, it=200):
    """Small Newton logistic regression (deterministic; no external fitting library state)."""
    X1 = np.column_stack([np.ones(len(X)), X])
    w = np.zeros(X1.shape[1])
    for _ in range(it):
        p = 1 / (1 + np.exp(-X1 @ w))
        g = X1.T @ (p - y) + l2 * np.r_[0, w[1:]]
        H = (X1 * (p * (1 - p))[:, None]).T @ X1 + l2 * np.diag(np.r_[0, np.ones(len(w) - 1)])
        step = np.linalg.solve(H + 1e-9 * np.eye(len(w)), g)
        w -= step
        if np.abs(step).max() < 1e-10:
            break
    return w


def predict(w, X):
    return 1 / (1 + np.exp(-np.column_stack([np.ones(len(X)), X]) @ w))


def r2_part(preds, cfg):
    pp = h1.pp
    pol = pp._policies(cfg)["primary"]
    av = np.zeros(len(preds), bool)
    for f, pf in preds.groupby("fold"):
        av[pf.index] = pp._available(np.zeros(len(pf)), pf.support_flags.fillna(""), pol)
    e = preds[av].copy()
    P = e[[f"p_cal_{c}" for c in h1.CLASSES]].to_numpy(float)
    Ps = np.sort(P, axis=1)
    e["conf"], e["margin"] = Ps[:, -1], Ps[:, -1] - Ps[:, -2]
    e["negH"] = (P * np.log(np.clip(P, 1e-12, 1))).sum(1)
    rows = []
    for t, g in e.groupby("topology"):
        q = pd.qcut(g.conf.rank(method="first"), 5, labels=False)
        for b in range(5):
            gg = g[q == b]
            rows.append(dict(topology=t, confidence_quintile=b + 1, n=len(gg), errors=int((~gg.correct).sum()),
                             conf_min=gg.conf.min(), conf_max=gg.conf.max(), auroc_D_within_stratum=auroc(gg.D, gg.correct),
                             auroc_conf_within_stratum=auroc(gg.conf, gg.correct)))
    pd.DataFrame(rows).to_csv(OUT / "x1_conditional_D_given_confidence.csv", index=False, lineterminator="\n")
    # X2 leave-one-template-out incremental utility
    feats = {"conf": ["lc"], "conf+D": ["lc", "D"], "conf+margin+negH": ["lc", "margin", "negH"],
             "conf+margin+negH+D": ["lc", "margin", "negH", "D"]}
    e["lc"] = logit(e.conf)
    y = e.correct.to_numpy(float)
    oof = {k: np.full(len(e), np.nan) for k in feats}
    for anc in sorted(e.ancestor.unique()):
        te = (e.ancestor == anc).to_numpy()
        for k, cols in feats.items():
            X = e[cols].to_numpy(float)
            mu, sd = X[~te].mean(0), X[~te].std(0) + 1e-12
            w = fit_lr((X[~te] - mu) / sd, y[~te])
            oof[k][te] = predict(w, (X[te] - mu) / sd)
    res = []
    for k in feats:
        p = np.clip(oof[k], 1e-6, 1 - 1e-6)
        res.append(dict(model=k, oof_log_loss=float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))),
                        oof_brier=float(np.mean((p - y) ** 2)), oof_auroc=auroc(p, y.astype(bool)), n=len(e),
                        groups=e.ancestor.nunique(), errors=int((1 - y).sum())))
    X2 = pd.DataFrame(res)
    # template-level paired difference in log-loss: (conf+D) - conf, and full+D - full
    per = []
    for anc in sorted(e.ancestor.unique()):
        m = (e.ancestor == anc).to_numpy()
        def ll(k):
            p = np.clip(oof[k][m], 1e-6, 1 - 1e-6)
            return float(-np.mean(y[m] * np.log(p) + (1 - y[m]) * np.log(1 - p)))
        per.append(dict(template=anc, n=int(m.sum()), errors=int((1 - y[m]).sum()),
                        d_logloss_add_D_to_conf=ll("conf+D") - ll("conf"),
                        d_logloss_add_D_to_full=ll("conf+margin+negH+D") - ll("conf+margin+negH")))
    per = pd.DataFrame(per)
    X2.to_csv(OUT / "x2_incremental_utility_lotemplate.csv", index=False, lineterminator="\n")
    per.to_csv(OUT / "x2_incremental_utility_per_template.csv", index=False, lineterminator="\n")
    # X3 artifact test (all windows)
    x3 = []
    for t, g in preds.groupby("topology"):
        x3.append(dict(topology=t, n=len(g), auroc_1mD_for_error=auroc(1 - g.D, ~g.correct),
                       auroc_1mD_for_disputed=auroc(1 - g.D, g.attribution_disputed),
                       share_disputed=g.attribution_disputed.mean()))
    pd.DataFrame(x3).to_csv(OUT / "x3_D_artifact_test.csv", index=False, lineterminator="\n")
    return X2, per


def synthetic():
    rng = np.random.default_rng(SEED)
    rows = []
    for sep in (0.5, 1.0, 2.0):
        n = 4000
        y = rng.integers(0, 2, n)
        X = rng.normal(size=(n, 4))
        X[:, 0] += sep * (2 * y - 1) / 2          # informative feature 0
        X[:, 1] += sep * (2 * y - 1) / 2          # informative feature 1 (hidden from classifier c)
        tr, te = np.arange(n) < 2000, np.arange(n) >= 2000
        bayes = 1 / (1 + np.exp(-sep * (X[:, 0] + X[:, 1])))       # exact posterior P(y=1|x) for this design
        clfs = {"a_calibrated_bayes": bayes,
                "b_overconfident_T0.2": 1 / (1 + np.exp(-sep * (X[:, 0] + X[:, 1]) / 0.2)),
                "c_blind_to_feature_1": 1 / (1 + np.exp(-sep * X[:, 0] / np.sqrt(1 + 0)))}
        es = EmpiricalSupport(DConfig(k=25)).fit(X[tr], [str(v) for v in y[tr]], np.arange(tr.sum()) % 50,
                                                 np.arange(tr.sum()) % 100, ["0", "1"])
        D = es.compute(X[te], np.full(te.sum(), 999))["D"].to_numpy()
        for name, p in clfs.items():
            pt = p[te]
            conf = np.maximum(pt, 1 - pt)
            corr = ((pt >= 0.5).astype(int) == y[te])
            ytr, yte = None, corr.astype(float)
            # fit on half of the test half, evaluate on the other half (synthetic, independent draws)
            h = np.arange(te.sum()) < te.sum() // 2
            lc = logit(conf)
            res = {}
            for k, Xf in {"conf": lc[:, None], "conf+D": np.column_stack([lc, D])}.items():
                mu, sd = Xf[h].mean(0), Xf[h].std(0) + 1e-12
                w = fit_lr((Xf[h] - mu) / sd, yte[h])
                pp = np.clip(predict(w, (Xf[~h] - mu) / sd), 1e-6, 1 - 1e-6)
                res[k] = float(-np.mean(yte[~h] * np.log(pp) + (1 - yte[~h]) * np.log(1 - pp)))
            rows.append(dict(separation=sep, classifier=name, accuracy=corr.mean(), auroc_conf=auroc(conf, corr),
                             auroc_D=auroc(D, corr), logloss_conf=res["conf"], logloss_conf_plus_D=res["conf+D"],
                             delta_logloss=res["conf+D"] - res["conf"], status="SYNTHETIC (method check only)"))
    S = pd.DataFrame(rows)
    S.to_csv(OUT / "x5_synthetic_dx_control.csv", index=False, lineterminator="\n")
    return S


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--r2-run", type=Path, default=os.environ.get("H2PRISM_R2_RUN"))
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    cfg, preds, dec, src = h1.load(Path(a.r2_run))
    X2, per = r2_part(preds, cfg)
    s = pd.read_csv(REPO / "03_results/primary_protocol/SENSITIVITY_SUMMARY/sensitivity_summary.csv")
    s[["analysis", "population_note", "target", "status", "run_id"]].to_csv(OUT / "x4_registered_sensitivities.csv", index=False,
                                                                            lineterminator="\n")
    S = synthetic()
    print(X2.to_string()); print(per.describe().to_string()); print(S.round(4).to_string())


if __name__ == "__main__":
    main()
