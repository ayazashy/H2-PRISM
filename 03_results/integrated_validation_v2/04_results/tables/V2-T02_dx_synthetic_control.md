### V2-T02_dx_synthetic_control — D(x) synthetic method check

SYNTHETIC two-class Gaussian design with known posterior; not evidence about H2-SimNet.

| separation | classifier | accuracy | auroc_conf | auroc_D | logloss_conf | logloss_conf_plus_D | delta_logloss | status |
|---|---|---|---|---|---|---|---|---|
| 0.5 | a_calibrated_bayes | 0.621 | 0.6077 | 0.5629 | 0.644 | 0.644 | 7.931e-05 | SYNTHETIC (method check only) |
| 0.5 | b_overconfident_T0.2 | 0.621 | 0.6077 | 0.5629 | 0.644 | 0.644 | 7.931e-05 | SYNTHETIC (method check only) |
| 0.5 | c_blind_to_feature_1 | 0.5965 | 0.543 | 0.5648 | 0.671 | 0.6647 | -0.006267 | SYNTHETIC (method check only) |
| 1 | a_calibrated_bayes | 0.772 | 0.7131 | 0.6766 | 0.4828 | 0.4834 | 0.0005782 | SYNTHETIC (method check only) |
| 1 | b_overconfident_T0.2 | 0.772 | 0.7131 | 0.6766 | 0.484 | 0.4845 | 0.0004822 | SYNTHETIC (method check only) |
| 1 | c_blind_to_feature_1 | 0.704 | 0.6482 | 0.6663 | 0.5925 | 0.569 | -0.02348 | SYNTHETIC (method check only) |
| 2 | a_calibrated_bayes | 0.9135 | 0.9009 | 0.8751 | 0.1829 | 0.1832 | 0.0002918 | SYNTHETIC (method check only) |
| 2 | b_overconfident_T0.2 | 0.9135 | 0.9009 | 0.8751 | 0.1944 | 0.1942 | -0.000179 | SYNTHETIC (method check only) |
| 2 | c_blind_to_feature_1 | 0.841 | 0.8026 | 0.8235 | 0.3415 | 0.2955 | -0.04594 | SYNTHETIC (method check only) |
