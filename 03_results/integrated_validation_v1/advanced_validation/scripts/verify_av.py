"""Verify the advanced-validation package: figure hashes and QA, invariant and certificate results,
table reconciliations against analysis outputs, and that nothing outside the package changed.
Writes quality_control/AV_VERIFICATION.csv. Usage (repository root): python .../scripts/verify_av.py
"""
import hashlib
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

AV = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[4]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    rows = []

    def chk(item, reported, expected, ok):
        rows.append(dict(item=item, reported=reported, expected=expected, match=bool(ok)))

    m = pd.read_csv(AV / "quality_control/AV_FIGURE_MANIFEST.csv")
    for r in m.itertuples():
        for k in ("png", "svg"):
            p = REPO / getattr(r, k)
            chk(f"{r.figure_id}.{k} sha256", getattr(r, f"{k}_sha256")[:16], sha(p)[:16] if p.exists() else "missing",
                p.exists() and sha(p) == getattr(r, f"{k}_sha256"))
        chk(f"{r.figure_id} QA", r.qa_status, "APPROVED", r.qa_status == "APPROVED")
    d = pd.read_csv(AV / "analysis/dy_experiment_runs.csv")
    chk("decisions computed", len(d), 2376, len(d) == 2376)
    chk("exclusion certificates re-verified", int(d.excl_cert_verified.sum()), int(d.excl_cert_total.sum()),
        d.excl_cert_verified.sum() == d.excl_cert_total.sum())
    chk("feasibility witnesses re-verified", int(d.witness_verified.sum()), int(d.witness_total.sum()),
        d.witness_verified.sum() == d.witness_total.sum())
    inv = pd.read_csv(AV / "analysis/dy_invariant_checks.csv")
    chk("invariant violations", int(inv.violations.sum()), 0, inv.violations.sum() == 0)
    a08 = pd.read_csv(AV / "tables/A08.csv").set_index("config_family")
    e1 = d[(d.experiment == "E1_sensors") & (d.config == "flow_only")]
    chk("A08 flow_only wrong SPECIFIC vs runs", int(a08.loc["flow_only", "specific_wrong"]), int((e1.outcome == "SPECIFIC_WRONG").sum()),
        int(a08.loc["flow_only", "specific_wrong"]) == int((e1.outcome == "SPECIFIC_WRONG").sum()))
    a01 = pd.read_csv(AV / "tables/A01.csv")
    h = pd.read_csv(AV.parent / "h1_validation/analysis/h1_05_paired_comparisons.csv")
    chk("A01 rows equal H1 paired comparisons", len(a01), len(h), len(a01) == len(h) and np.allclose(a01.delta_R, h.delta_R))
    acc = pd.read_csv(AV / "analysis/av_r2_wrong_specific_accounting.csv")
    s = pd.read_csv(AV.parent / "h1_validation/analysis/h1_04_selection_by_method.csv")
    s = s[s.scope == "pooled"]
    mm = acc.merge(s, left_on=["coverage_requested", "method"], right_on=["coverage", "method"])
    chk("A02a wrong counts equal H1 selections", int((mm.n_wrong_specific == mm.n_errors).sum()), len(mm),
        (mm.n_wrong_specific == mm.n_errors).all())
    iso = pd.read_csv(AV / "analysis/dy_pairwise_isolability.csv")
    ms = pd.read_csv(AV / "analysis/dy_minimum_sensor_sets.csv").set_index("scenario")
    chk("REF isolable pairs (all channels) vs minimum-set record", int(iso[(iso.scenario == "REF") & (iso.config == "all")].isolable.sum()),
        int(ms.loc["REF", "isolable_pairs_full_set"]),
        int(iso[(iso.scenario == "REF") & (iso.config == "all")].isolable.sum()) == int(ms.loc["REF", "isolable_pairs_full_set"]))
    st = subprocess.run(["git", "status", "--porcelain"], cwd=REPO, capture_output=True, text=True).stdout.splitlines()
    outside = [l for l in st if not l[3:].startswith("03_results/integrated_validation_v1")]
    chk("files changed outside the package", len(outside), 0, not outside)
    V = pd.DataFrame(rows)
    V.to_csv(AV / "quality_control/AV_VERIFICATION.csv", index=False, lineterminator="\n")
    print(f"{int(V.match.sum())}/{len(V)} checks pass")
    if not V.match.all():
        print(V[~V.match].to_string())
        sys.exit(1)


if __name__ == "__main__":
    main()
