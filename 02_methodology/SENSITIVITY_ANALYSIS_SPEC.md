# Registered Sensitivity Analyses: Execution Paths (F-ROBUST / F11 / A15)

- **Status:** all 9 registered analyses (config `sensitivity_analyses`) have an execution path. Each was tested end to end on the synthetic fixture and structurally on real data (feature build plus preflight only; **no model fitting, no results**).
- **Implementation:** `primary_protocol.SENSITIVITY_OVERRIDES` and `apply_sensitivity`.
  - Each analysis changes **exactly one** config value, read off its registered name; this is tested.
  - The pinned config file and its hash `f788b6d8…` are untouched. The derived config hash is recorded as `effective_config_sha256`.
  - Outputs carry `analysis=<name>` and artifact class `SENSITIVITY_EXPERIMENT`. They are reported next to the primary result and never replace it.

| Name | Single deviation from primary | How to run | Synthetic E2E | Real structural dry run (2026-11-11) |
| --- | --- | --- | --- | --- |
| clean_realization | `dataset.realization_primary: clean` | `--execute-robustness` (scope ROBUSTNESS_EXPERIMENT) or `--execute-sensitivity --sensitivity clean_realization` | pass | 27/27 checks; 27,993 windows; table `3bc7e712…` |
| windows_60_60 | `windows.stride_s: 60` | `--execute-sensitivity --sensitivity windows_60_60` | pass | 27/27; 14,013 windows |
| pre_event_label_normal | `windows.pre_event_policy: label_normal` (pre-event rows of event runs → NORMAL; post-event rows stay excluded) | same pattern | pass, plus a relabelling test | 27/27; 31,929 windows (NORMAL 5,931; 1,893 post-event windows dropped) |
| offset_invariant_features | `features.statistics: [std, range, last_minus_first, slope, mean_abs_diff]` (80 features) | same | pass (80 features) | 27/27; 80 features |
| k_10 | `distinguishability.k: 10` | same | pass | 27/27 |
| k_50 | `distinguishability.k: 50` | same | pass | 27/27 |
| prior_correction | `distinguishability.prior_correction: true` | same | pass | 27/27 |
| extended_family_map | `dataset.family_column: family_extended_sensitivity` (32 families, nested in topology) | same | pass | 27/27 |
| policy_warning_only | specific-blocking flags = [LOW_SCENARIO_DIVERSITY] only | **embedded**: produced inside every run as `variant=warning_only`; a separate run is refused | pass (variant present) | n/a (no separate run) |

- The real dry runs predate the `inner_folds_match_runner` check, so they show 27 checks; the primary dry run now shows 28/28.
- **Execution gate:** `--execute-sensitivity` requires an authorization with `scope: SENSITIVITY_EXPERIMENT:<name>`, the config hash and all `governance_clearance` items (tested).
- **Tie-order sensitivity** (20 salts) is produced inside each run (`tie_sensitivity.csv`). It is separate from these 9.
- **Not changed by any analysis:** folds, classes, policy targets, safeguards (except the registered warning-only variant), seeds.
