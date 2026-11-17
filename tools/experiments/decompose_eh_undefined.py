#!/usr/bin/env python3
"""
Why E_h (arm F) was undefined for ~80% of development windows: exact reproduction and decomposition.

Recomputes E_h exactly as the runner did for arm F (same config, same features, same cross-topology references, same
hypotheses = F's stored classifier labels). E_h stores the reference and computes neighbourhood shares; no classifier
or other model is fitted. The reproduced E values are checked against F's stored score_E_evidence_margin (all
windows must match, NaN pattern included) before any decomposition is reported.

Writes 03_results/diagnostics/distinguishability_v2/{EH_UNDEFINED_DECOMPOSITION.csv, EH_REPRODUCTION.json}.
EXPLORATORY_DIAGNOSTIC. Usage: python tools/experiments/decompose_eh_undefined.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from h2prism.evidence_margin import EvidenceConfig, EvidenceMargin  # noqa: E402
from h2prism.experiments import primary_protocol as pp  # noqa: E402
from h2prism.features import model_feature_columns  # noqa: E402
from h2prism.independence import independence_groups  # noqa: E402

ARM = "F_EVIDENCE_MARGIN"
RUN = REPO / "03_results" / "ablation_runs" / ARM
CFG = REPO / "06_audit_preparation" / "protocol2" / "arms" / f"{ARM}.yaml"
OUT = REPO / "03_results" / "diagnostics" / "distinguishability_v2"


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main() -> int:
    lst = next((REPO / "03_results" / "ablation_runs" / "logs").glob(f"{ARM}_*_OUTPUT_HASHES.sha256"))
    for line in lst.read_text(encoding="utf-8").splitlines():
        h, name = line.split(maxsplit=1)
        if _sha(RUN / name.lstrip("*")) != h:
            raise SystemExit(f"stored F output changed: {name}")
    cfg = yaml.safe_load(CFG.read_text(encoding="utf-8"))
    ft, _ = pp.build_features(cfg, REPO, REPO / "data" / "raw", cfg["dataset"]["realization_primary"])
    feats = [c for c in model_feature_columns(ft) if "__" in c]
    folds = pd.read_csv(REPO / cfg["splits"]["outer"]["file"])
    classes = list(cfg["dataset"]["classes"])
    d = cfg["distinguishability"]
    ec = EvidenceConfig(k=int(d.get("k", 25)), min_units=int(d.get("evidence_min_units", 2)),
                        out_of_support_quantile=float(d.get("out_of_support_quantile", 0.99)))
    rows, match = [], []
    for k, fd in folds.groupby("outer_fold_id"):
        dev = ft[ft.Scenario_ID.isin(set(fd[fd.split_role == "train"].Scenario_ID))].copy()
        stored = pd.read_parquet(RUN / "folds" / f"fold_{k}" / "dev_oof.parquet").set_index("window_id")
        hyp = stored.loc[dev.window_id, "y_hat"].to_numpy(dtype=object)
        groups = dev.Scenario_ID.map(independence_groups(dev.Scenario_ID, dev.Scenario_Family_ID)).to_numpy()
        topo = dev.topology.to_numpy()
        for t in sorted(set(topo)):
            r, q = topo != t, topo == t
            em = EvidenceMargin(ec).fit(dev[feats].to_numpy(float)[r], dev.label_mapped.to_numpy()[r], groups[r], classes)
            res = em.compute(dev[feats].to_numpy(float)[q], list(hyp[q]), groups[q])
            res["window_id"] = dev.window_id.to_numpy()[q]
            res["fold"], res["topology"] = int(k), t
            res["true_class"] = dev.label_mapped.to_numpy()[q]
            res["query_group_in_reference"] = [g in set(groups[r]) for g in groups[q]]
            res["hypothesis_class_groups_in_reference_excluding_own"] = [
                len(set(groups[r][(dev.label_mapped.to_numpy()[r] == h) & (groups[r] != g)])) for h, g in zip(hyp[q], groups[q])]
            s = stored.loc[res.window_id, "score_E_evidence_margin"].to_numpy(float)
            e = res.E.to_numpy(float)
            match.append(bool(np.array_equal(np.isnan(s), np.isnan(e)) and np.allclose(s[~np.isnan(s)], e[~np.isnan(e)])))
            rows.append(res)
    R = pd.concat(rows, ignore_index=True)
    if not all(match):
        raise SystemExit("reproduction does not match the stored E_h: decomposition withheld")
    R["state"] = np.where(R.E.notna(), "DEFINED", R.flag)
    dec = (R.groupby(["state", "hypothesis"]).size().rename("window_fold_instances").reset_index()
           .assign(share=lambda x: x.window_fold_instances / len(R)))
    # mechanism behind HYPOTHESIS_UNSUPPORTED: after removing the query's own independence group, no group of class h
    uns = R[R.state == "HYPOTHESIS_UNSUPPORTED"]
    few = R[R.state == "INSUFFICIENT_INDEPENDENT_EVIDENCE"]
    OUT.mkdir(parents=True, exist_ok=True)
    dec.assign(evidence_status="EXPLORATORY_DIAGNOSTIC").to_csv(OUT / "EH_UNDEFINED_DECOMPOSITION.csv", index=False,
                                                               lineterminator="\n", float_format="%.6g")
    summ = {"arm": ARM, "reproduction_matches_stored_E": True, "n_window_fold_instances": int(len(R)),
            "share_undefined": float(R.E.isna().mean()),
            "share_by_state": R.state.value_counts(normalize=True).round(6).to_dict(),
            "unsupported_where_only_group_of_h_is_query_own_group": float(
                (uns.hypothesis_class_groups_in_reference_excluding_own == 0).mean()) if len(uns) else None,
            "unsupported_hypotheses": uns.hypothesis.value_counts().to_dict(),
            "insufficient_units_median_n_units": float(few.n_units.median()) if len(few) else None,
            "share_query_group_present_in_reference": float(R.query_group_in_reference.mean()),
            "evidence_status": "EXPLORATORY_DIAGNOSTIC", "model_fitted": False}
    (OUT / "EH_REPRODUCTION.json").write_text(json.dumps(summ, indent=2), encoding="utf-8")
    print(json.dumps(summ, indent=2))
    print(dec.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
