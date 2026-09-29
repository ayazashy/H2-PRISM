# H2-PRISM — Step 4 Scenario Selection Manifest

## Selection Policy

Initial validation set consists of complete scenario/run files.
No random row sampling is used.
Complete temporal sequences are preserved.
Raw H2-SimNet files are not modified.

Configuration:
- Selected operating configuration: center
- Reason: use one documented network/withdrawal-point configuration consistently across the initial scenario set.
- This is a methodological control choice, not a claim that center is superior to down or up.
- Physical station ordering is not inferred from PS1–PS12 or MFS1–MFS4.

## Selected Scenarios

| ID | Category | Scenario | Configuration | Native Ground Truth | Original Path | Selection Rationale |
|---|---|---|---|---|---|---|
| S01 | Normal | normality_gest_center.csv | center | label_anomaly=0 | data/raw/H2-SimNet/normality-scenarios/csv/normality_gest_center.csv | Complete normal operating run used as baseline |
| S02 | Weak/moderate leak | leakG5_weak.csv | center | Leak=1; leak_G5=1 | data/raw/H2-SimNet/anomalous-scenarios/csv/anom_gestcent/constant_segment/leakG5_weak.csv | Single-leak scenario with documented weak classification and distinct G5 component |
| S03 | Stronger leak | leakG4_strong.csv | center | Leak=1; leak_G4=1 | data/raw/H2-SimNet/anomalous-scenarios/csv/anom_gestcent/constant_segment/leakG4_strong.csv | Single-leak scenario with documented strong classification |
| S04 | Compressor/operational event | brokenC1_strong.csv | center | CompressorFault=1; Leak=0 | data/raw/H2-SimNet/anomalous-scenarios/csv/anom_gestcent/constant_segment/brokenC1_strong.csv | Isolated compressor-fault event without simultaneous leak |
| S05 | Startup/delayed response | startdelayC1.csv | center | CompressorDelay=1; anomaly rows 25–1000 | data/raw/H2-SimNet/anomalous-scenarios/csv/anom_gestcent/constant_segment/startdelayC1.csv | Explicit compressor startup-delay scenario with short transient event |
| S06 | Overlapping | leakG5G6_overlapped.csv | center | Leak=1; leak_G4=1; leak_G6=1 | data/raw/H2-SimNet/anomalous-scenarios/csv/anom_gestcent/assestment_transient/leakG5G6_overlapped.csv | Simultaneous two-component leak scenario; filename contains G5G6 but audited labels identify G4+G6 |

## Temporal Integrity

All selected files are complete runs.
No rows are removed.
No random sampling is performed.
The native sequence order is preserved.

## Important Interpretation Limits

- "Weak" and "strong" are dataset scenario classifications based on documented file/scenario naming; they are not treated as independently verified physical leak-rate magnitudes.
- leakG5G6_overlapped.csv is labeled by its audited ground truth as G4 + G6, despite the filename containing G5G6.
- center/down/up are network/withdrawal-point configurations, not physical sensor locations.
- PS1–PS12 and MFS1–MFS4 do not establish physical station ordering.
- Component-level leak identification is supported by the native labels; meter-level physical localization is not yet validated.
- Native H2-SimNet data are simulated rather than field measurements.

## Holdout Policy

No final held-out scenario is modified or consumed by this manifest.
Final holdout selection will be documented separately before model evaluation.
"@ | Set-Content "results\step4_scenario_selection.md" -Encoding UTF8
