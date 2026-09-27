# H2-PRISM Architecture Overview

```
                      +-----------------------------+
                      |   Multi-Station Pipeline    |
                      | (P1, T1, m1) & (P2, T2, m2) |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |  Quality Control & Sync     |  <-- src/quality.py (Ahmed)
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      | Stage 1: Candidate Detector |  <-- src/detector.py (Yazan)
                      +--------------+--------------+
                                     | (Trigger Window)
             +-----------------------+-----------------------+
             |                                               |
             v                                               v
+---------------------------+                   +---------------------------+
| Physics Consistency       |                   | Propagation Delay         |
| - Real-gas density        |                   | - Cross-correlation       |
| - Line-pack mass balance  |                   | - Conditional interval    |
| <-- src/physics.py (Ahmed)|                   | <-- src/propagation.py    |
+-------------+-------------+                   +-------------+-------------+
              |                                               |
              +-----------------------+-----------------------+
                                      |
                                      v
                      +-----------------------------+
                      | Multi-Group Feature Engine  |  <-- src/features.py (Faisal)
                      | + Candidate Wavelet Layer   |  <-- src/fingerprint.py
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      | AI Attribution (XGBoost)    |  <-- src/model.py (Faisal)
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      | Contradiction & Fusion      |  <-- src/evidence.py (Faisal)
                      | (Stacking vs Dempster-Shaf) |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      | Observability Engine        |  <-- src/observability.py (Yazan)
                      | O = min(O_Q, O_S, O_E)      |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      | Gated Decision Engine       |  <-- src/decision.py (Yazan)
                      | -> Attribution or UNKNOWN   |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      | Structured Event Report     |  <-- SCADA / Historian format
                      +-----------------------------+
```
