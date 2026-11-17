# TAB_02 — Mass accounting across fixed integration steps

Mass in kg; residual is storage change minus signed integrated boundary flow.

| step_s | method | initial_storage_kg | final_storage_kg | storage_change_kg | integrated_net_kg | residual_kg | absolute_residual_fraction_of_storage_change | absolute_residual_fraction_of_gross |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.8 | trapezoid | 991686 | 1.00011e+06 | 8421.39 | 8877.35 | -455.953 | 0.0541423 | 0.000108238 |
| 0.8 | simpson | 991686 | 1.00011e+06 | 8421.39 | 8728.74 | -307.343 | 0.0364955 | 7.29596e-05 |
| 0.8 | step_left_trapezoid | 991686 | 1.00011e+06 | 8421.39 | 8410.76 | 10.6303 | 0.00126229 | 2.5235e-06 |
| 0.8 | step_split_simpson | 991686 | 1.00011e+06 | 8421.39 | 8417.67 | 3.72528 | 0.000442359 | 8.84338e-07 |
| 0.4 | trapezoid | 991686 | 1.00011e+06 | 8421.38 | 8655.6 | -234.217 | 0.0278122 | 5.5603e-05 |
| 0.4 | simpson | 991686 | 1.00011e+06 | 8421.38 | 8736.61 | -315.235 | 0.0374327 | 7.48367e-05 |
| 0.4 | step_left_trapezoid | 991686 | 1.00011e+06 | 8421.38 | 8422.31 | -0.927028 | 0.00011008 | 2.20076e-07 |
| 0.4 | step_split_simpson | 991686 | 1.00011e+06 | 8421.38 | 8424.66 | -3.28575 | 0.000390168 | 7.80036e-07 |
| 0.2 | trapezoid | 991686 | 1.00009e+06 | 8406.32 | 8521.07 | -114.749 | 0.0136503 | 2.72419e-05 |
| 0.2 | simpson | 991686 | 1.00009e+06 | 8406.32 | 8563.31 | -156.992 | 0.0186755 | 3.72707e-05 |
| 0.2 | step_left_trapezoid | 991686 | 1.00009e+06 | 8406.32 | 8404.47 | 1.84953 | 0.000220017 | 4.39087e-07 |
| 0.2 | step_split_simpson | 991686 | 1.00009e+06 | 8406.32 | 8407.62 | -1.30379 | 0.000155096 | 3.09525e-07 |
