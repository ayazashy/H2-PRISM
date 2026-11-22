# Techno-economic comparison

Tables A15 (cost terms), A16a/b (sensor count) and A14 (compute).

## Answers

- **Can a hardware-cost saving be credibly quantified?** **No.** The repository holds no source-supported sensor, installation, calibration, maintenance, data-acquisition or inspection prices. No value was invented.
- **Parametric model, with every coefficient unquantified:**

  C_total = Σ_i n_i (c_s,i + c_inst,i + c_cal,i + T·c_m,i + c_daq) + c_pwr + c_compute + c_FP·N_FP + c_FN·N_FN

- **Measured per-decision computational cost:** about 0.4 s median wall time per formal decision on a laptop-class CPU (A14c; the value varies between runs). In the isolated benchmark a 13-channel, 6-hypothesis decision takes 0.36 s (A14a). This is a time cost, not a monetary one.
- **Which sensor arrangements are efficient?** Only conditional, Center-specific statements are possible (A16):
  - Two flow meters (MFS1 + MFS3) keep every formally separable hypothesis pair at the REF bounds.
  - Flow-only sensing (3 channels) keeps all 8 correct SPECIFIC decisions but doubles wrong ones.
  - Pressure-only sensing (10 channels) keeps no wrong decision but loses 6 of the 8 correct ones.
  - The two-meter result is a property of templates under hypothetical bounds in one air-like simulation. It is not a field sensor design.
- **Asymmetric error costs (missed leak vs false leak vs delay):** a framework only (c_FP, c_FN terms). There is no defensible basis for values.

## What a credible cost study needs

1. Vendor-quoted or published prices with dates and currency, for each sensor type at hydrogen service ratings.
2. Installation and calibration labour models.
3. Failure and maintenance rates.
4. Consequence costs for false and missed detections from a recognised risk-assessment method.
5. Diagnostic rates from an independent evaluation. The current rates are conditional or exploratory.
