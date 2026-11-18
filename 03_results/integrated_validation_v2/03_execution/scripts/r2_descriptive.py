"""Descriptive diagnostic performance of the frozen R2 classifier (Part 5; EXPLORATORY, labels disputed under D1).

No model is refit. Every metric is reported (a) on all windows and (b) restricted to runs whose source-model
attribution is consistent with the manifest, because 36/57 runs carry disputed attribution. Units:
  window level (dependent windows), run level (majority vote of a run's windows), family and ancestor counts.
Outputs (04_results/analysis): r1_class_metrics.csv, r1_confusion.csv, r1_unit_level.csv
Usage: python r2_descriptive.py --r2-run <frozen R2 run>
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

OUT = V2 / "04_results/analysis"


def metrics(g, scope):
    rows, C = [], h1.CLASSES
    for c in C:
        tp = int(((g.y_hat == c) & (g.y_true == c)).sum())
        fp = int(((g.y_hat == c) & (g.y_true != c)).sum())
        fn = int(((g.y_hat != c) & (g.y_true == c)).sum())
        prec = tp / (tp + fp) if tp + fp else np.nan
        rec = tp / (tp + fn) if tp + fn else np.nan
        f1 = 2 * prec * rec / (prec + rec) if tp and not np.isnan(prec + rec) else (0.0 if tp + fp + fn else np.nan)
        rows.append(dict(scope=scope, cls=c, support_windows=int((g.y_true == c).sum()),
                         support_runs=g[g.y_true == c].Scenario_ID.nunique(),
                         support_families=g[g.y_true == c].Scenario_Family_ID.nunique(),
                         support_ancestors=g[g.y_true == c].ancestor.nunique(), precision=prec, recall=rec, f1=f1))
    df = pd.DataFrame(rows)
    present = df[df.support_windows > 0]
    df = pd.concat([df, pd.DataFrame([dict(scope=scope, cls="ALL", support_windows=len(g), support_runs=g.Scenario_ID.nunique(),
                                           support_families=g.Scenario_Family_ID.nunique(), support_ancestors=g.ancestor.nunique(),
                                           precision=np.nan, recall=float(g.correct.mean()), f1=np.nan,
                                           balanced_accuracy=float(present.recall.mean()), macro_f1=float(present.f1.mean()),
                                           classes_present=len(present))])])
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--r2-run", type=Path, default=os.environ.get("H2PRISM_R2_RUN"))
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    cfg, p, dec, src = h1.load(Path(a.r2_run))
    scopes = {"all_windows": p, "undisputed_runs_only": p[~p.attribution_disputed]}
    M = pd.concat([metrics(g, s) for s, g in scopes.items()] +
                  [metrics(g, f"topology={t}") for t, g in p.groupby("topology")])
    M.to_csv(OUT / "r1_class_metrics.csv", index=False, lineterminator="\n")
    conf = pd.concat([pd.crosstab(g.y_true, g.y_hat).reindex(index=h1.CLASSES, columns=h1.CLASSES, fill_value=0)
                      .assign(scope=s).reset_index() for s, g in scopes.items()])
    conf.to_csv(OUT / "r1_confusion.csv", index=False, lineterminator="\n")
    runs = p.groupby("Scenario_ID").agg(y_true=("y_true", "first"), topology=("topology", "first"),
                                        family=("Scenario_Family_ID", "first"), ancestor=("ancestor", "first"),
                                        disputed=("attribution_disputed", "first"), windows=("y_true", "size"),
                                        window_accuracy=("correct", "mean"),
                                        run_vote=("y_hat", lambda s: s.value_counts().idxmax()))
    runs["run_correct"] = runs.run_vote == runs.y_true
    U = []
    for s, g in {"all": runs, "undisputed": runs[~runs.disputed], "disputed": runs[runs.disputed]}.items():
        U.append(dict(scope=s, runs=len(g), families=g.family.nunique(), ancestors=g.ancestor.nunique(),
                      run_majority_accuracy=float(g.run_correct.mean()) if len(g) else np.nan,
                      mean_window_accuracy_per_run=float(g.window_accuracy.mean()) if len(g) else np.nan,
                      normal_runs=int((g.y_true == "NORMAL").sum()),
                      normal_runs_called_event=int(((g.y_true == "NORMAL") & (g.run_vote != "NORMAL")).sum()),
                      event_runs=int((g.y_true != "NORMAL").sum()),
                      event_runs_called_normal=int(((g.y_true != "NORMAL") & (g.run_vote == "NORMAL")).sum())))
    pd.DataFrame(U).to_csv(OUT / "r1_unit_level.csv", index=False, lineterminator="\n")
    print(M.round(3).to_string()); print(pd.DataFrame(U).round(3).to_string())


if __name__ == "__main__":
    main()
