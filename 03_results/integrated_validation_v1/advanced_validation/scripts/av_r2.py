"""R2 false-specific accounting, negative controls and leakage checks (EXPLORATORY_POST_HOC).

Reuses the hash-verified loader and the registered selection of h1_validation/scripts/h1_analysis.py.
Nothing frozen is written; no model is refit.
Usage: python av_r2.py --r2-run <frozen R2 run directory>
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

AV = Path(__file__).resolve().parents[1]
H1S = AV.parent / "h1_validation/scripts"
sys.path.insert(0, str(H1S))
import h1_analysis as h1  # noqa: E402

pp = h1.pp
GRID = h1.GRID
METHODS = ["s_C", "s_C_minus_D", "confidence", "margin", "neg_entropy", "D_only", h1.BASELINE]
TAG = "EXPLORATORY_POST_HOC"


def write(df, name):
    (AV / "analysis").mkdir(parents=True, exist_ok=True)
    df.to_csv(AV / "analysis" / name, index=False, lineterminator="\n", float_format="%.10g")
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--r2-run", type=Path, default=os.environ.get("H2PRISM_R2_RUN"))
    a = ap.parse_args()
    cfg, preds, dec, src = h1.load(Path(a.r2_run))
    pol = pp._policies(cfg)["primary"]
    av = np.zeros(len(preds), bool)
    for f, pf in preds.groupby("fold"):
        av[pf.index] = pp._available(np.zeros(len(pf)), pf.support_flags.fillna(""), pol)
    err = ~preds.correct.to_numpy()
    conf = preds.score_confidence.to_numpy()
    disp = preds.attribution_disputed.to_numpy()
    yt, yh = preds.y_true.to_numpy(), preds.y_hat.to_numpy()
    N = len(preds)
    rows, cls_rows, neg = [], [], []

    def account(name, c, m, eligible_mask):
        sel_err = m & err
        rej = eligible_mask & ~m
        rows.append({"coverage_requested": c, "method": name, "n_population": N, "n_specific": int(m.sum()),
                     "coverage": m.sum() / N, "n_wrong_specific": int(sel_err.sum()), "n_correct_specific": int((m & ~err).sum()),
                     "wrong_specific_risk": sel_err.sum() / m.sum() if m.sum() else np.nan,
                     "wrong_conf_ge_0.9": int((sel_err & (conf >= 0.9)).sum()),
                     "wrong_conf_lt_0.9": int((sel_err & (conf < 0.9)).sum()),
                     "wrong_in_disputed_runs": int((sel_err & disp).sum()), "wrong_in_undisputed_runs": int((sel_err & ~disp).sum()),
                     "eligible_not_selected": int(rej.sum()),
                     "error_rate_eligible_not_selected": err[rej].mean() if rej.any() else np.nan,
                     "errors_blocked_by_evidence_flags": int((err & ~eligible_mask).sum()),
                     "ancestors_selected": int(preds.ancestor[m].nunique()),
                     "ancestors_with_wrong_specific": int(preds.ancestor[sel_err].nunique()),
                     "families_with_wrong_specific": int(preds.Scenario_Family_ID[sel_err].nunique())})
        for y in ("NORMAL", "LEAK", "COMPRESSOR_FAULT", "COMPRESSOR_DELAY"):
            mm = m & (yt == y)
            cls_rows.append({"coverage_requested": c, "method": name, "true_class": y, "n_class_windows": int((yt == y).sum()),
                             "n_specific": int(mm.sum()), "class_coverage": mm.sum() / max((yt == y).sum(), 1),
                             "n_wrong_specific": int((mm & err).sum()),
                             "wrong_specific_risk": (mm & err).sum() / mm.sum() if mm.sum() else np.nan,
                             "ancestors_specific": int(preds.ancestor[mm].nunique())})
        nm = m & (yt == "NORMAL")
        neg.append({"coverage_requested": c, "method": name, "normal_windows": int((yt == "NORMAL").sum()),
                    "normal_specific": int(nm.sum()), "false_leak_calls": int((nm & (yh == "LEAK")).sum()),
                    "false_fault_or_delay_calls": int((nm & np.isin(yh, ["COMPRESSOR_FAULT", "COMPRESSOR_DELAY"])).sum()),
                    "normal_ancestors": int(preds.ancestor[yt == "NORMAL"].nunique())})

    # A: no abstention (every window is a specific diagnosis)
    account("A_classifier_no_abstention", 1.0, np.ones(N, bool), np.ones(N, bool))
    for c in GRID:
        S = h1.selections(preds, cfg, c)
        for meth in METHODS:
            account(meth, c, S[meth], np.ones(N, bool) if meth == h1.BASELINE else av)
    write(pd.DataFrame(rows).assign(analysis_status=TAG), "av_r2_wrong_specific_accounting.csv")
    write(pd.DataFrame(cls_rows).assign(analysis_status=TAG), "av_r2_wrong_specific_by_class.csv")
    write(pd.DataFrame(neg).assign(analysis_status=TAG), "av_r2_negative_control_normal.csv")
    # shared-coverage eligibility matrix (registered targets + exploratory grid) per fold
    em = []
    for f, pf in preds.groupby("fold"):
        n = len(pf)
        for v, pv in pp._policies(cfg).items():
            e = int(pp._available(np.zeros(n), pf.support_flags.fillna(""), pv).sum())
            for c in (*GRID, 0.6, 0.8, 0.9):
                req = int(np.ceil(c * n - 1e-9))
                em.append({"fold": f, "held_out_topology": pf.topology.iloc[0], "variant": v, "coverage": c,
                           "registered_target": c in (0.6, 0.8, 0.9), "requested_count": req, "eligible": e,
                           "estimable": req <= e})
    write(pd.DataFrame(em), "av_r2_shared_coverage_eligibility.csv")
    # leakage checks on R2: template (ancestor) sharing between held-out and training topologies
    lk = []
    for f, pf in preds.groupby("fold"):
        train = preds[preds.fold != f]
        shared = pf.ancestor.isin(set(train.ancestor))
        lk.append({"fold": f, "held_out_topology": pf.topology.iloc[0], "test_ancestors": pf.ancestor.nunique(),
                   "test_ancestors_also_in_training_topologies": int(pf[shared].ancestor.nunique()),
                   "share_test_windows_with_training_ancestor": shared.mean(),
                   "test_families_in_training": int(pf.Scenario_Family_ID.isin(set(train.Scenario_Family_ID)).sum())})
    write(pd.DataFrame(lk), "av_r2_template_sharing.csv")
    # training vs held-out gap (inner-selection macro-F1 vs outer accuracy per fold)
    sel = pd.concat([pd.read_csv(h1.R2 / "folds" / f"fold_{f}" / "selection.csv") for f in (1, 2, 3)])
    gap = []
    for f, pf in preds.groupby("fold"):
        s = sel[(sel.fold == f) & sel.selected].iloc[0]
        gap.append({"fold": f, "held_out_topology": pf.topology.iloc[0], "inner_cv_macro_f1_selected": s.inner_macro_f1,
                    "outer_test_accuracy": pf.correct.mean(),
                    "outer_test_accuracy_undisputed_runs": pf[~pf.attribution_disputed].correct.mean()
                    if (~pf.attribution_disputed).any() else np.nan})
    write(pd.DataFrame(gap), "av_r2_train_test_gap.csv")
    print("ok")


if __name__ == "__main__":
    main()
