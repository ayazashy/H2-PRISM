"""Baseline reproduction and data-integrity audit (01_audit). Read-only with respect to frozen evidence.

Checks, each written as one row of 01_audit/BASELINE_REPRODUCTION.csv:
  * git branch, HEAD and whether any tracked file outside the v2 package and the new test file is modified;
  * SHA-256 of the frozen R2 inputs and Center/HY2RES sources against the hashes recorded by the v1 H1 package;
  * Center raw MAT captures re-hashed by center_enhancement.load (raises on any mismatch);
  * HY2RES CSV MD5 against the value asserted by the frozen HY2RES builder;
  * the v1 package verifiers (verify_package.py, verify_av.py) re-run; their outputs must leave git clean;
  * the full pytest suite (junit XML parsed for counts; log kept in 03_execution/logs).
Usage: python audit_baseline.py --r2-run <frozen R2 run> --workspace <Center workspace> --hy2res <csv>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

V2 = Path(__file__).resolve().parents[2]
REPO = Path(__file__).resolve().parents[4]
V1 = REPO / "03_results/integrated_validation_v1"
LOGS = V2 / "03_execution/logs"
OWN = ("03_results/integrated_validation_v2/", "tests/test_dy_adversarial.py")


def sha(p, algo="sha256"):
    return hashlib.new(algo, Path(p).read_bytes()).hexdigest()


def git(*a):
    return subprocess.run(["git", *a], cwd=REPO, capture_output=True, text=True).stdout.rstrip()


def foreign_changes():
    lines = [l for l in git("status", "--porcelain").splitlines() if l]
    return [l for l in lines if not any(l[3:].startswith(o) for o in OWN) and not l[3:].startswith("matlab_backups")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--r2-run", type=Path, default=os.environ.get("H2PRISM_R2_RUN"))
    ap.add_argument("--workspace", type=Path, default=os.environ.get("H2PRISM_CENTER_WORKSPACE"))
    ap.add_argument("--hy2res", type=Path, required=True)
    ap.add_argument("--skip-pytest", action="store_true")
    ap.add_argument("--reuse-pytest-log", action="store_true", help="parse the existing log instead of re-running (~19 min)")
    a = ap.parse_args()
    LOGS.mkdir(parents=True, exist_ok=True)
    rows = []

    def rec(check, observed, expected, ok, evidence):
        rows.append(dict(check=check, observed=observed, expected=expected, status="PASS" if ok else "FAIL", evidence=evidence))

    rec("git branch", git("branch", "--show-current"), "research/integrated-validation",
        git("branch", "--show-current") == "research/integrated-validation", "git branch --show-current")
    rec("git HEAD at audit", git("rev-parse", "--short", "HEAD"), "recorded", True, "git rev-parse HEAD")
    fc = foreign_changes()
    rec("tracked changes outside v2 package", len(fc), 0, not fc, "; ".join(fc) or "git status --porcelain")
    rec_hash = json.loads((V1 / "h1_validation/analysis/h1_summary.json").read_text())["sources_sha256"]
    src = {"r2_predictions.parquet": a.r2_run / "predictions.parquet", "r2_decisions.parquet": a.r2_run / "decisions.parquet",
           "FINAL_EXPERIMENT_CONFIG.yaml": REPO / "06_audit_preparation/FINAL_EXPERIMENT_CONFIG.yaml",
           "source_model_attribution.csv": REPO / "03_results/diagnostics/forensics/source_model_attribution.csv"}
    for k, p in src.items():
        ok = p.exists() and sha(p) == rec_hash[k]
        rec(f"sha256 {k}", sha(p)[:16] if p.exists() else "missing", rec_hash[k][:16], ok,
            "v1 h1_validation/analysis/h1_summary.json sources_sha256")
    sys.path.insert(0, str(REPO / "src"))
    from h2prism import center_enhancement as ce
    t0 = time.perf_counter()
    d = ce.load(a.workspace)
    rec("Center raw captures re-hashed on load", len(d.hashes), "all verified (load raises on mismatch)", True,
        f"center_enhancement.load, {time.perf_counter() - t0:.1f} s")
    md5 = sha(a.hy2res, "md5")
    rec("HY2RES CSV md5", md5[:16], "9a3c3e3b1668596854b43bfd790d3e0e"[:16], md5 == "9a3c3e3b1668596854b43bfd790d3e0e",
        "assert in hy2res_external_validation/publication/distinguishability/build_distinguishability.py")
    py = sys.executable
    own_untracked = len([l for l in git("status", "--porcelain").splitlines() if l[3:].startswith(OWN)])
    for name, script in (("v1 publication package verifier", V1 / "publication_q1/scripts/verify_package.py"),
                         ("v1 advanced-validation verifier", V1 / "advanced_validation/scripts/verify_av.py")):
        t0 = time.perf_counter()
        r = subprocess.run([py, str(script)], cwd=REPO, capture_output=True, text=True,
                           env={**os.environ, "PYTHONPATH": str(REPO / "src")})
        (LOGS / f"{script.stem}.log").write_text(r.stdout + r.stderr, encoding="utf-8", newline="\n")
        # The verifiers rewrite their committed QC records. Accept only the expected difference (the
        # 'files changed outside the package' row, which counts this uncommitted v2 work, and the checksum of
        # that QC file), then restore the committed bytes so no v1 record is altered.
        changed = [l[3:] for l in git("status", "--porcelain", "--", str(V1.relative_to(REPO))).splitlines()]
        qc_lines = [l for c in changed if c.endswith("VERIFICATION.csv")
                    for l in git("diff", "-U0", "--", c).splitlines() if l[:1] in "+-" and l[:3] not in ("+++", "---")]
        sums_ok = all(any(q in l for q in ("VERIFICATION.csv",)) for c in changed if c.endswith("SHA256SUMS.csv")
                      for l in git("diff", "-U0", "--", c).splitlines() if l[:1] in "+-" and l[:3] not in ("+++", "---"))
        only_outside = all("files changed outside the package" in l for l in qc_lines)
        if changed:
            subprocess.run(["git", "checkout", "--", *changed], cwd=REPO, check=True)
        expected_only = (r.returncode == 0 and not changed) or (only_outside and sums_ok and
                                                                 all(c.endswith(("VERIFICATION.csv", "SHA256SUMS.csv")) for c in changed))
        rec(name, f"exit {r.returncode}; rewritten QC files {len(changed)} (restored)",
            f"all checks pass except 'files changed outside the package' = uncommitted v2 work ({own_untracked} entries)",
            expected_only, f"03_execution/logs/{script.stem}.log ({time.perf_counter() - t0:.0f} s)")
    log = LOGS / "pytest_full.log"
    if not a.skip_pytest and not a.reuse_pytest_log:
        t0 = time.perf_counter()
        r = subprocess.run([py, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--continue-on-collection-errors"], cwd=REPO,
                           capture_output=True, text=True, env={**os.environ, "PYTHONPATH": str(REPO / "src")})
        log.write_text(r.stdout[-20000:] + r.stderr[-5000:] + f"\nWALL_S {time.perf_counter() - t0:.0f}\n",
                       encoding="utf-8", newline="\n")
        # tests may rewrite tracked governance records; restore committed bytes and report it
        touched = [l[3:] for l in git("status", "--porcelain").splitlines() if l[:2] == " M" and not l[3:].startswith(OWN)]
        if touched:
            subprocess.run(["git", "checkout", "--", *touched], cwd=REPO, check=True)
        (LOGS / "pytest_restored_files.txt").write_text("\n".join(touched) + "\n", encoding="utf-8", newline="\n")
    if not a.skip_pytest:
        txt = log.read_text(encoding="utf-8")
        summ = [l for l in txt.splitlines() if " in " in l and ("passed" in l or "failed" in l)][-1]
        cnt = {k: int(v) for v, k in re.findall(r"(\d+) (passed|failed|skipped|errors?)", summ)}
        err = sorted(set(re.findall(r"^ERROR (\S+)", txt, re.M)))
        restored = (LOGS / "pytest_restored_files.txt").read_text(encoding="utf-8").split() if (LOGS / "pytest_restored_files.txt").exists() else []
        rec("full pytest suite", summ.strip("= "), "0 failed; errors only the known blocker",
            cnt.get("failed", 0) == 0 and err in ([], ["tests/test_faisal_pipeline.py"]),
            "03_execution/logs/pytest_full.log; failures triaged in 01_audit/TEST_FAILURE_TRIAGE.csv")
        rec("known blocker: tests/test_faisal_pipeline.py import", "; ".join(err) or "none",
            "documented in commit 6eddd4a: Stage-2 modules need the pre-merge windows.py (owner decision)",
            err == ["tests/test_faisal_pipeline.py"], "git show 6eddd4a; KNOWN_BLOCKED, not repaired here (owner-controlled code)")
        rec("tracked files rewritten by the test suite (restored)", "; ".join(restored) or "none", "none",
            not restored, "03_execution/logs/pytest_restored_files.txt")
    out = V2 / "01_audit"
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out / "BASELINE_REPRODUCTION.csv", index=False, lineterminator="\n")
    print(pd.DataFrame(rows).to_string())


if __name__ == "__main__":
    main()
