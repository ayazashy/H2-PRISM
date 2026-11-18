"""Verify the integrated publication package and write checksums.

Checks: (1) every figure listed in the manifests exists and matches its recorded SHA-256; (2) every figure is
APPROVED; (3) Times New Roman resolves to a real Times file; (4) key table numbers reconcile with their sources;
(5) no tracked frozen file is modified (git). Writes quality_control/NUMERICAL_VERIFICATION.csv and
integrated_validation_v1/SHA256SUMS.csv (all package files except the checksum file itself).
Usage (repository root): python 03_results/integrated_validation_v1/publication_q1/scripts/verify_package.py
"""
import hashlib
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

Q1 = Path(__file__).resolve().parents[1]
ROOT = Q1.parent
REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from q1style import font_path  # noqa: E402


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    rows = []

    def chk(item, reported, recomputed, ok):
        rows.append({"item": item, "reported": reported, "recomputed": recomputed, "match": bool(ok)})

    for man in (Q1 / "quality_control/FIGURE_MANIFEST.csv", ROOT / "h1_validation/quality_control/H1_FIGURE_MANIFEST.csv"):
        m = pd.read_csv(man)
        for r in m.itertuples():
            for kind in ("png", "svg"):
                p = REPO / getattr(r, kind)
                h = sha(p) if p.exists() else "missing"
                chk(f"{r.figure_id}.{kind} sha256", getattr(r, f"{kind}_sha256")[:16], h[:16], h == getattr(r, f"{kind}_sha256"))
            chk(f"{r.figure_id} QA", r.qa_status, "APPROVED", r.qa_status == "APPROVED")
            chk(f"{r.figure_id} size", f"{r.width_px}x{r.height_px}@{r.dpi}", ">=3200 px, 400 dpi",
                max(r.width_px, r.height_px) >= 3200 and r.dpi >= 400)
    fp = Path(font_path())
    chk("Times New Roman font file", fp.name, "times*.ttf", fp.name.lower().startswith("times"))
    # table reconciliation
    t02 = pd.read_csv(Q1 / "tables/T02_prediction_benchmark.csv")
    eq = pd.read_csv(REPO / "study_b/evidence_enhancement/results/analysis/error_quantiles.csv")
    for ch in ("P-2", "MFC-3"):
        for mdl, col in (("persistence", "persistence_MAE"), ("ridge", "ridge_MAE")):
            a = t02[(t02.channel == ch) & (t02.scope == "3 held-out runs pooled")][col].iloc[0]
            b = eq[(eq.run == "all 3 runs") & (eq.channel == ch) & (eq.model == mdl)]["mean"].iloc[0]
            chk(f"T02 {ch} pooled {mdl} MAE vs error_quantiles", a, b, abs(a - b) < 1e-9)
    t03 = pd.read_csv(Q1 / "tables/T03_error_resolution.csv").set_index("channel")
    q = pd.read_csv(REPO / "03_results/hy2res_external_validation/evidence_enhancement/results/tables/TAB_H02.csv").set_index("channel")
    for ch in ("pres_buf", "pres_comp"):
        a, b = t03.loc[ch, "delta_RMSE_incr"], q.loc[ch, "ridge_rmse_incr"] - q.loc[ch, "persistence_rmse_incr"]
        chk(f"T03 {ch} ΔRMSE in increments vs TAB_H02", a, b, abs(a - b) < 1e-9)
    t08 = pd.read_csv(Q1 / "tables/T08b_rq1_exploratory_shared_coverage.csv")
    h = pd.read_csv(ROOT / "h1_validation/analysis/h1_05_paired_comparisons.csv")
    h = h[h.method_b == "s_C_minus_D"].set_index("coverage")
    for r in t08.itertuples():
        chk(f"T08b Δ at {r.coverage}", r.delta_R, h.loc[r.coverage, "delta_R"], abs(r.delta_R - h.loc[r.coverage, "delta_R"]) < 1e-9)
    t07 = pd.read_csv(Q1 / "tables/T07a_dy_conditional_decisions.csv")
    r7 = t07[t07.universe == "restricted"]
    chk("T07a restricted SPECIFIC correct / wrong", f"{int(r7.specific_correct.sum())}/{int(r7.specific_wrong.sum())}", "48/11",
        int(r7.specific_correct.sum()) == 48 and int(r7.specific_wrong.sum()) == 11)
    c06 = pd.read_csv(REPO / "03_results/validation/center_evidence_enhancement/tables/TAB_C06.csv")
    rr = c06[(c06.universe == "restricted") & (c06.decision == "SPECIFIC")]
    a = t07[(t07.universe == "restricted") & (t07.group == "all") & (t07.clock_bound_s == 1.0)]
    chk("T07a all-sensor ±1 s vs TAB_C06 (8 correct, 2 wrong)", f"{int(a.specific_correct.iloc[0])}/{int(a.specific_wrong.iloc[0])}",
        f"{int((rr.correctness == 'correct').sum())}/{int((rr.correctness != 'correct').sum())}",
        int(a.specific_correct.iloc[0]) == int((rr.correctness == "correct").sum()))
    hv = pd.read_csv(ROOT / "h1_validation/analysis/h1_verification.csv")
    chk("H1 reproduction checks", f"{int(hv.match.sum())}/{len(hv)}", "all", hv.match.all())
    # frozen preservation
    st = subprocess.run(["git", "status", "--porcelain"], cwd=REPO, capture_output=True, text=True).stdout.splitlines()
    # any change outside this additive package (new, staged, modified or deleted) counts as a failure
    outside = [l for l in st if not l[3:].startswith("03_results/integrated_validation_v1")]
    chk("files changed outside the package (git status)", len(outside), 0, not outside)
    vs_base = subprocess.run(["git", "diff", "--name-only", "6eddd4a", "--", ".", ":(exclude)03_results/integrated_validation_v1"],
                             cwd=REPO, capture_output=True, text=True).stdout.split()
    chk("files differing from base 6eddd4a outside the package", len(vs_base), 0, not vs_base)
    V = pd.DataFrame(rows)
    V.to_csv(Q1 / "quality_control/NUMERICAL_VERIFICATION.csv", index=False, lineterminator="\n")
    files = sorted(p for p in ROOT.rglob("*") if p.is_file() and p.name != "SHA256SUMS.csv" and "__pycache__" not in p.parts)
    pd.DataFrame({"path": [p.relative_to(ROOT).as_posix() for p in files], "sha256": [sha(p) for p in files],
                  "bytes": [p.stat().st_size for p in files]}).to_csv(ROOT / "SHA256SUMS.csv", index=False, lineterminator="\n")
    print(f"{int(V.match.sum())}/{len(V)} checks pass; {len(files)} files hashed")
    if not V.match.all():
        print(V[~V.match].to_string())
        sys.exit(1)


if __name__ == "__main__":
    main()
