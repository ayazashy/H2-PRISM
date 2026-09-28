# H2-SimNet Measurement Configuration \& Validation Scope



## 1. Purpose



This document records the verified measurement configuration, temporal resolution,

spatial observability, labels, and validation scope of the H2-SimNet dataset used by

H2-PRISM.



All statements in this document are based on direct inspection of the dataset files

and the accompanying dataset documentation. Project-level assumptions are not treated

as dataset facts.



\---



## 2. Verified Measurement Channels



H2-SimNet contains 16 direct measurement channels:



### Pressure

\- PS1

\- PS2

\- PS3

\- PS4

\- PS5

\- PS6

\- PS7

\- PS8

\- PS9

\- PS10

\- PS11

\- PS12



Unit: MPa



### Mass Flow

\- MFS1

\- MFS2

\- MFS3

\- MFS4



Unit: kg/s



All 16 measurement channels are present across the audited dataset files.



\---



## 3. Variables Not Directly Measured



The following variables are not available as direct measurement channels in the

audited H2-SimNet files:



\- Temperature

\- Density

\- Flow velocity

\- Verified physical sensor coordinates

\- Verified sensor-to-sensor distances

\- Verified station ordering



Density and velocity may be derived only if the required thermodynamic properties,

pipe geometry, and cross-sectional area are independently established.



\---



## 4. Temperature Availability



No temperature measurement channel was detected.



Temperature status:



**NOT AVAILABLE**



Therefore, any H2-PRISM method requiring measured temperature cannot be claimed as

validated against the native H2-SimNet measurements.



\---



## 5. Temporal Resolution



The audited files have an effective sampling interval of:



**1.0 second (1 Hz)**



All 121 audited files were found to have consistent 1-second sampling.



For files without a stored timestamp column, the audit uses an in-memory implicit

1-second time index based on the documented 20,000-sample simulation structure.

This convention does not modify the source files and must not be interpreted as a

physical timestamp column.



### Propagation-delay implication



The 1-second sampling interval can support delay estimation when a disturbance spans

multiple samples.



However, it does not provide native sub-second timing resolution.



Physical propagation-delay localization additionally requires:



\- sensor spacing,

\- physical sensor ordering,

\- pipeline geometry,

\- disturbance propagation speed,

\- adequate signal-to-noise characteristics.



These quantities are not sufficiently verified in the current dataset extraction.



\---



## 6. Spatial / Station Configuration



The physical station arrangement is:



**UNKNOWN / UNVERIFIED**



PS1–PS12 and MFS1–MFS4 are confirmed sensor channels, but their numbering must not

be interpreted as physical station order.



The documented `down`, `center`, and `up` configurations represent different

network / withdrawal-point operating configurations. They do not establish the

physical locations of individual sensors.



Therefore, the dataset cannot currently support a verified meter-level spatial

localization claim.



\---



## 7. Propagation-Delay Localization



Cross-sensor temporal analysis may be computationally investigated.



However, physically grounded localization cannot be conclusively validated from

the current measurement configuration because verified sensor spacing, physical

sensor ordering, and propagation-speed information are unavailable.



Therefore:



**Propagation-delay localization: CONDITIONAL / NOT YET VALIDATED**



Any localization result should be reported as conditional unless the missing

geometric information is independently established.



\---



## 8. Sensor-Fault Ground Truth



Native H2-SimNet sensor-fault ground truth is:



**NOT AVAILABLE**



The labels `CompressorFault` and `CompressorDelay` refer to compressor/system

events and are not sensor-fault labels.



The H2-PRISM repository contains a separate `data/synthetic/` area for controlled

synthetic sensor-fault scenarios. These scenarios are distinct from the native

H2-SimNet dataset and must be reported separately in evaluation.



Quality states such as `GOOD`, `MISSING`, `GAP`, `STUCK`, and `INVALID` are data

quality indicators, not native H2-SimNet sensor-failure ground truth.



\---



## 9. Leak Ground Truth and Localization



H2-SimNet provides localized leak labels:



\- `leak\_G3`

\- `leak\_G4`

\- `leak\_G5`

\- `leak\_G6`



The dataset also contains single-leak, multiple-leak, and overlapping-leak

scenarios.



This provides ground truth at the simulated component level.



It does NOT establish physical leak coordinates or meter-level distances because

the corresponding verified geometry and sensor spacing are unavailable.



Therefore:



**Leak-component localization: VALIDATABLE**



**Meter-level physical localization: NOT VALIDATED**



\---



## 10. Native Anomaly Classes



The native H2-SimNet dataset supports validation of:



1\. Normal operation

2\. Leak / local restriction events

3\. Compressor faults

4\. Compressor startup delays

5\. Overlapping anomaly scenarios



Weak / strong categories are available for some scenarios through documented

filename/path conventions. They should not automatically be interpreted as a

precisely quantified physical anomaly magnitude.



Operational phases such as transient and startup conditions are available as

scenario context.



\---



## 11. Validation Boundaries



### Directly validated by H2-SimNet



\- Pressure-based anomaly behavior

\- Mass-flow-based anomaly behavior

\- Normal vs anomalous operation

\- Leak detection

\- Leak component identification at G3–G6

\- Compressor fault detection

\- Compressor startup-delay detection

\- Overlapping anomaly behavior

\- Transient scenario behavior



### Not directly validated by native H2-SimNet



\- Temperature-based inference

\- Native sensor-fault classification

\- Meter-level leak localization

\- Geometry-dependent physical localization

\- Claims requiring verified sensor spacing

\- Claims requiring verified physical station ordering



\---



## 12. Data Integrity Summary



Dataset audit results:



\- Total files: 121

\- CSV files: 60

\- Parquet files: 61

\- Pressure channels: 12

\- Mass-flow channels: 4

\- Temperature channels: 0

\- Effective sampling interval: 1.0 s

\- Missing-value files: 0

\- Duplicate-timestamp files: 0

\- Non-monotonic timestamp files: 0

\- Inconsistent-sampling files: 0

\- File-read errors: 0



\---



## 13. Interpretation Rule



For H2-PRISM development and reporting:



**The actual dataset configuration takes precedence over project-level design

assumptions.**



A capability may be implemented in the H2-PRISM architecture without being claimed

as experimentally validated if the required measurements, labels, geometry, or

ground truth are unavailable in H2-SimNet.



This distinction must be preserved in all subsequent experiments, reports,

presentations, and publications.


