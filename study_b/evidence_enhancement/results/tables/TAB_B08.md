### TAB_B08 — H₂-PRISM evidence qualification

Evidence vocabulary as in the project.

| capability | data_requirement | available_evidence | numerical_finding | qualification_status | claim_allowed | claim_prohibited |
| --- | --- | --- | --- | --- | --- | --- |
| Causal one-step prediction | decision-time inputs only | frozen benchmark + bit-identical replay | 15,885 rows/channel, 3 runs | VALIDATED WITHIN SCOPE | Causal reference prediction on MHC dual-stage runs | Generality beyond this apparatus |
| Reference error behaviour | observation-level residuals | replayed predictions | Ridge RMSE gain from rare large steps; MAE loss on unchanged rows | DESCRIPTIVELY SUPPORTED | Metric-dependent ranking explained | Practical superiority of Ridge |
| Measurement resolution | instrument specs | recorded values only | P-2 0.2 barg grid; MFC-3 0.01 ln/min grid | NUMERICALLY VERIFIED (observed grid) | ΔMAE is 0.07 (P-2) and ~1 (MFC-3) recorded increment | Certified accuracy statements |
| Controller role of MFC-3 | control signals | workbook notes + coupled P-2/MFC-3 data | P-2 ≤ outlet set pressure + 1 barg whenever MFC-3 = 0 (3/3 runs) | DESCRIPTIVELY SUPPORTED | MFC-3 is a controlled outlet (release) flow | Modelling the control law (setpoint not recorded) |
| Operating-condition dependence | controlled factorial design | 3 runs, confounded settings | Run 29 carries 82 % of P-2 ΔSSE | DESCRIPTIVELY SUPPORTED | Run-level variation exists | Attribution to material, pressure or cycle time |
| Competing event hypotheses | qualified event mechanisms | operator notes (valve timing, safety valve, back-pressure error) | notes only | NOT ESTABLISHED | Notes recorded as metadata | Event labels |
| Fault classification / localization | independent labels, locations | none | — | BLOCKED BY EVIDENCE | None | Any accuracy or localization metric |
| Formal D(Y) | qualified observation and model bounds | none | — | BLOCKED BY EVIDENCE | None | Exclusion or certified diagnosis |
| Independent equipment transfer | other apparatus | one apparatus | — | NOT ESTABLISHED | None | Industrial generalization |
