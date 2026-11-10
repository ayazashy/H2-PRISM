"""Every PRE-EXPERIMENT deliverable named in the original Yazan/Faisal/Ahmed plans exists at its plan path,
and the governance artifacts that back the completion matrix are well formed. Post-experiment result files
(03_results/*, manuscript, methodology draft) are intentionally NOT required here."""

import hashlib
import re
from pathlib import Path

import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]

PRE_EXPERIMENT_DELIVERABLES = {
    "Y1": ["01_dataset_audit/raw_checksums.sha256", "01_dataset_audit/FILE_LEVEL_AUDIT.csv", "01_dataset_audit/SENSOR_CHANNEL_AUDIT.csv",
           "01_dataset_audit/DUPLICATE_EXPORT_AUDIT.csv", "01_dataset_audit/DATASET_INVENTORY.md", "01_dataset_audit/Y1_AUDIT_LOG.md",
           "01_dataset_audit/DATASET_AUDIT_AMENDMENT_2026-11.md",
           "06_audit_preparation/phase8_execution_readiness/RAW_CHECKSUMS_OFFICIAL_ARCHIVE.sha256"],
    "Y2": ["01_dataset_audit/DATASET_SCENARIO_MAP.csv", "01_dataset_audit/SCENARIO_RELATIONSHIP_EDGES.csv",
           "01_dataset_audit/SCENARIO_FAMILY_REPORT.md", "01_dataset_audit/SCENARIO_INDEPENDENCE_AUDIT.md",
           "01_dataset_audit/GROUPING_SENSITIVITY_REPORT.md", "06_audit_preparation/pre_experiment_review/CANDIDATE_FAMILY_MAP.csv"],
    "Y3": ["01_dataset_audit/OPERATING_CONDITIONS_AUDIT.csv", "01_dataset_audit/EVENT_TIMING_AUDIT.csv",
           "01_dataset_audit/PHASE_AND_LABEL_DISTRIBUTION.md", "01_dataset_audit/PHASE_CONFOUNDING_REPORT.md"],
    "Y4": ["01_dataset_audit/ORIGINAL_LABEL_INVENTORY.csv", "01_dataset_audit/LABEL_OVERLAP_MATRIX.csv", "01_dataset_audit/LABEL_MAPPING_SPEC.md",
           "01_dataset_audit/LABEL_ANNOTATION_AUDIT.md", "01_dataset_audit/class_mapping.yaml",
           "06_audit_preparation/pre_experiment_review/CANDIDATE_LABEL_MAPPING.yaml"],
    "Y5": ["01_dataset_audit/FAMILY_CLASS_DISTRIBUTION.csv", "01_dataset_audit/SPLIT_FEASIBILITY_REPORT.md",
           "01_dataset_audit/DATA_LEAKAGE_ASSESSMENT.md", "01_dataset_audit/PROPOSED_GROUPED_EVALUATION_DESIGN.md",
           "06_audit_preparation/pre_experiment_review/CANDIDATE_OUTER_FOLDS.csv"],
    "Y7": ["01_dataset_audit/DATASET_READINESS_REPORT.md", "01_dataset_audit/YAZAN_TECHNICAL_ACCEPTANCE_PACKAGE.md"],
    "Y8": ["01_dataset_audit/provisional/PROVISIONAL_DATA_FREEZE_MANIFEST.csv", "01_dataset_audit/provisional/PROVISIONAL_LABEL_MAPPING.yaml",
           "01_dataset_audit/provisional/PROVISIONAL_DATA_FREEZE_NOTES.md", "01_dataset_audit/provisional/PROVISIONAL_DATA_FREEZE_VERSION.txt"],
    "Y-RISK": ["00_governance/RISK_REGISTER.csv"],
    "F1": ["00_governance/REPO_CLASSIFICATION.csv", "00_governance/REPOSITORY_AUDIT_REPORT.md", "00_governance/LEGACY_RESULTS_STATUS.md"],
    "F2": ["02_methodology/DIAGNOSTIC_PROBLEM_FORMULATION.md"],
    "F3": ["02_methodology/PREPROCESSING_SPEC.md", "02_methodology/WINDOWING_SPEC.md", "02_methodology/FEATURE_EXTRACTION_SPEC.md",
           "02_methodology/FEATURE_DEFINITION_REGISTER.csv", "src/h2prism/io.py", "src/h2prism/windows.py", "src/h2prism/features.py",
           "tests/test_io.py", "tests/test_windows.py", "tests/test_features.py"],
    "F4": ["02_methodology/GROUPED_EVALUATION_PROTOCOL.md", "02_methodology/FOLD_VALIDATION_REPORT.md",
           "configs/frozen_evaluation_config.yaml", "06_audit_preparation/FINAL_EXPERIMENT_CONFIG.yaml"],
    "F5": ["02_methodology/BASELINE_MODEL_SPEC.md", "src/h2prism/baseline.py"],
    "F6": ["02_methodology/PROBABILITY_CALIBRATION_SPEC.md", "src/h2prism/calibration.py"],
    "F7": ["02_methodology/DISTINGUISHABILITY_MATHEMATICAL_SPEC.md", "02_methodology/D_STATISTIC_IMPLEMENTATION_SPEC.md",
           "02_methodology/D_STATISTIC_EDGE_CASES.md", "02_methodology/D_STATISTIC_DESIGN_DECISION.md",
           "src/h2prism/distinguishability.py", "tests/test_distinguishability.py"],
    "F8": ["02_methodology/UNCERTAINTY_AND_DISTINGUISHABILITY_COMPARATORS.md"],
    "F9": ["02_methodology/SELECTIVE_DIAGNOSTIC_POLICY.md", "02_methodology/AMBIGUITY_SET_CONSTRUCTION.md",
           "02_methodology/DECISION_POLICY_PSEUDOCODE.md", "02_methodology/POLICY_THRESHOLD_SELECTION.md",
           "src/h2prism/policy.py", "tests/test_policy.py"],
    "F10": ["src/h2prism/experiments/primary_protocol.py", "tools/experiments/run_primary_protocol.py"],
    "F11": ["02_methodology/STATISTICAL_ANALYSIS_PLAN.md", "02_methodology/SENSITIVITY_ANALYSIS_SPEC.md", "src/h2prism/uncertainty.py"],
    "F12": ["00_governance/TECHNICAL_INTEGRATION_ARCHITECTURE_FREEZE.md", "configs/interface_contracts.yaml",
            "00_governance/CHANGE_CONTROL_LOG.csv"],
    "F13": ["04_validation/TEST_RESULTS.md", "04_validation/LEAKAGE_TEST_REPORT.md", "04_validation/EXPERIMENT_REPRODUCIBILITY_REPORT.md"],
    "A1": ["05_documentation/METHODOLOGY_MASTER_STRUCTURE.md"],
    "A2": ["05_documentation/PROBLEM_FORMULATION_AND_MOTIVATION.md"],
    "A3": ["05_documentation/DATASET_DESCRIPTION.md", "05_documentation/REPOSITORY_DERIVED_FINDINGS.md", "05_documentation/DATASET_LIMITATIONS.md"],
    "A4": ["05_documentation/MATHEMATICAL_CONSISTENCY_REVIEW.md"],
    "A5": ["05_documentation/RESULTS_REPORTING_TEMPLATE.md", "05_documentation/RESULTS_TABLE_SPECIFICATION.md",
           "05_documentation/FIGURE_SPECIFICATION.md", "05_documentation/FIGURE_PROVENANCE_REGISTER.csv"],
    "A6": ["05_documentation/METHOD_IMPLEMENTATION_TRACEABILITY.md"],
    "A7": ["05_documentation/SCIENTIFIC_CLAIM_AND_LIMITATION_REGISTER.md"],
    "A9": ["00_governance/MASTER_TASK_REGISTER.csv", "00_governance/GATE_DECISIONS.md"],
    "A10": ["05_documentation/DATA_PROVENANCE.md", "05_documentation/DATA_PROCESSING_HISTORY.md", "05_documentation/PROVENANCE_REGISTER.csv"],
    "A12": ["tools/research_audit/validate_artifacts.py", "tools/research_audit/build_provenance_index.py", "tests/test_research_audit.py",
            "05_documentation/ARTIFACT_VALIDATION_REPORT.md"],
    "A13": ["tools/reporting/build_research_figures.py", "tools/reporting/build_research_tables.py", "configs/reporting_figures.yaml",
            "tests/test_reporting_outputs.py", "05_documentation/REPORTING_AUTOMATION_SPEC.md", "05_documentation/FIGURE_BUILD_MANIFEST.csv"],
    "A14": ["src/h2prism/secondary_baseline.py", "configs/secondary_baseline.yaml", "tests/test_secondary_baseline.py",
            "02_methodology/SECONDARY_BASELINE_SPEC.md"],
    "A15": ["src/h2prism/experiments/feature_sensitivity.py", "configs/feature_sensitivity.yaml", "tests/test_feature_sensitivity.py",
            "02_methodology/FEATURE_SENSITIVITY_PROTOCOL.md"],
    "A16": ["src/h2prism/comparators.py", "src/h2prism/experiments/supporting_ablations.py", "tests/test_comparators.py",
            "tests/test_supporting_ablations.py", "02_methodology/SUPPORTING_COMPARATOR_AND_ABLATION_SPEC.md"],
}


@pytest.mark.parametrize("task", sorted(PRE_EXPERIMENT_DELIVERABLES))
def test_pre_experiment_deliverables_exist(task):
    missing = [p for p in PRE_EXPERIMENT_DELIVERABLES[task] if not (ROOT / p).is_file()]
    assert not missing, missing


def test_frozen_config_pointer_matches_pinned_config():
    ptr = yaml.safe_load((ROOT / "configs" / "frozen_evaluation_config.yaml").read_text(encoding="utf-8"))["frozen_config"]
    assert hashlib.sha256((ROOT / ptr["file"]).read_bytes()).hexdigest() == ptr["sha256"]


def test_risk_register_has_plan_fields_and_all_plan_risks():
    r = pd.read_csv(ROOT / "00_governance" / "RISK_REGISTER.csv")
    plan_fields = ["risk_id", "description", "probability", "impact", "early_warning_signal", "mitigation", "fallback",
                   "owner", "status", "effect_on_claims"]
    assert set(plan_fields) <= set(r.columns) and r.risk_id.is_unique and len(r) >= 17
    assert r[plan_fields].notna().all().all()


def test_superseded_dataset_documents_point_to_amendment():
    for f in ["DATASET_INVENTORY.md", "Y1_AUDIT_LOG.md", "SCENARIO_FAMILY_REPORT.md", "SPLIT_FEASIBILITY_REPORT.md",
              "DATA_LEAKAGE_ASSESSMENT.md", "DATASET_READINESS_REPORT.md", "PHASE_CONFOUNDING_REPORT.md", "LABEL_MAPPING_SPEC.md"]:
        head = (ROOT / "01_dataset_audit" / f).read_text(encoding="utf-8")[:400]
        assert "DATASET_AUDIT_AMENDMENT_2026-11.md" in head, f


def test_task_register_uses_plan_vocabulary_and_no_premature_execution():
    r = pd.read_csv(ROOT / "00_governance" / "MASTER_TASK_REGISTER.csv")
    allowed = {"VERIFIED", "SPECIFIED", "TESTED", "PENDING", "PROVISIONAL", "DEFERRED", "IMPLEMENTED"}
    assert set(r.status) <= allowed
    assert not ({"EXECUTED", "VALIDATED", "FROZEN"} & set(r.status))
    assert {f"A{i}" for i in range(1, 17)} | {f"F{i}" for i in range(1, 14)} | {f"Y{i}" for i in range(1, 9)} <= set(r.task_id)


def test_completion_matrix_covers_all_37_plan_tasks():
    m = pd.read_csv(ROOT / "06_audit_preparation" / "final_acceptance" / "TEAM_PLAN_COMPLETION_MATRIX.csv")
    tasks = {re.sub(r"-.*", "", t) for t in m.plan_task_id}
    assert {f"Y{i}" for i in range(1, 9)} | {f"F{i}" for i in range(1, 14)} | {f"A{i}" for i in range(1, 17)} <= tasks
    assert set(m.phase10_status) <= {"VERIFIED_PRE_EXPERIMENT_COMPLETE", "PRE_EXPERIMENT_INCOMPLETE", "POST_EXPERIMENT_DEPENDENCY",
                                     "HUMAN_ATTESTATION_REQUIRED", "NOT_APPLICABLE_WITH_EVIDENCE"}
    for r in m.itertuples():  # every claimed completion cites evidence that exists
        if r.phase10_status == "VERIFIED_PRE_EXPERIMENT_COMPLETE":
            for p in str(r.evidence).split(";"):
                p = p.strip()
                if p and not p.startswith("("):
                    assert (ROOT / p).exists(), (r.requirement_id, p)


def test_no_research_results_or_authorization_exist():
    assert not (ROOT / "03_results" / "primary_protocol").exists()
    assert not list((ROOT / "06_audit_preparation").glob("EXECUTION_AUTHORIZATION*"))


def test_documentation_has_no_local_absolute_paths():
    pat = re.compile(r"(file:///|[A-Za-z]:\\Users\\|/Users/[a-z]+/)")
    for d in ("02_methodology", "05_documentation", "00_governance", "04_validation"):
        for f in (ROOT / d).glob("*.md"):
            assert not pat.search(f.read_text(encoding="utf-8")), f
    assert not pat.search((ROOT / "README.md").read_text(encoding="utf-8"))
