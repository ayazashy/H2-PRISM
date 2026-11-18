"""Run the three package verifiers on the committed tree and record their results (logs/VERIFIERS.csv, logs/<name>.log).

The verifiers rewrite their own output records (v1 NUMERICAL_VERIFICATION.csv, SCOPE_CHECK.csv, SHA256SUMS.csv;
AV_VERIFICATION.csv; v2 V2_VERIFICATION.csv, SHA256SUMS.csv). Those outputs are the verification record to commit.
Usage (repository root, H2PRISM_R2_RUN set): python 03_results/maintenance/verify_all.py
"""
import os
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
LOGS = REPO / "03_results/maintenance/logs"
# Order matters: each verifier fails on uncommitted changes outside its package. v2 and AV rewrite outputs that must
# reproduce their committed bytes; v1 runs last because its scope record changes with every commit. Logs are written
# only after all verifiers have run.
V = [("v2 validation package", "03_results/integrated_validation_v2/03_execution/scripts/verify_v2.py"),
     ("v1 advanced validation", "03_results/integrated_validation_v1/advanced_validation/scripts/verify_av.py"),
     ("v1 publication package", "03_results/integrated_validation_v1/publication_q1/scripts/verify_package.py")]


def main():
    rows, logs = [], {}
    for name, script in V:
        r = subprocess.run([sys.executable, script], cwd=REPO, capture_output=True, text=True,
                           env={**os.environ, "PYTHONPATH": str(REPO / "src")})
        out = r.stdout + r.stderr
        logs[Path(script).stem] = out
        m = re.search(r"(\d+)/(\d+) checks pass", out)
        ok = bool(m) and m.group(1) == m.group(2) and r.returncode == 0
        rows.append(dict(verifier=name, script=script, result=m.group(0) if m else f"exit {r.returncode}", exit_code=r.returncode,
                         status="PASS" if ok else "FAIL"))
    LOGS.mkdir(parents=True, exist_ok=True)
    for stem, out in logs.items():
        (LOGS / f"{stem}.log").write_text(out, encoding="utf-8", newline="\n")
    df = pd.DataFrame(rows)
    df.to_csv(LOGS / "VERIFIERS.csv", index=False, lineterminator="\n")
    print(df.to_string())


if __name__ == "__main__":
    main()
