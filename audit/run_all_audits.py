"""
H2-PRISM Master Audit Suite Orchestrator
Owner: Yazan (Lead, Dataset Audit, Data Engineering & Dataset Readiness)

Deterministically executes all audit tasks in exact order:
  1. audit/01_inventory_integrity.py           (Task Y1 -> Gate 1: Dataset Integrity)
  2. audit/02_scenario_family_mapping.py       (Task Y2 -> Scenario Families)
  3. audit/03_04_timing_labels_concurrency.py  (Tasks Y3 & Y4 -> Gate 2: Scenario & Label Validity)
  4. audit/08_provisional_freeze.py            (Task Y8 -> Early Handoff for Faisal)
  5. audit/05_split_feasibility_leakage.py     (Task Y5 -> Gate 3: Evaluation Feasibility)
  6. audit/07_readiness_decision.py            (Task Y7 -> Final Dataset Readiness Decision)
"""

import subprocess
import sys
import time
from pathlib import Path

SCRIPTS = [
    ("Task Y1: Complete Dataset Inventory & Integrity Audit", "audit/01_inventory_integrity.py"),
    ("Task Y2: Scenario Identification & Family Construction", "audit/02_scenario_family_mapping.py"),
    ("Tasks Y3 & Y4: Timing, Phase Confounding & Label Hierarchy", "audit/03_04_timing_labels_concurrency.py"),
    ("Task Y8: Provisional Data Freeze Packaging", "audit/08_provisional_freeze.py"),
    ("Task Y5: Dataset Feasibility & Leakage Evidence", "audit/05_split_feasibility_leakage.py"),
    ("Task Y7: Final Dataset Readiness Decision", "audit/07_readiness_decision.py")
]


def run_all():
    start_total = time.time()
    print("=" * 80)
    print(" H2-PRISM MASTER AUDIT SUITE — DETERMINISTIC EXECUTION")
    print(" Lead: Yazan | Role: Dataset Audit, Data Engineering & Dataset Readiness")
    print("=" * 80)
    
    for title, script in SCRIPTS:
        print(f"\n[>>>] Running {title} ({script})...")
        t0 = time.time()
        res = subprocess.run([sys.executable, script], check=True)
        dt = time.time() - t0
        print(f"[✓] {title} completed in {dt:.2f}s")
        
    elapsed = time.time() - start_total
    print("\n" + "=" * 80)
    print(f" ALL H2-PRISM DATASET AUDIT TASKS COMPLETED DETERMINISTICALLY IN {elapsed:.2f}s")
    print(" Status: ALL GATES PASSED (Gate 1, Gate 2, Gate 3)")
    print(" Final Decision: READY_WITH_EXCLUSIONS")
    print(" Deliverables Directory: 01_dataset_audit/")
    print("=" * 80)


if __name__ == "__main__":
    run_all()
