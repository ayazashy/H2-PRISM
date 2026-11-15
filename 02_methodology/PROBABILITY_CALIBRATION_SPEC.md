# Probability Calibration Specification (Faisal F6)

Compare no calibration, classwise sigmoid (Platt) calibration, and classwise
isotonic calibration. Fit calibrators only to inner grouped OOF raw
probabilities from the current outer training split. Select the method with
the lowest multiclass log loss on those development OOF predictions; ties use
the fixed order `none`, `sigmoid`, `isotonic`. Refit the selected mapping on
the complete development OOF probability/label pairs, apply it to the outer
test probabilities, and renormalize the four classwise outputs to sum to one.

Report log loss, multiclass Brier score, 10-bin expected calibration error,
reliability-bin accuracy/confidence, and counts. Outer-test calibration
metrics are evaluation only and never select the method. Because the method is
selected on the same OOF rows used to fit each candidate calibrator, the
development comparison is not an independent calibration-validation estimate;
outer test remains untouched until evaluation.

Implementation: `src/h2prism/evaluation.py`. Results:
`03_results/CALIBRATION_RESULTS.csv` and
`03_results/figures/fig5_calibration_reliability_stage2.png`.
