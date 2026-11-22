# H2-PRISM Web UI Architecture (`apps/web/`)

## Ownership & Boundaries
- **UI & Visualization**: `apps/web/src/`
- **Frozen Contract**: `contracts/schema/v1/*.schema.json` & `docs/interface-contract.md`
- **ETL Producer**: `tools/data_pipeline/build_web_bundle.py` -> `apps/web/public/data/`

## Views & State
1. **Workspace (`App.tsx`)**: Single-screen diagnostic replay combining `NetworkSchematic2D` (default) / lazy `NetworkScene3D` (WebGL with `document.hidden` pause + error boundary), `DecisionCard`, `SignalCharts` (ECharts pressure & mass flow with click-to-scrub and table fallback), and `PlaybackBar` (`requestAnimationFrame`).
2. **Benchmarks (`BenchmarksView.tsx`)**: Renders verified R2 primary LOTO results (`confusion_matrices_by_scope`, `risk_coverage_series`, `matched_coverage_06`, `three_outcome_by_class`), explicit `NOT_ESTIMABLE_UNDER_PRIMARY_PROTOCOL` disclosure, and gated feature availability cards.
3. **Methods & Limits (`MethodsView.tsx`)**: Plain-English glossary (`SPECIFIC`, `AMBIGUOUS`, `UNRESOLVED`, `D(x)`, `s_C`), R-18 attribution notes, and explicit prohibited claims.

## Fail-Closed Invariants
- Every fetched scenario and metrics file is hashed via `crypto.subtle.digest('SHA-256')` and checked against `catalog.json`.
- Any mismatch, non-monotonic timestamp, NaN/Infinity, or disallowed `location_prediction` throws `IntegrityError` and disables diagnostics.
- Per-run inference defaults to `EVIDENCE UNAVAILABLE` unless validated predictions are exported.
