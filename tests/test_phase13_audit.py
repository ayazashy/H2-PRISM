import numpy as np
import pandas as pd
import pytest

pytest.importorskip("xgboost")

from h2prism.phase13_audit import permute_groups
from h2prism.phase13_benchmark import CLASSES, estimators, fit


def test_equal_size_block_permutation_preserves_training_class_counts():
    table = pd.DataFrame({"Scenario_ID": ["a", "b", "c", "d"],
                          "Scenario_Family_ID": ["1", "1", "2", "2"],
                          "label_mapped": ["NORMAL", "NORMAL", "LEAK", "LEAK"]})
    result = permute_groups(table, np.random.default_rng(3))
    pd.testing.assert_series_equal(result.label_mapped.value_counts().sort_index(),
                                   table.label_mapped.value_counts().sort_index())
    assert result.groupby("Scenario_Family_ID").label_mapped.nunique().eq(1).all()


@pytest.mark.parametrize("name", ["linear_svm", "rbf_svm", "logistic"])
def test_held_out_values_do_not_enter_scaler_fit(name):
    train = pd.DataFrame({"pressure": [1., 2., 3., 4.], "label_mapped": CLASSES})
    held = pd.DataFrame({"pressure": [100000., -70000.]})
    model = estimators()[name]
    fit(model, name, train, ["pressure"])
    scaler = model.named_steps["scale"]
    assert scaler.n_samples_seen_ == len(train)
    np.testing.assert_array_equal(scaler.mean_, [2.5])
    model.predict(held)
    np.testing.assert_array_equal(scaler.mean_, [2.5])
