"""Verify the v2 package independently of the scripts that built it; write SHA256SUMS.csv.

Checks: figure hashes and QA status; key numbers reconciled against independent sources (frozen R2 class metrics,
published HY2RES table, v1 isolability record, v1 baseline D(Y) outcomes); every RESULTS_INDEX source exists with its
recorded hash; no tracked file outside the package is modified. Writes 07_reproducibility/V2_VERIFICATION.csv.
Usage (repository root): python .../verify_v2.py   (H2PRISM_R2_RUN for the R2 reconciliation)
"""
import hashlib
import os
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

V2 = Path(__file__).resolve().parents[2]
REPO = Path(__file__).resolve().parents[4]
AV = REPO / "03_results/integrated_validation_v1/advanced_validation"
AN = V2 / "04_results/analysis"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    rows = []

    def chk(item, reported, expected, ok):
        rows.append(dict(item=item, reported=str(reported), expected=str(expected), match=bool(ok)))

    m = pd.read_csv(V2 / "05_figures/V2_FIGURE_MANIFEST.csv")
    for r in m.itertuples():
        for k in ("png", "svg"):
            p = REPO / getattr(r, k)
            chk(f"{r.figure_id}.{k} sha256", getattr(r, f"{k}_sha256")[:16], sha(p)[:16] if p.exists() else "missing",
                p.exists() and sha(p) == getattr(r, f"{k}_sha256"))
        chk(f"{r.figure_id} QA", r.qa_status, "APPROVED", r.qa_status == "APPROVED")
    # R2 class metrics vs the frozen run's own class_metrics.csv
    run = Path(os.environ.get("H2PRISM_R2_RUN", REPO / "../H2-PRISM/03_results/primary_protocol/PRIMARY"))
    fz = pd.read_csv(run / "class_metrics.csv")
    fz = fz[fz.analysis == "primary"].set_index("class")
    mine = pd.read_csv(AN / "r1_class_metrics.csv")
    mine = mine[(mine.scope == "all_windows") & (mine.cls != "ALL")].set_index("cls")
    for c in fz.index:
        for k in ("precision", "recall"):
            chk(f"R2 {c} {k} vs frozen class_metrics", round(mine.loc[c, k], 9), round(fz.loc[c, k], 9),
                np.isclose(mine.loc[c, k], fz.loc[c, k], atol=1e-9))
    # HY2RES reproduction and certified totals
    eq = pd.read_csv(AN / "h2_hy2res_equivalence_summary.csv").iloc[0]
    chk("HY2RES frozen rule reproduces published table", eq.frozen_rule_reproduced_vs_published_table, True,
        bool(eq.frozen_rule_reproduced_vs_published_table))
    h = pd.read_csv(AN / "h1_hy2res_certified_vs_frozen.csv")
    chk("HY2RES rows accounted", int(h.rows.sum()), int(eq.test_rows), h.rows.sum() == eq.test_rows)
    chk("HY2RES certified wrong SPECIFIC", int(eq.certified_specific_wrong_vs_power_label), 0, eq.certified_specific_wrong_vs_power_label == 0)
    # isolability at REF vs the v1 template-level record (different code path: v1 uses fixed eps, v2 the lambda* scale)
    v1 = pd.read_csv(AV / "analysis/dy_pairwise_isolability.csv")
    v1r = v1[(v1.scenario == "REF") & v1.config.isin(["all", "pressure_only", "flow_only"])]
    i1 = pd.read_csv(AN / "i1_isolability_onset.csv")
    for cfg in ("all", "pressure_only", "flow_only"):
        a = set(map(tuple, i1[(i1.channels == cfg) & i1.isolable_at_REF][["hyp_a", "hyp_b"]].values))
        b = set(map(tuple, v1r[(v1r.config == cfg) & v1r.isolable][["hyp_a", "hyp_b"]].values))
        chk(f"isolable pairs at REF ({cfg}) v2 lambda* vs v1", len(a), len(b), a == b)
    # unperturbed stress baseline vs v1 E1 'all' runs at S4 and REF
    st = pd.read_csv(AN / "s1_dy_synthetic_stress_runs.csv")
    base = st[st.fault == "none"].set_index(["query", "scenario"]).outcome
    e1 = pd.read_csv(AV / "analysis/dy_experiment_runs.csv")
    e1 = e1[(e1.experiment == "E1_sensors") & (e1.config == "all") & e1.scenario.isin(["S4", "REF"])]
    e1o = e1.set_index(["query", "scenario"]).outcome
    same = all(base.loc[k] == e1o.loc[k] for k in base.index)
    chk("stress baseline equals v1 E1 all-channel outcomes (S4, REF)", int(same), 1, same)
    # results index sources
    idx = pd.read_csv(V2 / "04_results/tables/RESULTS_INDEX.csv")
    ok = all((REPO / f).exists() and sha(REPO / f) == s for f, s in zip(idx.file, idx.sha256))
    chk("RESULTS_INDEX sources present with recorded hash", int(ok), 1, ok)
    # nothing outside the package changed
    st_ = subprocess.run(["git", "status", "--porcelain"], cwd=REPO, capture_output=True, text=True).stdout.splitlines()
    outside = [l for l in st_ if not l[3:].startswith(("03_results/integrated_validation_v2", "tests/test_dy_adversarial.py", "matlab_backups"))]
    chk("files changed outside the package", len(outside), 0, not outside)
    V = pd.DataFrame(rows)
    (V2 / "07_reproducibility").mkdir(exist_ok=True)
    V.to_csv(V2 / "07_reproducibility/V2_VERIFICATION.csv", index=False, lineterminator="\n")
    files = sorted(p for p in V2.rglob("*") if p.is_file() and p.name != "SHA256SUMS.csv" and "__pycache__" not in p.parts)
    pd.DataFrame({"file": [p.relative_to(V2).as_posix() for p in files], "sha256": [sha(p) for p in files],
                  "bytes": [p.stat().st_size for p in files]}).to_csv(V2 / "SHA256SUMS.csv", index=False, lineterminator="\n")
    print(f"{int(V.match.sum())}/{len(V)} checks pass")
    print(V[~V.match].to_string())


if __name__ == "__main__":
    main()
