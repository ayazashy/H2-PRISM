# Open-set mechanism screening v1

**Decision — REVISE_OR_REJECT the routing rule.** The full library is useful as a descriptive comparison. The agreement gate did not reliably make conditional localization eligible.

## Methods

The evaluator rechecked the 12 accepted Center raw hashes and sensor clocks using the NRES loader. It uses the established B3 kernel (equal per-channel, scaled matched residual RMS, one bounded shared shift). The nominal SID 213 control before 1,000 s defines the fixed channel scale. No template weights or thresholds were fit to the alternate profile. The library contains three controlled withdrawals, operational pressure command, command issuance shift, a quiet reference and a nominal pressure-transient prototype. The nominal transient uses a different matched control run (SID 312 control) as the template; the nominal query comes from SID 213 control. They share the Center source and schedule.

B0 forces the nearest outlet from the same ranked distance rows and common evidence mask. B1 chooses the nearest mechanism, taking the smallest distance over that mechanism's templates. B2 tests unique withdrawal leadership under both exact-clock and bounded-shift ranking, and requires complete selected evidence. B3 performs conditional descriptive location ranking only when that gate passes. It retains all three location candidates. B4 is the frozen formal policy. No experimental rank is passed to the formal engine as qualified evidence.

Prefixes are 1, 2, 5, 10, 30, 60 and 120 seconds on the 0.2 s grid. The clock-bound ablation is 0, ±0.5, ±1 and ±2 s; ±0.5 s permits ±0.4 s on-grid. Each rank uses only the query prefix and a pre-existing template. Controlled anchors are reported separately from the saved causal-alert anchors. Late alerts were the first alert in a fixed scope starting at 200 s, and the timing query uses the first startup alert. There is no eligible late alert for SID 215, and quiet has no alert-anchored row. The controlled anchor for SID 215 is explicitly retrospective. No archived intervention ID or annotation enters the ranker. Truth is appended after scoring. Identical self-templates occur for five queries and are flagged. Sensor subsets and timing settings are sensitivity rows, not independent tests.

## Outcomes

At 30 s, all sensors and ±1 s, forced location assigned sites to all four non-withdrawal observations: SID 215 for pressure, timing and quiet, and SID 213 for the nominal transient. Full-library leaders were pressure, timing, NORMAL and NORMAL, respectively, and the gate suppressed all four location interpretations. All four withdrawal observations were retained: nominal SID 213, 312, 215 and alternate-profile SID 213. The three nominal withdrawal templates were in the library. The alternate profile was held out from the template library, but shares the same source and has been examined before.

Across 3,584 controlled settings, B0 forced a site in 1,792/1,792 non-withdrawal settings. B1 would route 165/1,792 by the leading mechanism. B3 still routed 164/1,792. The 164 errors all come from the one timing observation, with 82 each at zero and ±0.5 s. B3 retained 1,792/1,792 withdrawal settings. These counts describe sensitivity, not classifier accuracy or inferential sample size. The extra consensus gate prevented one wrong route compared with nearest full-library mechanism. It does not justify qualified localization.

Removing the timing rival causes a false SID 215 route even in the 30 s, ±1 s focal test. Removing the pressure rival makes timing its closest mechanism and still blocks location in that fixture. This tests omitted templates explicitly. UNKNOWN remains an unresolved candidate, not a trained physical class or a calibrated open-set detector. Dropping MFS3 through an invalid-channel mask blocks routing, while a deliberately selected complete reduced schema can still be scored. Neither is a deployable sensor-loss guarantee.

For the held-template alternate profile at 30 s and ±1 s, mechanism margin falls from 0.028358 to 0.000141 with MFS3 omitted. Conditional location margin falls from 0.028432 to 0.002125. Pressure-only and flow-only mechanism margins are about 0.000023 and 0.059032. MFS3 contributes to both judgments in this configuration. All 896 alternate-profile sensitivity rows rank nominal SID 213 first after routing, including the 1 s causal-alert prefix. This is one observation. Detection timestamps are separately recorded, and prefixes measure available evidence after alert. Qualified formal decision and operational latency remain unestablished. The local computation was 2.286 ms median, 9.665 ms p95 across the heterogeneous grid; it excludes sensing, alert delay and reference acquisition.

## Reference feasibility

A nominal run loaded offline can serve as a pre-established template when model, commands and operating point match. In these pairs the same nominal trajectories define the residual, so exact matches mostly have zero mismatch by construction. They are not sufficient evidence that an operational counterfactual can be selected without intervention metadata. The separately recorded normal controls have nearly identical startup signatures.

A causal 5 s pre-anchor median is available from telemetry and excludes the anchor and future. At a 30 s prefix the normalized reference mismatch RMS is about 0.000163 for the alternate and pressure cases, but 0.263691 for timing and 0.253620 for the ordinary nominal pressure transient. A one-second nominal-reference clock mismatch yields 0.013530 for timing and 0.027740 for the nominal transient. No nominal context is inferred from hidden archive commands. A simple physical reference would need synchronized operational commands, validated model and operating-state context, and compatible sensors. These are not qualified here. The operational API rejects matched-control references even when a caller marks one qualified. Future samples are clipped. Irregular times are accepted only for exact timestamp matching at the residual layer; shared-shift ranking still requires a supported regular comparison grid. **Operational result remains BLOCKED_REFERENCE / UNRESOLVED.**

## Formal and scientific conclusion

Formal results stay **12/12 UNRESOLVED**, zero qualified exclusions, L0. Candidate sets remain broad. No demonstrated formal decision benefit, calibrated risk–coverage gain, independent mechanism diagnosis, or localization accuracy. The experiment shows a measurable reduction relative to a forced location library, but an important route failure still occurs and the gate adds little over a full library. All cases belong to one Center family, with zero verified independent generating families. A defensible next use needs a prospectively available operating reference and independent mechanisms including traceable equipment FAULT and actuator-response DELAY, along with simultaneous qualified uncertainty enclosures. Neither pressure command nor command issuance timing qualifies those missing classes.

**Poster Methods.** Compare a forced outlet library and full competing mechanism library with the same pressure/flow residuals and bounded timing shifts. Route to exploratory location only when withdrawal leads with and without alignment and selected evidence is complete.

**Poster Results.** The full library blocked four forced non-withdrawal locations at the 30 s comparison while retaining four withdrawals. Timing still triggered an inappropriate route under narrower offset assumptions. Formal diagnosis abstained on all 12 accepted captures.

## Reproduction

From the repository with PYTHONPATH set to src, use a fresh destination.

```powershell
.\.venv\Scripts\python.exe -m h2prism.mechanism_screen '<workspace>' '<fresh-output>'
.\.venv\Scripts\python.exe -m h2prism.mechanism_screen_figures '<fresh-output>'
```
