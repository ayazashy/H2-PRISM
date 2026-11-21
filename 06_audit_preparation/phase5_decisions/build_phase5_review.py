#!/usr/bin/env python3
"""Phase 5 decision review layer over the Phase 4 matrix (single source of truth).
Writes DECISION_REVIEW_P5.csv, CRITICAL_PATH_DECISIONS.md and the three owner sign-off sheets.
Approval fields stay blank: no human decision is recorded here.
Usage (repo root): python 06_audit_preparation/phase5_decisions/build_phase5_review.py"""

import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
P4 = HERE.parent / "phase4_approvals" / "MASTER_DECISION_MATRIX.csv"
IE = "INSUFFICIENT_EVIDENCE"

# id: (priority, phase5_class, phase5_recommendation_or_refinement, main_risk, blocks)
R = {
 "Y-D01": ("P0", "TECHNICAL_RECOMMENDATION", "Approve 57-run identity model", "Rejection reintroduces the duplicate scenario that leaked in fold 3", "Y-D07, all folds/counts"),
 "Y-D02": ("P1", "VERIFIED_FACT", "Confirm (numerical evidence)", "None material; double counting if ignored", "F-D01"),
 "Y-D03": ("P1", "UNRESOLVED", "11 start-up pairs separate; 8 near-identical pairs grouped conservatively in sensitivity view. Ancestry itself: " + IE + " (needs .slx inspection)", "Treating signal similarity as ancestry (or ignoring it) mis-sizes families", "Y-D04, F-D13 only. Phase-5 finding: no effect on LOTO outer or LOTO inner splits (all pairs within topology), so not P0"),
 "Y-D04": ("P1", "SCIENTIFIC_CHOICE", "Primary map (39 eligible families) + extended map (32) as registered sensitivity", "Family count drives bootstrap precision; over-splitting understates dependence", "F-D13, D(x) development query-family exclusion. Not split assignment under LOTO"),
 "Y-D05a": ("P3", "UNRESOLVED", "Keep raw labels; record mismatch; prohibit location analyses. Ground truth: " + IE, "Wrong location semantics if localisation is ever attempted", "None for 4-class task"),
 "Y-D05b": ("P0", "UNRESOLVED", "Exclude from exclusive task (restriction). Ground truth: " + IE, "Re-including would add doubtful labels to a 6-run class", "Eligible inventory (51), Y-D07"),
 "Y-D05c": ("P1", "VERIFIED_FACT", "Exclude compound runs; exploratory multi-label only", "None", "Y-D07"),
 "Y-D05d": ("P0", "SCIENTIFIC_CHOICE", "Multi-location single-type leaks = LEAK (consistent rule); alternative excludes 15 runs", "Construct validity of LEAK class", "Class counts, folds, A-D05"),
 "Y-D06a": ("P0", "UNRESOLVED", "Exclude post-delay rows (no relabelling). Why labels end at 1000 s: " + IE, "Relabelling would invent ground truth; counting as NORMAL adds phase-confounded windows", "F-D05, F-D04, window table"),
 "Y-D06b": ("P2", "TECHNICAL_RECOMMENDATION", "Use verified onset; folder name only as segment_dir", "Phase used as feature or stratum would be wrong for C1 runs", "A-D06"),
 "Y-D07": ("P0", "TECHNICAL_RECOMMENDATION", "Issue manifest v0.2 after Y-D01, Y-D05*, Y-D06a", "Experiments on an unversioned manifest", "F-D17, everything downstream"),
 "Y-D08": ("P0", "SCIENTIFIC_CHOICE", "READY_WITH_EXCLUSIONS (restricted): pooled LOTO; NORMAL/FAULT/DELAY descriptive only", "Overstated readiness", "A-D10, experimental authorization"),
 "Y-D09": ("P2", "TECHNICAL_RECOMMENDATION", "Adopt src/h2prism/dataset_manifest.py as reference builder", "Divergent IDs if audit/ scripts reused", "Reproducibility only"),
 "Y-D10": ("P2", "VERIFIED_FACT", "Regenerate raw_checksums.sha256 from untouched archive", "Provenance mismatch on re-verification", "A10 provenance"),
 "F-D01": ("P0", "SCIENTIFIC_CHOICE", "Noise-added primary + clean pre-registered secondary. Evidence does not prove one realization 'better'; rationale is realism stated by the publisher. Never pool", "Choosing after seeing results; pooling duplicates runs", "F-D04, window table, F-D17"),
 "F-D02": ("P0", "TECHNICAL_RECOMMENDATION", "LOTO (only design with every class in every train/test fold and no cross-split dependence)", "Estimand is narrow: unseen withdrawal topology of one simulated network; n=3 folds", "F-D03, F-D13, A-D03"),
 "F-D03": ("P0", "TECHNICAL_RECOMMENDATION", "LOTO_within_train (the family-k3 scheme lacks thin classes in some validation splits). Restriction: each inner train has 1 NORMAL and 1 DELAY run, so per-class development estimates rest on single runs", "Development selection driven by one run per thin class", "F-D08, F-D09, F-D12"),
 "F-D04": ("P0", "SCIENTIFIC_CHOICE", "60/30 primary, 60/60 non-overlapping sensitivity (DELAY keeps 31 windows/run; boundary loss <0.3%). No physical derivation of 60 s exists; it is a sampling/support compromise", "Window length interacts with event dynamics; overlap inflates apparent n (not used for inference)", "F-D06, window table"),
 "F-D05": ("P0", "SCIENTIFIC_CHOICE", "exclude primary; label_normal as pre-registered secondary (raises NORMAL runs 3 -> 45 but all early-time windows: phase confound)", "Exclude: NORMAL = 3 runs; label_normal: NORMAL confounded with time-in-run", "F-D04, F-D07, A-D01"),
 "F-D06": ("P0", "TECHNICAL_RECOMMENDATION", "128 features primary; 80 offset-invariant as A15 sensitivity; no cross-channel features", "Absolute levels may fingerprint topology/run", "Window table, F-D08"),
 "F-D07": ("P0", "SCIENTIFIC_CHOICE", "Pooled primary metrics; per-family tables; NORMAL/FAULT/DELAY DESCRIPTIVE_ONLY", "Class-level claims from 1 test run per fold", "F-D13, A-D01, A-D03"),
 "F-D08": ("P0", "SCIENTIFIC_CHOICE", "k=25 uniform, no prior correction primary; k=10/50 and prior correction as sensitivity. Restriction: outer-train DELAY reference = 62 windows from 2 runs, so DELAY neighbourhoods will carry LOW_SCENARIO_DIVERSITY; D for thin classes interpreted descriptively", "D dominated by one run for thin classes", "F-D11, F-D12, RQ1"),
 "F-D09": ("P1", "TECHNICAL_RECOMMENDATION", "Log-loss criterion over {none, sigmoid}; isotonic NOT recommended (one run per thin class in inner folds)", "Isotonic overfits single-run classes", "F-D12"),
 "F-D10": ("P0", "TECHNICAL_RECOMMENDATION", "Implement cross-fitted s_C / s_C-D meta-model (plan definition; implementation may proceed now)", "Without it RQ1 (C vs C-D) cannot be run", "F-D12, F-D17, RQ1"),
 "F-D11": ("P0", "SCIENTIFIC_CHOICE", "p-only candidates; singleton -> UNRESOLVED; max_set_size=2; OUT_OF_SUPPORT/INVALID/NO_REFERENCE -> UNRESOLVED; LOW_SCENARIO_DIVERSITY blocks SPECIFIC. Consistent with RQ2 (informative pairs, explicit abstention); max_set_size=3 is the alternative if Ahmed wants broader sets", "Policy too strict -> few SPECIFIC outcomes; too loose -> uninformative sets", "F-D12, A-D02"),
 "F-D12": ("P0", "TECHNICAL_RECOMMENDATION", "Development-only thresholds; target coverage 0.80 primary, 0.60/0.90 secondary - prespecified in the Faisal plan (F10 step 85), not chosen from results; report realized coverage", "Threshold transfer may not reach 0.80 on held-out topology", "F-D17"),
 "F-D13": ("P1", "SCIENTIFIC_CHOICE", "Phase-5 refinement: paired family bootstrap STRATIFIED WITHIN TOPOLOGY on pooled C vs C-D difference; per-fold estimates reported; no class-level or topology-level intervals. Families nest in only 3 topologies, so intervals are conditional on these topologies", "Unstratified bootstrap over 39 families ignores topology clustering and model-per-fold structure", "A-D03, A-D04, F-D17"),
 "F-D14": ("P1", "TECHNICAL_RECOMMENDATION", "Accept plan RF grid, seed 20261104", "None material", "F-D17"),
 "F-D15": ("P0", "TECHNICAL_RECOMMENDATION", "Code review then technical acceptance of new modules", "Unreviewed code in primary pipeline", "All execution"),
 "F-D16": ("P1", "TECHNICAL_RECOMMENDATION", "Amend interface contracts; open change-control log", "Schema drift", "F-D17"),
 "F-D17": ("P0", "SCIENTIFIC_CHOICE", "Freeze only when no PENDING placeholder remains (29 open)", "Premature freeze", "A-D10, experimental authorization"),
 "F-D18": ("P1", "TECHNICAL_RECOMMENDATION", "Review A12-A16 after F3/F4 exist", "Supporting runs integrated without acceptance", "A14-A16 execution"),
 "A-D01": ("P1", "SCIENTIFIC_CHOICE", "RQ1 TESTABLE_WITH_RESTRICTIONS (pooled, family-paired, LEAK-dominated)", "Over-reading a pooled effect as class-general", "A-D08, manuscript"),
 "A-D02": ("P1", "SCIENTIFIC_CHOICE", "RQ2 TESTABLE_WITH_RESTRICTIONS; 'meaningful' ambiguity EXPLORATORY unless criterion fixed in advance", "Post-hoc meaning attached to ambiguity sets", "F-D11, manuscript"),
 "A-D03": ("P1", "SCIENTIFIC_CHOICE", "Scope = unseen withdrawal topology of the H2-SimNet simulated network; no industrial/field claim", "Overgeneralisation", "A-D08"),
 "A-D04": ("P0", "SCIENTIFIC_CHOICE", "Effect sizes only, unless a justified threshold is approved BEFORE any outer-test run", "Post-hoc significance threshold", "F-D17"),
 "A-D05": ("P0", "SCIENTIFIC_CHOICE", "Adopt candidate class definitions (with Y-D05d, Y-D06a, F-D05)", "Class construct validity", "Y-D07, F-D17"),
 "A-D06": ("P2", "TECHNICAL_RECOMMENDATION", "Adopt corrected dataset description (57 runs, realizations, 1 s verified, H2 fraction unverified)", "Inaccurate dataset section", "A11"),
 "A-D07": ("P1", "TECHNICAL_RECOMMENDATION", "Sign off; document tie-inclusive neighbourhood and natural-log entropy", "Undocumented deviations", "A8"),
 "A-D08": ("P2", "TECHNICAL_RECOMMENDATION", "Adopt claim register", "Overclaiming", "A8, A11"),
 "A-D09": ("P3", "TECHNICAL_RECOMMENDATION", "Rewrite README 2/6/7 and FIGURE_SPECIFICATION; keep quarantine until then", "Public docs still show fabricated figures and 'zero leakage'", "None (documentation)"),
 "A-D10": ("P0", "SCIENTIFIC_CHOICE", "Re-record Gates 1-3 after Y/F decisions", "Experiments under unsupported PASS records", "Experimental authorization"),
 "A-D11": ("P3", "VERIFIED_FACT", "Add Plan 2 PDFs to assets/", "Traceability gap", "None"),
 "G-D01": ("P3", "TECHNICAL_RECOMMENDATION", "Executed with explicit user authorization in session (commits 1fda183, db6876a, 5926a6c, 78618db; follow-up df4c539). Matrix status left unchanged per Phase-5 rule; the user may record it", "None", "None"),
}

ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}


def main():
    rows = list(csv.DictReader(open(P4, encoding="utf-8")))
    assert {r["decision_id"] for r in rows} == set(R), "decision ID mismatch with Phase 4 matrix"
    out = []
    for r in rows:
        p, cls, rec, risk, blocks = R[r["decision_id"]]
        out.append({"decision_id": r["decision_id"], "owner": r["owner"], "priority": p, "phase5_class": cls,
                    "decision_required": r["question"], "evidence_available": r["available_evidence"],
                    "evidence_files": r["evidence_files"], "options": r["valid_options"],
                    "phase5_recommendation": rec, "justification_p4": r["justification"], "main_risk": risk,
                    "blocks": blocks, "human_approval_required": "YES", "status": "PENDING_HUMAN_APPROVAL"})
    out.sort(key=lambda x: (ORDER[x["priority"]], x["decision_id"]))
    with open(HERE / "DECISION_REVIEW_P5.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, list(out[0]), lineterminator="\n"); w.writeheader(); w.writerows(out)

    cnt = {k: sum(1 for x in out if x["priority"] == k) for k in ORDER}
    cls = {k: sum(1 for x in out if x["phase5_class"] == k) for k in ("VERIFIED_FACT", "TECHNICAL_RECOMMENDATION", "SCIENTIFIC_CHOICE", "UNRESOLVED")}
    md = ["# Critical-Path Decisions (Phase 5; generated by build_phase5_review.py)", "",
          f"44 decisions reviewed: P0 {cnt['P0']} · P1 {cnt['P1']} · P2 {cnt['P2']} · P3 {cnt['P3']}. "
          f"Classes: " + ", ".join(f"{k} {v}" for k, v in cls.items()) + ". **All PENDING_HUMAN_APPROVAL.**", "",
          "Priority rules: **P0** blocks valid experimental execution (data/class/split/model/threshold definitions, missing implementation, gates). "
          "**P1** must be settled before the configuration freeze but does not change split assignment or class definitions. "
          "**P2** can be completed alongside implementation. **P3** documentation / non-blocking.", "",
          "Key Phase-5 re-assessment: under LOTO outer and LOTO_within_train inner splits every family nests inside one topology, so the family-map decisions "
          "(Y-D03, Y-D04) do **not** change any split; they affect only the uncertainty unit (F-D13) and development-mode query-family exclusion, hence P1.", "",
          "| Priority | Decision ID | Owner | Recommended action | Evidence | Blocks | Approval needed |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for x in out:
        md.append(f"| {x['priority']} | {x['decision_id']} | {x['owner']} | {x['phase5_recommendation'].replace('|', '/')} | "
                  f"{x['evidence_files'].replace('|', '/')} | {x['blocks'].replace('|', '/')} | {x['owner']} |")
    (HERE / "CRITICAL_PATH_DECISIONS.md").write_bytes(("\n".join(md) + "\n").encode("utf-8"))

    for who in ("Yazan", "Faisal", "Ahmed"):
        sub = [x for x in out if who in x["owner"]]
        s = [f"# {who}: Sign-off Sheet (Phase 5)", "",
             f"{len(sub)} decisions ({sum(1 for x in sub if x['priority']=='P0')} P0). Joint decisions also appear on the co-owners' sheets and need every owner's signature. "
             "Recommendations are not decisions; fill the fields yourself. Full context: `TEAM_DECISION_BRIEF.md`, `DECISION_REVIEW_P5.csv`.", ""]
        for x in sub:
            s += [f"## {x['decision_id']} [{x['priority']} · {x['phase5_class']}] ({x['owner']})", "",
                  f"- **Decision:** {x['decision_required']}",
                  f"- **Recommended:** {x['phase5_recommendation']}",
                  f"- **Evidence:** {x['evidence_files']}",
                  f"- **Implications / main risk:** {x['main_risk']}",
                  f"- **Triggers / unblocks:** {x['blocks']}",
                  "- **Approve (exact option, artifact hash/version, conditions):** ______________________",
                  "- **Reject / alternative / send back for evidence (reason):** ______________________",
                  "- **Signature / date / evidence reference:** ______________________", ""]
        (HERE / f"{who.upper()}_SIGNOFF.md").write_bytes(("\n".join(s) + "\n").encode("utf-8"))
    print(cnt, cls)


if __name__ == "__main__":
    main()
