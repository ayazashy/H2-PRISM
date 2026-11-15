from dataclasses import replace
from fractions import Fraction

import pytest

from h2prism.certified_evidence import DecisionStatus, diagnose
from h2prism.phase2 import COMPATIBILITY, DATA_HASH, PARQUET, checked_file, execute, reference, replay, source_case
from h2prism.data.loader import RAW_DATASET_DIR
from h2prism.phase2_evaluation import EvaluationCase, summarize
from h2prism.physical_reference import BoundStatus


@pytest.mark.parametrize("case, expected, feasible", [
    ("normal", DecisionStatus.SPECIFIC, ("NORMAL",)),
    ("leak", DecisionStatus.SPECIFIC, ("LEAK",)),
    ("overlap", DecisionStatus.AMBIGUOUS, ("NORMAL", "LEAK")),
    ("missing", DecisionStatus.UNRESOLVED, ()),
])
def test_controlled_decisions(case, expected, feasible):
    decision = diagnose(*reference(case))
    assert decision.status == expected
    assert decision.certificate.feasible == feasible


@pytest.mark.parametrize("field, value, message", [
    ("volume_m3", 0, "nonpositive"),
    ("boundary_convention", "UNSPECIFIED", "sign convention"),
    ("max_duration_s", 1, "outside the model domain"),
    ("role", "SOURCE_PHYSICAL", "unsupported"),
])
def test_invalid_physics_is_indeterminate(field, value, message):
    measurement, (normal, leak) = reference("normal")
    broken = replace(normal, adapter=replace(normal.adapter, **{field: value}))
    result = diagnose(measurement, (broken, leak))
    assert result.status == DecisionStatus.UNRESOLVED
    assert result.certificate.indeterminate == ("NORMAL",)
    assert message in result.certificate.results[0].reason


@pytest.mark.parametrize("edit", [
    {"interval": None, "status": BoundStatus.UNKNOWN},
    {"interval": (3, 2)},
    {"unit": "m3/s"},
    {"interval": (-1, 2)},
    {"domain": "different-model"},
    {"status": BoundStatus.UNSUPPORTED},
])
def test_missing_or_invalid_boundary_bounds_remain_indeterminate(edit):
    measurement, (normal, leak) = reference("leak")
    model = normal.adapter
    bound = replace(model.uncertainty.inlet, **edit)
    invalid = replace(model, uncertainty=replace(model.uncertainty, inlet=bound))
    result = diagnose(measurement, (replace(normal, adapter=invalid), leak))
    assert result.status == DecisionStatus.UNRESOLVED
    assert result.certificate.indeterminate == ("NORMAL",)


def test_missing_composition_and_evidence_cannot_default():
    measurement, (normal, _) = reference("normal")
    adapter = normal.adapter
    for invalid in (replace(adapter, network=replace(adapter.network, composition={})),
                    replace(adapter, ledger=replace(adapter.ledger, entries=adapter.ledger.entries[1:]))):
        result = diagnose(measurement, (replace(normal, adapter=invalid),))
        assert result.status == DecisionStatus.UNRESOLVED


@pytest.mark.parametrize("inlet, outlet, loss, expected", [
    (0, 0, 0, (100000, 100000, 100000)),
    (2, 2, 0, (100000, 100000, 100000)),
    (3, 2, 0, (100000, 101000, 102000)),
    (2, 2, 1, (100000, 99000, 98000)),
])
def test_storage_balance_and_density(inlet, outlet, loss, expected):
    measurement, (normal, _) = reference("normal")
    cv = normal.adapter
    uncertainty = replace(cv.uncertainty, inlet=replace(cv.uncertainty.inlet, interval=(inlet, inlet)),
                          outlet=replace(cv.uncertainty.outlet, interval=(outlet, outlet)),
                          leak=replace(cv.uncertainty.leak, interval=(loss, loss)))
    cv = replace(cv, uncertainty=uncertainty)
    for step in (1, 0.5):
        times = tuple(i * step for i in range(int(2 / step) + 1))
        values = tuple(1000 * (100 + (inlet - outlet - loss) * t) for t in times)
        m = replace(measurement, timestamps_s=times,
                    sensors=(replace(measurement.sensors[0], sampling_period_s=step),),
                    channels=(replace(measurement.channels[0], timestamps_s=times, values=values,
                                      absolute_errors=(0,) * len(times)),))
        result = diagnose(m, (replace(normal, adapter=cv),))
        assert result.certificate.feasible == ("NORMAL",)
        assert values[0] == expected[0] and values[-1] == expected[-1]
        assert cv.gas.rho(values[-1], cv.temperature_k) * cv.volume_m3 == pytest.approx(
            100 + 2 * (inlet - outlet - loss))


def test_single_sample_is_insufficient():
    measurement, models = reference("normal")
    channel = replace(measurement.channels[0], timestamps_s=(0,), values=(100000,), absolute_errors=(0,))
    decision = diagnose(replace(measurement, timestamps_s=(0,), channels=(channel,)), models)
    assert decision.status == DecisionStatus.UNRESOLVED


def test_replay_rejects_incorrectly_narrowed_enclosure(tmp_path):
    payload = execute("normal", tmp_path / "reference")
    assert replay(payload) == {"NORMAL": True, "LEAK": True}
    proof = payload["decision"]["certificate"]["results"][1]["separation"]
    proof["predicted"] = [str(Fraction(proof["predicted"][0]) - 1)] * 2
    assert replay(payload) == {"NORMAL": True, "LEAK": False}
    payload["decision"]["certificate"]["measurement"]["channels"][0]["resampled"] = True
    assert replay(payload) == {"NORMAL": False, "LEAK": False}
    with pytest.raises(FileExistsError):
        execute("normal", tmp_path / "reference")


def test_source_checksum_and_contract_no_imputation(tmp_path):
    fake = tmp_path / "export.parquet"
    fake.write_bytes(b"wrong export")
    with pytest.raises(ValueError, match="checksum"):
        checked_file(fake, DATA_HASH)
    if not (RAW_DATASET_DIR / PARQUET).exists():
        pytest.skip("Official archive is not installed")
    measurement, inventory = source_case(RAW_DATASET_DIR)
    assert measurement.timestamps_s == (0, 1, 2)
    assert len(measurement.channels) == 13
    assert all(not channel.absolute_errors for channel in measurement.channels)
    assert inventory["compatibility"] == COMPATIBILITY
    assert "INVALID_UNCERTAINTY" in measurement.issues()


def test_family_and_truth_safeguards():
    decision = diagnose(*reference("normal"))
    case = EvaluationCase("family", "controlled", decision, "NORMAL", True, True)
    assert summarize((case,))["selective_risk"] == 0
    assert summarize((replace(case, truth_verified=False),))["selective_risk"] is None
    unresolved = replace(case, decision=diagnose(*reference("missing")))
    assert summarize((unresolved,))["specific_coverage"] == 0
    assert summarize((unresolved,))["selective_risk"] is None
    assert summarize((replace(case, eligible=False),))["specific_coverage"] is None
    with pytest.raises(ValueError, match="independent"):
        summarize((case, case))
    with pytest.raises(ValueError, match="domain"):
        summarize((case, replace(case, family="other", domain="source")))



def test_sensor_removal_prevents_diagnosis():
    measurement, models = reference("normal")
    decision = diagnose(replace(measurement, channels=()), models)
    assert decision.status == DecisionStatus.UNRESOLVED
    assert decision.certificate.measurement_issues == ("MISSING_SENSOR",)
