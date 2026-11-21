# H2-PRISM final research study

## Introduction and research gap

A network sensor departure can support an operational review while leaving several physical explanations compatible. H2-PRISM studies when an evidence contract supports a specific diagnosis, which rival hypotheses survive, and whether conditional location evidence is available. The method distinguishes classifier confidence from consistency with qualified physical predictions.

## Objective and hypotheses

The exploratory objective is to test whether source-traced interventions produce different sensor trajectories under matched conditions. The confirmatory objective is to compare an evidence-guided decision policy and calibrated confidence-based abstention at matched specific-diagnosis coverage on eligible independent families. The first objective uses the Center simulation family. The second requires qualified uncertainty, physical labels, independent generating families, and a frozen development/calibration/test protocol.

## Methodology

The original Center model was reproduced and audited at 0.8, 0.4 and 0.2 s. The controlled experiments use fixed-step ode14x at 0.2 s and 13 native pressure and signed flow channels. Captures include six signed external flows and eight storage histories. The outlet twins start at the source nominal 0.0010 m^2; an engineered case commands 0.0011 m^2 at 1,000 s. The gas, original boundary controls, initial-state policy, clock and sensing are matched within each twin pair. Numeric MAT outputs preserve the original timestamps. Results carry parent, approved model, execution, capture and preflight hashes. Each rival is compared with its own control to account for common differences introduced by its variable-restriction realization.

The cross-case signature calculation divides opening-minus-control by each control channel's pre-event RMS, then compares those dimensionless differences on exact shared saved times. RMS distance and cosine describe relative sensitivity to sensor choice and observation window. A zero response has no defined cosine. Per-channel results retain native units and exact times. These calculations provide exploratory support rather than a validated decision threshold.

The current consistency engine reports FEASIBLE only with verified evidence, EXCLUDED only with a valid certificate, and INDETERMINATE when required inputs are unavailable. A surviving indeterminate hypothesis blocks a specific diagnosis. Conditional localization follows the existing L0/L1/L2 rules. No empirical reporting threshold is promoted to a measurement-error or model-discrepancy bound.

## Results from the existing source and SID 213 captures

The audited source reproduction matches the archived solver trajectory to approximately 2.38e-7 MPa and 2.53e-7 kg/s. At the shared 28 s knot the clean release differs from the archived CSV by +0.089703 MPa for PS1 and +0.053028 kg/s for MFS3. Its exact generating transformation remains unverified. The event-aware numerical conservation residual at the original 0.2 s NORMAL resolution is about -1.304 kg. See the included Phase 11 convergence figure and the preserved Phase 10 audit for scope and details.

The accepted SID 213 pair recorded the 0.0010 to 0.0011 m^2 area change at 1,000.0 s. Outlet flow increased by 0.691269 kg/s at onset, peaked at 0.694549 kg/s, and withdrew an additional 13,064.834 kg through the atmospheric branch. Peak PS1 response was -0.000604902 MPa. The paired event-aware residuals were -0.939 and -1.306 kg. Before the event the maximum pair offsets were 1.80073e-4 MPa and 9.37436e-5 kg/s. All quantities are recorded in the Phase 12 paired result and manifest.

## Discussion and limitations

The archive eligibility audit checks actual catalog classes, conservative relationships and historical exposure. It finds 57 historical candidates, 11 conservative dependency components, 39 legacy fold/group crossing records under conservative grouping, and zero qualified confirmatory test or calibration families. The legacy crossings are warnings about possible dependence. No historical generating provenance justifies treating those 11 components as independent evaluation units. Accuracy, selective risk, matched-coverage incremental value, calibration and confidence intervals therefore remain undefined.

Phase 11 measures solver refinement effects; it supplies no certified trajectory enclosure. Pressure and flow calibration, timing error, parameter tolerances, a bounded source-compatible model discrepancy over an operating domain, and effective gas composition remain unqualified. The numerical residuals and repeatable simulation clocks provide different evidence from physical sensor uncertainty. The outlet configurations establish designed ground truth. Independent location evidence is conditional on qualified model predictions and competing location tests.

## Contribution and conclusion

The contribution is a reproducible link from source-model identity and actual physical actuation to verified numerical trajectories and an explicit distinction between descriptive sensor separation and formal diagnostic evidence. The existing exact joint set-membership engine supplies the formal decision semantics. The study supports publication as exploratory model-based research on diagnostic justification and abstention. Industrial readiness, hydrogen fidelity, and comparative diagnostic superiority remain unverified.

## Future work

Build a source-compatible bounded prediction model with an independently justified operating envelope, parameter tolerances, numerical error enclosure and measurement-error model. The traced SID 55 pressure source provides a native operational rival mechanism; qualify a matched late command and its operating-domain limits before running it. The archived Upstream and Downstream alternatives change physical wiring, so a separately traced boundary-only profile is still required for the unchanged Center topology. Any additional variants retain their shared source-family ancestry until independently generated families are documented.

## Reproducibility

The v7 numeric captures and frozen Phase 12 manifest remain in place. To regenerate analysis using the already completed captures, run from the repository root with a fresh output directory.

    $env:PYTHONPATH = 'src'
    .\.venv\Scripts\python.exe -m h2prism.final_research report 'C:/Users/ahmd1/Documents/Codex/2026-11-16/before-starting-the-new-h-prism/work/phase12_sdi_retry_01' --matrix 'C:/Users/ahmd1/Documents/Codex/2026-11-16/before-starting-the-new-h-prism/work/final_research_matrix' --reference 'C:/Users/ahmd1/Documents/Codex/2026-11-16/before-starting-the-new-h-prism/work/phase11_cases/step_0.2' --output $newReportDir

The MATLAB runner compiles both cases of each rival, compares the saved model/configuration records, checks both approval receipts, and uses the numeric export path. In a separate reproducibility run, first use the Python prepare action with a new matrix root. Execute the matrix in the authorized MATLAB Command Window.

    addpath('C:/Users/ahmd1/Documents/H2-PRISM/tools/simulation');
    rehash;
    h2prism_run_final_outlet_matrix(newMatrixRoot);

Existing complete cases are never executed again by this runner. A case with partial output requires inspection and a separate fresh location. The report checks complete outputs and hashes before including a new pair in the cross-scenario comparison.
