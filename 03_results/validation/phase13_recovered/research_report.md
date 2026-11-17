# H₂-PRISM final exploratory results

## Methods
The controlled study used the checksum-pinned H₂-SimNet Center source with ode14x, fixed step 0.2 s, and a 20,000 s horizon. Every opening had its own control. The alternate profile supplied an extra 5 kPa at the reservoir from 500 s and opened SID 213 from 0.001 to 0.0011 m² at 1,000 s. Sensors, signed flow and storage were audited against the saved numeric extraction, approved model hashes and matched model differences.

The diagnostic comparison used treatment-minus-control sensor differences over fixed observation windows, divided by the nominal Center control's pre-event RMS per channel. Native engineering units appear separately in the sensor and physical-accounting results. Qualified formal consistency used the actual engine, with missing prediction and uncertainty bounds left unknown. Rectangular sensitivity boxes use assumed half-widths, in fractions of the same channel scales, and are exploratory self-matched prototype comparisons.

The separate release-label ML study used five 1 s samples per archive scenario (4 s from first to last), starting at the annotated event onset or a fixed 1,000 s anchor for NORMAL. No sliding or overlapping windows were used. Features are mean, standard deviation, end-minus-start and linear slope on 16 common telemetries. Nonfinite windows are excluded. Logistic scaling is fitted inside each training partition. The full-archive fits are exploratory model artifacts. Test predictions hold out entire conservative dependency components. Missing class support causes fold exclusion rather than fallback to window-level splitting. The archived labels, topology-varying channels, supplied onset, and possibly shared ancestry limit the task to retrospective annotation recognition.

## Controlled results
All four Phase 13 captures are accepted. The registry also includes the six previously accepted Phase 12 captures. The final retry succeeded in a fresh MATLAB session following an earlier duplicate logging-variable error. The session effect is a plausible explanation, with exact cause unproven.

- The alternate-profile opening increased outlet flow by **0.691931667 kg/s at 1,000 s**, approximately **0.000663 kg/s** above the nominal SID 213 result of 0.691269 kg/s. The alternate run withdrew an additional **13,104.883 kg** relative to its own control over the post-event window. This is approximately **40.049 kg (0.307%)** above the nominal pair.
- MFS3 reached a peak response of **+0.696818 kg/s** and PS1 reached **−0.000607437 MPa**. Both showed a sustained response from 1,000 s. The maximum pre-event differences for those channels were **2.92×10⁻⁷ kg/s** and **5.57×10⁻⁷ MPa**. The paired storage-change difference from onset to the last sample was **−431.991 kg**. Final event-aware conservation residuals were **−0.943198 kg** in the alternate control and **−0.941687 kg** in its intervention.
- The 30 s normalized distance between the nominal and alternate SID 213 signatures was **2.76120×10⁻⁵** with all sensors, **1.40526×10⁻⁷** with pressure only, and **5.74783×10⁻⁵** with flow only. This is evidence for sensitivity to one small operating-profile change.
- SID 55 received a **0.17 MPa reduction** and displayed a modeled flow reversal at the event knot. Its closest outlet rival over 30 s with all sensors remained SID 215 (**0.04738**), falling to **0.00983** when MFS2 was omitted. This depends on the intervention magnitudes and normalization. Sensor removal and window-specific comparisons are in the pairwise table.

## Diagnostics and machine learning
Both evidence-based policies were **Specific 0/10, Ambiguous 0/10, Unresolved 10/10**. All declared consistency states remained indeterminate and no rival locations were excluded. Formal localization remains **L0**. This is a null decision ablation under the current evidence. The matched reference-domain comparison previously found equivalence to exact joint set-membership. A classifier score supplies no qualified formal exclusion.

Logistic regression and random forest each trained on 51 archived scenario windows for the final exploratory fit. Each had eight scored held-out-component folds, with 42–48 training scenarios per fold and 39 total scored predictions. **Every scored observation carried a LEAK label.** Two folds containing the other 12 scenarios lacked at least one training class and were excluded. Logistic regression matched **30/39 (76.92%)** and random forest matched **36/39 (92.31%)**. These fractions are restricted LEAK recall. No four-class balanced accuracy, macro F1, class-wide precision/recall, calibrated abstention, or matched-coverage risk comparison is established. The confusion counts document predictions on the observed support. Neither classifier was evaluated against the controlled simulations.

## Discussion and conclusion
The source-derived experiments quantify a pressure-command rival and demonstrate measurable responses to three configured outlet locations. Discrimination depends on sensor coverage and normalization. Neither the archive nor the controlled captures supply qualified independent test families, calibrated bounds, confirmed hydrogen fidelity, or independent location labels. Numerical solver refinement and mass-balance checks establish simulator behavior only. The clean-release trajectory discrepancy remains unresolved. A future confirmation needs source-traceable labels, qualified sensors and model enclosures, and independently generated calibration and test families.

**Poster Methods.** Compare matched pressure-command and outlet interventions in a pinned Center simulation; separately train simple classifiers on archived annotations with dependency-component holdouts.

**Poster Results.** The pressure rival reversed modeled source flow at onset. A +5 kPa operating-profile change increased modeled SID 213 extra withdrawal by about 40 kg over the run. Both formal decision policies abstained on every accepted capture. Archive ML scores describe only held-out LEAK recognition.

## Reproduction

From the repository in PowerShell, use a fresh output directory:

```powershell
$env:PYTHONPATH = 'src'
$env:MPLBACKEND = 'Agg'
.\.venv\Scripts\python.exe -m h2prism.phase13_integrated '<workspace>' '<fresh-results-directory>'
.\.venv\Scripts\python.exe -m h2prism.phase13_ml '<fresh-results-directory>/ml'
```
