# H2-SimNet Dataset Audit Report
# Produced according to Forensic Materials Audit (Person 3 / Person 1)

## 1. File & Storage Inventory
- Number of files: 123 CSV scenario runs + 7 MATLAB Simscape (.slx) models
- File formats: CSV, SLX, PDF, TXT
- Total size: ~999.2 MB (~1.0 GB uncompressed)

## 2. Variables & Measurement Configuration
- Pressure channels: 12 channels (PS1–PS12) in MPa
- Mass-flow channels: 4 channels (MFS1–MFS4) in kg/s
- Temperature channels: 0 (Unmetered / Isothermal nominal 293.15 K assumed)
- Sampling interval (dt): 1.0 s (1.0 Hz nominal rate)
- Sampling-rate consistency: Verified across all 123 scenarios

## 3. Anomaly & Scenario Coverage
- Normal operation: 12 scenarios across gest_down, gest_center, gest_up topologies
- Leaks: 72 scenarios (G3, G4, G5, G6 individual and overlapped)
- Operational transients: 24 scenarios (compressor ramp failure C1, startup delay C1)
- Sensor faults: Handled via dedicated synthetic fault suite (data/synthetic/)
- Ambiguous scenarios: Weak leaks near boundary detection thresholds

## 4. Propagation Feasibility
- Hydrogen acoustic wave speed: ~1300 m/s (nominal at 20 C, 3.5 MPa)
- Sampling interval vs transit time: dt = 1.0 s, tau = L / a = 10000 / 1300 ~ 7.7 s
- Resolution floor (a * dt / 2): +/- 650 m at 1 Hz sampling rate
