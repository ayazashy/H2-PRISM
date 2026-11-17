# Distinguishability v2: evidence baseline (verified 2026-11-13)

- **Branch:** `audit/preparation-integration`.
- **Working tree:** clean at start.
- **HEAD:** `d26060a`.

Every hash list was re-verified before any recorded result was used.

| Artifact | Location | Verification |
| --- | --- | --- |
| R2 primary run `a10530f1fcf2` (protocol 1.1) | `03_results/primary_protocol/PRIMARY/` | 68/68 files match `logs/PRIMARY_a10530f1fcf2_OUTPUT_HASHES.sha256` |
| Development arms A–G2 | `03_results/ablation_runs/<arm>/` (commit `81baba4`) | 9/9 files each, `logs/<arm>_*_OUTPUT_HASHES.sha256` |
| Arm H (position-matched) | `03_results/ablation_runs/H_POSITION_MATCHED/` (commit `407aa0d`) | 9/9 |
| Arm H root-cause diagnostics | `03_results/diagnostics/arm_h_failures/` (commit `d26060a`) | 19/19, `OUTPUT_HASHES.sha256` |
| RC1 | `release_candidate/P2_0_RC1.yaml` | sha256 `0566843e…` equals its pin |
| Manifest v0.3 | `CANDIDATE_MANIFEST_V03.csv` (pinned in RC1) | RC1 pin |
| Position map v0.1 | `CANDIDATE_SENSOR_POSITION_MAP_V01.csv` | sha256 `7b3b8cf1…` equals its pin |
| Independence groups | `src/h2prism/independence.py`; manifest column `independence_group` | 51 runs = 13 groups |
| Root-cause report | `05_documentation/ARM_H_ROOT_CAUSE_REPORT.md` | — |
| RC1 resolution | `05_documentation/PROTOCOL_2_0_RC1_RESOLUTION.md` | — |

**Facts carried into this phase (exploratory development evidence only):**

- **NORMAL→LEAK:** 3,930 window-fold instances, 3,151 of them confident, from **1** independence group.
- **LEAK→NORMAL:** 866 instances (101 confident) from 3 groups.
- **Risk at the 0.6 development point (H):**

  | Score | Group-balanced risk |
  | --- | --- |
  | s_C | 0.109 |
  | s_C−D | 0.109 |
  | Confidence | 0.099 |

Nothing in this phase modifies these artifacts. Protocol 2.0 is not active, and Yazan's and Faisal's approvals are not recorded.
