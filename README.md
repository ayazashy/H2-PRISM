# H2-PRISM: Physics-Anchored, Observability-Gated Framework for Event Attribution in Hydrogen Pipelines

> **Document Status**: Functional Prototype & Engineering Workspace  
> **Evaluation Protocol Focus**: False Physical Attribution Rate (FPAR), Leak Recall, and Decision Coverage under Condition-Based Splitting.

---

## 1. Project Concept & Core Philosophy

Abnormal pressure or flow readings in a hydrogen transmission pipeline do not automatically indicate a leak. Operational maneuvers (valve throttling, compressor cycles), dynamic line-pack inventory redistribution, sensor drift/biases, and packet dropouts produce transient signatures that mimic genuine loss of containment.

**H2-PRISM** reframes pipeline monitoring from generic anomaly detection into **event attribution under structural ambiguity**:
1. **Treats Sensor and Operational Transients as First-Class Competing Hypotheses**: Never collapses abnormalities into a single scalar anomaly score.
2. **Physics-Anchored Consistency**: Leverages real-gas hydrogen equation of state (EOS), line-pack-corrected mass conservation, and acoustic cross-station propagation delay.
3. **Independent Observability Gating**: Computes an objective observability score $O = \min(O_Q, O_S, O_E)$ strictly from data quality and instrumentation topology—independent of classifier confidence.
4. **Honest Abstention (UNKNOWN)**: Withholds classification and issues an explicit diagnostic reason whenever data quality, sensor topology, or propagation evidence is structurally incapable of distinguishing hypotheses.

---

## 2. Repository & Workspace Structure

```
H2-PRISM/
├── .vscode/                               # Development workspace configuration
│   ├── settings.json                      # Python, pytest, formatting settings
│   └── extensions.json                    # Recommended VS Code extensions
├── assets/                                # Foundation project assets & signed plans
│   ├── Ahmed Plan.pdf                     # Person 1 master specification
│   ├── Faisal Plan.pdf                    # Person 2 master specification
│   ├── Yazan Plan.pdf                     # Person 3 master specification
│   ├── _Materials & Data Provenance Lead.pdf # Materials lead mandate
│   ├── H2-PRISM_Proposal.pdf             # Engineering & scientific proposal
│   └── Team Contribution & Authorship.pdf # Intellectual property & authorship agreement
├── data/                                  # Data directory (Raw untouched vs Derived)
│   ├── raw/H2-SimNet/                     # Primary official dataset (Zenodo 17871393)
│   ├── selected/                          # The 6 representative evaluation scenarios
│   ├── processed/                         # Standardized/synchronized scenario copies
│   └── synthetic/                         # Controlled synthetic sensor faults (strictly isolated)
├── docs/                                  # Architectural documentation
│   ├── ARCHITECTURE.md                    # Data flow and component block diagrams
│   └── TEAM_ROLES.md                      # Authorship and responsibility division
├── notebooks/                             # Exploratory and experimental notebooks
│   ├── baseline_models.ipynb              # Baseline evaluation (LR, RF, XGBoost)
│   ├── feature_ablation.ipynb             # Feature ablation study (Configs A-D)
│   └── demonstration.ipynb                # 4-scenario end-to-end demonstration
├── results/                               # Reproducibility manifests and generated outputs
│   ├── figures/                           # Exported evaluation plots
│   ├── data_audit.csv                     # Automated forensic audit metrics
│   ├── dataset_truth_table.md             # Verified vs assumed properties table
│   └── materials_manifest.csv             # Machine-readable data manifest
├── scripts/                               # Inspection and utility scripts
│   └── data_inspection/
│       └── audit_dataset.py               # Reproducible forensic inspection script
├── src/                                   # Core modular codebase
│   ├── __init__.py                        # Package root and public exports
│   ├── schema.py                          # Shared dataclasses and cross-module contracts
│   ├── data.py                            # Data loader & mock scenario generator (Person 1)
│   ├── quality.py                         # Quality control & flag generator (Person 1)
│   ├── physics.py                         # Line-pack corrected mass balance engine (Person 1)
│   ├── propagation.py                     # Cross-correlation delay & localization (Person 1)
│   ├── detector.py                        # Stage 1 lightweight candidate detector (Person 3)
│   ├── features.py                        # Multi-group feature extraction (Person 2)
│   ├── fingerprint.py                     # Candidate transient wavelet/CWT layer (Person 2)
│   ├── model.py                           # XGBoost attribution & calibration (Person 2)
│   ├── evidence.py                        # Contradiction scoring & fusion (Person 2)
│   ├── observability.py                   # Independent 3-axis observability engine (Person 3)
│   ├── decision.py                        # Gating engine & UNKNOWN abstention (Person 3)
│   └── pipeline.py                        # Master pipeline orchestrator (Person 3)
├── tests/                                 # Unit & integration test suite
│   ├── __init__.py
│   ├── test_physics.py                    # Physics engine & residual unit tests (Person 1)
│   ├── test_model.py                      # Classifier & feature tests (Person 2)
│   ├── test_observability.py              # Observability gating tests (Person 3)
│   └── test_pipeline.py                   # End-to-end integration tests (Person 3)
├── run_scenario.py                        # Unified CLI scenario execution tool
├── AUDIT.md                               # H2-SimNet dataset forensic audit report
├── ASSUMPTIONS.md                         # Scientific & thermodynamic assumptions log
├── MATERIALS.md                           # Materials inventory & provenance record
├── README_data.md                         # Data acquisition & reproducibility guide
├── requirements.txt                       # Project dependencies
└── .gitignore                             # Git ignore rules
```

---

## 3. Specialized Member Plans & File Ownership

### 3.1 Ahmed — Project Lead / Plan 1
* **Scope**: Data Audit + Data Engineering + Physics Consistency + Propagation / Time-Delay.
* **Daily Workflow**:
  - **Day 1**: Inspect repo, execute forensic dataset audit (`AUDIT.md`), select 6 complete representative scenarios, build data loader (`src/data.py`), implement quality control flags (`src/quality.py`).
  - **Day 2**: Implement real-gas line-pack mass balance residual $z_{MB}$ (`src/physics.py`), implement cross-correlation acoustic propagation delay $\Delta t_{12}$ and conditional localization interval $\hat{x} \pm \delta$ (`src/propagation.py`), write unit tests (`tests/test_physics.py`).
  - **Day 3**: Clean interfaces, document all physical assumptions in `ASSUMPTIONS.md`, and complete dataset truth table.
* **Corresponding Files & Exact Roles**:
  - [`src/data.py`](file:///c:/Users/f/Documents/cmds/New%20folder/!inprog/H2-PRISM/src/data.py): Ingests CSV/Parquet scenarios, standardizes columns, and preserves metadata without altering variables.
  - [`src/quality.py`](file:///c:/Users/f/Documents/cmds/New%20folder/!inprog/H2-PRISM/src/quality.py): Computes non-destructive quality flags (`GOOD`, `MISSING`, `GAP`, `STUCK`, `INVALID`) and data adequacy $O_Q$.
  - [`src/physics.py`](file:///c:/Users/f/Documents/cmds/New%20folder/!inprog/H2-PRISM/src/physics.py): Evaluates real-gas hydrogen density $\rho(P, T)$, line-pack mass accumulation $\Delta \hat{M}_{line}$, and normalized residual $z_{MB} = \hat{m}_{loss} / \sigma_{MB}$.
  - [`src/propagation.py`](file:///c:/Users/f/Documents/cmds/New%20folder/!inprog/H2-PRISM/src/propagation.py): Estimates cross-station lag $\Delta t_{12} = \arg\max_\tau C_{12}(\tau)$ and outputs localization interval bounded by sampling resolution floor $\delta = a \cdot \Delta t / 2$.
  - [`AUDIT.md`](file:///c:/Users/f/Documents/cmds/New%20folder/!inprog/H2-PRISM/AUDIT.md): Detailed forensic audit of Zenodo record 17871393.
  - [`ASSUMPTIONS.md`](file:///c:/Users/f/Documents/cmds/New%20folder/!inprog/H2-PRISM/ASSUMPTIONS.md): Rigorous ledger of thermodynamic, geometric, and sampling assumptions.
  - [`tests/test_physics.py`](file:///c:/Users/f/Documents/cmds/New%20folder/!inprog/H2-PRISM/tests/test_physics.py): Sanity unit tests verifying sign conventions, steady state zero imbalance, and synthetic leak responses.
* **Hard Exclusions**: Do NOT build XGBoost, deep learning (CNN/GRU/TCN), the final fusion engine, dashboard UI, or fabricate missing sensor measurements.

---

### 3.2 Faisal — Engineering / AI Lead (Plan 2)
* **Scope**: Feature Engineering + Transient Fingerprinting + XGBoost + Event Attribution + Evidence Fusion.
* **Daily Workflow**:
  - **Day 1**: Inspect Person 1's interfaces, construct multi-group feature extraction (`src/features.py`), establish leakage-safe scenario-level splits, build sanity baselines (Logistic Regression, Random Forest, XGBoost).
  - **Day 2**: Implement candidate CWT/wavelet transient fingerprinting (`src/fingerprint.py`), run ablation against non-wavelet features, train multi-class XGBoost classifier with probability calibration (`src/model.py`).
  - **Day 3**: Build contradiction-aware evidence engine and compare fusion mechanisms (Calibrated Stacking vs. Dempster-Shafer) (`src/evidence.py`), evaluate FPAR and coverage curves.
* **Corresponding Files & Exact Roles**:
  - [`src/features.py`](file:///c:/Users/f/Documents/cmds/New%20folder/!inprog/H2-PRISM/src/features.py): Extracts Group A (raw), Group B (temporal rates/derivatives), Group C (cross-station coupling), and incorporates Group D (physics) and Group E (propagation) from Person 1.
  - [`src/fingerprint.py`](file:///c:/Users/f/Documents/cmds/New%20folder/!inprog/H2-PRISM/src/fingerprint.py): Candidate wavelet/CWT spectral energy layer; subject to strict ablation testing (A6/B4 vs B3).
  - [`src/model.py`](file:///c:/Users/f/Documents/cmds/New%20folder/!inprog/H2-PRISM/src/model.py): Implements multi-class attribution classifier and post-hoc probability calibration (Platt/Isotonic).
  - [`src/evidence.py`](file:///c:/Users/f/Documents/cmds/New%20folder/!inprog/H2-PRISM/src/evidence.py): Computes contradiction metric (disagreement between ML leak likelihood and physical mass balance) and fuses multi-stream evidence.
  - [`notebooks/baseline_models.ipynb`](file:///c:/Users/f/Documents/cmds/New%20folder/!inprog/H2-PRISM/notebooks/baseline_models.ipynb): Benchmark experiments comparing simple linear/tree baselines against XGBoost.
  - [`notebooks/feature_ablation.ipynb`](file:///c:/Users/f/Documents/cmds/New%20folder/!inprog/H2-PRISM/notebooks/feature_ablation.ipynb): Controlled ablation study across feature configurations A, B, C, and D.
  - [`tests/test_model.py`](file:///c:/Users/f/Documents/cmds/New%20folder/!inprog/H2-PRISM/tests/test_model.py): Unit tests verifying feature vector dimensions, heuristic fallback, and probability calibration.
* **Hard Exclusions**: Do NOT build the data loader, redesign physics equations, build final pipeline orchestration, or use random row-level train/test splits.

---

### 3.3 Yazan — Materials / Data Provenance & Integration Lead (Plan 3)
* **Scope**: Materials Verification + Pipeline Orchestration + Observability + Decision Logic + Validation + Reproducibility.
* **Daily Workflow**:
  - **Day 1**: Execute dataset acquisition and forensic verification (`MATERIALS.md`, `README_data.md`), establish shared dataclass contracts (`src/schema.py`), implement Stage 1 lightweight candidate event trigger (`src/detector.py`).
  - **Day 2**: Connect Person 1 and Person 2 modules into master pipeline (`src/pipeline.py`, `run_scenario.py`), implement independent 3-axis observability engine (`src/observability.py`), implement gated UNKNOWN abstention logic (`src/decision.py`).
  - **Day 3**: Architecture freeze, evaluate on held-out operating regimes, generate four representative demonstration walkthroughs (`notebooks/demonstration.ipynb`), package full reproducibility suite.
* **Corresponding Files & Exact Roles**:
  - [`src/schema.py`](file:///c:/Users/f/Documents/cmds/New%20folder/!inprog/H2-PRISM/src/schema.py): Master dataclass contracts (`EventCandidate`, `PhysicsEvidence`, `PropagationEvidence`, `MLResult`, `ObservabilityResult`, `Decision`, `StructuredEventReport`).
  - [`src/detector.py`](file:///c:/Users/f/Documents/cmds/New%20folder/!inprog/H2-PRISM/src/detector.py): Stage 1 online trigger that scans rolling mass imbalance and $dP/dt$, extracting isolated pre/post event analysis windows.
  - [`src/observability.py`](file:///c:/Users/f/Documents/cmds/New%20folder/!inprog/H2-PRISM/src/observability.py): Independent 3-axis observability calculation $O = \min(O_Q, O_S, O_E)$, quantifying data quality, structural acoustic discriminability, and evidential conflict.
  - [`src/decision.py`](file:///c:/Users/f/Documents/cmds/New%20folder/!inprog/H2-PRISM/src/decision.py): Enforces gating thresholds on confidence, margin, and observability; returns `UNKNOWN` with explicit diagnostics when evidence is weak.
  - [`src/pipeline.py`](file:///c:/Users/f/Documents/cmds/New%20folder/!inprog/H2-PRISM/src/pipeline.py): Orchestrates end-to-end execution across all stages and produces SCADA-compatible event reports.
  - [`run_scenario.py`](file:///c:/Users/f/Documents/cmds/New%20folder/!inprog/H2-PRISM/run_scenario.py): Command-line scenario execution entrypoint.
  - [`MATERIALS.md`](file:///c:/Users/f/Documents/cmds/New%20folder/!inprog/H2-PRISM/MATERIALS.md): Forensic materials record, dataset claims, verified vs unverified items, and provenance statement.
  - [`README_data.md`](file:///c:/Users/f/Documents/cmds/New%20folder/!inprog/H2-PRISM/README_data.md): Step-by-step instructions for acquiring and verifying H2-SimNet data.
  - [`results/materials_manifest.csv`](file:///c:/Users/f/Documents/cmds/New%20folder/!inprog/H2-PRISM/results/materials_manifest.csv): Machine-readable record of all scenario files and roles.
  - [`notebooks/demonstration.ipynb`](file:///c:/Users/f/Documents/cmds/New%20folder/!inprog/H2-PRISM/notebooks/demonstration.ipynb): Four end-to-end demonstrations (Normal, Leak, Operational Transient, Ambiguous / UNKNOWN).
  - [`tests/test_observability.py`](file:///c:/Users/f/Documents/cmds/New%20folder/!inprog/H2-PRISM/tests/test_observability.py) & [`tests/test_pipeline.py`](file:///c:/Users/f/Documents/cmds/New%20folder/!inprog/H2-PRISM/tests/test_pipeline.py): Pipeline validation tests.
* **Hard Exclusions**: Do NOT modify physics equations, build separate ML models, fabricate metrics, or claim real-world field validation.

---

## 4. Cross-Module Data Flow & Contracts

```
[Raw Scenario Data]
         │
         ▼
src/quality.py (Ahmed) ──────────► Data Quality Flags & O_Q
         │
         ▼
src/detector.py (Yazan) ─────────► EventCandidate Window
         │
    ┌────┴───────────────────────────┐
    ▼                                ▼
src/physics.py (Ahmed)     src/propagation.py (Ahmed)
    │ PhysicsEvidence                │ PropagationEvidence
    └────┬───────────────────────────┘
         ├───────────────────────────┐
         ▼                           ▼
src/features.py (Faisal)   src/fingerprint.py (Faisal)
         │ Multi-Group Feature Vector
         ▼
src/model.py (Faisal) ────────────► MLResult (Likelihoods)
         │
         ▼
src/evidence.py (Faisal) ─────────► EvidenceResult & Contradiction Score
         │
         ▼
src/observability.py (Yazan) ────► ObservabilityResult O = min(O_Q, O_S, O_E)
         │
         ▼
src/decision.py (Yazan) ─────────► Decision (Attribution or UNKNOWN)
         │
         ▼
src/pipeline.py (Yazan) ─────────► StructuredEventReport
```

---

## 5. Non-Negotiable Scientific Guidelines

1. **No Data Fabrication**: Never invent missing sensor channels (e.g., temperature) or undocumented physical geometry.
2. **Strict Scenario Splitting**: Never use random row-level train/test splits. Always split by scenario/run to prevent temporal data leakage.
3. **Condition-Based Generalization**: At least one complete operational regime must be held out entirely from training.
4. **Joint Evaluation Metric Reporting**: False Physical Attribution Rate (FPAR) must **always** be reported jointly with leak recall and decision coverage. Never report accuracy or FPAR in isolation.
5. **Ablation-Driven Architecture**: The candidate wavelet/CWT transient fingerprinting layer must earn its place via measurable FPAR reduction in ablation testing; otherwise, it must be removed.
6. **Simulation-Only Ground Truth**: All validation is strictly simulation-based (H2-SimNet). Never describe simulation results as field-validated data.

---

## 6. Quickstart & Demonstration

### Installation
```bash
pip install -r requirements.txt
```

### Running Mock Scenario Demonstrations
Execute the four representative demonstration scenarios:
```bash
# 1. Genuine Leak with Acoustic Propagation Delay & Mass Balance Residual
python run_scenario.py --mock leak

# 2. Operational Transient Explained by Line-Pack Accumulation
python run_scenario.py --mock operational_transient

# 3. Sensor Fault (Single-Channel Pressure Deviation without Flow Loss)
python run_scenario.py --mock sensor_fault

# 4. Ambiguous Scenario (Low Observability -> UNKNOWN Abstention)
python run_scenario.py --mock ambiguous
```

### Running Test Suite
```bash
pytest tests/
```
