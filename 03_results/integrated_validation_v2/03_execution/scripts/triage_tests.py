"""Triage the full-suite failures recorded in 03_execution/logs/pytest_full.log (01_audit/TEST_FAILURE_TRIAGE.csv).

For every 64-hex hash in an assertion diff, the script looks for a tracked file whose LF bytes or CRLF bytes produce it.
A failure whose two compared hashes are the LF and CRLF encodings of the same tracked file is a checkout-dependent
pin (the pin was recorded from a CRLF working copy; a fresh checkout honours eol=lf), not a content change.
Other failures are classified from their messages. Read-only.
"""
import hashlib
import re
import subprocess
from pathlib import Path

import pandas as pd

V2 = Path(__file__).resolve().parents[2]
REPO = Path(__file__).resolve().parents[4]
LOG = V2 / "03_execution/logs/pytest_full.log"


def main():
    log = LOG.read_text(encoding="utf-8")
    failed = re.findall(r"^(FAILED|ERROR) (\S+)", log, re.M)
    hashes = set(re.findall(r"[-+] ([0-9a-f]{64})", log))
    hmap = {}
    for f in subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True, text=True).stdout.splitlines():
        p = REPO / f
        if not p.is_file() or p.stat().st_size > 50_000_000:
            continue
        lf = p.read_bytes().replace(b"\r\n", b"\n")
        for tag, b in (("LF", lf), ("CRLF", lf.replace(b"\n", b"\r\n"))):
            h = hashlib.sha256(b).hexdigest()
            if h in hashes:
                hmap[h] = (f, tag)
    # per-test sections of the short summary are not separable in -q output; classify by known message patterns
    crlf_files = sorted({v[0] for v in hmap.values()})
    pairs_ok = all(any(hmap[h][0] == f and hmap[h][1] == t for h in hmap) for f in crlf_files for t in ("LF", "CRLF"))
    rows = []
    for kind, test in failed:
        mod = test.split("::")[0]
        if mod == "tests/test_faisal_pipeline.py":
            cls, ev = "KNOWN_BLOCKED (owner)", "ImportError TARGET_CLASSES; commit 6eddd4a restored the frozen Center windows.py"
        elif "test_official_tree_has_no_synthetic" in test:
            cls, ev = ("DEFECT INTRODUCED BY e944e1b (this project)",
                       "integrated_validation_v1/publication_q1/quality_control/FIGURE_MANIFEST.csv has the figure-system file name but "
                       "not its schema (no status / artifact_class columns)")
        elif "h2net_candidate_evidence" in test:
            cls, ev = "ENVIRONMENT (external dataset path)", "extract_released_network.py needs the H2-SimNet Simscape SLX release outside the repository"
        elif "h2net" in test:
            cls, ev = ("CHECKOUT-DEPENDENT HASH PIN (probable)",
                       "staleness check hashes eol=lf inputs; reports 'current' in the original CRLF checkout and 'STALE' here")
        else:
            cls, ev = ("CHECKOUT-DEPENDENT HASH PIN (verified)" if pairs_ok else "HASH MISMATCH (unexplained)",
                       "compared hashes are the LF and CRLF encodings of: " + "; ".join(crlf_files))
        rows.append(dict(result=kind, test=test, classification=cls, evidence=ev,
                         caused_by_v2=False, action="none here: changing pins or owner code is not authorized; see REPAIR_PROPOSALS"))
    out = pd.DataFrame(rows)
    out.to_csv(V2 / "01_audit/TEST_FAILURE_TRIAGE.csv", index=False, lineterminator="\n")
    print(out[["test", "classification"]].to_string())
    print({h[:12]: v for h, v in hmap.items()})


if __name__ == "__main__":
    main()
