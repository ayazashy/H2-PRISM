# Reporting Automation Specification (A13)

- **Status:** IMPLEMENTED and TESTED (`tests/test_reporting_outputs.py`, 8 tests, including an integration test on real runner output schemas from a synthetic run).
- **No research figure or table exists.**

| Item | Specification |
| --- | --- |
| Tools | `tools/reporting/build_research_figures.py`, `build_research_tables.py`, shared `_common.py`; read-only consumers, never recompute metrics |
| Config | `configs/reporting_figures.yaml`; inputs are the PRIMARY runner outputs under `03_results/primary_protocol/PRIMARY/` |
| Row selection | `filter:` (e.g. `variant: primary`, `mode: rank_matched`); an empty selection raises an error |
| Routing | `artifact_class` SYNTHETIC_TEST or PREFLIGHT_ONLY → `illustrative/` (watermark); `data_status` FIXTURE/ILLUSTRATIVE → `illustrative/`; `evidence_status` VALIDATED/FROZEN → `final/`; otherwise `preliminary/` (watermark) |
| Safeguards | missing input → `NOT_BUILT_MISSING_EVIDENCE` with a clear error; selective risk without coverage is rejected; deterministic PNG/SVG metadata |
| Provenance | `FIGURE_BUILD_MANIFEST.csv` / `TABLE_BUILD_MANIFEST.csv`: output and input SHA-256, config hash, source experiment, evidence status, caption |
| Current state | Fig. 1 and T1–T3 built from verified structural data (`03_results/figures|tables/dataset_design/`); Figs. 2–6 / T4–T8: `05_documentation/FIGURE_BUILD_MANIFEST.csv` records NOT_BUILT_MISSING_EVIDENCE (no authorized run) |
| Figure kinds | six multi-panel scientific kinds + two legacy single-panel kinds (`FIGURE_SPECIFICATION.md` selection register); style from `h2prism.visualization.theme` via `tools/reporting/_style.py`; PNG/PDF/SVG |
