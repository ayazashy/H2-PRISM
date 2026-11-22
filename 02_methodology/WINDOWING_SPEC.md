# Windowing Specification (F3)

- **Status:** SPECIFIED from `src/h2prism/windows.py`; IMPLEMENTED and TESTED (`tests/test_windows.py`).
- **Config:** `windows: {window_s: 60, stride_s: 30, min_samples: 60, label_mode: row_level, pre_event_policy: exclude}`. These are prespecified, not optimised.

## Generation (per run, never across runs)

- **Starts:** `t0 + stride·j` for j = 0..n−1, with `n = floor((span − window_s)/stride + 1e-9) + 1` and `span = t_last + median(dt) − t0`.
- **Rows:** a window covers the half-open interval [s, s + 60 s). Fewer than `min_samples` rows → excluded (`INSUFFICIENT_SAMPLES`).
- **window_id:** `{Scenario_ID}_w{index:04d}`; stable under regeneration. More than 9,999 windows per run raises an error.
- **Overlap:** 60/30 windows overlap by 50%, only within a run. Runs never span folds.

## Row-level labels (`map_rows_to_primary`)

- Exactly one fault indicator active → that class (LEAK / COMPRESSOR_FAULT / COMPRESSOR_DELAY).
- No indicator → NORMAL.
- More than one → COMPOUND_EVENT (excluded).
- A typed anomaly flag without a class → excluded.

## Window label and boundary status

| Situation | Label | boundary_status | Primary eligibility |
| --- | --- | --- | --- |
| Run without event rows | NORMAL | NO_EVENT | eligible |
| All rows in the event | event class | DURING_EVENT | eligible |
| Rows before onset, all NORMAL | NORMAL | PRE_EVENT | **excluded** (`pre_event_policy: exclude`) |
| Rows after the event ended (CompressorDelay after row 1000) | NORMAL | POST_EVENT | **excluded** |
| Mixed labels | MIXED | BOUNDARY_CROSSING | excluded |
| File-level labels only | run label | UNKNOWN_TIMING | not used (all eligible runs have row-level labels) |

- Every eligible window carries its run's class. The runner fails if not (`build_features`).
- **Sensitivity `pre_event_label_normal`:**
  - PRE_EVENT windows of event runs become eligible as NORMAL.
  - POST_EVENT windows stay excluded: the runner drops them, so exactly one choice differs.
  - Real data: +3,936 NORMAL windows; 1,893 post-event windows dropped.
- **Sensitivity `windows_60_60`:** stride 60 s (non-overlapping). Real data: 14,013 windows.

## Real-data counts (primary, 60/30)

27,993 eligible windows per realization: NORMAL 1,995, LEAK 21,921, FAULT 3,984, DELAY 93. DELAY windows all lie in the start-up segment (limitation 11).
