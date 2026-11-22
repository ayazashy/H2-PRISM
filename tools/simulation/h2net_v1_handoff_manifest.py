#!/usr/bin/env python3
"""
Writes handoff/h2net_v1/HANDOFF_MANIFEST.json: every file the Windows handoff depends on, with SHA-256, plus the
released-model and hydrogen-table hashes it will verify. --check exits 1 if any listed file changed or is missing.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "handoff" / "h2net_v1" / "HANDOFF_MANIFEST.json"
FILES = sorted(
    [p.relative_to(REPO).as_posix() for p in (REPO / "handoff" / "h2net_v1").glob("*") if p.is_file() and p.name != OUT.name]
    + [p.relative_to(REPO).as_posix() for p in (REPO / "tools" / "matlab").glob("*") if p.suffix in (".m", ".py", ".json")]
    + [f"tools/simulation/{n}" for n in ("h2net_v1_gates.py", "h2net_v1_v2_targets.py", "h2net_v1_provisional_network.py",
                                         "h2net_v1_build_spec_decided.py", "h2net_v1_validation.py", "h2net_v1_scenarios.py",
                                         "h2net_v1_package_return.py", "h2net_v1_reference.py", "h2net_v1_envelope_screening.py",
                                         "extract_released_network.py", "h2net_v1_handoff_manifest.py")]
    + ["tools/governance/verify_frozen_hashes.py", "tools/dataset/trace_slx_sensors.py", "src/h2prism/gas_physics.py",
       "src/h2prism/data_contracts.py", "requirements-lock.txt",
       "06_audit_preparation/simulation/h2net_v1/PARAMETER_DECISIONS_TEMPLATE.yaml",
       "06_audit_preparation/simulation/h2net_v1/EXECUTOR_DESIGNATION_TEMPLATE.yaml",
       "06_audit_preparation/simulation/h2net_v1/AUTH_MODEL_DEVELOPMENT_H2NET_V1_REQUEST.yaml",
       "06_audit_preparation/simulation/h2net_v1/H2NET_V1_DESIGN_FREEZE_SPEC.md",
       "06_audit_preparation/simulation/h2net_v1/H2NET_V1_APPROVAL_CHECKLIST.md",
       "06_audit_preparation/simulation/h2net_v1/candidate/RELEASED_NETWORK_GRAPH.json",
       "06_audit_preparation/simulation/h2net_v1/properties/H2_REALGAS_TLU2.json",
       "06_audit_preparation/simulation/h2net_v1/properties/H2_REALGAS_TLU2_params.m"])


def build() -> dict:
    E = json.loads((REPO / "tools/matlab/h2prism_matlab_expectations.json").read_text(encoding="utf-8"))
    return {"handoff": "H2Net v1 Windows execution", "status": "STATICALLY_TESTED; MATLAB steps UNVERIFIED until executed",
            "entrypoints": ["01_PREFLIGHT.ps1", "02_VALIDATE_ENVIRONMENT.ps1", "03_BUILD_AND_VALIDATE.ps1",
                            "04_RUN_AUTHORIZED_SCENARIOS.ps1", "05_PACKAGE_RETURN.ps1"],
            "files": {f: hashlib.sha256((REPO / f).read_bytes()).hexdigest() for f in FILES},
            "released_models": {m["file"]: m["sha256"] for m in E["models"]},
            "not_included": "data/raw (the released dataset must already be in the checkout), large outputs, archives"}


def main(argv) -> int:
    d = build()
    if "--check" in argv:
        old = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
        bad = [f for f, h in old.get("files", {}).items() if not (REPO / f).exists() or hashlib.sha256((REPO / f).read_bytes()).hexdigest() != h]
        print("handoff manifest: " + ("current" if old.get("files") == d["files"] and not bad else f"STALE {bad[:5]}"))
        return 0 if old.get("files") == d["files"] and not bad else 1
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout.strip()
    d["built_from_commit"] = head
    OUT.write_text(json.dumps(d, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(d['files'])} files -> {OUT.relative_to(REPO).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
