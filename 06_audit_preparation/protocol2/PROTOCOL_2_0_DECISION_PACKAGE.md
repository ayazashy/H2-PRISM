# Protocol 2.0: minimum decision package to freeze

- **Status (2026-11-12):** CANDIDATE, NOT APPROVED.
- **Already verified:**
  - candidate tests pass (14 candidate, 10 evidence-margin counterexamples, 5 develop-mode);
  - manifest v0.3 checks pass;
  - R2 D(x)/flags reproduced 27,993/27,993 with protocol 1.1 defaults;
  - all 8 registered ablation arms pass the real preflight (`ABLATION_MATRIX.md`).
- **The project lead's publication approval (2026-11-12) covers DESCRIPTIVE publication of 11 R2 artifacts only.** It is not authorization for new runs, and it is not Yazan's or Faisal's scientific acceptance.

## Decisions that block freezing (owner, exact question)

| # | Owner | Decision | Options | Evidence |
| --- | --- | --- | --- | --- |
| D1 | Yazan | R-18 topology attribution of 36 event runs | A keep release attribution / B adopt manifest v0.3 (`topology_source_model`) / C ask dataset authors first | `01_dataset_audit/YAZAN_TOPOLOGY_DECISION_PACKAGE.md`; `CANDIDATE_MANIFEST_V03_CHECKS.json` |
| D2 | Yazan | Are PS1–PS10 and MFS1–MFS3 the **same physical sensors** in the three models? (e.g. PS5 averages about 0.10 in the down model and about 0.69 in the others) | same position (common-sensor set valid) / different positions (common-sensor set must be redefined) | `03_results/diagnostics/forensics/padded_channel_evidence.csv`; model `.slx` files |
| D3 | Faisal | Accept or reject each component: P2-B common sensors (F3), P2-C independence-group support (F7/F11), P2-D evidence-conflict policy (F9), P2-E development-only target rule (F10), P2-F fail-closed meta-model (F10), E_h evidence margin (F7, only if arm F meets its criterion) | accept / reject / revise, per component | `02_methodology/PROSPECTIVE_VALIDATION_PROTOCOL_PROPOSAL.md`; `src/h2prism/evidence_margin.py`; tests |
| D4 | Faisal | Inference units and contrasts for protocol 2.0: independence groups as bootstrap units; one registered contrast | accept / revise | proposal Section 3 |
| D5 | Project lead | Authorize development-only ablation arms (each `DEVELOPMENT_EXPERIMENT:<arm>`) | per arm | `ABLATION_MATRIX.csv` |
| D6 | Yazan / authors | Commission independent confirmation simulations | yes / no | `02_methodology/INDEPENDENT_CONFIRMATION_DATA_SPEC.md` |

**Order of freezing:**

1. D1, D2 and D3 decide which components exist.
2. D5's development results inform the D3 component decisions, but never choose them by held-out performance.
3. Freeze the config.
4. D6 provides independent data.
5. One confirmatory run on that data, under a new authorization.

## Development-stage evidence for the decisions (2026-11-13; exploratory)

`05_documentation/PROTOCOL_2_ABLATION_REPORT.md`:

- **D1:** the v0.3 attribution raises development group-balanced accuracy from 0.47 to 0.88.
- **D2:** is now **blocking**, because the down model stays out of support even on the 13 shared sensors.
- **D3:** recommendations are in report section 4. E_h is not recommended for inclusion now.
