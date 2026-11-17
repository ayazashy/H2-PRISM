import numpy as np
import pandas as pd

from h2prism.phase13_ml import evaluation_metrics


def test_single_class_holdout_does_not_report_multiclass_performance():
    truth = pd.Series(["LEAK", "LEAK"])
    prediction = pd.Series(["LEAK", "NORMAL"])
    result = evaluation_metrics(truth, prediction, np.full((2, 4), 0.25))
    assert result["restricted_accuracy"] == 0.5
    assert result["balanced_accuracy"] is None
    assert result["classification"] is None
    assert result["test_support"]["NORMAL"] == 0
