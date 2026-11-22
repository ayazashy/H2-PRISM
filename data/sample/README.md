# H2-PRISM Quickstart Sample Dataset

This directory contains 4 representative, full-duration (20,000 timestep) scenario recordings from the peer-reviewed H2-SimNet dataset (Zenodo 17871393). They are tracked in Git to allow immediate offline testing and evaluation without downloading the full ~1 GB raw archive.

## Included Scenarios

| File | Scenario ID | Target Class | Topology | Description |
| :--- | :--- | :--- | :--- | :--- |
| `normality_gest_center.parquet` | `SCEN_NORMAL_GEST_CENTER` | `NORMAL` | Center | Baseline operation with zero injected faults |
| `leakG4.parquet` | `SCEN_CENTER_TRANSIENT_LEAKG4` | `LEAK` | Center | Transient leak at local restriction valve G4 |
| `brokenC1_strong.parquet` | `SCEN_CENTER_STEADY_STATE_BROKENC1_STRONG` | `COMPRESSOR_FAULT` | Center | Severe mechanical fault on compressor C1 |
| `startdelayC1.parquet` | `SCEN_CENTER_STEADY_STATE_STARTDELAYC1` | `COMPRESSOR_DELAY` | Center | Startup timing delay disturbance on compressor C1 |

## Quick Python Usage

```python
from h2prism.data import load_scenario

# Load any scenario by filename or ID
df_leak = load_scenario("leakG4")
df_normal = load_scenario("normality_gest_center")

print(f"Leak scenario loaded: {df_leak.shape} (20,000 rows x 24 columns)")
print(f"Pressure inlet (PS1): {df_leak['PS1'].iloc[0]:.2f} MPa")
print(f"Mass flow inlet (MFS1): {df_leak['MFS1'].iloc[0]:.2f} kg/s")
```
