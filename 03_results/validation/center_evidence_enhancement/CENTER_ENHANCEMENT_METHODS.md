# Center evidence enhancement — Methods

Scope: additive analysis of the 12 accepted Center captures frozen at `h2prism-center-baseline-v1` (`6fee8a0`). No capture, frozen table, kernel, split or formal-engine semantics was changed. Code: `src/h2prism/center_enhancement.py` (analysis) and `src/h2prism/center_enhancement_report.py` (tables and figures).

## M1 Source qualification

Each capture was re-read through the frozen loader (`nres.load_pairs`), which verifies the raw `center_raw.mat` SHA-256 against its acceptance receipt, the common 0.2 s clock (100,001 samples, 0–20,000 s) and the sensor units (PS1–PS10 in MPa, MFS1–MFS3 in kg/s). Configured interventions, outlet SIDs, branch flow-sensor SIDs, reservoir SIDs and overlays were read from each capture's `design.json`. The gas parameters were read directly from the source model `Normal_HNetwork_gest_center.slx` (SHA-256 `710711f4…`): `R = 0.287 kJ/(kg·K)`, an air-like specific gas constant. The Center model is therefore qualified as an air-like controlled simulation, not a hydrogen pipeline.

## M2 Observation objects

For every intervention pair the observation is the matched residual

  r(t) = x_intervention(t) − x_matched-control(t),

on the exact shared clock, as in the frozen B3 baseline. Windows are the frozen focal 30 s prefix (151 samples) from the retrospective controlled anchor (1,000 s; 26 s for the timing case; 25 s for the nominal start-up query). Anchors use configured truth and are therefore retrospective; no causal-alert latency is claimed.

## M3 Frozen B3 kernel (unchanged)

`nres.rank` computes, for query q and template h with a shared integer shift k ∈ {−K,…,K} (K = bound/0.2 s),

  B3(q,h) = min_k sqrt( Σ_{t,c} ((q_tc − h_{t+k,c}) / s_c)² / (T·C) ),

where s_c is the frozen per-channel scale: the RMS of the SID 213 control before 1,000 s. The scale is an absolute operating level (≈ 6 MPa for most pressures, ≈ 6 kg/s for MFS1/MFS3, 0.0022 kg/s for MFS2), so B3 is a dimensionless relative deviation. Equal channel weights are retained.

## M4 Self-template exclusion (Experiment A)

Predeclared rule: a template is excluded for a query when its *primary* capture (the capture whose intervention it encodes) equals the query's primary capture. Shared nominal controls are disclosed dependencies, not exclusions (the SID 213, SID 55 and SID 59 controls are bitwise identical). A template is flagged as a *near duplicate* when its B3 distance to the query is ≤ 1 % of the query's B3 distance to the zero residual. Three library conditions are compared:

| Condition | Library |
|---|---|
| frozen | frozen mechanism-screen library (self-templates present) |
| loto | frozen library minus the query's own template |
| loto_replicate | loto plus the alternate-profile capture as a second SID 213 template |

A query whose configured mechanism has no remaining template is UNSUPPORTED; its nearest mechanism is recorded but not counted as a prediction. Ties use a relative tolerance of 1e-12. QUIET (an all-zero construct) is reported but excluded from counts.

## M5 Location ranking (Experiment B)

Candidate set: outlet SIDs with an admissible withdrawal template after exclusion (eligibility fixed before scoring; truth is appended afterwards). Site score = minimum B3 over that site's templates. Reported: rank of every candidate, top-1, top-2, margin, ties and support status.

## M6 Sensor groups (Experiment C)

Groups: all 13 channels, pressure (PS1–PS10), flow (MFS1–MFS3), all minus MFS3. For each pair of withdrawal templates the report gives (i) the B3 distance per group, (ii) pressure and flow shares of the B3 squared sum, and (iii) the largest native-unit difference at the best shift within ±1 s, separately in MPa and kg/s (never summed). Location separation is summarised as runner-up/correct B3 ratio, which is invariant to B3's per-group channel averaging.

## M7 Conditional D(Y) (Experiment D)

The frozen engine `certified_evidence.diagnose` is used unchanged. A new adapter, `TemplateEnvelopeAdapter`, represents hypothesis h by the union of its admissible templates over the declared clock-shift set, widened by a model half-width ε_m,k per channel kind k:

  P_h = ∪_{template, k} { template(t+k) + d : |d_c| ≤ ε_m,kind(c) }.

The observation box is Y = { r(t) + e : |e_c| ≤ ε_o,kind(c) } with ε_o supplied through the measurement contract (so the engine's own uncertainty checks run).

- **EXCLUDED** only through the engine's certificate form: one coordinate (sensor, time) whose full hull [min_k h − ε_m, max_k h + ε_m] is disjoint from the observation interval. The engine re-verifies the certificate.
- **FEASIBLE** only with an exact witness: one template and shift whose widened trajectory meets every observation interval.
- Otherwise **INDETERMINATE**. A hypothesis whose only template is the query's own capture has no adapter (UNSUPPORTED → INDETERMINATE).

All comparisons are exact rationals of the float inputs; floats only preselect candidates.

**Proposition (used, and verified numerically).** Intervals [y−ε_o, y+ε_o] and [h−ε_m, h+ε_m] intersect iff |y−h| ≤ ε_o+ε_m. Hence only ε = ε_o+ε_m enters, and

  excluded ⇔ ∃k: ε_k < E_k, E_k = max_{c∈k} dist(y_c, [min_s h_c(s), max_s h_c(s)]);
  feasible ⇔ ∃s: ∀k: ε_k ≥ M_k(s), M_k(s) = max_{c∈k} |y_c − h_c(s)|.

Exclusion is monotone non-increasing and feasibility monotone non-decreasing in ε, so E_k and F_k = min_s M_k(s) (single-kind groups) are exact onsets; no search or extrapolation is used. Gates: the engine status equals this closed-form prediction in all 3,584 hypothesis checks, and moving the whole budget from model to observation (split 0.5 → 1.0) changes no decision.

**Bound scenarios** (declared, hypothetical, total half-widths per kind): S1–S6 = (10⁻⁶…10⁻¹ MPa, 10⁻⁵…10⁰ kg/s) in decades, plus REF = (0.0344 MPa, 0.0182 kg/s), the largest observed 0.4 → 0.2 s solver-refinement differences recorded in `final_research/research_evidence.json`. REF is a scale reference, not an enclosure. Clock-shift sets: ±1 s (frozen focal) and 0 s.

**Hypothesis universes.**
- *Full declared*: NORMAL, withdrawal at SID 213 / 312 / 215, SID 55 pressure command, SID 59 command shift, plus three declared hypotheses with no adapter: withdrawal at SID 222 (in the frozen universe), COMPRESSOR_FAULT and ACTUATOR_DELAY (original four-class contract).
- *Restricted supported*: only hypotheses with an adapter after self-exclusion. This is a conditional sensitivity view, not a production policy.

## M8 Decision assessment (Experiment E)

SPECIFIC / AMBIGUOUS / UNRESOLVED and reason codes come directly from the frozen engine. Correctness is assessed only where the configured hypothesis is in the evaluated universe; AMBIGUOUS sets are checked for retention of the configured hypothesis.

## M9 Historical classification (Experiment F)

Read-only examination of `05_documentation/FORENSIC_FINDINGS_REPORT.md`, `05_documentation/PROTOCOL_2_ABLATION_REPORT.md`, `03_results/primary_protocol/PRIMARY/` and `06_audit_preparation/protocol2/PROTOCOL_2_0_OWNER_DECISIONS.md`. No classifier was trained or rerun.

## Relation to earlier work

`phase13_integrated/research_report.md` reported a self-matched hypothetical-width table in fractions of pre-event RMS. The present analysis differs in four ways: own templates are excluded, bounds are in native units per kind, results come from the frozen engine, and onsets are exact rather than gridded.
