# Phase 13 Center research closure

## Results and evidence
Nine runs enter this exploratory analysis: six earlier outlet captures, the two SID 55 pressure captures and the alternate-profile control. The three completed Phase 13 runs passed re-audit at 0.2 s through 20,000 s, with 13 sensors, six external flows and eight storage histories. The alternate-profile intervention is blocked pending interactive retry. The failed run reached SIM_STARTED and produced no accepted MAT capture. The saved pair differs only in the approved outlet final value. No available evidence identifies whether initialization, runtime execution, cancellation or output production caused the exception.

At 1,000 s SID 55 received 6.23 MPa versus 6.40 MPa in the control. The logged pressure difference matched the input to 2.8e-9 Pa and the signed port rates summed to zero at saved knots. Flow into A went from +106.413 kg/s in the control to -265.429 kg/s in the intervention at this knot, a modeled reversal. Outlet flow changed by only +2.13e-8 kg/s at onset; its integrated change was -1,841.32 kg over the post-event window. Network stock change differed by -3,655.20 kg. Event-aware final balance residuals were -0.939 and -0.716 kg for control and intervention. These residuals describe numerical accounting. PS7 changed by -0.170 MPa at 1,000 s, PS1 reached -0.169324 MPa, and MFS3 reached -0.097949 kg/s. The largest pre-event sensor differences were 6.43e-7 MPa and 3.37e-7 kg/s. The pre-event internal through-flow difference reached 0.00725 kg/s.

The alternate control's reservoir command and physical pressure moved from 720 to 725 kPa at 500 s. Reservoir flow into the network was 129.758 kg/s at that knot and 107.049 kg/s at 1,000 s. The outlet area held at 0.001 m2. The event-aware final balance residual was -0.943 kg. Equilibration and profile sensitivity of the opening remain unverified.

| SID 55 compared with | All sensors, 30 s | Pressure only | Flow only |
|---|---:|---:|---:|
| SID 213 | 0.058195 | 0.010187 | 0.119707 |
| SID 312 | 0.056506 | 0.010177 | 0.116150 |
| SID 215 | 0.047376 | 0.010179 | 0.096853 |

These are paired treatment-minus-control responses divided by the same nominal Center control pre-event RMS for each channel. SID 215 is closest with all sensors. Removing MFS2 reduces that distance to 0.009827. MFS2 has a small reference scale, so this influence is conditional on the normalization. The contrasts combine mechanism and the chosen intervention magnitudes. They cannot establish general separability.

## Decision policies and uncertainty
Both policies used the same qualified consistency states and hypothesis universe. The singleton policy makes a specific decision only with one feasible member and all other hypotheses excluded. The full engine additionally reports ambiguity when multiple hypotheses are feasible and none are indeterminate. All nine observations yielded zero feasible and zero excluded hypotheses, and both policies returned UNRESOLVED in 9/9 cases with zero unsupported exclusions. Specific coverage was 0/9 and selective risk is undefined. Configured outlet locations were known in the controlled experiments, but the formal localization decision remained L0. Phase 4's matched-domain regression tests verify equivalence to exact joint set-membership for the tested reference domain. This work demonstrates auditability and explicit treatment of insufficient evidence. It demonstrates no extra mathematical exclusion power or empirical gain.

The hypothetical sensitivity table compares saved response signatures with centered measurement and model boxes. Half-widths are separate fractions of each sensor's pre-event RMS (MPa for pressure and kg/s for flow). A rival matches when every saved coordinate differs by at most the sum of the widths. The exact pairwise transition is the maximum normalized absolute difference. The observation's own prototype is included, so this calculation is descriptive and self-matched. For SID 55 at 30 s, equal 1% widths leave one hypothetical match in all, flow-only and pressure-only subsets. At equal 10% widths, pressure-only expands to five matches; all and flow-only retain one. Changing one width can compensate for the other in this box model. None of the widths is qualified. Solver refinements quantify variation for one model; sensor uncertainty, boundary and initial-condition uncertainty, parameter bounds and physical model discrepancy remain unqualified.

**NO DEMONSTRATED INCREMENTAL DECISION VALUE**

**CONFIRMATORY DIAGNOSTIC ACCURACY: NOT ESTABLISHED**
**CONFIRMATORY SELECTIVE-RISK IMPROVEMENT: NOT ESTABLISHED**
**CONFIRMATORY ADDED VALUE OF DISTINGUISHABILITY: NOT ESTABLISHED**

## Claims and limitations
Supported: the matched interventions produced different numerical signatures, the sensors contributing most to this difference depend on scaling, and the formal method exposed missing evidence through abstention. Unsupported: physical hydrogen fidelity, independent diagnostic performance, localization beyond L0, or robustness across operating profiles. The archived clean-release reconciliation remains unresolved. The next independent study needs source-traceable event labels and physical measurements, separate calibration and held-out scenario families, and validated prediction and uncertainty enclosures.

## Poster text
**Methods.** Compare matched pressure and outlet interventions in a checksum-pinned Center gas-network simulation. Compute aligned 13-channel response contrasts and test hypothesis consistency on identical evidence with two decision policies.

**Results.** The 0.17 MPa command reduction reversed modeled source flow at onset. Flow-channel responses carried much of the descriptive contrast with outlet interventions. Both policies abstained on all nine captures, and location remained unresolved.

**Contribution.** The framework records why available evidence cannot support a specific decision. Independent evidence is required to test whether that behavior improves diagnostic outcomes.

## Reproduction
From the repository, set PYTHONPATH to src and run the Phase 13 analysis with the existing Python environment:

```powershell
$env:PYTHONPATH = 'src'
.\.venv\Scripts\python.exe -m h2prism.phase13_integrated 'C:/Users/ahmd1/Documents/Codex/2026-11-16/before-starting-the-new-h-prism' '<fresh-output-directory>'
```

The evidence JSON contains capture approvals, hashes, physical knots and formal certificates. The pairwise CSV contains every window and subset, including leave-one-out analyses. The alternate-profile opening has no result row.
