#!/usr/bin/env python3
"""Phase 6: UPDATED_DECISION_MATRIX.csv = Phase-5 review + Phase-6 technical status + resolution.
Technical status never implies human approval. Only G-D01 carries APPROVED_BY_HUMAN (explicit user
instruction approving the commit plan; commits 1fda183..78618db).
Usage (repo root): python 06_audit_preparation/phase6_resolution/build_updated_matrix.py"""

import csv
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
P5 = HERE.parent / "phase5_decisions" / "DECISION_REVIEW_P5.csv"
PS, VE, IM, TE, RE, BL, AP = ("PROVISIONALLY_SELECTED", "VERIFIED", "IMPLEMENTED", "TESTED",
                              "RECOMMENDED_FOR_APPROVAL", "BLOCKED_BY_EVIDENCE", "APPROVED_BY_HUMAN")
S = {  # id: (technical_status, phase-6 resolution / artifact)
 "Y-D01": (PS, "57 runs / 51 eligible encoded in CANDIDATE_MANIFEST_V02.csv"),
 "Y-D02": (VE, "60/60 clean-vs-noise relations; one realization per run enforced in feature_table.py"),
 "Y-D03": (BL, "Ancestry undeterminable from data; interim: primary map keeps 11 start-up pairs separate, extended map groups all 19; no split affected"),
 "Y-D04": (PS, "Scenario_Family_ID = family_primary in v0.2; extended/conservative columns for sensitivity"),
 "Y-D05a": (BL, "True location unknown; restriction implemented: location_analysis_allowed=False for leakG5G6 runs"),
 "Y-D05b": (BL, "Annotation truth unknown; restriction implemented: excluded (eligible_primary=False)"),
 "Y-D05c": (VE, "Compound runs excluded in v0.2"),
 "Y-D05d": (PS, "15 multi-location leak runs mapped to LEAK in v0.2"),
 "Y-D06a": (BL, "Cause of 1000 s offset unknown; restriction: post-event rows excluded by pre_event_policy=exclude"),
 "Y-D06b": (PS, "phase_used=False; onset_s recorded"),
 "Y-D07": (IM, "CANDIDATE_MANIFEST_V02.csv built deterministically (sha256 36bcbaf9...)"),
 "Y-D08": (RE, "READY_WITH_EXCLUSIONS (restricted) - see YAZAN_RESOLUTION.md A6"),
 "Y-D09": (IM, "src/h2prism/dataset_manifest.py is the reference builder"),
 "Y-D10": (VE, "CRLF->LF cause verified; regeneration is Yazan's action"),
 "F-D01": (PS, "noise_added primary, clean secondary, pooling forbidden (config + feature_table.py)"),
 "F-D02": (PS, "LOTO folds pinned in config"),
 "F-D03": (PS, "LOTO_within_train pinned in config"),
 "F-D04": (PS, "60/30, min_samples 60; 60/60 sensitivity"),
 "F-D05": (PS, "exclude primary; label_normal secondary"),
 "F-D06": (PS, "128 features; 80 offset-invariant sensitivity"),
 "F-D07": (PS, "pooled primary; NORMAL/FAULT/DELAY descriptive only"),
 "F-D08": (TE, "k=25 uniform; new TOP_CLASS_FEW_INDEPENDENT_RUNS flag implemented and tested"),
 "F-D09": (TE, "candidates none/sigmoid; calibration_feasibility fallback implemented and tested"),
 "F-D10": (TE, "src/h2prism/combined_score.py cross-fitted meta-model implemented and tested"),
 "F-D11": (PS, "p-only, singleton->UNRESOLVED, max 2; blocking flags incl. TOP_CLASS_FEW_INDEPENDENT_RUNS (consequence documented)"),
 "F-D12": (PS, "0.80 primary target from plan F10; unattainable coverage reported, never forced"),
 "F-D13": (TE, "src/h2prism/uncertainty.py stratified paired family bootstrap implemented and tested"),
 "F-D14": (PS, "plan RF grid, seed 20261104"),
 "F-D15": (TE, "all modules tested; human code review pending"),
 "F-D16": (RE, "contract amendments listed in MODEL_AND_EXPERIMENT_READINESS.md"),
 "F-D17": (PS, "CANDIDATE_EVALUATION_CONFIG.yaml complete; no open value, every block PENDING_HUMAN_SIGNOFF"),
 "F-D18": (TE, "A12-A16 tested; acceptance pending"),
 "A-D01": (RE, "RQ1 testable with restrictions; inference protocol in AHMED_RESOLUTION.md"),
 "A-D02": (RE, "RQ2 operational criteria defined before experiments"),
 "A-D03": (RE, "scope: unseen withdrawal topology of the simulated network"),
 "A-D04": (PS, "effect sizes only (config)"),
 "A-D05": (RE, "candidate class definitions consistent across v0.2, label mapping and config"),
 "A-D06": (RE, "dataset description text prepared"),
 "A-D07": (VE, "code/method consistency re-verified incl. combined score"),
 "A-D08": (RE, "SCIENTIFIC_LIMITATIONS_AND_CLAIMS.md"),
 "A-D09": (RE, "replacement text for README 2/6/7 and FIGURE_SPECIFICATION prepared, not applied"),
 "A-D10": (RE, "gate re-record after Y/F signoff"),
 "A-D11": (VE, "Plan 2 PDFs exist outside repo; adding them is Ahmed's action"),
 "G-D01": (AP, "User explicitly approved the 4-commit plan (executed) and the LF fix commit"),
}


def main():
    rows = list(csv.DictReader(open(P5, encoding="utf-8")))
    assert {r["decision_id"] for r in rows} == set(S)
    out = []
    for r in rows:
        t, res = S[r["decision_id"]]
        out.append({"decision_id": r["decision_id"], "owner": r["owner"], "priority": r["priority"],
                    "decision_class": r["phase5_class"], "decision_required": r["decision_required"],
                    "phase6_technical_status": t, "phase6_resolution": res,
                    "recommendation": r["phase5_recommendation"], "evidence_files": r["evidence_files"],
                    "signoff_status": AP if t == AP else "PENDING_HUMAN_SIGNOFF",
                    "approver": "", "approval_date": "", "approval_evidence": "" if t != AP else "user instruction in session; commits 1fda183, db6876a, 5926a6c, 78618db, df4c539"})
    with open(HERE / "UPDATED_DECISION_MATRIX.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, list(out[0]), lineterminator="\n"); w.writeheader(); w.writerows(out)
    print(Counter(o["phase6_technical_status"] for o in out), Counter(o["signoff_status"] for o in out))


if __name__ == "__main__":
    main()
