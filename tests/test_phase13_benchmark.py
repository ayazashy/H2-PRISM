import pandas as pd
import pytest

pytest.importorskip("xgboost")

from h2prism.phase13_benchmark import CLASSES, estimators, fit, inner_validation_support, predict


def test_inner_holdouts_cannot_score_a_class_concentrated_in_one_group():
    table = pd.DataFrame({
        "label_mapped": [*CLASSES, "LEAK", "LEAK"],
        "Scenario_Family_ID": ["only", "only", "only", "only", "other", "third"],
    })
    assert inner_validation_support(table) == ["LEAK"]


def test_xgboost_maps_training_classes_and_decodes_predictions():
    labels = list(CLASSES) * 8
    table = pd.DataFrame({"signal": list(range(len(labels))), "label_mapped": labels})
    model = estimators()["xgboost"]
    with pytest.raises(ValueError, match="class support"):
        fit(model, "xgboost", table[table.label_mapped != "NORMAL"], ["signal"])
    fit(model, "xgboost", table, ["signal"])
    assert set(predict(model, "xgboost", table, ["signal"])) <= set(CLASSES)
