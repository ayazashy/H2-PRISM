# Materials, Data Provenance & Verification Record
# H2-PRISM — Materials & Data Provenance Lead (Yazan / Person 3)

## 1. Official Dataset
- **Full dataset name**: H2-SimNet Dataset
- **Zenodo Record**: 17871393
- **DOI**: 10.5281/zenodo.17871393
- **Version**: 1.0
- **Date Accessed**: 2026-09-28
- **License**: Open-access (CC-BY 4.0)
- **Total Download Size**: 999.2 MB (~1.0 GB)
- **Number of Files**: 123 CSV scenario runs + 7 MATLAB/Simscape model artifacts (`.slx`)
- **File Formats**: CSV, SLX, PDF, TXT
- **Official Description**: Simulated hydrogen-blend transport network anomaly dataset generated with MATLAB/Simscape model of a pipeline segment under 3 end-user topologies (`gest_down`, `gest_center`, `gest_up`).
- **Source / Reference**: Zenodo Record 17871393 (Acampora et al., 2025)

## 2. Dataset Claims (Author Claims)
- Scenario types documented: Normal Operation, Leaks (G3, G4, G5, G6 single & overlapping), Compressor Faults (C1 ramp failure), Compressor Startup Delays (C1).
- Measurement variables: 12 Pressure sensors (`PS1`–`PS12`) in MPa, 4 Mass flow rate sensors (`MFS1`–`MFS4`) in kg/s.
- Simulation duration: ~20,000 steps (~5.5 hours per scenario at 1.0 Hz nominal rate).
- Noise: 1–2% Gaussian white noise added to pressure and flow signals.

## 3. Independently Verified Contents
- **Total Scenarios Analyzed**: 123 CSV files
- **Total Timesteps Verified**: 2,478,894 timesteps
- **Actual variables**: 12 Pressure (`PS1`–`PS12`), 4 Flow (`MFS1`–`MFS4`), 8 Label flags (`label_anomaly`, `Leak`, `CompressorFault`, `CompressorDelay`, `leak_G3`, `leak_G4`, `leak_G5`, `leak_G6`)
- **Pressure range**: [0.739 MPa, 4.398 MPa] across operational scenarios
- **Flow range**: [-0.336 kg/s, 5.620 kg/s] (slight zero-flow sensor noise oscillation)
- **Actual sampling interval (dt)**: 1.0 s (1.0 Hz sampling rate)
- **Forensic Manifest**: Recorded in `results/materials_manifest.csv`
- **Truth Table**: Recorded in `results/dataset_truth_table.md`

## 4. Missing or Unverified Information
| Item | Status | Evidence / Notes |
| :--- | :--- | :--- |
| Temperature | Not available / Unmetered | Assumed nominal isothermal $T = 293.15\text{ K}$ ($20^\circ\text{C}$) |
| Density | Derived | Real-gas relation: $\rho = \frac{P M_{\text{H2}}}{Z R T}$ with compressibility factor $Z$ |
| Compressibility | Assumed | Calculated via real-gas H2 EOS ($Z \approx 1.0006$ at pipeline pressures) |
| Pipe Geometry | Partial / Documented | Segment length assumed $10\text{ km}$, diameter documented in Simscape |
| Sensor Locations | Mapped | Upstream `PS1`, Downstream `PS12`/`PS6`, Inflow `MFS1`, Outflow `MFS3`/`MFS4` |
| Sensor Fault Labels | Synthetic only | Dedicated synthetic sensor fault injection module (`data/synthetic/`) |

## 5. Scenario Selection & Leakage Control
- **Benchmark Selection Directory**: `data/selected/`
- **Processed / Synchronized Directory**: `data/processed/`
- **6 Canonical Benchmark Scenarios**:
  1. `scen_normal_001`: `normality_gest_center.csv` (Normal baseline)
  2. `scen_leak_g4_weak`: `leakG4.csv` (Weak transient leak at restriction valve G4)
  3. `scen_leak_g3_strong`: `leakG3.csv` (Strong steady-state leak at valve G3)
  4. `scen_leak_g5g6_overlap`: `leakG5G6_overlapped.csv` (Overlapping multi-point leak)
  5. `scen_comp_fault_c1`: `brokenC1.csv` (Compressor failure transient)
  6. `scen_comp_delay_c1`: `delayC1.csv` (Compressor startup delay)

## 6. Provenance Statement
> **Data Provenance**: The primary experimental results in this prototype were obtained exclusively from the H2-SimNet simulated hydrogen-pipeline dataset (Zenodo Record 17871393). No real-world field data were used. Any team-generated synthetic sensor-fault examples are explicitly identified as synthetic demonstration material and are excluded from primary H2-SimNet validation metrics.

