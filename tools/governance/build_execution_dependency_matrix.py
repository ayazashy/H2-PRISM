#!/usr/bin/env python3
"""
Builds 00_governance/EXECUTION_DEPENDENCY_MATRIX.csv: every proposed action, its prerequisites (other action ids or
decisions), the issues it closes (MASTER_ISSUE_REGISTER.csv ids), validation criterion, authorization boundary and
workstream. Leverage = number of CRITICAL/HIGH issues the action is necessary for (computed from the register).
Usage: python tools/governance/build_execution_dependency_matrix.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REG = REPO / "00_governance" / "MASTER_ISSUE_REGISTER.csv"
OUT = REPO / "00_governance" / "EXECUTION_DEPENDENCY_MATRIX.csv"
FIELDS = ["action_id", "action", "workstream", "prerequisites", "closes_or_unblocks", "can_start_now", "environment",
          "validation_criterion", "authorization_boundary", "owner"]

A = [
("X01", "Record owner decisions D1 (topology v0.3) and D2 (position map v0.1)", "WS1 governance", "", "B-01;B-02;B-03;B-04;C-08;D-14;G-06;G-07",
 "yes", "none", "decisions recorded with name/date in owner records", "owner decision (Yazan); no execution", "Yazan"),
("X02", "Faisal component decisions (B, C', D, E, F, target rule, meta-model, inference unit) and F-D15/16/18", "WS1 governance", "", "G-06;G-07;C-13;D-14",
 "yes", "none", "decisions recorded", "owner decision (Faisal)", "Faisal"),
("X03", "Fix H2Net v1 engineering parameters S2-S6, S8 and operating envelope with sources", "WS2 physics", "", "A-04;A-05;A-06;A-07;A-08;A-09;A-12;A-14",
 "yes", "none", "PARAMETER_DECISIONS.yaml decided: true for every item, sources cited", "owner decision (Yazan + modeller; Faisal review)", "Yazan"),
("X04", "Confirm active gas_spec and Pipe (G) friction correlation in MATLAB", "WS2 physics", "MATLAB", "A-16;A-17",
 "no", "MATLAB R2025a+", "recorded outputs", "covered by H2Net v1 authorization (read-only)", "executor"),
("X05", "Build H2Net v1 model copies (S1-S8) with parameter diff", "WS2 physics", "X03;MATLAB", "A-01;A-02;A-04..A-11;A-15",
 "no", "MATLAB R2025a+", "diff complete; released models byte-identical", "MODEL_DEVELOPMENT:H2NET_V1 (active)", "executor"),
("X06", "Compute V2 reference steady states with the independent solver for the decided operating points", "WS2 physics", "X03", "A-15",
 "after X03", "Python (.venv + tables)", "targets recorded before simulation", "none (no simulation)", "Ahmed"),
("X07", "Run validation V2-V8 on H2Net v1", "WS2 physics", "X05;X06", "A-15;A-11;A-17",
 "no", "MATLAB R2025a+", "all V criteria PASS (spec section 4)", "MODEL_DEVELOPMENT:H2NET_V1 (active)", "executor"),
("X08", "Systematic literature and novelty register", "WS3 science", "", "E-01;E-02;D-13",
 "yes", "literature access", "each contribution mapped to closest prior work with differences", "none", "Ahmed + Faisal"),
("X09", "Add standard comparators to the v2 matrix: Chow rule, split-conformal sets, density/Mahalanobis OOD, ensemble disagreement (implement + synthetic tests)", "WS3 science", "X08", "D-13;E-02",
 "yes", "Python", "comparators implemented and unit-tested; registered before data", "none for implementation; arm registration needs Faisal", "Ahmed"),
("X10", "Register endpoint reporting rule: per-group and window-level risk beside group-balanced risk", "WS3 science", "X02", "D-05;D-11",
 "yes", "none", "rule in frozen protocol text", "owner decision (Faisal)", "Faisal"),
("X11", "Fix the multiclass design files and partition rule from validated H2Net v1 parameters", "WS4 data", "X07", "B-06;B-08;B-09;B-10;B-12;B-13;B-16;A-18",
 "no", "Python", "design meets MULTICLASS_SIMULATION_DESIGN minima; partition hashed", "none (design only)", "Ahmed + Yazan"),
("X12", "Generate NORMAL groups on H2Net v1 (staged, atomic claim)", "WS4 data", "X11", "B-06;C-02;C-09;D-07",
 "no", "MATLAB R2025a+", "physical checks pass; seal pinned", "NEW SIMULATION_GENERATION authorization", "executor"),
("X13", "Generate LEAK, FAULT, DELAY groups with counterfactual pairs (staged)", "WS4 data", "X12", "B-05;B-06;C-03;C-04;D-07",
 "no", "MATLAB R2025a+", "per-class minima met; visibility recorded; seal pinned", "NEW authorization per class", "executor"),
("X14", "Instrument runner outputs (per-class probabilities, meta-model coefficients)", "WS5 software", "", "C-12",
 "yes", "Python", "fields present in synthetic runs", "code change outside frozen runs; no execution", "Ahmed"),
("X15", "Freeze development protocol for H2Net data (classifier, representation H-R2 family, v2 settings, matrix A-F + comparators)", "WS3 science", "X02;X09;X10;X11", "D-01;D-02;D-03;D-04;D-06;D-08;E-04",
 "no", "none", "config hash pinned; owner sign-off", "owner decisions", "Faisal"),
("X16", "Development analyses: v2 estimability, matrix arms, H-R1/H-R2 on development partition only", "WS3 science", "X12;X13;X15", "D-04;D-07;D-08;D-09;D-10;C-02;C-05;C-06;C-07;C-11;B-17;E-08;F-05",
 "no", "Python", "estimability report; prespecified criteria applied", "NEW DEVELOPMENT_EXPERIMENT authorizations", "Ahmed"),
("X17", "Confirmatory run E vs A on the sealed partition", "WS3 science", "X16", "D-04;E-05;C-10",
 "no", "Python", "single registered contrast reported with group bootstrap; null reported as null", "NEW confirmatory authorization", "project lead"),
("X18", "Generalization tests G2-G6 (held-out levels, LOCO, sensor dropout, class/reference scaling)", "WS6 generalization", "X16", "F-02;F-04;F-05;F-09",
 "no", "Python", "each test reported separately with its held-out unit", "NEW authorizations", "Ahmed"),
("X19", "Fourth network with a different graph (G4)", "WS6 generalization", "X07", "F-01;D-12",
 "no", "MATLAB R2025a+", "own V1-V8 passed; G4 transfer test", "NEW model-development + generation authorizations", "Yazan"),
("X20", "Hydrogen-methane mixture tables (GERG-2008) and per-composition validation", "WS7 cross-gas", "X07", "A-03;F-03;D-12",
 "after X07", "GERG-2008 implementation", "V1-equivalent per composition", "NEW authorization (software install / model development)", "Ahmed"),
("X21", "Streaming inference prototype with data-quality gate and latency budget (synthetic replay)", "WS8 deployment", "X15", "F-07;F-08;F-10",
 "partly", "Python", "latency/memory within budget on replay; sensor-fault injection handled as UNRESOLVED", "none for prototype; no industrial claim", "Ahmed"),
("X22", "CI (fast test tier + frozen-hash verification incl. R1 prefix rule) and dependency lock", "WS5 software", "", "G-01;G-02;G-09;B-15",
 "yes", "CI service", "CI green on clean clone", "repository setting (project lead)", "Ahmed"),
("X23", "Field or laboratory data partnership for sim-to-real validation", "WS9 external", "", "A-13;F-11",
 "yes (outreach)", "external", "data agreement and provenance", "external agreements", "project lead"),
("X24", "Authors' clarification of weak-leak and event mechanisms of the released data", "WS9 external", "", "B-05;A-19;A-20",
 "yes (outreach)", "external", "written answer recorded", "none", "Yazan"),
("X25", "Publication claims plan: disclosure of the gas limitation (C16) on all released-data artifacts, negative results retained, superseded documents marked", "WS1 governance", "", "E-06;E-07;G-08",
 "yes", "none", "every planned artifact carries the required disclosure; claim register current", "owner decision (project lead)", "project lead"),
("X26", "Reduce v2 leave-one-group-out calibration cost (within-group sampling) with an equivalence test", "WS5 software", "", "F-06",
 "yes", "Python", "thresholds within tolerance of exact computation on synthetic data", "none (research code)", "Ahmed"),
("X27", "Provision an executor environment with MATLAB R2025a+, Simulink, Simscape", "WS2 physics", "", "G-03;A-16",
 "yes (procurement)", "external", "step A of the handoff passes", "licence / infrastructure decision", "project lead"),
]


def main() -> int:
    reg = {r["issue_id"]: r for r in csv.DictReader(REG.open(encoding="utf-8"))}
    rows = []
    for a in A:
        d = dict(zip(FIELDS, a))
        ids = []
        for tok in d["closes_or_unblocks"].split(";"):
            if ".." in tok:
                pre, a0 = tok.split("-")[0], int(tok.split("..")[0].split("-")[1])
                a1 = int(tok.split("..")[1].split("-")[1])
                ids += [f"{pre}-{k:02d}" for k in range(a0, a1 + 1)]
            elif tok:
                ids.append(tok)
        missing = [i for i in ids if i not in reg]
        if missing:
            raise SystemExit(f"{d['action_id']}: unknown issue ids {missing}")
        d["leverage_critical_high"] = sum(reg[i]["severity"] in ("CRITICAL", "HIGH") for i in ids)
        d["issue_ids_expanded"] = ";".join(ids)
        rows.append(d)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS + ["leverage_critical_high", "issue_ids_expanded"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    for r in sorted(rows, key=lambda r: -r["leverage_critical_high"])[:10]:
        print(r["action_id"], r["leverage_critical_high"], r["can_start_now"], r["action"][:80])
    return 0


if __name__ == "__main__":
    sys.exit(main())
