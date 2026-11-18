### TAB_C04 — Sensor-group identifiability of outlet pairs

Native contrasts are the largest absolute template difference at the best shift within ±1 s, reported separately in MPa and kg/s. B3 combines normalized channels with equal weights (frozen scaling: pre-1000 s RMS of the SID 213 control per channel).

| pair | group | channels | pressure_contrast_MPa | flow_contrast_kg_s | b3_combined | pressure_share_of_b3 | flow_share_of_b3 | relative_change_vs_all | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SID213–SID312 | all | PS1,PS2,PS3,PS4,PS5,PS6,PS7,PS8,PS9,PS10,MFS1,MFS2,MFS3 | 0.00114843 | 0.691261 | 0.0404991 | 2.99561e-06 | 0.999997 | 0 | flow-separated: a branch meter sees one outlet but not the other |
| SID213–SID312 | pressure | PS1,PS2,PS3,PS4,PS5,PS6,PS7,PS8,PS9,PS10 | 0.00114843 | — | 7.99208e-05 | 1 | 0 | -0.998027 | pressure-only view: 1.15 kPa largest contrast |
| SID213–SID312 | flow | MFS1,MFS2,MFS3 | — | 0.691261 | 0.0843055 | 0 | 1 | 1.08166 | flow-separated: a branch meter sees one outlet but not the other |
| SID213–SID312 | omit_MFS3 | PS1,PS2,PS3,PS4,PS5,PS6,PS7,PS8,PS9,PS10,MFS1,MFS2 | 0.00114843 | 0.646715 | 0.0300934 | 5.87755e-06 | 0.999994 | -0.256937 | flow-separated: a branch meter sees one outlet but not the other |
| SID213–SID215 | all | PS1,PS2,PS3,PS4,PS5,PS6,PS7,PS8,PS9,PS10,MFS1,MFS2,MFS3 | 0.0054739 | 0.691292 | 0.0284326 | 0.000135461 | 0.999865 | 0 | flow-separated: a branch meter sees one outlet but not the other |
| SID213–SID215 | pressure | PS1,PS2,PS3,PS4,PS5,PS6,PS7,PS8,PS9,PS10 | 0.0054739 | — | 0.000377308 | 1 | 0 | -0.98673 | pressure-only view: 5.47 kPa largest contrast |
| SID213–SID215 | flow | MFS1,MFS2,MFS3 | — | 0.691292 | 0.0591831 | 0 | 1 | 1.08153 | flow-separated: a branch meter sees one outlet but not the other |
| SID213–SID215 | omit_MFS3 | PS1,PS2,PS3,PS4,PS5,PS6,PS7,PS8,PS9,PS10,MFS1,MFS2 | 0.0054739 | 0.000301324 | 0.00212697 | 0.0262234 | 0.973777 | -0.925193 | flow nearly blind (0.0003 kg/s); contrast carried by 5.47 kPa of pressure |
| SID213–ALT | all | PS1,PS2,PS3,PS4,PS5,PS6,PS7,PS8,PS9,PS10,MFS1,MFS2,MFS3 | 2.45437e-06 | 0.000683636 | 2.7612e-05 | 1.99239e-05 | 0.99998 | 0 | same outlet; differs only through reservoir overlay |
| SID213–ALT | pressure | PS1,PS2,PS3,PS4,PS5,PS6,PS7,PS8,PS9,PS10 | 2.45437e-06 | — | 1.40526e-07 | 1 | 0 | -0.994911 | same outlet; differs only through reservoir overlay |
| SID213–ALT | flow | MFS1,MFS2,MFS3 | — | 0.000683636 | 5.74783e-05 | 0 | 1 | 1.08165 | same outlet; differs only through reservoir overlay |
| SID213–ALT | omit_MFS3 | PS1,PS2,PS3,PS4,PS5,PS6,PS7,PS8,PS9,PS10,MFS1,MFS2 | 2.45437e-06 | 1.48911e-06 | 7.94778e-07 | 0.0260519 | 0.973948 | -0.971216 | same outlet; differs only through reservoir overlay |
| SID312–SID215 | all | PS1,PS2,PS3,PS4,PS5,PS6,PS7,PS8,PS9,PS10,MFS1,MFS2,MFS3 | 0.00479682 | 0.646772 | 0.029388 | 0.000121032 | 0.999879 | 0 | flow-separated: a branch meter sees one outlet but not the other |
| SID312–SID215 | pressure | PS1,PS2,PS3,PS4,PS5,PS6,PS7,PS8,PS9,PS10 | 0.00479682 | — | 0.000347035 | 1 | 0 | -0.988191 | pressure-only view: 4.8 kPa largest contrast |
| SID312–SID215 | flow | MFS1,MFS2,MFS3 | — | 0.646772 | 0.0611723 | 0 | 1 | 1.08154 | flow-separated: a branch meter sees one outlet but not the other |
| SID312–SID215 | omit_MFS3 | PS1,PS2,PS3,PS4,PS5,PS6,PS7,PS8,PS9,PS10,MFS1,MFS2 | 0.00479682 | 0.646772 | 0.030588 | 0.000121032 | 0.999879 | 0.040833 | flow-separated: a branch meter sees one outlet but not the other |
| SID312–ALT | all | PS1,PS2,PS3,PS4,PS5,PS6,PS7,PS8,PS9,PS10,MFS1,MFS2,MFS3 | 0.00117315 | 0.691914 | 0.0405422 | 3.32377e-06 | 0.999997 | 0 | flow-separated: a branch meter sees one outlet but not the other |
| SID312–ALT | pressure | PS1,PS2,PS3,PS4,PS5,PS6,PS7,PS8,PS9,PS10 | 0.00117315 | — | 8.34522e-05 | 1 | 0 | -0.997942 | pressure-only view: 1.17 kPa largest contrast |
| SID312–ALT | flow | MFS1,MFS2,MFS3 | — | 0.691914 | 0.0843952 | 0 | 1 | 1.08166 | flow-separated: a branch meter sees one outlet but not the other |
| SID312–ALT | omit_MFS3 | PS1,PS2,PS3,PS4,PS5,PS6,PS7,PS8,PS9,PS10,MFS1,MFS2 | 0.00117315 | 0.646769 | 0.0306034 | 6.19664e-06 | 0.999994 | -0.245148 | flow-separated: a branch meter sees one outlet but not the other |
| SID215–ALT | all | PS1,PS2,PS3,PS4,PS5,PS6,PS7,PS8,PS9,PS10,MFS1,MFS2,MFS3 | 0.00552328 | 0.691918 | 0.0279897 | 0.000148426 | 0.999852 | 0 | flow-separated: a branch meter sees one outlet but not the other |
| SID215–ALT | pressure | PS1,PS2,PS3,PS4,PS5,PS6,PS7,PS8,PS9,PS10 | 0.00552328 | — | 0.000388424 | 1 | 0 | -0.986123 | pressure-only view: 5.52 kPa largest contrast |
| SID215–ALT | flow | MFS1,MFS2,MFS3 | — | 0.691918 | 0.058261 | 0 | 1 | 1.08151 | flow-separated: a branch meter sees one outlet but not the other |
| SID215–ALT | omit_MFS3 | PS1,PS2,PS3,PS4,PS5,PS6,PS7,PS8,PS9,PS10,MFS1,MFS2 | 0.00552328 | 0.000312253 | 0.00214569 | 0.0273086 | 0.972691 | -0.92334 | flow nearly blind (0.00031 kg/s); contrast carried by 5.52 kPa of pressure |
