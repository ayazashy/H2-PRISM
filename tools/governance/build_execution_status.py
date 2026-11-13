#!/usr/bin/env python3
"""
Master Execution Directive records (2026-11-13). The baseline register (MASTER_ISSUE_REGISTER.csv, commit ff11c87)
and the dependency matrix are NOT modified. This script:
  1. validates referential integrity: every issue id in the matrix exists; every open baseline issue is covered by >= 1
     action; prerequisites name existing actions or declared external resources; the action graph is acyclic;
  2. writes 00_governance/ACTION_EXECUTION_STATUS.csv (27 actions, directive status vocabulary);
  3. writes 00_governance/ISSUE_CLOSURE_MATRIX.csv (95 issues: baseline status beside current status and evidence).
Usage: python tools/governance/build_execution_status.py   (exit 1 on any integrity failure)
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
G = REPO / "00_governance"
STATUS = {"FIXED_AND_VERIFIED", "IMPLEMENTED_NOT_VALIDATED", "EXPLORATORY_EVIDENCE", "BLOCKED_EXTERNAL_RESOURCE",
          "BLOCKED_AUTHORIZATION", "BLOCKED_OWNER_DECISION", "NOT_ESTIMABLE", "REJECTED_BY_EVIDENCE"}
EXTERNAL_PREREQ = {"MATLAB"}

# action -> (status, implementation / evidence, tests, artifacts, blocker)
A = {
 "X01": ("BLOCKED_OWNER_DECISION", "none (decision record only)", "-", "-", "Yazan must record D1 (topology v0.3) and D2 (position map v0.1); acceptance cannot be recorded on his behalf"),
 "X02": ("BLOCKED_OWNER_DECISION", "none", "-", "-", "Faisal component decisions (B, C', D, E, F, target rule, meta-model, inference unit)"),
 "X03": ("BLOCKED_OWNER_DECISION", "CANDIDATE design + screening; 2026-11-14: released network extracted read-only (all six models), candidate H2 reference calcs: released end vent passes 3.3-3.5x line capacity with H2 (S4: replace vents/orifices by controlled sinks), roughness sensitivity (S6), leak sizes 12/24/53 mm (S4), steady-state lumping error < 1e-5 (S5 needed for transients only)", "tests/test_h2net_candidate_evidence.py (2 passed); screening run; --targets refusal (exit 2)", "06_audit_preparation/simulation/h2net_v1/candidate/{CANDIDATE_DESIGN.md, SIMSCAPE_SOURCE_EVIDENCE.md, REFERENCE_CALCS.json, ENVELOPE_SCREENING.csv}", "Yazan + modeller decide S2-S6, S8, V8 (PARAMETER_DECISIONS.yaml unchanged: OWNER_DECISIONS_REQUIRED); U-value and roughness literature sources still to cite"),
 "X04": ("FIXED_AND_VERIFIED", "static evidence from the installed R2026b Simscape source (the release that will run the models) and the released .slx XML: gas_spec = 1 = perfect_gas (enum gas_spec.m); Pipe (G) friction = Haaland (-1.8, 6.9, 1.11), laminar 64/Re, blend 2000-4000, effective length L + length_add (pipe_friction.ssc, pipe.ssc); installed-file SHA-256 recorded", "tests/test_h2net_candidate_evidence.py", "06_audit_preparation/simulation/h2net_v1/candidate/SIMSCAPE_SOURCE_EVIDENCE.md; RELEASED_NETWORK_GRAPH.json; tools/simulation/extract_released_network.py", "runtime confirmation is additionally recorded by readiness Phase 3 (check .5) when a memory-compliant MATLAB run occurs"),
 "X05": ("BLOCKED_EXTERNAL_RESOURCE", "gated gas-application function for h2net_v1_ copies (refuses released files, changed grant hashes, undecided parameters, implicit gas_spec); NOT run", "tests/test_matlab_readiness.py::test_gas_application_is_gated", "tools/matlab/h2prism_apply_h2_gas_to_copy.m", "X03 decisions (build gate CLOSED), MATLAB readiness PASS (X27), executor designation in the grant"),
 "X06": ("BLOCKED_OWNER_DECISION", "target mode implemented and fail-closed on undecided parameters", "manual run exit 2", "tools/simulation/h2net_v1_envelope_screening.py --targets", "decided operating points (X03)"),
 "X07": ("BLOCKED_EXTERNAL_RESOURCE", "8 GB resource-safe procedure for V2-V6 runs defined (one run per process, memory guard)", "-", "06_audit_preparation/simulation/matlab_readiness/MATLAB_READINESS.md", "X05 model and X06 targets"),
 "X08": ("IMPLEMENTED_NOT_VALIDATED", "15 references verified by bibliographic web search; method contributions mapped to closest prior work", "-", "00_governance/LITERATURE_REGISTER.csv", "domain prior work (hydrogen pipeline leak detection / simulation datasets) not yet searched; review by Ahmed + Faisal"),
 "X09": ("IMPLEMENTED_NOT_VALIDATED", "trust score, split conformal LAC/APS with unit-level calibration, Mahalanobis and kNN OOD, ensemble disagreement; v2-trust-score relation tested", "tests/test_reference_comparators.py (8 passed)", "src/h2prism/reference_comparators.py", "registration (Faisal, X02/X15) and evaluation on H2Net data (X16)"),
 "X10": ("BLOCKED_OWNER_DECISION", "selective_risk_report: window-level, group-balanced and per-group risk, saturation flag", "tests/test_risk_report.py (3 passed)", "src/h2prism/evaluation_metrics.py", "registering the rule in the frozen protocol text is Faisal's decision"),
 "X11": ("BLOCKED_EXTERNAL_RESOURCE", "data contracts (network, sensor, run, partition integrity) ready for the design files", "tests/test_data_contracts.py (5 passed)", "src/h2prism/data_contracts.py", "validated H2Net v1 parameters (X07)"),
 "X12": ("BLOCKED_AUTHORIZATION", "none", "-", "-", "X11 and a new scoped generation authorization; the v3 NORMAL request remains unauthorized"),
 "X13": ("BLOCKED_AUTHORIZATION", "none", "-", "-", "X12 and a scoped authorization"),
 "X14": ("FIXED_AND_VERIFIED", "develop runner stores p_cal_<class> per window and meta-model coefficients in DONE.json", "tests/test_ablation_develop.py::test_develop_outputs_are_instrumented_for_failure_analysis", "src/h2prism/experiments/primary_protocol.py", "-"),
 "X15": ("BLOCKED_OWNER_DECISION", "none", "-", "-", "Faisal decisions and H2Net data (X12/X13)"),
 "X16": ("BLOCKED_EXTERNAL_RESOURCE", "none", "-", "-", "H2Net development data (X12/X13) and frozen protocol (X15)"),
 "X17": ("BLOCKED_AUTHORIZATION", "none", "-", "-", "confirmatory test requires X16 and explicit authorization; confirmation data stay sealed"),
 "X18": ("BLOCKED_EXTERNAL_RESOURCE", "streaming scalability benchmark (channels 16-256) as engineering evidence only", "tools/experiments/streaming_benchmark.py", "03_results/diagnostics/streaming/STREAMING_BENCHMARK.json", "G2-G6 need H2Net data (X16)"),
 "X19": ("BLOCKED_AUTHORIZATION", "none", "-", "-", "new authorization and MATLAB"),
 "X20": ("BLOCKED_AUTHORIZATION", "versioned composition interface refusing blends on pure-H2 tables; CoolProp GERG-2008-parameter feasibility probe (default flash fails for H2-rich blends; imposed gas phase evaluates)", "tests/test_gas_composition.py (8 passed)", "src/h2prism/gas_composition.py; 02_methodology/GAS_COMPOSITION_INTERFACE.md; h2net_v1/H2CH4_FEASIBILITY_PROBE.json", "owner scope decision on blends, new table-generation authorization, transport validation, X07"),
 "X21": ("IMPLEMENTED_NOT_VALIDATED", "causal windower, data-quality gate (faults -> UNRESOLVED), synthetic replay benchmark: p99 latency 8 / 17 / 54 ms for 16 / 64 / 256 channels vs 30 s budget", "tests/test_streaming.py (8 passed)", "src/h2prism/streaming.py; 03_results/diagnostics/streaming/STREAMING_BENCHMARK.json", "frozen classifier (X15) not yet available; scorer is a fixed untrained map; no industrial claim"),
 "X22": ("IMPLEMENTED_NOT_VALIDATED", "frozen-hash verifier (R1 prefix rule; 23 lists OK); requirements-lock.txt; slow marker; fast tier 86 s locally; CI workflow", "verify_frozen_hashes.py; pytest -m 'not slow' (338 passed, 2 skipped)", ".github/workflows/ci.yml; requirements-lock.txt; tools/governance/verify_frozen_hashes.py", "CI never run on a service (no push permitted); fresh-install reproduction not tested"),
 "X23": ("BLOCKED_EXTERNAL_RESOURCE", "none", "-", "-", "field/laboratory data partner"),
 "X24": ("BLOCKED_OWNER_DECISION", "query DRAFT (not sent)", "-", "00_governance/drafts/X24_DATASET_AUTHOR_QUERY_DRAFT.md", "sending is outreach: needs project-lead approval; answer is external"),
 "X25": ("BLOCKED_OWNER_DECISION", "claims plan DRAFT with C16 disclosure text", "-", "00_governance/drafts/X25_CLAIMS_PLAN_DRAFT.md", "project-lead decision"),
 "X26": ("EXPLORATORY_EVIDENCE", "opt-in calibration_max_per_group (default exact, unchanged); s and theta_oos within 1 %, theta_det 1.2-1.5 % off -> registered 1 % criterion NOT met", "tests/test_distinguishability_v2.py::test_17_...", "src/h2prism/distinguishability_v2.py", "a different reduction (e.g. exact detectability threshold with sampled resolution) is needed to close F-06"),
 "X27": ("BLOCKED_EXTERNAL_RESOURCE", "MATLAB R2026b Update 1 installed and activated; Simulink 26.2 and Simscape 26.2 licensed (checkout OK); Phase 1 run 2026-11-13 23:04: 26 PASS / 1 FAIL (E4: 771 MB available < 2500 MB); tooling defects fixed (no Java runtime -> pure-MATLAB SHA-256; run log + stale-report check); standalone run 23:42 (logged): Phase 1 FAIL on E4 only (712 MB available); MATLAB grew 2.3 -> 4.6 GB after loading the Simscape libraries", "ENVIRONMENT_REPORT.json; tests/test_matlab_readiness.py (26 passed)", "tools/matlab/*; 06_audit_preparation/simulation/matlab_readiness/{MATLAB_READINESS.md, run_2026-11-13/}", "E4: >= 2.5 GB available with MATLAB + Simscape libraries (about 4.6 GB) is not reachable on this 8 GB laptop with other applications open; run with only MATLAB open or on a >= 16 GB executor; Phases 3 and 4 not executed"),
}

# issue -> (current_status, evidence); issues not listed keep their baseline status
I = {
 "B-15": ("FIXED_AND_VERIFIED", "verify_frozen_hashes.py implements and documents the R1 prefix rule; R1 68/68 OK, all 23 lists OK"),
 "C-12": ("FIXED_AND_VERIFIED", "X14 instrumentation; synthetic develop-run test"),
 "G-09": ("FIXED_AND_VERIFIED", "fast tier 86 s (< 2 min) locally: 338 passed, 2 skipped, 130 deselected"),
 "F-08": ("FIXED_AND_VERIFIED", "synthetic: injected missing/stuck/spike/range/inf faults -> UNRESOLVED (tests/test_streaming.py); not validated on real sensors"),
 "G-01": ("IMPLEMENTED_NOT_VALIDATED", "workflow written; never executed on a CI service"),
 "G-02": ("IMPLEMENTED_NOT_VALIDATED", "requirements-lock.txt pinned; fresh install not tested"),
 "D-13": ("IMPLEMENTED_NOT_VALIDATED", "comparators implemented and tested synthetically; registration pending (Faisal)"),
 "E-02": ("IMPLEMENTED_NOT_VALIDATED", "comparators implemented; not run on project data (needs X15/X16)"),
 "E-01": ("IMPLEMENTED_NOT_VALIDATED", "LITERATURE_REGISTER.csv (15 verified refs, method contributions mapped); domain prior work missing"),
 "D-05": ("BLOCKED_OWNER_DECISION", "selective_risk_report implemented and tested; registration in the frozen protocol is Faisal's decision"),
 "F-06": ("EXPLORATORY_EVIDENCE", "sampled calibration fails the 1 % criterion for theta_det (1.2-1.5 %); default remains exact"),
 "F-07": ("IMPLEMENTED_NOT_VALIDATED", "synthetic replay within budget (p99 54 ms at 256 channels vs 30 s); real classifier not yet frozen"),
 "A-03": ("BLOCKED_AUTHORIZATION", "interface refuses blends; mixture tables need owner scope decision + new authorization (feasibility probe recorded)"),
 "A-16": ("FIXED_AND_VERIFIED", "released XML gas_spec = 1; installed R2026b enum foundation.enum.gas_spec: 1 = perfect_gas (SIMSCAPE_SOURCE_EVIDENCE.md)"),
 "A-17": ("FIXED_AND_VERIFIED", "installed pipe_friction.ssc: Haaland with the same constants as gas_physics.friction_factor; V2 must include length_add (SIMSCAPE_SOURCE_EVIDENCE.md)"),
 "A-14": ("BLOCKED_OWNER_DECISION", "candidate envelope screened on released geometry; decision and sources pending"),
}


def read(p):
    with open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    reg = read(G / "MASTER_ISSUE_REGISTER.csv")
    mat = read(G / "EXECUTION_DEPENDENCY_MATRIX.csv")
    ids = {r["issue_id"] for r in reg}
    acts = {r["action_id"] for r in mat}
    errs = []
    if len(reg) != 95 or len(mat) != 27:
        errs.append(f"expected 95 issues / 27 actions, got {len(reg)} / {len(mat)}")
    covered = set()
    for r in mat:
        for i in filter(None, r["issue_ids_expanded"].split(";")):
            (covered.add(i) if i in ids else errs.append(f"{r['action_id']}: unknown issue {i}"))
        for p in filter(None, re.split(r"[;,]\s*", r["prerequisites"])):
            if p not in acts and p not in EXTERNAL_PREREQ:
                errs.append(f"{r['action_id']}: unknown prerequisite {p}")
    for r in reg:
        if r["status"] != "FIXED" and r["issue_id"] not in covered:
            errs.append(f"open issue {r['issue_id']} not covered by any action")
    deps = {r["action_id"]: [p for p in re.split(r"[;,]\s*", r["prerequisites"]) if p in acts] for r in mat}
    state = {}

    def visit(a, path):
        if state.get(a) == 1:
            errs.append("cycle: " + " -> ".join(path + [a]))
            return
        if state.get(a) == 2:
            return
        state[a] = 1
        for p in deps[a]:
            visit(p, path + [a])
        state[a] = 2
    for a in deps:
        visit(a, [])
    if set(A) != acts:
        errs.append(f"status records differ from matrix actions: {sorted(set(A) ^ acts)}")
    for a, v in A.items():
        if v[0] not in STATUS:
            errs.append(f"{a}: status {v[0]}")
    for i, v in I.items():
        if i not in ids or v[0] not in STATUS:
            errs.append(f"issue update {i}: {v[0]}")
    if errs:
        print("INTEGRITY FAILURES:\n  " + "\n  ".join(errs))
        return 1

    with open(G / "ACTION_EXECUTION_STATUS.csv", "w", encoding="utf-8", newline="\n") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["action_id", "action", "linked_issues", "baseline_can_start_now", "dependencies", "acceptance_criterion",
                    "authorization_boundary", "status", "implementation_and_new_evidence", "tests", "artifacts", "blocker"])
        for r in mat:
            s = A[r["action_id"]]
            w.writerow([r["action_id"], r["action"], r["issue_ids_expanded"], r["can_start_now"], r["prerequisites"],
                        r["validation_criterion"], r["authorization_boundary"], s[0], s[1], s[2], s[3], s[4]])
    by_issue = {}
    for r in mat:
        for i in filter(None, r["issue_ids_expanded"].split(";")):
            by_issue.setdefault(i, []).append(r["action_id"])
    with open(G / "ISSUE_CLOSURE_MATRIX.csv", "w", encoding="utf-8", newline="\n") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["issue_id", "title", "severity", "baseline_status", "current_status", "changed", "actions",
                    "acceptance_criteria", "closure_evidence_or_blocker"])
        for r in reg:
            cur, ev = I.get(r["issue_id"], (r["status"], "unchanged since baseline ff11c87"))
            acts_i = by_issue.get(r["issue_id"], [])
            if r["issue_id"] not in I and acts_i:
                ev = "unchanged; blocker: " + " | ".join(f"{a}: {A[a][4]}" for a in acts_i if A[a][4] != "-")
            w.writerow([r["issue_id"], r["title"], r["severity"], r["status"], cur, "yes" if r["issue_id"] in I else "no",
                        ";".join(acts_i), r["acceptance_criteria"], ev])
    from collections import Counter
    print("integrity: OK (95 issues, 27 actions, all open issues covered, prerequisite graph acyclic)")
    print("actions:", dict(Counter(v[0] for v in A.values())))
    print("issues changed:", len(I), dict(Counter(v[0] for v in I.values())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
