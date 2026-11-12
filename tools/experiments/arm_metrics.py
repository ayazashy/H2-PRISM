#!/usr/bin/env python3
"""
Prespecified metrics for one ablation arm from its recorded run outputs (h2prism.evaluation_metrics; no fitting).

For Arm A (protocol 1.1 reference = R2) this reads 03_results/primary_protocol/PRIMARY. Because every R2 window was an
outer-test window already inspected during the forensic work, Arm A metrics are a REFERENCE (EXPLORATORY), never a
confirmation. Outputs: 03_results/ablation/<arm_id>/{classifier_metrics,decision_metrics,score_metrics}.csv + manifest.
Usage: python tools/experiments/arm_metrics.py --arm A_P11_REFERENCE --run 03_results/primary_protocol/PRIMARY
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from h2prism import evaluation_metrics as em  # noqa: E402
from h2prism.independence import independence_groups  # noqa: E402

CLASSES = ["NORMAL", "LEAK", "COMPRESSOR_FAULT", "COMPRESSOR_DELAY"]
SCORES = ("s_C", "s_C_minus_D", "confidence", "margin", "neg_entropy", "D_only")


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def compute(run: Path, status: str):
    P = pd.read_parquet(run / "predictions.parquet")
    D = pd.read_parquet(run / "decisions.parquet")
    pc = P[[f"p_cal_{c}" for c in CLASSES]].to_numpy(float)
    yidx = P.y_true.map({c: i for i, c in enumerate(CLASSES)}).to_numpy()
    yhat = np.array(CLASSES, dtype=object)[pc.argmax(1)]
    ok = yhat == P.y_true.to_numpy()
    grp = P.Scenario_ID.map(independence_groups(P.Scenario_ID, P.Scenario_Family_ID)).to_numpy()
    conf = pc.max(1)
    cls_rows = []
    for scope, m in [("POOLED", np.ones(len(P), bool))] + [(t, (P.topology == t).to_numpy()) for t in sorted(P.topology.unique())]:
        r = {"scope": scope, **em.classifier_metrics(P.y_true[m], yhat[m], CLASSES), **em.group_level_accuracy(ok[m], grp[m]),
             "ece_10": em.ece(pc[m], yidx[m]), "brier": em.brier(pc[m], yidx[m]),
             "share_errors_conf_ge_0_9": float((conf[m][~ok[m]] >= 0.9).mean()) if (~ok[m]).any() else np.nan,
             "n_errors": int((~ok[m]).sum())}
        cls_rows.append(r)
    sc_rows = []
    flagfree = P.support_flags.fillna("").to_numpy() == ""
    for scope, m in [("POOLED", np.ones(len(P), bool))] + [(t, (P.topology == t).to_numpy()) for t in sorted(P.topology.unique())]:
        for s in SCORES:
            v = P[f"score_{s}"].to_numpy(float)
            sc_rows.append({"scope": scope, "score": s, "auroc_correctness_all": em.auroc(v[m], ok[m]),
                            "auroc_correctness_flag_free": em.auroc(v[m & flagfree], ok[m & flagfree]),
                            "saturation_share_at_max": em.saturation(v[m])})
    dec_rows = []
    for (var, meth, tg, mo), g in D.groupby(["variant", "method", "target", "mode"]):
        for scope, gg in [("POOLED_ESTIMABLE", g)] + [(t, x) for t, x in g.groupby("topology")]:
            dec_rows.append({"variant": var, "method": meth, "target": tg, "mode": mo, "scope": scope,
                             "topologies": "|".join(sorted(gg.topology.unique())),
                             **em.decision_metrics(gg.policy_outcome, gg.y_pred_specific, gg.ambiguity_set.fillna(""), gg.y_true)})
    tag = lambda df: df.assign(evidence_status=status)  # noqa: E731
    return tag(pd.DataFrame(cls_rows)), tag(pd.DataFrame(dec_rows)), tag(pd.DataFrame(sc_rows))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True)
    ap.add_argument("--run", type=Path, required=True)
    ap.add_argument("--status", default="EXPLORATORY_REFERENCE_R2_OUTER_TEST_ALREADY_INSPECTED")
    a = ap.parse_args(argv)
    out = REPO / "03_results" / "ablation" / a.arm
    out.mkdir(parents=True, exist_ok=True)
    c, d, s = compute(a.run, a.status)
    for name, df in (("classifier_metrics", c), ("decision_metrics", d), ("score_metrics", s)):
        df.to_csv(out / f"{name}.csv", index=False, lineterminator="\n", float_format="%.6g")
    man = json.loads((a.run / "run_manifest.json").read_text(encoding="utf-8"))
    (out / "ARM_METRICS_MANIFEST.json").write_text(json.dumps({
        "arm_id": a.arm, "source_run_key": man.get("run_key"), "source_status": man.get("status"), "evidence_status": a.status,
        "source_sha256": {f: _sha(a.run / f) for f in ("predictions.parquet", "decisions.parquet")},
        "code_sha256": {"tools/experiments/arm_metrics.py": _sha(Path(__file__)),
                        "src/h2prism/evaluation_metrics.py": _sha(REPO / "src" / "h2prism" / "evaluation_metrics.py")},
        "outputs": {f"{n}.csv": _sha(out / f"{n}.csv") for n in ("classifier_metrics", "decision_metrics", "score_metrics")}},
        indent=2) + "\n", encoding="utf-8")
    print(c[["scope", "accuracy", "balanced_accuracy", "macro_f1", "group_balanced_accuracy", "worst_group_accuracy", "ece_10"]].round(3).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
