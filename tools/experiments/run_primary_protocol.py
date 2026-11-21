#!/usr/bin/env python3
"""
H2-PRISM primary protocol runner (CLI). Core: src/h2prism/experiments/primary_protocol.py

Modes (outer-test evaluation is disabled unless --execute-primary/--execute-robustness AND a
matching authorization file are given):

  --dry-run                       preflight + feature build on the configured data; NO model fitting
                                  (artifact class PREFLIGHT_ONLY). Default mode.
  --synthetic                     full pipeline on a SYNTHETIC_TEST_CONFIG (e.g. a fixture made with
                                  --make-synthetic-fixture); output may not be under 03_results/.
  --execute-primary               full pipeline on the real noise-added realization (PRIMARY_EXPERIMENT)
  --execute-robustness            full pipeline on the clean realization (ROBUSTNESS_EXPERIMENT)
  --execute-sensitivity --sensitivity NAME
                                  one registered sensitivity analysis (SENSITIVITY_EXPERIMENT); scope
                                  SENSITIVITY_EXPERIMENT:NAME. --sensitivity NAME also works with --synthetic.
                                  All execute modes require --authorization <yaml> with: authorized: true,
                                  scope: <class>, config_sha256: <sha of --config>, authorized_by, date,
                                  governance_clearance {F-D15, F-D16, A-D10, PA-1: ATTESTED.../WAIVED...}.

Examples
  python tools/experiments/run_primary_protocol.py --config 06_audit_preparation/FINAL_EXPERIMENT_CONFIG.yaml --out <dir> --dry-run
  python tools/experiments/run_primary_protocol.py --make-synthetic-fixture <dir>
  python tools/experiments/run_primary_protocol.py --config <dir>/config.yaml --root <dir> --raw-parent <dir>/raw --out <out> --synthetic
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from h2prism.experiments import primary_protocol as pp  # noqa: E402
from h2prism.experiments.synthetic_protocol_fixture import make_fixture  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="H2-PRISM primary protocol runner")
    ap.add_argument("--config", type=Path)
    ap.add_argument("--root", type=Path, default=ROOT, help="base for relative paths in the config")
    ap.add_argument("--raw-parent", type=Path, default=ROOT / "data" / "raw")
    ap.add_argument("--out", type=Path)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--synthetic", action="store_true")
    g.add_argument("--execute-primary", action="store_true")
    g.add_argument("--execute-robustness", action="store_true")
    g.add_argument("--execute-sensitivity", action="store_true", help="registered sensitivity analysis (needs --sensitivity)")
    g.add_argument("--make-synthetic-fixture", type=Path)
    g.add_argument("--develop", action="store_true",
                   help="development-only ablation arm (needs an authorization scoped DEVELOPMENT_EXPERIMENT:<arm_id>)")
    ap.add_argument("--authorization", type=Path)
    ap.add_argument("--sensitivity", choices=sorted(pp.SENSITIVITY_OVERRIDES), help="registered sensitivity analysis name")
    a = ap.parse_args(argv)
    if a.make_synthetic_fixture:
        print(json.dumps({k: str(v) for k, v in make_fixture(a.make_synthetic_fixture).items()}, indent=2))
        return 0
    if not a.config or not a.out:
        ap.error("--config and --out are required")
    try:
        if a.synthetic:
            res = pp.run(a.config, a.root, a.raw_parent, a.out, "synthetic", sensitivity=a.sensitivity)
        elif a.develop:
            res = pp.run(a.config, a.root, a.raw_parent, a.out, "develop", authorization=a.authorization)
        elif a.execute_primary or a.execute_robustness or a.execute_sensitivity:
            cls = ("PRIMARY_EXPERIMENT" if a.execute_primary else "ROBUSTNESS_EXPERIMENT" if a.execute_robustness
                   else "SENSITIVITY_EXPERIMENT")
            res = pp.run(a.config, a.root, a.raw_parent, a.out, "execute", artifact_class=cls, authorization=a.authorization,
                         sensitivity=a.sensitivity)
        else:
            res = pp.run(a.config, a.root, a.raw_parent, a.out, "preflight", sensitivity=a.sensitivity)
    except (pp.PreflightError, pp.AuthorizationError) as exc:
        print(f"REFUSED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": res["status"], "artifact_class": res["artifact_class"], "out": str(a.out)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
