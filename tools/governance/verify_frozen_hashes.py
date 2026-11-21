#!/usr/bin/env python3
"""
Verify every frozen output against its recorded hash list (action X22; issue B-15).

Hash lists and the directories they describe:
  03_results/primary_protocol/logs/<RUN>_<key>_OUTPUT_HASHES.sha256 -> 03_results/primary_protocol/<RUN>/
  03_results/primary_protocol/logs/PRIMARY_db9acd23ef58_OUTPUT_HASHES.sha256 -> archive/PRIMARY_db9acd23ef58_INVALID_CALIBRATION/
      (R1 was archived after its list was written: entries carry the pre-archive prefix 'PRIMARY/', which is stripped
       here; the frozen list itself is never rewritten)
  03_results/ablation_runs/logs/<ARM>_<key>_OUTPUT_HASHES.sha256 -> 03_results/ablation_runs/<ARM>/
  <dir>/OUTPUT_HASHES.sha256 (self-describing lists in diagnostics and simulation packages)
Files listed but absent (git-ignored large outputs in a fresh clone) are reported as MISSING, not as failures, unless
--strict. Exit 1 on any mismatch.
Usage: python tools/governance/verify_frozen_hashes.py [--strict]
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PP = REPO / "03_results" / "primary_protocol"
AR = REPO / "03_results" / "ablation_runs"
SELF_LISTS = ["03_results/diagnostics/arm_h_failures", "03_results/diagnostics/distinguishability_v2",
              "03_results/diagnostics/feature_representation", "06_audit_preparation/simulation/h2net_v1/properties"]
PREFIX_RULES = {"PRIMARY_db9acd23ef58_OUTPUT_HASHES.sha256": ("PRIMARY/", PP / "archive" / "PRIMARY_db9acd23ef58_INVALID_CALIBRATION")}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def parse(lst: Path):
    for line in lst.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            h, name = line.split(maxsplit=1)
            yield h, name.lstrip("*")


def targets():
    for lst in sorted((PP / "logs").glob("*_OUTPUT_HASHES.sha256")):
        if lst.name in PREFIX_RULES:
            pre, d = PREFIX_RULES[lst.name]
            yield lst, d, pre
        else:
            run = re.sub(r"_[0-9a-f]{12}_OUTPUT_HASHES\.sha256$", "", lst.name)
            yield lst, PP / run, ""
    for lst in sorted((AR / "logs").glob("*_OUTPUT_HASHES.sha256")):
        yield lst, AR / re.sub(r"_[0-9a-f]{12}_OUTPUT_HASHES\.sha256$", "", lst.name), ""
    for d in SELF_LISTS:
        yield REPO / d / "OUTPUT_HASHES.sha256", REPO / d, ""


def verify(strict: bool = False) -> dict:
    res = {}
    for lst, d, pre in targets():
        ok = bad = missing = 0
        for h, name in parse(lst):
            if name == "OUTPUT_HASHES.sha256":
                continue
            if pre and name.startswith(pre):
                name = name[len(pre):]
            f = d / name
            if not f.exists():
                missing += 1
            elif _sha(f) == h:
                ok += 1
            else:
                bad += 1
        res[str(lst.relative_to(REPO)).replace("\\", "/")] = {"ok": ok, "mismatch": bad, "missing": missing}
    return res


def main(argv=None) -> int:
    strict = "--strict" in (argv or sys.argv[1:])
    res = verify(strict)
    failed = False
    for k, v in res.items():
        flag = "FAIL" if v["mismatch"] or (strict and v["missing"]) else "OK"
        failed |= flag == "FAIL"
        print(f"{flag:4s} {k}: ok={v['ok']} mismatch={v['mismatch']} missing={v['missing']}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
