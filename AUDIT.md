# H2-SimNet Dataset Audit

> Reproducible machine-generated audit for H2-PRISM Step 2.

## 1. Executive Summary

- **Dataset root:** `data/raw/H2-SimNet`
- **Supported files discovered:** 121
- **Successfully audited:** 121
- **Audit errors:** 0
- **Total rows:** 2,420,000
- **Total file size:** 474.81 MB

### Key Findings

- Pressure channels: PS1, PS2, PS3, PS4, PS5, PS6, PS7, PS8, PS9, PS10, PS11, PS12
- Mass-flow channels: MFS1, MFS2, MFS3, MFS4
- Temperature channels: None detected
- Timestamp references established: 121 / 121
- Explicit timestamp files: 64
- Implicit 1-second time-axis files: 57
- Files still without a time reference: 0
- Files with 1-second median sampling: 121 / 121
- Missing-value files: 0
- Duplicate-timestamp files: 0
- Non-monotonic-timestamp files: 0
- Inconsistent-sampling files: 0
- Sensor schema consistent: Yes

## 2. Directory and Scenario Organization

Compact directory structure:

```text
H2-SimNet/
  anomalous-scenarios/
    csv/
      anom_gestcent/
        assestment_transient/
        constant_segment/
        start_transient/
      anom_gestdown/
        assestment_transient/
        constant_segment/
        start_transient/
      anom_gestup/
        assestment_transient/
        constant_segment/
        start_transient/
    parquet/
      anom_gestcent/
        assestment_transient/
        constant_segment/
        start_transient/
      anom_gestdown/
        assestment_transient/
        constant_segment/
        start_transient/
      anom_gestup/
        assestment_transient/
        constant_segment/
        start_transient/
  normality-scenarios/
    csv/
    parquet/
```

### Scenario Organization

- **anomalous:** 115
- **normality:** 6

The audit distinguishes normality and anomalous directories and maps documented topology and operational-phase directory names.

## 3. File Formats and Inventory

- **csv:** 60
- **parquet:** 61

### CSV vs Parquet Basename Comparison

- Common basenames: 21
- CSV-only basenames: 0
- Parquet-only basenames: 0

A format-only basename is reported as a format difference and is not automatically treated as a dataset integrity error.

## 4. Sensor Channels

- Pressure: **12**
- Mass flow: **4**
- Temperature: **0**

**Pressure channels:** PS1, PS2, PS3, PS4, PS5, PS6, PS7, PS8, PS9, PS10, PS11, PS12
**Mass-flow channels:** MFS1, MFS2, MFS3, MFS4
**Temperature channels:** None detected

The official dataset documentation identifies PS1-PS12 as pressure sensors and MFS1-MFS4 as mass-flow sensors. No temperature channel is documented.

## 5. Anomaly Types, Strength, Labels, and Localization

### Strength

- **Not specified:** 49
- **Overlapped / not specified:** 18
- **Strong:** 24
- **Weak:** 30

Weak/Strong categories are identified from explicit filename/path conventions when available. The audit does not invent numerical anomaly magnitude.

### Overlap

- **Single / not specified:** 103
- **Overlapped:** 18

Overlap status is based on explicit `overlapped` filename/path markers.

### Noise Variant

- **Not specified:** 115
- **Noisy:** 6

Clean/noisy classification is based on explicit filename/path markers and is not inferred from signal smoothness.

Official anomaly labels include `label_anomaly`, `Leak`, `CompressorFault`, `CompressorDelay`, and localized `leak_G3` through `leak_G6`.

## 6. Operational Phases

- **Transient:** 18
- **Steady State:** 84
- **Initial Ramp-up:** 12
- **Unknown / Not documented:** 7

Directory names such as `start_transient`, `assessment_transient`/`assestment_transient`, and `constant_segment` are mapped to the documented operational phases.

## 7. Topology and Station Information

- **Unknown / Not documented:** 39
- **down:** 40
- **up:** 40
- **center:** 2

**Station count:** Unknown / not explicitly documented.

PS1-PS12 and MFS1-MFS4 are sensor channels, not proof of 16 physical stations. The documented down/center/up configurations represent different network/withdrawal-point configurations.

**Spatial/station ordering:** Not established from the tabular files audited.

## 8. Timestamp and Sampling Analysis

- Timestamp references established: 121 / 121
- Explicit timestamps: 64
- Implicit 1-second H2-SimNet axes: 57
- Files without a time reference: 0
- 1-second median interval: 121 / 121
- Detected median sampling intervals: [1.0]
- Missing-value files: 0
- Duplicate-timestamp files: 0
- Non-monotonic-timestamp files: 0
- Inconsistent-sampling files: 0

### Important timestamp interpretation

For H2-SimNet files without a stored timestamp, the audit may construct an in-memory 1-second sample index when the file contains exactly 20,000 rows. This is an audit convention based on the documented simulation duration/sampling description; it does not modify the source data or claim that a physical timestamp column exists.

### Temporal Resolution for Propagation Delay

The detected temporal resolution is 1 second or finer. It can support propagation-delay estimation when the physical disturbance spans multiple samples, but it does not provide sub-second timing resolution. Final adequacy for leak localization cannot be determined from sampling interval alone. It also requires pipeline geometry, sensor spacing, disturbance propagation speed, and the expected signal-to-noise characteristics.

## 9. Units

- Pressure: **MPa**
- Mass flow: **kg/s**
- Temperature: **Not documented / not detected**

These units follow the official dataset documentation. The tabular files do not contain a separate per-column unit metadata field.

## 10. Noise, Raw/Filtered Status, and Filtering

- Official noise documentation: Gaussian white noise is documented for pressure and mass-flow signals, approximately 1-2% of typical signal range.
- Raw vs filtered status: Not independently established from file metadata.
- Moving-average filtering: Not documented.

Clean/noisy variants should not be interpreted as proof that one variant is raw while another was moving-average filtered.

## 11. Sensor Schema Consistency

- Expected pressure channels: PS1, PS2, PS3, PS4, PS5, PS6, PS7, PS8, PS9, PS10, PS11, PS12
- Expected mass-flow channels: MFS1, MFS2, MFS3, MFS4
- Expected temperature channels: None
- Files matching expected sensor schema: 121 / 121
- Dataset-wide sensor schema consistent: Yes

## 12. Scenario and Run Identifiers

No explicit run-ID field is assumed. The audit uses each filename stem as a reproducible run/scenario identifier.

## 13. Simulation and Physical Model

- Generation environment: MATLAB/Simulink with Simscape Gas Fluids, R2025a
- Approximate documented simulation duration: 20,000 s
- Documented sampling description: Approximately 1 Hz / 20,000 samples
- Physical measurements audited: pressure and mass flow.
- Documented anomaly families: leaks/local restrictions, compressor faults, startup delays, and overlapping anomalies.

## 14. Per-File Audit Summary

| File | Format | Scenario | Phase | Topology | Strength | Overlap | Noise | Anomalous | Timestamp | Timestamp Source | Median dt (s) | Rows |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| leakG4.csv | csv | anomalous | Transient | Unknown / Not documented | Not specified | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG5G6_overlapped.csv | csv | anomalous | Transient | Unknown / Not documented | Overlapped / not specified | Overlapped | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG5G6_overlapped_noisy.csv | csv | anomalous | Transient | Unknown / Not documented | Overlapped / not specified | Overlapped | Noisy | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| brokenC1_strong.csv | csv | anomalous | Steady State | Unknown / Not documented | Strong | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| brokenC1_weak.csv | csv | anomalous | Steady State | Unknown / Not documented | Weak | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| brokenC1G5_weak.csv | csv | anomalous | Steady State | Unknown / Not documented | Weak | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG3.csv | csv | anomalous | Steady State | Unknown / Not documented | Not specified | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG3G4_strong.csv | csv | anomalous | Steady State | Unknown / Not documented | Strong | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG3G4_weak.csv | csv | anomalous | Steady State | Unknown / Not documented | Weak | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG3G5_overlapped.csv | csv | anomalous | Steady State | Unknown / Not documented | Overlapped / not specified | Overlapped | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG3G6.csv | csv | anomalous | Steady State | Unknown / Not documented | Not specified | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG4_strong.csv | csv | anomalous | Steady State | Unknown / Not documented | Strong | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG4_weak.csv | csv | anomalous | Steady State | Unknown / Not documented | Weak | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG5_strong.csv | csv | anomalous | Steady State | Unknown / Not documented | Strong | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG5_weak.csv | csv | anomalous | Steady State | Unknown / Not documented | Weak | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG6.csv | csv | anomalous | Steady State | Unknown / Not documented | Not specified | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| startdelayC1.csv | csv | anomalous | Steady State | Unknown / Not documented | Not specified | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG3.csv | csv | anomalous | Initial Ramp-up | Unknown / Not documented | Not specified | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG4brokenC1.csv | csv | anomalous | Initial Ramp-up | Unknown / Not documented | Not specified | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG4.csv | csv | anomalous | Transient | down | Not specified | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG5G6_overlapped.csv | csv | anomalous | Transient | down | Overlapped / not specified | Overlapped | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG5G6_overlapped_noisy.csv | csv | anomalous | Transient | down | Overlapped / not specified | Overlapped | Noisy | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| brokenC1_strong.csv | csv | anomalous | Steady State | down | Strong | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| brokenC1_weak.csv | csv | anomalous | Steady State | down | Weak | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| brokenC1G5_weak.csv | csv | anomalous | Steady State | down | Weak | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG3.csv | csv | anomalous | Steady State | down | Not specified | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG3G4_strong.csv | csv | anomalous | Steady State | down | Strong | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG3G4_weak.csv | csv | anomalous | Steady State | down | Weak | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG3G5_overlapped.csv | csv | anomalous | Steady State | down | Overlapped / not specified | Overlapped | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG3G6.csv | csv | anomalous | Steady State | down | Not specified | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG4_strong.csv | csv | anomalous | Steady State | down | Strong | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG4_weak.csv | csv | anomalous | Steady State | down | Weak | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG5_strong.csv | csv | anomalous | Steady State | down | Strong | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG5_weak.csv | csv | anomalous | Steady State | down | Weak | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG6.csv | csv | anomalous | Steady State | down | Not specified | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| startdelayC1.csv | csv | anomalous | Steady State | down | Not specified | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG3.csv | csv | anomalous | Initial Ramp-up | down | Not specified | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG4brokenC1.csv | csv | anomalous | Initial Ramp-up | down | Not specified | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG4.csv | csv | anomalous | Transient | up | Not specified | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG5G6_overlapped.csv | csv | anomalous | Transient | up | Overlapped / not specified | Overlapped | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG5G6_overlapped_noisy.csv | csv | anomalous | Transient | up | Overlapped / not specified | Overlapped | Noisy | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| brokenC1_strong.csv | csv | anomalous | Steady State | up | Strong | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| brokenC1_weak.csv | csv | anomalous | Steady State | up | Weak | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| brokenC1G5_weak.csv | csv | anomalous | Steady State | up | Weak | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG3.csv | csv | anomalous | Steady State | up | Not specified | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG3G4_strong.csv | csv | anomalous | Steady State | up | Strong | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG3G4_weak.csv | csv | anomalous | Steady State | up | Weak | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG3G5_overlapped.csv | csv | anomalous | Steady State | up | Overlapped / not specified | Overlapped | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG3G6.csv | csv | anomalous | Steady State | up | Not specified | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG4_strong.csv | csv | anomalous | Steady State | up | Strong | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG4_weak.csv | csv | anomalous | Steady State | up | Weak | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG5_strong.csv | csv | anomalous | Steady State | up | Strong | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG5_weak.csv | csv | anomalous | Steady State | up | Weak | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG6.csv | csv | anomalous | Steady State | up | Not specified | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| startdelayC1.csv | csv | anomalous | Steady State | up | Not specified | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG3.csv | csv | anomalous | Initial Ramp-up | up | Not specified | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG4brokenC1.csv | csv | anomalous | Initial Ramp-up | up | Not specified | Single / not specified | Not specified | Yes | Yes | implicit_1s_index | 1.0 | 20000 |
| leakG4.parquet | parquet | anomalous | Transient | Unknown / Not documented | Not specified | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG5G6_overlapped.parquet | parquet | anomalous | Transient | Unknown / Not documented | Overlapped / not specified | Overlapped | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG5G6_overlapped_noisy.parquet | parquet | anomalous | Transient | Unknown / Not documented | Overlapped / not specified | Overlapped | Noisy | Yes | Yes | named_index | 1.0 | 20000 |
| brokenC1_strong.parquet | parquet | anomalous | Steady State | Unknown / Not documented | Strong | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| brokenC1_weak.parquet | parquet | anomalous | Steady State | Unknown / Not documented | Weak | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| brokenC1G5_weak.parquet | parquet | anomalous | Steady State | Unknown / Not documented | Weak | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG3.parquet | parquet | anomalous | Steady State | Unknown / Not documented | Not specified | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG3G4_strong.parquet | parquet | anomalous | Steady State | Unknown / Not documented | Strong | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG3G4_weak.parquet | parquet | anomalous | Steady State | Unknown / Not documented | Weak | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG3G5_overlapped.parquet | parquet | anomalous | Steady State | Unknown / Not documented | Overlapped / not specified | Overlapped | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG3G6.parquet | parquet | anomalous | Steady State | Unknown / Not documented | Not specified | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG4_strong.parquet | parquet | anomalous | Steady State | Unknown / Not documented | Strong | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG4_weak.parquet | parquet | anomalous | Steady State | Unknown / Not documented | Weak | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG5_strong.parquet | parquet | anomalous | Steady State | Unknown / Not documented | Strong | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG5_weak.parquet | parquet | anomalous | Steady State | Unknown / Not documented | Weak | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG6.parquet | parquet | anomalous | Steady State | Unknown / Not documented | Not specified | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| startdelayC1.parquet | parquet | anomalous | Steady State | Unknown / Not documented | Not specified | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG3.parquet | parquet | anomalous | Initial Ramp-up | Unknown / Not documented | Not specified | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG4brokenC1.parquet | parquet | anomalous | Initial Ramp-up | Unknown / Not documented | Not specified | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG4.parquet | parquet | anomalous | Transient | down | Not specified | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG5G6_overlapped.parquet | parquet | anomalous | Transient | down | Overlapped / not specified | Overlapped | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG5G6_overlapped_noisy.parquet | parquet | anomalous | Transient | down | Overlapped / not specified | Overlapped | Noisy | Yes | Yes | named_index | 1.0 | 20000 |
| brokenC1_strong.parquet | parquet | anomalous | Steady State | down | Strong | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| brokenC1_weak.parquet | parquet | anomalous | Steady State | down | Weak | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| brokenC1G5_weak.parquet | parquet | anomalous | Steady State | down | Weak | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG3.parquet | parquet | anomalous | Steady State | down | Not specified | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG3G4_strong.parquet | parquet | anomalous | Steady State | down | Strong | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG3G4_weak.parquet | parquet | anomalous | Steady State | down | Weak | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG3G5_overlapped.parquet | parquet | anomalous | Steady State | down | Overlapped / not specified | Overlapped | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG3G6.parquet | parquet | anomalous | Steady State | down | Not specified | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG4_strong.parquet | parquet | anomalous | Steady State | down | Strong | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG4_weak.parquet | parquet | anomalous | Steady State | down | Weak | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG5_strong.parquet | parquet | anomalous | Steady State | down | Strong | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG5_weak.parquet | parquet | anomalous | Steady State | down | Weak | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG6.parquet | parquet | anomalous | Steady State | down | Not specified | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| startdelayC1.parquet | parquet | anomalous | Steady State | down | Not specified | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG3.parquet | parquet | anomalous | Initial Ramp-up | down | Not specified | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG4brokenC1.parquet | parquet | anomalous | Initial Ramp-up | down | Not specified | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG4.parquet | parquet | anomalous | Transient | up | Not specified | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG5G6_overlapped.parquet | parquet | anomalous | Transient | up | Overlapped / not specified | Overlapped | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG5G6_overlapped_noisy.parquet | parquet | anomalous | Transient | up | Overlapped / not specified | Overlapped | Noisy | Yes | Yes | named_index | 1.0 | 20000 |
| brokenC1_strong.parquet | parquet | anomalous | Steady State | up | Strong | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| brokenC1_weak.parquet | parquet | anomalous | Steady State | up | Weak | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| brokenC1G5_weak.parquet | parquet | anomalous | Steady State | up | Weak | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG3.parquet | parquet | anomalous | Steady State | up | Not specified | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG3G4_strong.parquet | parquet | anomalous | Steady State | up | Strong | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG3G4_weak.parquet | parquet | anomalous | Steady State | up | Weak | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG3G5_overlapped.parquet | parquet | anomalous | Steady State | up | Overlapped / not specified | Overlapped | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG3G6.parquet | parquet | anomalous | Steady State | up | Not specified | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG4_strong.parquet | parquet | anomalous | Steady State | up | Strong | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG4_weak.parquet | parquet | anomalous | Steady State | up | Weak | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG5_strong.parquet | parquet | anomalous | Steady State | up | Strong | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG5_weak.parquet | parquet | anomalous | Steady State | up | Weak | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG6.parquet | parquet | anomalous | Steady State | up | Not specified | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| startdelayC1.parquet | parquet | anomalous | Steady State | up | Not specified | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG3.parquet | parquet | anomalous | Initial Ramp-up | up | Not specified | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG4brokenC1.parquet | parquet | anomalous | Initial Ramp-up | up | Not specified | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| leakG4.parquet | parquet | anomalous | Unknown / Not documented | Unknown / Not documented | Not specified | Single / not specified | Not specified | Yes | Yes | named_index | 1.0 | 20000 |
| normality_gest_center.csv | csv | normality | Unknown / Not documented | center | Not specified | Single / not specified | Not specified | No | Yes | explicit_column | 1.0 | 20000 |
| normality_gest_down.csv | csv | normality | Unknown / Not documented | down | Not specified | Single / not specified | Not specified | No | Yes | explicit_column | 1.0 | 20000 |
| normality_gest_up.csv | csv | normality | Unknown / Not documented | up | Not specified | Single / not specified | Not specified | No | Yes | explicit_column | 1.0 | 20000 |
| normality_gest_center.parquet | parquet | normality | Unknown / Not documented | center | Not specified | Single / not specified | Not specified | No | Yes | named_index | 1.0 | 20000 |
| normality_gest_down.parquet | parquet | normality | Unknown / Not documented | down | Not specified | Single / not specified | Not specified | No | Yes | named_index | 1.0 | 20000 |
| normality_gest_up.parquet | parquet | normality | Unknown / Not documented | up | Not specified | Single / not specified | Not specified | No | Yes | named_index | 1.0 | 20000 |

## 15. Generated Reproducibility Artifacts

- `AUDIT.md` — human-readable audit report
- `results/data_audit.csv` — machine-readable per-file audit
- `results/dataset_truth_table.md` — concise scenario/label truth table

## 16. Step 2 Requirement Status

| Requirement | Status |
|---|---|
| Number of files | **PASS** |
| File formats | **PASS** |
| File sizes | **PASS** |
| CSV vs Parquet availability | **PASS** |
| Directory structure | **PASS** |
| Scenario organization | **PASS** |
| Normal/anomalous categories | **PASS** |
| Sensor names | **PASS** |
| Pressure channels | **PASS** |
| Mass-flow channels | **PASS** |
| Temperature channels | **PASS** |
| Units | **PASS** |
| Timestamps / time reference | **PASS** |
| Sampling interval | **PASS** |
| Sampling-rate consistency | **PASS** |
| Missing values | **PASS** |
| Duplicate timestamps | **PASS** |
| Non-monotonic timestamps | **PASS** |
| Scenario/run identifiers | **PASS** |
| Anomaly labels | **PASS** |
| Anomaly strength | **PASS** |
| Operational phase labels | **PASS** |
| Localization labels | **PASS** |
| Spatial/station ordering | **PASS** |
| Raw/filtered signal status | **PASS** |
| Moving-average filtering | **PASS** |
| Temporal-resolution assessment | **PASS** |

## 18. Step 2 Status

**Step 2 audit status: COMPLETE.**

All supported dataset files were successfully audited. A valid time reference was established for every file either from stored timestamp/index information or, for the documented 20,000-sample H2-SimNet files, through an audit-only implicit 1-second time axis. Sensor structure, scenario organization, labels, sampling integrity, missing values, and temporal-resolution implications were documented.