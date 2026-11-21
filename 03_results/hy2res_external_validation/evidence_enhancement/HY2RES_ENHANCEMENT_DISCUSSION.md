# Study C evidence enhancement — Discussion

1. **What does pressure quantization change?**
   The pressure targets are a 0.1 bar step process. Persistence is exactly right on 96 % (buffer) and 74 % (tank) of rows and otherwise off by exactly one step. The published MAE and RMSE differences amount to 0.005–0.10 of one recording step. They measure how well each model anticipates rare single-step transitions, not physically resolved accuracy.

2. **Is Ridge genuinely better?**
   Only in a narrow sense. Under squared loss it partly anticipates single-step transitions (tank ΔSSE −54.2 bar² on step rows), and it pays on unchanged rows (+15.2 bar²). Its buffer MAE is 38.8 % worse, and its tank MAE differs by only 0.0046 increments. There is no evidence of a practically meaningful improvement, and this test period cannot support a new superiority claim.

3. **What causes the large unresolved fraction?**
   Tank pressure above the development maximum: 31,589 of 32,308 unresolved rows (97.8 %). Nonfinite segment-start inputs (413) and empty development cells (306) account for the rest. It is not ambiguity between states, and no implementation error was found: the frozen rule reproduces exactly.

4. **Is drift associated with out-of-support observations?**
   Yes, descriptively. Tank-pressure medians rise from 94.2 bar (development) to 102.4 (validation) and 107.8 (test). In every 6-hour bin the unresolved fraction tracks the out-of-support fraction, and all bins with median tank pressure ≥ 107.0 bar are fully unresolved. Validation contained no out-of-support rows, so development-only checks could not have revealed the problem.

5. **Does the policy distinguish the minority state?**
   No. It makes 0 specific calls on the 817 compressor-powered rows (201 ambiguous, 616 out of support), and all 10,762 specific calls agree with the majority baseline.

6. **Does any operating-state conclusion support H₂-PRISM?**
   A limited one. Zero-flow observations reliably indicate the electrolyzer-only state, but once zero-flow rows are removed, pressure and flow do not separate the states (rank probabilities 0.47–0.55). This is evidence about evidence sufficiency, not state recognition.

7. **What is established for Layers I and II?**
   - Layer I: source identity, a causal segmented time base, and a documented 0.1 bar recording grid.
   - Layer II: a reconciled reference benchmark, explained error mechanics, and a channel-level support-validity diagnosis showing exactly when the empirical reference stops applying.

8. **Why is Layer III not validated?**
   There are no qualified observation or prediction bounds, no physical hypothesis library, no event labels and no locations. Out-of-support abstention is a correct empirical-domain warning, not a certified exclusion of physical hypotheses.

9. **What remains genuinely necessary for Study C?** Nothing within the approved question. Recommended engineering additions, not implemented as policy changes:
   - report channel-level support reasons alongside UNRESOLVED;
   - monitor development-domain coverage over time;
   - separate `OUT_OF_SUPPORT` from `INVALID_INPUT` and `EMPTY_CELL` in any future rule;
   - evaluate any re-designed reference (for example, drift-robust features) only on a genuinely untouched future period or another system.

   A separate repository repair is also needed: resolving the committed merge-conflict markers in 11 shared files before any integration.
