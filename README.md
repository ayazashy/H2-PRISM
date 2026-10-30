# H2-PRISM: Identifiability-Aware Event Attribution and Selective Diagnosis in Hydrogen-Blend Pipeline Networks

> **Project Phase**: Stage 2 Active Research & Engineering Workspace  
> **Target Research Deadline**: 4 November 2026  
> **Dataset Anchor**: Peer-Reviewed H2-SimNet Dataset (Zenodo Record 17871393)  
> **Legacy Archive**: Stage 1 prototype and visual dashboard are preserved on branch [`old-main`](https://github.com/ayazashy/H2-PRISM/tree/old-main).

---

## 1. Project Overview & Research Identity

Abnormal pressure or flow readings in hydrogen-blend transmission networks do not automatically indicate physical containment loss. Fast operational transients (compressor ramp-up, valve throttling) and sensor malfunctions produce steep transient signatures ($dP/dt$) that can mimic genuine pipeline leaks.

**H2-PRISM (Stage 2)** reformulates pipeline monitoring from generic scalar anomaly detection into **identifiability-aware event attribution and selective diagnosis under structural ambiguity**:
1. **Empirical Distinguishability $D(x)$**: Investigates whether an empirical class-support statistic $D(x) = q_{(1)}(x) - q_{(2)}(x)$ derived from reference neighborhoods provides incremental decision value beyond calibrated confidence, probability margin, and entropy at matched coverage (**RQ1**).
2. **Three-Outcome Selective Diagnostic Policy**: Formulates a policy $g(x) \in \{\text{SPECIFIC}, \text{AMBIGUITY\_SET}, \text{UNRESOLVED}\}$ that produces informative ambiguity sets and explicit diagnostic abstentions when evidence is structurally insufficient (**RQ2**).
3. **Leakage-Safe Grouped Evaluation**: Enforces `Scenario_Family_ID` and topology-stratified cross-validation, strictly prohibiting random window splitting.

---

## 2. Quickstart: 5 Simple Steps to Run & Verify

Anyone opening this repository can inspect data, audit, test, and visualize the entire framework in under 30 seconds:

```bash
# Step 1: Install dependencies and editable package
pip install -r requirements.txt
pip install -e .

# Step 2: Instant dataset inspection & direct scenario test load
python3 -m h2prism.data

# Step 3: Execute the deterministic dataset audit suite (Completes in ~12 seconds)
python3 audit/run_all_audits.py

# Step 4: Run the automated test suite (23 passing tests: Data loader, Audits, Visualizations)
pytest tests/

# Step 5: Generate research figures & interactive HTML evaluation dashboard
python3 scripts/visualize.py --demo
# (Optional: append --open to automatically launch the interactive dashboard in your browser)
```

---

## 3. Clean Repository Architecture (Stage 2 Standard)

This repository is strictly organized to maintain reproducibility, separation of concerns, and scientific traceability:

```
H2-PRISM/
├── 00_governance/                         # Governance, task tracking & audit ledgers
│   ├── MASTER_TASK_REGISTER.csv           # Complete tasks across Ahmed, Faisal, Yazan
│   ├── GATE_DECISIONS.md                  # Formal gate approval decisions (Gates 1–8)
│   ├── REPO_CLASSIFICATION.csv            # Forensic classification of all components (Task F1)
│   ├── REPOSITORY_AUDIT_REPORT.md         # Full audit report of legacy vs Stage 2 items
│   └── LEGACY_RESULTS_STATUS.md           # Explicit status of prior Stage 1 claims
├── 01_dataset_audit/                      # Complete verified dataset audit (Yazan Tasks Y1–Y8)
│   ├── raw_checksums.sha256               # Cryptographic SHA-256 for all 265 raw files
│   ├── FILE_LEVEL_AUDIT.csv               # 265 file records with row counts, sampling dt, missingness
│   ├── SENSOR_CHANNEL_AUDIT.csv           # Comprehensive audit of PS1–PS12, MFS1–MFS4 (0 temp)
│   ├── DUPLICATE_EXPORT_AUDIT.csv         # Reconciled CSV vs Parquet mirror exports (1,423 pairs)
│   ├── DATASET_INVENTORY.md               # Definitive dataset inventory specification
│   ├── DATASET_SCENARIO_MAP.csv           # Reconciled 242 data files -> 58 scenarios -> 13 families
│   ├── SCENARIO_RELATIONSHIP_EDGES.csv    # 481 relationship edges between exports and variants
│   ├── SCENARIO_FAMILY_REPORT.md          # 13 defensible scenario families
│   ├── OPERATING_CONDITIONS_AUDIT.csv     # Operating phases & network topologies
│   ├── EVENT_TIMING_AUDIT.csv             # Ground truth event onset/offset timestamps
│   ├── PHASE_CONFOUNDING_REPORT.md        # Confounding warning: phase shortcut prevention
│   ├── ORIGINAL_LABEL_INVENTORY.csv       # Raw multi-label binary indicators
│   ├── LABEL_OVERLAP_MATRIX.csv           # Label co-occurrence matrix
│   ├── class_mapping.yaml                 # Frozen YAML class mapping contract for Faisal
│   ├── provisional/                       # Task Y8: Early provisional freeze unblocking Faisal
│   │   ├── PROVISIONAL_DATA_FREEZE_MANIFEST.csv
│   │   ├── PROVISIONAL_LABEL_MAPPING.yaml
│   │   ├── PROVISIONAL_DATA_FREEZE_NOTES.md
│   │   └── PROVISIONAL_DATA_FREEZE_VERSION.txt
│   ├── SPLIT_FEASIBILITY_REPORT.md        # Mathematical proof: 3-fold topology CV feasible
│   ├── DATA_LEAKAGE_ASSESSMENT.md         # 6 leakage pathways & verified assertions
│   ├── folds.csv                          # Outer fold assignments (276 records, 0 leakage)
│   └── DATASET_READINESS_REPORT.md        # Final Task Y7 Decision: READY_WITH_EXCLUSIONS
├── 02_methodology/                        # Methodology specifications (Ahmed & Faisal)
├── 03_results/                            # Machine-readable outputs & visual artifacts (Faisal)
│   ├── figures/                           # High-resolution (300 DPI) publication figures
│   │   ├── fig1_family_distribution.png
│   │   ├── fig2_pipeline_telemetry.png
│   │   ├── fig3_confusion_matrix.png
│   │   ├── fig4_risk_coverage_curve.png
│   │   ├── fig5_calibration_reliability.png
│   │   └── fig6_distinguishability_separation.png
│   └── dashboard.html                     # Standalone interactive evaluation dashboard (self-contained Base64)
├── 04_validation/                         # Software testing & leakage verification (Faisal)
├── 05_documentation/                      # Scientific manuscripts & provenance registers (Ahmed)
│   └── FIGURE_SPECIFICATION.md            # Formal figure registry and RQ mapping
├── assets/                                # Foundation project assets & signed plans
│   ├── Ahmed new plan.pdf                 # Ahmed Stage 2 research plan
│   ├── Faisal new plan.pdf                # Faisal Stage 2 ML plan
│   ├── Yazan new plan.pdf                 # Yazan Stage 2 dataset & readiness plan
│   ├── H2-PRISM_Proposal.pdf              # Foundation proposal
│   └── Team Contribution & Authorship.pdf # Intellectual property agreement
├── audit/                                 # Deterministic Python audit scripts (Yazan)
│   ├── 01_inventory_integrity.py          # Task Y1 audit engine
│   ├── 02_scenario_family_mapping.py      # Task Y2 scenario & family mapper
│   ├── 03_04_timing_labels_concurrency.py # Tasks Y3 & Y4 timing & label auditor
│   ├── 05_split_feasibility_leakage.py    # Task Y5 split feasibility & fold generator
│   ├── 07_readiness_decision.py           # Task Y7 readiness decision synthesizer
│   ├── 08_provisional_freeze.py           # Task Y8 provisional freeze packager
│   └── run_all_audits.py                  # One-click master audit orchestrator
├── configs/                               # Configuration contracts (Faisal & Yazan)
│   └── interface_contracts.yaml           # Schema specifications (Task F12)
├── data/                                  # Primary data directory
│   ├── raw/                               # Untouched raw H2-SimNet dataset (Zenodo 17871393: 998 MB)
│   └── sample/                            # Lightweight 4-class sample dataset (Tracked in Git: 10 MB)
├── scripts/                               # Automation & reporting scripts
│   ├── download_data.py                   # Automated dataset download & SHA256 integrity verifier
│   └── visualize.py                       # Master CLI visualizer & dashboard compiler
├── src/                                   # Stage 2 modular codebase (H2-PRISM core package)
│   └── h2prism/                           # Core Python package
│       ├── data/                          # Dataset loader API (instant scenario & fold access)
│       │   ├── loader.py                  # Direct loaders (load_scenario, load_fold, list_scenarios)
│       │   └── __main__.py                # CLI inspection (python3 -m h2prism.data)
│       └── visualization/                 # Academic publication plotting engine
│           ├── theme.py                   # IEEE/Nature high-contrast, colorblind-safe theme
│           ├── curves.py                  # Risk-coverage curves, reliability diagrams, ablations
│           ├── matrices.py                # 4-class confusion matrix, family distributions
│           ├── distinguishability.py      # D(x) separation density, indicator correlations
│           ├── telemetry.py               # Synchronized pressure & mass flow timeseries
│           └── dashboard.py               # Self-contained HTML report compiler
├── tests/                                 # Automated test suite (Pytest: 23 passing tests)
│   ├── test_data_loader.py                # Dataset loading & fold integrity tests
│   ├── test_dataset_audit.py              # Audit integrity & zero-leakage assertions
│   └── test_visualization.py              # Plotting, CLI, and dashboard compilation tests
├── pyproject.toml                         # Project configuration
└── requirements.txt                       # Python dependencies
```

---

## 4. Direct Dataset Access & Testing (Python API)

A unified data access layer is provided in [`src/h2prism/data/`](file:///Users/ya/Documents/codes/H2-PRISM/src/h2prism/data/) and documented in [`01_dataset_audit/HOW_TO_ACCESS_DATA.md`](file:///Users/ya/Documents/codes/H2-PRISM/01_dataset_audit/HOW_TO_ACCESS_DATA.md).

### 1. Where Does the Data Live?
- **Full Benchmark (`data/raw/H2-SimNet-Dataset/`)**: **998 MB**, 265 files (Zenodo Record 17871393). Ignored by Git.
- **Offline Quickstart Sample (`data/sample/`)**: **10 MB**, 4 complete scenarios covering all 4 target classes (`NORMAL`, `LEAK`, `COMPRESSOR_FAULT`, `COMPRESSOR_DELAY`). **Tracked in Git for immediate zero-download testing**.

### 2. Load Any Scenario in Python (2 Lines):
```python
from h2prism.data import load_scenario, load_fold, list_scenarios

# Load any scenario by short name, ID, or relative path
df = load_scenario("leakG4")  # 20,000 timesteps x 24 channels (PS1-PS12, MFS1-MFS4)
print(f"Loaded scenario: {df.shape}, PS1={df['PS1'].iloc[0]:.2f} MPa")

# Load training and testing splits for Outer Fold 1:
train_scenarios, test_scenarios = load_fold(fold_id=1)
```

### 3. Dataset Provisioning & Checksum Verification:
```bash
# Verify cryptographic SHA-256 integrity against raw_checksums.sha256
python3 scripts/download_data.py --verify

# Print dataset summary & file locations
python3 scripts/download_data.py --summary
```

---

## 5. Team Ownership & Research Triad (Stage 2)

```
+─────────────────────────────────────────────────────────────────────────────+
|                                H2-PRISM TEAM                                |
+───────────────────────┬─────────────────────────────┬───────────────────────+
|         AHMED         |           FAISAL            |         YAZAN         |
|     (Research Lead)   |          (AI Lead)          |    (Data & Readiness) |
+───────────────────────┼─────────────────────────────┼───────────────────────+
| • Scientific problem  | • Windowing & Features      | • Forensic Data Audit |
|   formulation (A1, A2)| • Baseline Models (F5)      | • Scenario & Family   |
| • Notation consistency| • Probability Calibration   |   Mapping (Y2)        |
| • Scientific Claim &  | • Distinguishability D(x)   | • Timing & Labels     |
|   Limit Register (A7) | • Selective Policy (F9)     | • Provisional Freeze  |
| • Scientific          | • Statistical Evaluation    | • Split Feasibility   |
|   Provenance (A10)    |   & Matched Coverage (F10)  | • Readiness Decision  |
| • Final Paper & Freeze| • Technical Integration     |   (READY_WITH_EXCL)   |
+───────────────────────┴─────────────────────────────┴───────────────────────+
```

---

## 6. Visualization Subpackage & Research Reporting Engine

A centralized, publication-grade visual reporting suite is implemented in [`src/h2prism/visualization/`](file:///Users/ya/Documents/codes/H2-PRISM/src/h2prism/visualization/) and documented in [`05_documentation/FIGURE_SPECIFICATION.md`](file:///Users/ya/Documents/codes/H2-PRISM/05_documentation/FIGURE_SPECIFICATION.md).

### Quick Usage:
```bash
# 1. Generate full demonstration figure suite & compile interactive HTML dashboard
python3 scripts/visualize.py --demo

# 2. View generated dashboard in default browser
python3 scripts/visualize.py --demo --open
```

### Generated Figures:
| Figure File | Specification | Research Question / Task |
| :--- | :--- | :--- |
| `fig1_family_distribution.png` | Grouped Family Count per Target Class | Justifies 3-fold topology CV (Task Y2/Y5) |
| `fig2_pipeline_telemetry.png` | SCADA Pressure & Flow Dynamics with Event Shading | Visualizes raw physical transients (Task Y3) |
| `fig3_confusion_matrix.png` | Normalized 4-Class Attribution Matrix | Primary Attribution Evaluation (Task F5) |
| `fig4_risk_coverage_curve.png` | Risk-Coverage Comparison (Method C vs C-D vs B) | **RQ1**: Distinguishability value beyond confidence |
| `fig5_calibration_reliability.png` | 10-bin Reliability Diagram (ECE & Brier score) | Calibrated Probabilistic Attribution (Task F6) |
| `fig6_distinguishability_separation.png`| Empirical $D(x) = q_{(1)} - q_{(2)}$ Density Separation | **RQ1**: Separation between correct vs ambiguous cases |

### Standalone HTML Dashboard:
The compiler in [`src/h2prism/visualization/dashboard.py`](file:///Users/ya/Documents/codes/H2-PRISM/src/h2prism/visualization/dashboard.py) embeds all 300 DPI figures as Base64 URIs into [`03_results/dashboard.html`](file:///Users/ya/Documents/codes/H2-PRISM/03_results/dashboard.html). The resulting dashboard is **100% self-contained**, responsive, and requires zero external servers, local dependencies, or active internet connection to inspect.

---

## 7. Verified Dataset Truth & Scientific Boundaries

1. **Fluid Composition**: The raw dataset simulates a **10% $\text{H}_2$ / 90% $\text{CH}_4$ blend** in Simscape Gas Fluids R2025a, **not** pure hydrogen.
2. **Sensor Channels**: Pressure transmitters `PS1` through `PS12` (MPa) and mass flow meters `MFS1` through `MFS4` (kg/s) are verified. **Zero localized temperature channels exist**.
3. **No Continuous Metric Localization Over-claiming**: Categorical valve restriction labels (`leak_G3` through `leak_G6`) represent discrete valve zones, not continuous metric coordinates.
4. **Primary Evaluation Strategy**: A **3-Fold Topology-Stratified Cross-Validation** (holding out Downstream, Center, or Upstream per fold) guarantees that all 4 target classes (`NORMAL`, `LEAK`, `COMPRESSOR_FAULT`, `COMPRESSOR_DELAY`) are present in both train and test with **zero scenario or topology leakage**.
5. **Phase-Event Confounding Safeguard**: Leaks were injected during steady state; compressor faults during initial ramp-up. Operational phase is **excluded as an input feature** to prevent trivial shortcut learning.

---

## 8. Historical Stage 1 Archive

All Stage 1 prototype implementations, presentation dashboard HTML, animations, and preliminary mock scripts have been retired from the active branch and are permanently preserved in Git history:
```bash
git checkout old-main
```
Or view online at [GitHub: `ayazashy/H2-PRISM/tree/old-main`](https://github.com/ayazashy/H2-PRISM/tree/old-main).
