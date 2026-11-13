#!/usr/bin/env python3
"""
Fail-closed authorization check for SIMULATION_GENERATION:V2_NORMAL_SUPPORT_DEV_AND_CONFIRMATION.

An authorization record is ACTIVE only if: authorized is true, its scope matches, its package version matches,
and EVERY bound file's current SHA-256 equals the bound value. Any change to the design, generator, post-processing
or validator therefore voids it automatically; a rerun after a change needs a new record (AUTHORIZATION_HISTORY.csv).
postprocess_v2_normal_runs.py and validate_v2_normal_outputs.py call require_active() and refuse otherwise.
Usage: python tools/simulation/v2_normal_authorization.py      (exit 0 if an active record exists)
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
PKG = REPO / "06_audit_preparation" / "simulation" / "v2_normal_support"
SCOPE = "SIMULATION_GENERATION:V2_NORMAL_SUPPORT_DEV_AND_CONFIRMATION"
PACKAGE = "v2"
BOUND = {"design": PKG / "DESIGN.csv", "generator": PKG / "generate_v2_normal_support.m",
         "postprocess": REPO / "tools" / "simulation" / "postprocess_v2_normal_runs.py",
         "validator": REPO / "tools" / "simulation" / "validate_v2_normal_outputs.py",
         "authorization_check": REPO / "tools" / "simulation" / "v2_normal_authorization.py"}


class NotAuthorized(RuntimeError):
    pass


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def current_hashes() -> dict:
    return {k: _sha(p) for k, p in BOUND.items()}


def evaluate(record: dict) -> list:
    """Reasons why a record is NOT active (empty list = active)."""
    why = []
    if record.get("authorized") is not True:
        why.append("authorized is not true")
    if record.get("scope") != SCOPE:
        why.append("scope differs")
    if str(record.get("package_version")) != PACKAGE:
        why.append("package version differs")
    bound = record.get("bound_to") or {}
    cur = current_hashes()
    for k in BOUND:
        if (bound.get(k) or {}).get("sha256") != cur[k]:
            why.append(f"{k} hash differs from the bound value (file changed: authorization void)")
    return why


def require_active(path: Path | None = None) -> dict:
    cands = [path] if path else sorted(PKG.glob("AUTH_SIMULATION_GENERATION*.yaml"))
    reasons = {}
    for p in cands:
        rec = yaml.safe_load(Path(p).read_text(encoding="utf-8")) or {}
        why = evaluate(rec)
        if not why:
            return rec
        reasons[Path(p).name] = why
    raise NotAuthorized(f"no active authorization for {SCOPE} package {PACKAGE}: {reasons}")


if __name__ == "__main__":
    try:
        rec = require_active()
        print(f"ACTIVE: {rec.get('authorized_by')} {rec.get('date')}")
        sys.exit(0)
    except NotAuthorized as e:
        print(f"NOT AUTHORIZED: {e}")
        sys.exit(1)
