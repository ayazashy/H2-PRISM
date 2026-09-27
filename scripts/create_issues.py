"""
Script to create GitHub Issues for H2-PRISM workspace project plan.
"""

import subprocess
import json

ISSUES = [
    # --- Ahmed (Plan 1) ---
    {
        "title": "[Ahmed - Day 1] Audit H2-SimNet Dataset & Document Measurement Configuration",
        "labels": ["plan:ahmed", "phase:day-1", "documentation"],
        "body": """### Scope: Person 1 (Ahmed) - Day 1
**References**: `assets/Ahmed Plan.pdf` (Steps 1-3), `AUDIT.md`

#### Objectives:
- [ ] Inspect raw dataset files downloaded into `data/raw/H2-SimNet/`.
- [ ] Verify sampling interval (dt), channel names, and units.
- [ ] Confirm presence or absence of temperature measurements.
- [ ] Check whether sensor-fault labels or explicit leak locations exist.
- [ ] Output forensic summary to `AUDIT.md` and `results/data_audit.csv`.

> **Rule**: Do not infer answers from the proposal if the dataset contradicts them. The actual dataset wins."""
    },
    {
        "title": "[Ahmed - Day 1] Select 6 Representative Benchmark Scenarios",
        "labels": ["plan:ahmed", "phase:day-1", "enhancement"],
        "body": """### Scope: Person 1 (Ahmed) - Day 1
**References**: `assets/Ahmed Plan.pdf` (Step 4), `MATERIALS.md`

#### Objectives:
- [ ] Select 6 complete representative scenario/run files:
  1. Normal operation
  2. Weak / moderate leak
  3. Stronger leak
  4. Compressor / operational transient
  5. Startup / delayed response
  6. Overlapping or ambiguous scenario
- [ ] Place scenario references in `data/selected/` and record in `results/materials_manifest.csv`.
- [ ] Ensure full temporal continuity is preserved (no random row sampling)."""
    },
    {
        "title": "[Ahmed - Day 1] Implement Ingestion Loader & Sensor Quality Control",
        "labels": ["plan:ahmed", "phase:day-1", "enhancement"],
        "body": """### Scope: Person 1 (Ahmed) - Day 1
**References**: `assets/Ahmed Plan.pdf` (Steps 5-7), `src/data.py`, `src/quality.py`

#### Objectives:
- [ ] Finalize `src/data.py` to return standardized DataFrames preserving original metadata.
- [ ] Finalize `src/quality.py` to flag:
  - Missing values, duplicates, non-monotonic timestamps, sampling gaps.
  - Sensor saturation, stuck segments, and physical range violations.
- [ ] Compute overall data adequacy score $O_Q \in [0, 1]$.
- [ ] Ensure non-destructive flagging (`GOOD`, `MISSING`, `GAP`, `STUCK`, `INVALID`)."""
    },
    {
        "title": "[Ahmed - Day 2] Implement Line-Pack Corrected Mass Balance Residual",
        "labels": ["plan:ahmed", "phase:day-2", "enhancement"],
        "body": """### Scope: Person 1 (Ahmed) - Day 2
**References**: `assets/Ahmed Plan.pdf` (Steps 8-11), `src/physics.py`

#### Objectives:
- [ ] Implement hydrogen real-gas density $\\rho = \\frac{P \\cdot M_{H_2}}{Z(P,T) R T}$ in `src/physics.py`.
- [ ] Implement line-pack mass estimation $\\hat{M}_{line} \\approx A \\cdot L \\cdot \\bar{\\rho}$.
- [ ] Calculate corrected loss rate $\\hat{m}_{loss} = \\int (\\dot{m}_{in} - \\dot{m}_{out}) dt - \\Delta \\hat{M}_{line}$.
- [ ] Calculate standardized statistic $z_{MB} = \\hat{m}_{loss} / \\sigma_{MB}$.
- [ ] Implement cross-sensor consistency score between $\\Delta P$ and $\\Delta \\dot{m}$."""
    },
    {
        "title": "[Ahmed - Day 2] Implement Cross-Correlation Delay & Conditional Localization",
        "labels": ["plan:ahmed", "phase:day-2", "enhancement"],
        "body": """### Scope: Person 1 (Ahmed) - Day 2
**References**: `assets/Ahmed Plan.pdf` (Steps 12-14), `src/propagation.py`

#### Objectives:
- [ ] Calculate theoretical temporal resolution floor $\\delta = \\frac{a \\cdot \\Delta t}{2}$ for hydrogen wave speed $a \\approx 1300$ m/s.
- [ ] Estimate time lag $\\Delta t_{12} = \\arg\\max_\\tau C_{12}(\\tau)$ via cross-correlation of upstream and downstream signals.
- [ ] Derive conditional location interval $\\hat{x} \\pm \\delta$.
- [ ] If propagation cannot be reliably resolved, return `LOCALIZATION_NOT_OBSERVABLE`. Never report false precision."""
    },
    {
        "title": "[Ahmed - Day 2/3] Physics Unit Tests & Scientific Assumptions Ledger",
        "labels": ["plan:ahmed", "phase:day-2", "phase:day-3", "documentation"],
        "body": """### Scope: Person 1 (Ahmed) - Day 2/3
**References**: `assets/Ahmed Plan.pdf` (Steps 15-19), `tests/test_physics.py`, `ASSUMPTIONS.md`

#### Objectives:
- [ ] Implement comprehensive sanity unit tests in `tests/test_physics.py` (sign convention, zero flow, synthetic leak, resolution floor).
- [ ] Update `ASSUMPTIONS.md` with explicit classifications (`VERIFIED`, `DERIVED`, `ASSUMED`, `UNKNOWN`).
- [ ] Complete `results/dataset_truth_table.md`."""
    },

    # --- Faisal (Plan 2) ---
    {
        "title": "[Faisal - Day 1] Multi-Group Feature Extraction & Scenario-Level Splitting",
        "labels": ["plan:faisal", "phase:day-1", "enhancement"],
        "body": """### Scope: Person 2 (Faisal) - Day 1
**References**: `assets/Faisal Plan.pdf` (Steps 1-3, 5), `src/features.py`

#### Objectives:
- [ ] Implement `src/features.py` to extract:
  - Group A: Raw signal levels
  - Group B: Temporal derivatives and rolling statistics
  - Group C: Cross-station correlations
  - Group D: Physics residuals (consuming Person 1)
  - Group E: Propagation metrics (consuming Person 1)
- [ ] Enforce strict scenario/run-level splitting (no windows from the same scenario in both train and test)."""
    },
    {
        "title": "[Faisal - Day 1] Benchmark Baseline Classifiers (LR, RF vs XGBoost)",
        "labels": ["plan:faisal", "phase:day-1", "enhancement"],
        "body": """### Scope: Person 2 (Faisal) - Day 1
**References**: `assets/Faisal Plan.pdf` (Steps 4, 6), `notebooks/baseline_models.ipynb`

#### Objectives:
- [ ] Evaluate Logistic Regression, Random Forest, and XGBoost baselines.
- [ ] Document in `notebooks/baseline_models.ipynb`.
- [ ] Validate whether physics-informed features add measurable separation over raw baselines."""
    },
    {
        "title": "[Faisal - Day 2] Candidate Transient Wavelet Layer & Feature Ablation",
        "labels": ["plan:faisal", "phase:day-2", "enhancement"],
        "body": """### Scope: Person 2 (Faisal) - Day 2
**References**: `assets/Faisal Plan.pdf` (Steps 7-9), `src/fingerprint.py`, `notebooks/feature_ablation.ipynb`

#### Objectives:
- [ ] Implement compact Continuous Wavelet Transform (CWT) feature extraction in `src/fingerprint.py`.
- [ ] Execute ablation study across Configurations:
  - Config A: Raw / Temporal only
  - Config B: Raw + Temporal + Physics
  - Config C: Raw + Temporal + Physics + Propagation
  - Config D: Raw + Temporal + Physics + Propagation + Transient Fingerprint
- [ ] Document whether wavelets improve attribution or should be dropped."""
    },
    {
        "title": "[Faisal - Day 2] Multi-Class Event Attribution & Probability Calibration",
        "labels": ["plan:faisal", "phase:day-2", "enhancement"],
        "body": """### Scope: Person 2 (Faisal) - Day 2
**References**: `assets/Faisal Plan.pdf` (Steps 10-12), `src/model.py`

#### Objectives:
- [ ] Implement multi-class attribution (`NORMAL`, `LEAK`, `OPERATIONAL_TRANSIENT`, `SENSOR_FAULT`).
- [ ] Return class probabilities, probability margin, and top/second hypotheses.
- [ ] Implement post-hoc probability calibration (Platt/Isotonic) on validation split.
- [ ] Separate synthetic sensor fault overlays from primary H2-SimNet evaluation."""
    },
    {
        "title": "[Faisal - Day 3] Contradiction-Aware Evidence Engine & Fusion Comparison",
        "labels": ["plan:faisal", "phase:day-3", "enhancement"],
        "body": """### Scope: Person 2 (Faisal) - Day 3
**References**: `assets/Faisal Plan.pdf` (Steps 13-17), `src/evidence.py`

#### Objectives:
- [ ] Implement contradiction score quantifying conflict between ML likelihood and physics/propagation.
- [ ] Compare fusion methods: Calibrated Probabilistic Stacking vs. Dempster-Shafer combination.
- [ ] Calculate False Physical Attribution Rate (FPAR) and coverage curves.
- [ ] Provide stable handoff interface (`MLResult` and `EvidenceResult`) to Person 3."""
    },

    # --- Yazan (Plan 3 & Materials Lead) ---
    {
        "title": "[Yazan - Day 1] Materials Lead: Dataset Acquisition & Provenance Ledger",
        "labels": ["plan:yazan", "phase:day-1", "documentation"],
        "body": """### Scope: Person 3 (Yazan) - Materials Lead Day 1
**References**: `assets/_Materials & Data Provenance Lead.pdf`, `MATERIALS.md`, `README_data.md`

#### Objectives:
- [ ] Acquire official H2-SimNet package (Zenodo Record 17871393) into `data/raw/H2-SimNet/`.
- [ ] Record metadata (DOI, version, license, download size, MD5/checksums).
- [ ] Create complete file inventory in `MATERIALS.md` and `results/materials_manifest.csv`.
- [ ] Formulate formal Data Provenance statement."""
    },
    {
        "title": "[Yazan - Day 1] Define Data Contracts & Stage 1 Candidate Event Detector",
        "labels": ["plan:yazan", "phase:day-1", "enhancement"],
        "body": """### Scope: Person 3 (Yazan) - Day 1
**References**: `assets/Yazan Plan.pdf` (Steps 2-6), `src/schema.py`, `src/detector.py`

#### Objectives:
- [ ] Define shared dataclasses in `src/schema.py` (`EventCandidate`, `PhysicsEvidence`, `PropagationEvidence`, `MLResult`, `ObservabilityResult`, `Decision`, `StructuredEventReport`).
- [ ] Implement Stage 1 candidate detector in `src/detector.py` based on uncorrected imbalance and $dP/dt$.
- [ ] Extract bounded event windows with pre-event context and post-event recovery."""
    },
    {
        "title": "[Yazan - Day 2] Master Pipeline Orchestrator & CLI Scenario Runner",
        "labels": ["plan:yazan", "phase:day-2", "enhancement"],
        "body": """### Scope: Person 3 (Yazan) - Day 2
**References**: `assets/Yazan Plan.pdf` (Steps 7-9), `src/pipeline.py`, `run_scenario.py`

#### Objectives:
- [ ] Integrate Person 1 and Person 2 modules into `src/pipeline.py`.
- [ ] Provide CLI execution runner in `run_scenario.py`.
- [ ] Verify execution without manual intervention or intermediate file copying."""
    },
    {
        "title": "[Yazan - Day 2] Independent 3-Axis Observability Engine & UNKNOWN Logic",
        "labels": ["plan:yazan", "phase:day-2", "enhancement"],
        "body": """### Scope: Person 3 (Yazan) - Day 2
**References**: `assets/Yazan Plan.pdf` (Steps 10-12), `src/observability.py`, `src/decision.py`

#### Objectives:
- [ ] Implement independent 3-axis observability: $O = \\min(O_Q, O_S, O_E)$.
- [ ] Implement decision gate: emit attribution only if observability, confidence, and margin clear thresholds.
- [ ] Return `UNKNOWN` with explicit failing diagnostic reason whenever evidence is insufficient.
- [ ] Report decision coverage alongside accuracy and FPAR."""
    },
    {
        "title": "[Yazan - Day 3] Architecture Freeze, 4 Demonstration Scenarios & Final Package",
        "labels": ["plan:yazan", "phase:day-3", "documentation"],
        "body": """### Scope: Person 3 (Yazan) - Day 3
**References**: `assets/Yazan Plan.pdf` (Steps 13-22), `notebooks/demonstration.ipynb`, `README.md`

#### Objectives:
- [ ] Freeze pipeline architecture (no major algorithmic changes on Day 3).
- [ ] Build and document 4 representative demonstration scenarios:
  1. Demo 1: NORMAL
  2. Demo 2: LEAK (with mass balance & propagation delay)
  3. Demo 3: OPERATIONAL TRANSIENT (with line-pack explanation)
  4. Demo 4: UNKNOWN (insufficient observability / ambiguity)
- [ ] Conduct final scientific audit: ensure no fabricated metrics, no unsupported claims, and field-validation disclaimers are preserved."""
    },
]

def main():
    repo = "ayazashy/H2-PRISM"
    for issue in ISSUES:
        cmd = [
            "gh", "issue", "create",
            "-R", repo,
            "--title", issue["title"],
            "--body", issue["body"]
        ]
        for lbl in issue["labels"]:
            cmd.extend(["--label", lbl])
        
        print(f"Creating: {issue['title']}")
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"  -> Created: {res.stdout.strip()}")
        else:
            print(f"  -> Error: {res.stderr.strip()}")

if __name__ == "__main__":
    main()
