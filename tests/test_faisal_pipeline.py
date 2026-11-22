import numpy as np
import pandas as pd

from h2prism.evaluation import (
    TARGET_CLASSES,
    apply_diagnostic_policy,
    compute_empirical_support,
    fit_calibrator,
    probability_metrics,
    threshold_for_coverage,
)
from h2prism.simnet_experiments import DEFAULT_CONFIG, _read_config
from h2prism.simnet_windows import SENSOR_CHANNELS, build_window_dataset, map_target_class


def _scenario_metadata(
    scenario_id,
    family_id,
    raw_label,
    onset=np.nan,
    offset=np.nan,
    eligible=True,
    reason="",
):
    return pd.Series(
        {
            "Scenario_ID": scenario_id,
            "Scenario_Family_ID": family_id,
            "event_label_raw": raw_label,
            "event_onset_s": onset,
            "event_offset_s": offset,
            "eligible_primary": eligible,
            "exclusion_reason": reason,
            "phase": "Steady State",
            "topology": "Center",
        }
    )


def _sensor_data(n_rows=120):
    values = np.arange(n_rows, dtype=float)
    data = {"Timestamp": values}
    for channel_index, channel in enumerate(SENSOR_CHANNELS):
        data[channel] = values * (channel_index + 1) / 100.0
    return pd.DataFrame(data)


def test_accepted_frozen_config_is_supported():
    config = _read_config(DEFAULT_CONFIG)
    assert config["config_version"] == "1.0.2"


def test_target_mapping_and_event_boundary_windows():
    assert map_target_class("Leak_G3_G4") == "LEAK"
    assert map_target_class("CompressorFault") == "COMPRESSOR_FAULT"
    normal = (_scenario_metadata("normal", "normal-family", "NORMAL"), _sensor_data())
    leak = (
        _scenario_metadata("leak", "leak-family", "Leak_G4", 20.0, 119.0),
        _sensor_data(),
    )

    manifest, features = build_window_dataset([normal, leak], window_size=60, stride=60)

    leak_windows = manifest[manifest["Scenario_ID"] == "leak"].set_index("window_id")
    assert list(leak_windows["boundary_status"]) == [
        "BOUNDARY_CROSSING",
        "DURING_EVENT",
    ]
    assert not leak_windows.iloc[0]["eligible_primary"]
    assert leak_windows.iloc[1]["eligible_primary"]
    assert len(features) == 3
    assert "topology" in features.columns
    assert not any(
        column in features.columns
        for column in ("phase", "Timestamp", "event_onset_s", "event_offset_s")
    )


def test_compound_windows_are_recorded_but_excluded():
    compound = (
        _scenario_metadata(
            "compound",
            "compound-family",
            "Combined_CompressorFault_LeakG5",
            25.0,
            119.0,
            eligible=False,
            reason="COMPOUND_FAULT_RESERVED_FOR_SECONDARY_MULTILABEL",
        ),
        _sensor_data(),
    )
    manifest, features = build_window_dataset([compound], window_size=60, stride=60)
    assert len(manifest) == 2
    assert not manifest["eligible_primary"].any()
    assert features.empty


def test_incomplete_tail_is_counted_but_not_used():
    metadata = _scenario_metadata("normal-tail", "normal-family", "NORMAL")
    manifest, features = build_window_dataset(
        [(metadata, _sensor_data(n_rows=125))],
        window_size=60,
        stride=60,
    )
    assert len(manifest) == 2
    assert manifest["tail_samples_omitted"].eq(5).all()
    assert len(features) == 2


def test_empirical_support_excludes_entire_query_family():
    reference = pd.DataFrame(
        {
            "window_id": ["a1w0", "a2w0", "b1w0", "c1w0"],
            "Scenario_ID": ["a1", "a2", "b1", "c1"],
            "Scenario_Family_ID": ["A", "A", "B", "C"],
            "label_mapped": ["NORMAL", "NORMAL", "LEAK", "COMPRESSOR_FAULT"],
            "PS1__mean": [0.0, 0.1, 5.0, 10.0],
        }
    )
    query = pd.DataFrame(
        {
            "window_id": ["a3w0"],
            "Scenario_ID": ["a3"],
            "Scenario_Family_ID": ["A"],
            "label_mapped": ["NORMAL"],
            "PS1__mean": [0.05],
        }
    )
    support = compute_empirical_support(query, reference, k=25)
    assert bool(support.iloc[0]["query_family_excluded"])
    assert int(support.iloc[0]["support_n_neighbors"]) == 2
    assert int(support.iloc[0]["support_n_families"]) == 2
    assert "NORMAL" in support.iloc[0]["support_missing_classes"]

    permuted_reference = reference.iloc[[3, 1, 2, 0]].reset_index(drop=True)
    permuted_query = query.iloc[::-1].reset_index(drop=True)
    permuted_support = compute_empirical_support(
        permuted_query, permuted_reference, k=25
    )
    assert np.isclose(support.iloc[0]["D"], permuted_support.iloc[0]["D"])


def test_query_family_is_excluded_from_D_scaler_as_well_as_neighbors():
    reference = pd.DataFrame(
        {
            "window_id": ["a1w0", "a2w0", "b1w0", "c1w0"],
            "Scenario_ID": ["a1", "a2", "b1", "c1"],
            "Scenario_Family_ID": ["A", "A", "B", "C"],
            "label_mapped": ["NORMAL", "NORMAL", "LEAK", "COMPRESSOR_FAULT"],
            "PS1__mean": [-10000.0, 10000.0, 10.0, 0.0],
            "PS2__mean": [0.1, 0.1, 0.0, 1.0],
        }
    )
    query = pd.DataFrame(
        {
            "window_id": ["a3w0"],
            "Scenario_ID": ["a3"],
            "Scenario_Family_ID": ["A"],
            "label_mapped": ["NORMAL"],
            "PS1__mean": [0.0],
            "PS2__mean": [0.1],
        }
    )

    support = compute_empirical_support(query, reference, k=1)
    assert support.iloc[0]["q_COMPRESSOR_FAULT"] == 1.0
    assert support.iloc[0]["q_LEAK"] == 0.0

    changed_query_family = reference.copy()
    changed_query_family.loc[:1, "PS1__mean"] = [-1e9, 1e9]
    changed_support = compute_empirical_support(query, changed_query_family, k=1)
    assert np.allclose(
        support[[f"q_{name}" for name in TARGET_CLASSES]].to_numpy(),
        changed_support[[f"q_{name}" for name in TARGET_CLASSES]].to_numpy(),
    )


def test_calibrators_return_normalized_probabilities_and_metrics():
    labels = np.asarray(list(TARGET_CLASSES) * 8)
    probabilities = np.full((len(labels), len(TARGET_CLASSES)), 0.05)
    for index, label in enumerate(labels):
        probabilities[index, TARGET_CLASSES.index(label)] = 0.85
    calibrator = fit_calibrator("sigmoid", probabilities, labels)
    calibrated = calibrator.transform(probabilities)
    assert np.allclose(calibrated.sum(axis=1), 1.0)
    assert probability_metrics(calibrated, labels)["log_loss"] >= 0.0


def test_coverage_threshold_and_three_policy_outcomes():
    assert threshold_for_coverage([0.1, 0.5, 0.9, 0.7], 0.5) == 0.7
    probabilities = np.asarray(
        [
            [0.90, 0.04, 0.03, 0.03],
            [0.50, 0.45, 0.03, 0.02],
            [0.25, 0.25, 0.25, 0.25],
        ]
    )
    support = pd.DataFrame(
        {
            "q_NORMAL": [0.90, 0.50, 0.25],
            "q_LEAK": [0.04, 0.50, 0.25],
            "q_COMPRESSOR_FAULT": [0.03, 0.00, 0.25],
            "q_COMPRESSOR_DELAY": [0.03, 0.00, 0.25],
            "D": [0.86, 0.00, 0.00],
            "support_n_neighbors": [25, 25, 25],
            "support_n_families": [5, 5, 5],
            "support_missing_classes": ["", "COMPRESSOR_FAULT;COMPRESSOR_DELAY", ""],
            "query_family_excluded": [True, True, True],
        }
    )
    results = apply_diagnostic_policy(
        probabilities,
        support,
        combined_scores=[0.95, 0.4, 0.25],
        specific_threshold=0.8,
    )
    assert list(results["policy_outcome"]) == [
        "SPECIFIC",
        "AMBIGUITY_SET",
        "UNRESOLVED",
    ]
    assert results.iloc[1]["ambiguity_set"] == "NORMAL;LEAK"
    assert results.iloc[2]["reason_code"] == "INSUFFICIENT_CONFIDENCE_AND_SUPPORT"
