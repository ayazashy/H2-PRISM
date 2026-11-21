# Study B evidence enhancement — Discussion

1. **Does Ridge provide an overall practical advantage?**
   No. Its run-mean RMSE gains are 0.53 % (P-2) and 0.08 % (MFC-3), against MAE penalties of 9.2 % and 34.0 %. Expressed in recording increments, the RMSE gains are 0.010 and 0.023 of one step.

2. **What explains the slight RMSE reductions?**
   The learned intercept of +0.0144 barg per second and the weak state terms act as a fixed drift correction. That correction helps on the minority of rows where the signal is moving (2–10 increments for P-2; >10 increments for MFC-3). It hurts on the majority of rows where the recorded value is unchanged, because persistence is exactly right there and Ridge cannot be (its predictions are off the recording grid on 99.6–99.8 % of rows). Squared loss rewards the first effect and absolute loss penalises the second, which is why the two metrics rank the models differently.

3. **Are errors concentrated?**
   Yes.
   - For MFC-3, the top 1 % of rows carry 93–94 % of squared error under both models. The whole net Ridge gain is inside that 1 %; outside it Ridge is worse (+2.80 (ln/min)²).
   - For P-2, run 29 provides 82 % of the net gain, and the top 5 % of persistence-error rows provide 83 %.

4. **How does resolution affect the conclusions?**
   For P-2, the model differences are a small fraction of the 0.2 barg recording step, so they have no measurable physical meaning. For MFC-3, the MAE penalty is about one 0.01 ln/min step per row: real, but at the resolution floor. No instrument accuracy is documented, so neither difference can be compared to certified measurement uncertainty.

5. **What limits generalization?**
   - Only 3 held-out workbooks from 2 dates on one apparatus.
   - Undefined initial states (runs 28 and 29).
   - Confounded material, set pressure and cycle time.
   - Operator-noted irregularities in several runs.
   - A controlled outlet flow (MFC-3) whose setpoint is unrecorded.

6. **Contribution to Layers I and II.**
   - Layer I: a verified causal pairing, faithful units, and documented channel semantics, including the controller role.
   - Layer II: a reference whose error behaviour is now explained and bounded relative to recording resolution. Persistence is the appropriate reference for steady operation; neither model anticipates the large release steps.

7. **What MHC fails to validate in Layer III.**
   Everything. There are no qualified competing hypotheses, observation or model bounds, incident labels, or locations. The operator notes — possible safety-valve release in run 24, back-pressure control error in run 27, late valve openings — are candidate incidents only. They are unqualified, untimed and partly in development runs, so they cannot serve as labels.

8. **Effect on the original H₂-PRISM hypothesis.**
   None directly; H1 concerns diagnostic selective risk, which Study B cannot test. The study reinforces two design requirements for the evidence layer:
   - residual references must be judged relative to measurement resolution;
   - controlled variables must be modelled as controlled, not as passive residuals.
