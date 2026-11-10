# Experiment Reproducibility Report (F13), pre-experiment portion

**Status:** software reproducibility VERIFIED. Experiment reproducibility (reruns of authorized real runs) is POST_EXPERIMENT. Detail: `06_audit_preparation/final_acceptance/FINAL_VALIDATION_EVIDENCE.md` §5.

| Property | Evidence |
| --- | --- |
| Deterministic feature table | real noise_added table `4d1310a6…` reproduced across independent preflight runs (Phases 8, 9, 10) |
| Deterministic results | synthetic aggregates byte-identical across: a direct run; an interrupted then resumed run; reversed manifest rows with shuffled fold rows |
| Platform independence | SHA-256 tie keys over UTF-8; CRLF-normalised code hash; LF-forced CSV/JSON/YAML in `06_audit_preparation/`; fixed float formatting |
| Traceability | `run_manifest.json`: git commit, config hash, effective config hash, code hash, input hashes (manifest, folds, mapping, register), feature-table hash, seed, status |
| Partial runs | status RUNNING with no aggregates until COMPLETED; resume only on an identical run_key; foreign output directories refused |
| Results provenance file (`03_results/RESULTS_PROVENANCE.csv`) | POST_EXPERIMENT; built by `tools/research_audit/build_provenance_index.py` from the run manifests |
