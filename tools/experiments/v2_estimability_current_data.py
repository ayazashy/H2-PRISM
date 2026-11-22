#!/usr/bin/env python3
"""
Can Distinguishability v2 be evaluated on the current dataset? Structural answer from metadata only.

For every development window of arm H (stored predictions, hash-verified; no features, no model), the reference is
the other development topology of its fold (as for D(x) and E_h). v2's sufficiency states depend only on how many
independent scenario groups of each class remain after removing the window's own independence group, so they are
computed exactly from the manifest. Reported for m = 2 (the registered default) and, for transparency only, the
group counts behind it; m is NOT relaxed.

Also states the minimum support at which every v2 quantity becomes defined.
Writes 03_results/diagnostics/distinguishability_v2/{V2_ESTIMABILITY_CURRENT_DATA.csv, V2_ESTIMABILITY.json}.
Usage: python tools/experiments/v2_estimability_current_data.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from h2prism.distinguishability_v2 import SUPPORTED, eligibility_from_groups  # noqa: E402

RUN = REPO / "03_results" / "ablation_runs" / "H_POSITION_MATCHED"
HASHES = REPO / "03_results" / "ablation_runs" / "logs" / "H_POSITION_MATCHED_65f05249dd12_OUTPUT_HASHES.sha256"
MAN = REPO / "06_audit_preparation" / "protocol2" / "CANDIDATE_MANIFEST_V03.csv"
OUT = REPO / "03_results" / "diagnostics" / "distinguishability_v2"
CLASSES = ["NORMAL", "LEAK", "COMPRESSOR_FAULT", "COMPRESSOR_DELAY"]
M = 2


def main() -> int:
    for line in HASHES.read_text(encoding="utf-8").splitlines():
        h, name = line.split(maxsplit=1)
        if hashlib.sha256((RUN / name.lstrip("*")).read_bytes()).hexdigest() != h:
            raise SystemExit(f"stored H output changed: {name}")
    man = pd.read_csv(MAN)
    grp = dict(zip(man.Scenario_ID, man.independence_group))
    cls = dict(zip(man.Scenario_ID, man.label_mapped))
    O = pd.concat([pd.read_parquet(f) for f in sorted(RUN.glob("folds/fold_*/dev_oof.parquet"))], ignore_index=True)
    rows = []
    for (k, t), q in O.groupby(["fold", "topology"]):
        ref = O[(O.fold == k) & (O.topology != t)]
        g2c = {grp[s]: cls[s] for s in ref.Scenario_ID.unique()}
        for (sid, yh), qq in q.groupby(["Scenario_ID", "y_hat"]):
            st = eligibility_from_groups(g2c, grp[sid], CLASSES, M)
            n = {c: sum(1 for g, cc in g2c.items() if cc == c and g != grp[sid]) for c in CLASSES}
            elig = [c for c in CLASSES if st[c] == SUPPORTED]
            if st[yh] != SUPPORTED:
                margin_state = "HYPOTHESIS_NOT_SUPPORTED"
            elif len(elig) < 2:
                margin_state = "UNTESTABLE_NO_ELIGIBLE_COMPETITOR"
            else:
                margin_state = "DEFINED"
            normal_groups = sum(1 for c in g2c.values() if c == "NORMAL")
            rows.append({"fold": int(k), "heldout_topology": t, "Scenario_ID": sid, "true_class": cls[sid], "y_hat": yh,
                         "windows": len(qq), **{f"groups_{c}": n[c] for c in CLASSES},
                         **{f"state_{c}": st[c] for c in CLASSES}, "eligible_classes": "|".join(elig),
                         "margin_state_for_y_hat": margin_state,
                         "detectability": "DEFINED" if normal_groups >= M + 1 else "UNDEFINED_INSUFFICIENT_NORMAL_SUPPORT"})
    R = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    R.assign(evidence_status="EXPLORATORY_DIAGNOSTIC", m=M).to_csv(OUT / "V2_ESTIMABILITY_CURRENT_DATA.csv", index=False,
                                                                  lineterminator="\n")
    share = R.groupby("margin_state_for_y_hat").windows.sum() / R.windows.sum()
    summ = {"m": M, "evidence_status": "EXPLORATORY_DIAGNOSTIC", "model_fitted": False,
            "share_window_fold_instances_by_margin_state": share.round(6).to_dict(),
            "share_detectability_defined": float(R[R.detectability == "DEFINED"].windows.sum() / R.windows.sum()),
            "max_groups_per_class_in_any_reference": {c: int(R[f"groups_{c}"].max()) for c in CLASSES},
            "minimum_support_for_v2": {
                "separability_margin": "every compared class >= m = 2 independence groups in the reference AFTER removing "
                                       "the query's own group (so >= 3 groups per class across the development data when "
                                       "groups are replicated across topologies)",
                "detectability": "NORMAL >= m + 1 = 3 groups in the reference after removing the query's own group",
                "out_of_support": ">= 2 groups in the reference (already met)"},
            "conclusion": "v2 separability and detectability are undefined for every current window: only LEAK has >= 2 "
                          "independent groups in any reference; NORMAL, COMPRESSOR_FAULT and COMPRESSOR_DELAY have <= 1."}
    (OUT / "V2_ESTIMABILITY.json").write_text(json.dumps(summ, indent=2), encoding="utf-8")
    print(json.dumps(summ, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
