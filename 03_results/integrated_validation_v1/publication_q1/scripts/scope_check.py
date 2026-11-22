"""Protected-scope integrity check used by verify_package.py.

Two protected scopes, each compared against its own baseline commit on committed content (git blobs, so the result
does not depend on the checkout's line endings):
  outside_v1  every repository file outside integrated_validation_v1, against 6eddd4a (the base the v1 package
              was built on: the frozen Center baseline plus the repaired integration);
  v1          every file inside integrated_validation_v1, against 6b98a8a (the v1 package release).
A file that differs from its baseline passes only if the change register
(03_results/maintenance/POST_BASELINE_CHANGE_REGISTER.csv) authorizes it:
  ADD_PREFIX  a path or directory prefix holding a later independent package (its own verifier covers its content);
  ADD         an added file with the exact SHA-256 of its committed content;
  MODIFY      a modified file whose baseline and committed SHA-256 both match the register;
  DELETE      a deleted file whose baseline SHA-256 matches the register.
Anything else (unregistered addition, unregistered or different modification, deletion) is UNAUTHORIZED.
Verifier outputs that are rewritten on every run are exempt by name.
"""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pandas as pd

V1 = "03_results/integrated_validation_v1"
REGISTER = "03_results/maintenance/POST_BASELINE_CHANGE_REGISTER.csv"
SCOPES = {"outside_v1": dict(base="6eddd4a", spec=[".", f":(exclude){V1}"]),
          "v1": dict(base="6b98a8a", spec=[V1])}
VERIFIER_OUTPUTS = {f"{V1}/SHA256SUMS.csv", f"{V1}/publication_q1/quality_control/NUMERICAL_VERIFICATION.csv",
                    f"{V1}/publication_q1/quality_control/SCOPE_CHECK.csv",
                    f"{V1}/advanced_validation/quality_control/AV_VERIFICATION.csv"}


def _git(repo, *a, binary=False):
    r = subprocess.run(["git", *a], cwd=repo, capture_output=True, check=True)
    return r.stdout if binary else r.stdout.decode("utf-8")


def blob_sha(repo, rev, path):
    return hashlib.sha256(_git(repo, "show", f"{rev}:{path}", binary=True)).hexdigest()


def changes(repo, base, head, spec):
    out = _git(repo, "-c", "core.quotepath=false", "diff", "--no-renames", "--name-status", base, head, "--", *spec)
    return [tuple(l.split("\t", 1)) for l in out.splitlines() if l.strip()]


def evaluate(repo, register: pd.DataFrame, scope: str, base: str, head: str = "HEAD", spec=None, exempt=VERIFIER_OUTPUTS):
    spec = spec or SCOPES[scope]["spec"]
    live = register.superseded.fillna("") == "" if "superseded" in register else True
    reg = register[(register.scope == scope) & live]
    prefixes = list(reg[reg.kind == "ADD_PREFIX"].path)
    exact = {(r.kind, r.path): r for r in reg[reg.kind != "ADD_PREFIX"].itertuples()}
    rows = []
    for status, path in changes(repo, base, head, spec):
        verdict, why = "UNAUTHORIZED", "not in change register"
        if path in exempt:
            verdict, why = "EXEMPT", "verifier output rewritten on every run"
        elif status == "A":
            new = blob_sha(repo, head, path)
            r = exact.get(("ADD", path))
            if r is not None:
                verdict, why = ("AUTHORIZED", r.issue) if r.authorized_sha256 == new else ("UNAUTHORIZED", "content differs from registered hash")
            elif any(path == p or path.startswith(p.rstrip("/") + "/") for p in prefixes):
                verdict, why = "AUTHORIZED", "registered independent package"
        elif status == "M":
            r = exact.get(("MODIFY", path))
            if r is not None:
                old, new = blob_sha(repo, base, path), blob_sha(repo, head, path)
                ok = r.baseline_sha256 == old and r.authorized_sha256 == new
                verdict, why = ("AUTHORIZED", r.issue) if ok else ("UNAUTHORIZED", "baseline or committed content differs from registered hashes")
        elif status == "D":
            r = exact.get(("DELETE", path))
            if r is not None:
                ok = r.baseline_sha256 == blob_sha(repo, base, path)
                verdict, why = ("AUTHORIZED", r.issue) if ok else ("UNAUTHORIZED", "baseline content differs from registered hash")
        rows.append(dict(scope=scope, base=base, status=status, path=path, verdict=verdict, reason=why))
    return pd.DataFrame(rows, columns=["scope", "base", "status", "path", "verdict", "reason"])


def uncommitted(repo, spec, exempt=VERIFIER_OUTPUTS):
    out = _git(repo, "-c", "core.quotepath=false", "status", "--porcelain", "--untracked-files=all", "--", *spec)
    return [l[3:] for l in out.splitlines() if l.strip() and l[3:] not in exempt]


def load_register(repo):
    p = Path(repo) / REGISTER
    return pd.read_csv(p, dtype=str).fillna("")
