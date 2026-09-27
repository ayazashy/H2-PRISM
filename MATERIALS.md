# Materials, Data Provenance & Verification Record
# H2-PRISM — Materials & Data Provenance Lead (Yazan / Person 3)

## 1. Official Dataset
- **Full dataset name**: H2-SimNet Dataset
- **Zenodo Record**: 17871393
- **DOI**: [Record DOI]
- **Version**: 1.0
- **Date Accessed**: 
- **License**: 
- **Total Download Size**: 
- **Number of Files**: 
- **File Formats**: 
- **Official Description**: Simulated hydrogen-blend transport network anomaly dataset generated with MATLAB/Simscape model of a pipeline segment.
- **Source / Reference**: Zenodo Record 17871393

## 2. Dataset Claims (Author Claims)
- Scenario types documented: Normal, Leaks, Compressor faults, Startup delays.
- Measurement variables: Pressure and mass flow.
- Sampling information: To be verified from raw files.

## 3. Independently Verified Contents
*(To be populated after inspecting raw downloaded files)*
- Actual variables:
- Actual column names:
- Actual sensor identifiers:
- Actual sampling rate:

## 4. Missing or Unverified Information
| Item | Status | Evidence / Notes |
| :--- | :--- | :--- |
| Temperature | Not available / Unverified | |
| Density | Derived / Assumed | Real-gas relation required |
| Compressibility | Assumed | H2 EOS formula |
| Pipe Geometry | Partial / Unverified | |
| Pipeline Topology | Partial / Unverified | |
| Sensor Locations | Partial / Unverified | |
| Sampling Rate | Unverified | |
| Sensor Fault Labels | Not available / Synthetic only | |

## 5. Scenario Selection & Leakage Control
- Selected scenarios list:
- Training scenarios:
- Validation / Testing scenarios:
- Held-out scenarios:

## 6. Provenance Statement
> **Data Provenance**: The primary experimental results in this prototype were obtained exclusively from the H2-SimNet simulated hydrogen-pipeline dataset (Zenodo Record 17871393). No real-world field data were used. Any team-generated synthetic sensor-fault examples are explicitly identified as synthetic demonstration material and are excluded from primary H2-SimNet validation metrics.
