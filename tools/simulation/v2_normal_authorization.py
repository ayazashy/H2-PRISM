#!/usr/bin/env python3
"""
Fail-closed authorization gate with an atomic one-attempt claim for
SIMULATION_GENERATION:V2_NORMAL_SUPPORT_DEV_AND_CONFIRMATION (package v3).

Policy (project-lead clarification, POLICY_CLARIFICATION_2026-11-13.yaml):
  * the one authorized execution attempt BEGINS when the MATLAB generator is started in 'run' mode;
  * read-only environment checks, hash verification, model loading, parameter read-back and the non-generating
    preflight do NOT consume the authorization;
  * a started attempt consumes it whether it succeeds, fails or is interrupted; any further simulation attempt
    needs a new authorization record.

Implementation:
  ACTIVE     = record granted, scope and package match, every bound file's SHA-256 equals its bound value.
  CLAIM      = <claims_dir>/<package>__<record stem>.claim.json, created with O_CREAT | O_EXCL (atomic: exactly one
               process can create it; concurrent starts lose). It is written BEFORE any simulation and never deleted
               or rewritten by any tool, so an interrupted or failed attempt stays consumed.
  preflight  -> require_active()                       (non-consuming; any number of times; also after a claim)
  run        -> claim(out_dir)                         (requires ACTIVE and no claim; consumes)
  postprocess/validate -> require_claimed(out_dir)     (requires ACTIVE and the claim for exactly this out_dir)
Any change to a bound file makes the record inactive (fail closed); there is no override.

CLI (run from the repository root):
  python tools/simulation/v2_normal_authorization.py check            exit 0 if ACTIVE and UNCLAIMED
  python tools/simulation/v2_normal_authorization.py status           prints the state, exit 0
  python tools/simulation/v2_normal_authorization.py claim --out-dir D  atomic claim; prints the claim JSON; exit 0/1
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import platform
import sys
import uuid
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
PKG = REPO / "06_audit_preparation" / "simulation" / "v2_normal_support"
SCOPE = "SIMULATION_GENERATION:V2_NORMAL_SUPPORT_DEV_AND_CONFIRMATION"
PACKAGE = "v3"
BOUND = {"design": PKG / "DESIGN.csv", "generator": PKG / "generate_v2_normal_support.m",
         "postprocess": REPO / "tools" / "simulation" / "postprocess_v2_normal_runs.py",
         "validator": REPO / "tools" / "simulation" / "validate_v2_normal_outputs.py",
         "authorization_check": REPO / "tools" / "simulation" / "v2_normal_authorization.py"}


class NotAuthorized(RuntimeError):
    pass


class AlreadyClaimed(NotAuthorized):
    pass


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def current_hashes() -> dict:
    return {k: _sha(p) for k, p in BOUND.items()}


def evaluate(record: dict) -> list:
    """Reasons why a record is NOT active (empty list = active). Never relaxed."""
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


def _records(pkg: Path):
    return sorted(Path(pkg).glob("AUTH_SIMULATION_GENERATION*.yaml"))


def require_active(record_path: Path | None = None, pkg: Path | None = None) -> tuple[dict, Path]:
    """Return (record, path) of an ACTIVE record; non-consuming."""
    cands = [Path(record_path)] if record_path else _records(pkg or PKG)
    reasons = {}
    for p in cands:
        rec = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        why = evaluate(rec)
        if not why:
            return rec, p
        reasons[p.name] = why
    raise NotAuthorized(f"no active authorization for {SCOPE} package {PACKAGE}: {reasons}")


def claim_path(record_path: Path, claims_dir: Path | None = None) -> Path:
    d = Path(claims_dir) if claims_dir else Path(record_path).parent / "claims"
    return d / f"{PACKAGE}__{Path(record_path).stem}.claim.json"


def read_claim(record_path: Path, claims_dir: Path | None = None) -> dict | None:
    p = claim_path(record_path, claims_dir)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"unreadable_claim": str(p)}      # a claim file exists: the attempt is consumed regardless


def _norm_out(out_dir) -> str:
    return Path(os.path.normcase(os.path.abspath(out_dir))).as_posix()


def claim(out_dir, record_path: Path | None = None, claims_dir: Path | None = None, pkg: Path | None = None) -> dict:
    """Atomically claim the single attempt. Raises AlreadyClaimed if any claim exists (also from a failed or
    interrupted attempt, or a concurrent start that won the race)."""
    rec, rp = require_active(record_path, pkg)
    cp = claim_path(rp, claims_dir)
    cp.parent.mkdir(parents=True, exist_ok=True)
    body = {"attempt_id": uuid.uuid4().hex, "scope": SCOPE, "package_version": PACKAGE, "record": rp.name,
            "record_sha256": _sha(rp), "bound_hashes": current_hashes(), "out_dir": _norm_out(out_dir),
            "claimed_utc": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "host": platform.node(), "pid": os.getpid(),
            "policy": "attempt begins at 'run'; consumed on success, failure or interruption"}
    try:
        fd = os.open(cp, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as e:
        raise AlreadyClaimed(f"authorization {rp.name} already consumed (claim {cp.name} exists); "
                             "a new simulation attempt requires a new authorization record") from e
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(json.dumps(body, indent=2))
        f.flush()
        os.fsync(f.fileno())
    return body


def require_claimed(out_dir, record_path: Path | None = None, claims_dir: Path | None = None,
                    pkg: Path | None = None) -> dict:
    """Post-processing and validation may only touch the outputs of the claimed attempt, with unchanged files."""
    rec, rp = require_active(record_path, pkg)
    c = read_claim(rp, claims_dir)
    if not c or "attempt_id" not in c:
        raise NotAuthorized("no valid claim: the generator was not started in 'run' mode under this authorization")
    if c.get("out_dir") != _norm_out(out_dir):
        raise NotAuthorized(f"out_dir {_norm_out(out_dir)} is not the claimed attempt's folder {c.get('out_dir')}")
    if c.get("bound_hashes") != current_hashes():
        raise NotAuthorized("bound files changed since the claim")
    return c


def state(record_path: Path | None = None, claims_dir: Path | None = None, pkg: Path | None = None) -> str:
    try:
        _, rp = require_active(record_path, pkg)
    except NotAuthorized:
        return "NOT_AUTHORIZED"
    return "CLAIMED" if read_claim(rp, claims_dir) else "ACTIVE_UNCLAIMED"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", nargs="?", default="check", choices=["check", "status", "claim"])
    ap.add_argument("--out-dir")
    a = ap.parse_args(argv)
    if a.command == "claim":
        if not a.out_dir:
            print("claim needs --out-dir", file=sys.stderr)
            return 2
        try:
            print(json.dumps(claim(a.out_dir)))
            return 0
        except NotAuthorized as e:
            print(f"REFUSED: {e}", file=sys.stderr)
            return 1
    s = state()
    if a.command == "status":
        print(s)
        return 0
    try:
        rec, _ = require_active()
    except NotAuthorized as e:
        print(f"NOT AUTHORIZED: {e}")
        return 1
    if s == "CLAIMED":
        print(f"CLAIMED: authorization by {rec.get('authorized_by')} {rec.get('date')} already consumed")
        return 1
    print(f"ACTIVE_UNCLAIMED: {rec.get('authorized_by')} {rec.get('date')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
