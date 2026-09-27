# H2-PRISM Team Responsibilities & Authorship Record

Based on `Team Contribution & Authorship.pdf` (Dated 27/9/2026).

## Ahmed — Project Lead / Original Concept Owner (Plan 1)
- **Role**: Data Audit + Data Engineering + Physics Consistency + Propagation/Time-Delay
- **Assigned Modules**:
  - `src/data.py`: Data ingestion, validation, and standardized schema
  - `src/quality.py`: Sensor quality control and flag generation
  - `src/physics.py`: Real-gas line-pack mass balance residual
  - `src/propagation.py`: Time-delay cross-correlation and conditional localization
  - `AUDIT.md` & `results/data_audit.csv`: Forensic audit of H2-SimNet
  - `ASSUMPTIONS.md`: Physical & thermodynamic assumptions
  - `tests/test_physics.py`: Physical unit tests
- **Hard Exclusions**: No XGBoost, no deep learning, no dashboard/UI, no final fusion engine.

## Faisal — Engineering / AI Lead (Plan 2)
- **Role**: Feature Engineering + Transient Fingerprinting + XGBoost + Event Attribution + Evidence Fusion
- **Assigned Modules**:
  - `src/features.py`: Multi-group feature extraction (Raw, Temporal, Cross-sensor, Physics, Propagation)
  - `src/fingerprint.py`: Candidate transient fingerprint (Wavelet/CWT energy)
  - `src/model.py`: Multi-class attribution model (XGBoost) and probability calibration
  - `src/evidence.py`: Evidence fusion (Stacking vs Dempster-Shafer) and contradiction scoring
  - `notebooks/baseline_models.ipynb`: Comparison against Logistic Regression and Random Forest
  - `notebooks/feature_ablation.ipynb`: Ablation study of feature configurations A/B/C/D
  - `tests/test_model.py`: Attribution and fusion unit tests
- **Hard Exclusions**: No main data loader, no redesign of physics, no final pipeline integration.

## Yazan — Materials / Data Provenance & Integration Lead (Plan 3)
- **Role**: Materials Verification + Pipeline Orchestration + Observability + Decision Logic + Validation + Reproducibility
- **Assigned Modules**:
  - `src/detector.py`: Stage 1 lightweight candidate event trigger
  - `src/observability.py`: Independent 3-axis observability engine O = min(O_Q, O_S, O_E)
  - `src/decision.py`: Decision gating and UNKNOWN abstention logic
  - `src/pipeline.py`: Master pipeline orchestration connecting all modules
  - `run_scenario.py`: End-to-end scenario execution script
  - `MATERIALS.md` & `README_data.md`: Provenance tracking and data reproducibility
  - `results/materials_manifest.csv` & `results/dataset_truth_table.md`: Materials manifest
  - `notebooks/demonstration.ipynb`: 4 representative scenario demonstrations
  - `tests/test_observability.py` & `tests/test_pipeline.py`: Integration testing
