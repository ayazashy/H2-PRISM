"""Re-run every v2 analysis, table, figure and report script in dependency order; record runtimes and a determinism
check (SHA-256 of every package output before vs after). Logs: 03_execution/logs/RUN_ALL.csv, DETERMINISM.csv, <script>.log.
Usage (repository root): python .../run_all.py --hy2res <HY2RES_202404.csv>   (needs H2PRISM_R2_RUN, H2PRISM_CENTER_WORKSPACE)
"""
import argparse
import hashlib
import os
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

V2 = Path(__file__).resolve().parents[2]
REPO = Path(__file__).resolve().parents[4]
S = V2 / "03_execution/scripts"
LOGS = V2 / "03_execution/logs"
SKIP = ("03_execution/logs/", "SHA256SUMS.csv", "07_reproducibility/V2_VERIFICATION.csv", "03_execution/ENVIRONMENT.txt")


def snapshot():
    out = {}
    for p in sorted(V2.rglob("*")):
        r = p.relative_to(V2).as_posix()
        if p.is_file() and not r.startswith("03_execution/scripts") and not any(r.startswith(k) or r == k for k in SKIP) \
                and "__pycache__" not in r:
            out[r] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hy2res", required=True)
    a = ap.parse_args()
    steps = [("d1_correction.py", []), ("dx_experiments.py", []), ("r2_descriptive.py", []), ("dy_stress.py", []),
             ("dy_isolability.py", []), ("hy2res_dy_adapter.py", ["--data", a.hy2res]), ("triage_tests.py", []),
             ("build_v2_tables.py", []), ("fig_v2.py", []), ("v2_reports.py", [])]
    before = snapshot()
    LOGS.mkdir(parents=True, exist_ok=True)
    rows = []
    env = {**os.environ, "PYTHONPATH": str(REPO / "src")}
    for name, args in steps:
        t0 = time.perf_counter()
        r = subprocess.run([sys.executable, str(S / name), *args], cwd=REPO, capture_output=True, text=True, env=env)
        dt = time.perf_counter() - t0
        (LOGS / f"{Path(name).stem}.log").write_text(r.stdout[-30000:] + r.stderr[-5000:], encoding="utf-8", newline="\n")
        rows.append(dict(script=name, exit_code=r.returncode, wall_s=round(dt, 1)))
        print(name, r.returncode, f"{dt:.1f} s", flush=True)
        if r.returncode:
            break
    pd.DataFrame(rows).to_csv(LOGS / "RUN_ALL.csv", index=False, lineterminator="\n")
    after = snapshot()
    det = [dict(file=k, identical=before.get(k) == after.get(k), before=(before.get(k) or "absent")[:16], after=(after.get(k) or "absent")[:16])
           for k in sorted(set(before) | set(after))]
    D = pd.DataFrame(det)
    D.to_csv(LOGS / "DETERMINISM.csv", index=False, lineterminator="\n")
    print(f"{int(D.identical.sum())}/{len(D)} outputs byte-identical after re-run")
    print(D[~D.identical].to_string())


if __name__ == "__main__":
    main()
