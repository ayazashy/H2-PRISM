from dataclasses import replace
from fractions import Fraction
import json

import pytest

from h2prism.certified_evidence import (
    AffineBoxAdapter, Channel, ConsistencyStatus, DecisionStatus, HypothesisModel,
    MeasurementContract, diagnose,
)
from h2prism.data_contracts import SensorRecord


@pytest.fixture
def measurement():
    sensor = SensorRecord("P", "analytical", "node", "N", "pressure", "Pa", 1)
    channel = Channel("P", "Pa", (0, 1, 2), "recorded column", (2, 2, 2), (0, 0, 0))
    return MeasurementContract((sensor,), (0, 1, 2), (channel,), "run", "family", "fixture", "exact")


def model(measurement, name, offset=0, slope=1, bounds=(0, 4), search=None):
    adapter = AffineBoxAdapter(measurement.coordinates(), (offset,) * 3, ((slope,),) * 3, (bounds,), search)
    return HypothesisModel(name, adapter, ("synthetic closed parameter domain",))


def test_unique_and_sound_negative_slope_exclusion(measurement):
    result = diagnose(measurement, (model(measurement, "A"), model(measurement, "B", 7, -1)))
    assert result.status == DecisionStatus.SPECIFIC
    assert result.hypothesis == "A"
    cert = result.certificate
    assert (cert.feasible, cert.excluded, cert.indeterminate) == (("A",), ("B",), ())
    assert cert.results[0].witness == ("2",)
    proof = cert.results[1].separation
    assert proof.coordinate == ("P", "Pa", 0)
    assert tuple(map(Fraction, proof.predicted)) == (3, 7)
    assert tuple(map(Fraction, proof.observed)) == (2, 2)


def test_multiple_feasible(measurement):
    result = diagnose(measurement, (model(measurement, "A"), model(measurement, "B", 2, 0)))
    assert result.status == DecisionStatus.AMBIGUOUS
    assert result.certificate.feasible == ("A", "B")
    assert result.hypothesis is None


def test_all_excluded_is_model_mismatch(measurement):
    result = diagnose(measurement, (model(measurement, "A", 9), model(measurement, "B", 8)))
    assert result.status == DecisionStatus.UNRESOLVED
    assert result.reason == "MODEL_MISMATCH"


@pytest.mark.parametrize("error, reason", [(TimeoutError, "SOLVER_TIMEOUT"), (RuntimeError, "SOLVER_FAILURE")])
def test_solver_failure_cannot_exclude(measurement, error, reason):
    def fail(_):
        raise error

    result = diagnose(measurement, (model(measurement, "A"), model(measurement, "B", search=fail)))
    assert result.status == DecisionStatus.UNRESOLVED
    assert result.certificate.indeterminate == ("B",)
    assert result.certificate.results[1].reason == reason


@pytest.mark.parametrize("candidate, reason", [(None, "NO_WITNESS_FOUND"), ((5,), "WITNESS_REJECTED"),
                                               ((1,), "WITNESS_REJECTED")])
def test_search_proposals_are_not_certificates(measurement, candidate, reason):
    result = diagnose(measurement, (model(measurement, "A", search=lambda _: candidate),))
    assert result.status == DecisionStatus.UNRESOLVED
    assert result.certificate.results[0].reason == reason


def test_marginal_overlap_does_not_establish_joint_feasibility(measurement):
    m = model(measurement, "A")
    adapter = replace(m.adapter, offset=(0, 1, 0))
    result = diagnose(measurement, (replace(m, adapter=adapter),))
    assert result.certificate.results[0].status == ConsistencyStatus.INDETERMINATE


def test_two_feasible_and_unsupported_competitor(measurement):
    result = diagnose(measurement, (model(measurement, "A"), model(measurement, "B"),
                                    HypothesisModel("C", None, ())))
    assert result.status == DecisionStatus.UNRESOLVED
    assert result.certificate.indeterminate == ("C",)
    assert result.certificate.results[2].reason == "UNSUPPORTED_HYPOTHESIS"


@pytest.mark.parametrize("edits, code", [
    ({"unit": "bar"}, "INCOMPATIBLE_UNIT"),
    ({"absolute_errors": (-1, 0, 0)}, "INVALID_UNCERTAINTY"),
    ({"absolute_errors": (float("inf"), 0, 0)}, "INVALID_UNCERTAINTY"),
    ({"values": (2, 2)}, "MEASUREMENT_GAP"),
    ({"timestamps_s": (0, 1)}, "MEASUREMENT_GAP"),
    ({"timestamps_s": (0.5, 1.5, 2.5)}, "TIMESTAMP_MISALIGNMENT"),
    ({"timestamps_s": (0, 1, 3)}, "IRREGULAR_SAMPLING"),
    ({"timestamps_s": (0, 0, 2)}, "IRREGULAR_SAMPLING"),
    ({"timestamp_source": ""}, "MISSING_TIMESTAMP_PROVENANCE"),
    ({"resampled": True}, "RESAMPLED_MEASUREMENT"),
])
def test_invalid_measurement_prevents_specific(measurement, edits, code):
    invalid = replace(measurement, channels=(replace(measurement.channels[0], **edits),))
    result = diagnose(invalid, (model(measurement, "A"),))
    assert result.status == DecisionStatus.UNRESOLVED
    assert code in result.certificate.measurement_issues


def test_missing_sensor(measurement):
    result = diagnose(replace(measurement, channels=()), (model(measurement, "A"),))
    assert result.status == DecisionStatus.UNRESOLVED
    assert result.certificate.measurement_issues == ("MISSING_SENSOR",)


def test_deterministic_serialization_and_closed_boundary(measurement):
    models = (model(measurement, "A", bounds=(2, 2)), model(measurement, "B", 9))
    result = diagnose(measurement, models)
    assert result.to_json() == diagnose(measurement, models).to_json()
    payload = json.loads(result.to_json())
    assert payload["status"] == "SPECIFIC"
    assert payload["certificate"]["results"][0]["witness"] == ["2"]
    assert payload["certificate"]["measurement"]["independence_group"] == "family"


def test_alignment_is_exact_even_with_cadence_tolerance(measurement):
    shifted = replace(measurement.channels[0], timestamps_s=(0.125, 1.125, 2.125))
    invalid = replace(measurement, cadence_tolerance_s=0.25, channels=(shifted,))
    assert invalid.issues() == ("TIMESTAMP_MISALIGNMENT",)


def test_derived_timestamp_provenance_is_preserved(measurement):
    channel = replace(measurement.channels[0], timestamp_source="audit-derived index, fixture schedule v1")
    derived = replace(measurement, channels=(channel,))
    result = diagnose(derived, (model(derived, "A"),))
    payload = json.loads(result.to_json())
    assert payload["certificate"]["measurement"]["channels"][0]["timestamp_source"] == channel.timestamp_source


def test_gap_nan_serializes_as_invalid_evidence(measurement):
    invalid = replace(measurement, channels=(replace(measurement.channels[0], values=(2, float("nan"), 2)),))
    result = diagnose(invalid, (model(measurement, "A"),))
    cert = json.loads(result.to_json())["certificate"]
    assert cert["measurement_issues"] == ["MEASUREMENT_GAP"]
    assert cert["measurement"]["channels"][0]["values"][1] == "nan"


def test_serialized_affine_evidence_can_be_replayed(measurement):
    result = diagnose(measurement, (model(measurement, "A"), model(measurement, "B", 7, -1)))
    records = json.loads(result.to_json())["certificate"]["results"]
    for record in records:
        evidence = record["affine_model"]
        adapter = AffineBoxAdapter(
            measurement.coordinates(),
            tuple(map(Fraction, evidence["offset"])),
            tuple(tuple(map(Fraction, row)) for row in evidence["matrix"]),
            tuple(tuple(map(Fraction, bound)) for bound in evidence["bounds"]),
            None if record["witness"] is None else lambda _: tuple(map(Fraction, record["witness"])),
        )
        replay = diagnose(measurement, (HypothesisModel(record["hypothesis"], adapter, ()),))
        actual = replay.certificate.results[0]
        assert actual.status == record["status"]
        assert actual.reason == record["reason"]
