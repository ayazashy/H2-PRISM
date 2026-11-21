# H₂-PRISM extended exploratory benchmark

All models used the frozen 51 historical-release scenario windows, 64 original features and the same eight component-held-out folds. Each fit used 42–48 training scenarios. Scoring covered 39 held-out LEAK annotations only. Two folds containing the other classes lacked one or more training classes and were excluded. The prior logistic and random forest predictions replayed exactly, by scenario ID.

| Model | Full | Pressure-only | Flow-only | Alternate settings, full |
|---|---:|---:|---:|---:|
| Logistic regression | 30/39 | 27/39 | 25/39 | — |
| Random forest | 36/39 | 36/39 | 37/39 | — |
| XGBoost | 39/39 | 39/39 | 39/39 | 39/39 |
| Linear SVM | 33/39 | 26/39 | 23/39 | 24/39 |
| RBF SVM | 23/39 | 20/39 | 23/39 | 0/39 |

XGBoost predicted LEAK for every scored case under every tested feature subset and both settings. An always-LEAK rule also scores 39/39 on these units. Linear SVM, RBF SVM and logistic regression assigned 6, 16 and 9 LEAK cases to NORMAL, respectively. Random forest assigned three to COMPRESSOR_DELAY. Full-feature fold recall ranged from 66.7% to 100% for linear SVM, 33.3% to 100% for RBF SVM, 55.6% to 100% for logistic regression, and 50% to 100% for random forest. The paired scenario table identifies where the errors occurred. Batch timing was recorded for each fit and prediction call and includes local Python overhead.

Every eligible outer training split had only LEAK support in valid component-held-out inner validation. Settings were predefined, and no model or parameter was selected on the test scores. The XGBoost settings use shallow trees and explicit L2 regularization; the two settings vary tree count, depth, learning rate, minimum child weight and L2 regularization jointly. The SVMs use fold-fitted standardization and balanced class weights. Alternate C and RBF gamma quantify sensitivity jointly. The runs provide no isolated estimate of parameter effects or validated feature importance.

## Discussion

These are exploratory annotation-recall results, not multiclass accuracy. The test design cannot measure false alarms, performance on other classes, macro F1, balanced accuracy, calibration or selective risk. The archive supplies event onset for the features and may contain unverified dependencies beyond the conservative split map. Pressure/flow ablations are descriptive on these same scenarios. The class-support restriction precludes a defensible model winner. Classifier outputs supply no qualified hypothesis exclusions, and H₂-PRISM remains INDETERMINATE / UNRESOLVED / L0.

## Reproduction

From the repository in PowerShell, with the existing environment and XGBoost 3.2.0 available:

```powershell
$env:PYTHONPATH = 'src'
.\.venv\Scripts\python.exe -m h2prism.phase13_benchmark '<previous-ml-output>' '<fresh-output-directory>'
```

The JSON records input file hashes, software versions, settings, exact scenario IDs and train/test class counts by fold. The serialized models fit all 51 windows for research replay. The held-out scores come from separate fold fits.
