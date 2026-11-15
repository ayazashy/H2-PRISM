"""Phase 1 consistency engine. Certification is conditional on the declared model."""
from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from enum import Enum
from fractions import Fraction
from typing import Optional, Protocol

from .data_contracts import SensorRecord, UNITS


def _json_value(value):
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    return value


class Record:
    def to_json(self) -> str:
        return json.dumps(_json_value(asdict(self)), sort_keys=True, allow_nan=False)


class ConsistencyStatus(str, Enum):
    FEASIBLE = "FEASIBLE"
    EXCLUDED = "EXCLUDED"
    INDETERMINATE = "INDETERMINATE"


class DecisionStatus(str, Enum):
    SPECIFIC = "SPECIFIC"
    AMBIGUOUS = "AMBIGUOUS"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class Channel:
    sensor_id: str
    unit: str
    timestamps_s: tuple[float, ...]
    timestamp_source: str
    values: tuple[float, ...]
    absolute_errors: tuple[float, ...]
    resampled: bool = False


@dataclass(frozen=True)
class MeasurementContract(Record):
    sensors: tuple[SensorRecord, ...]
    timestamps_s: tuple[float, ...]
    channels: tuple[Channel, ...]
    run_id: str
    independence_group: str
    source_id: str
    uncertainty_basis: str
    cadence_tolerance_s: float = 0.0

    def issues(self) -> tuple[str, ...]:
        issues = set()
        if not all((self.run_id, self.independence_group, self.source_id, self.uncertainty_basis)):
            issues.add("MISSING_PROVENANCE")
        grid = self.timestamps_s
        tolerance = self.cadence_tolerance_s
        if (not grid or not all(map(math.isfinite, grid)) or
                any(b <= a for a, b in zip(grid, grid[1:])) or
                not math.isfinite(tolerance) or tolerance < 0):
            return tuple(sorted(issues | {"INVALID_TIME_GRID"}))
        sensors = {s.sensor_id: s for s in self.sensors}
        channels = {c.sensor_id: c for c in self.channels}
        if not sensors or sensors.keys() - channels.keys():
            issues.add("MISSING_SENSOR")
        if len(sensors) != len(self.sensors) or len(channels) != len(self.channels):
            issues.add("DUPLICATE_SENSOR")
        if len({s.network_id for s in self.sensors}) > 1:
            issues.add("MIXED_NETWORK")
        for key, sensor in sensors.items():
            channel = channels.get(key)
            if channel is None:
                continue
            if channel.unit != sensor.unit or sensor.unit not in UNITS.get(sensor.quantity, ()):
                issues.add("INCOMPATIBLE_UNIT")
            if sensor.availability == "UNAVAILABLE":
                issues.add("MISSING_SENSOR")
            if not channel.timestamp_source.strip():
                issues.add("MISSING_TIMESTAMP_PROVENANCE")
            if channel.resampled:
                issues.add("RESAMPLED_MEASUREMENT")
            if (len(channel.timestamps_s) != len(grid) or len(channel.values) != len(grid) or
                    not all(map(math.isfinite, channel.values))):
                issues.add("MEASUREMENT_GAP")
            times = channel.timestamps_s
            if (not all(map(math.isfinite, times)) or
                    any(t != g for t, g in zip(times, grid))):
                issues.add("TIMESTAMP_MISALIGNMENT")
            period = sensor.sampling_period_s
            if (not math.isfinite(period) or period <= 0 or tolerance >= period / 2 or
                    any(b <= a or abs((b - a) - period) > tolerance
                        for clock in (grid, times) for a, b in zip(clock, clock[1:]))):
                issues.add("IRREGULAR_SAMPLING")
            if (len(channel.absolute_errors) != len(grid) or
                    any(not math.isfinite(e) or e < 0 for e in channel.absolute_errors)):
                issues.add("INVALID_UNCERTAINTY")
        return tuple(sorted(issues))

    def coordinates(self) -> tuple[tuple[str, str, float], ...]:
        return tuple((s.sensor_id, s.unit, t) for s in self.sensors for t in self.timestamps_s)

    def intervals(self) -> tuple[tuple[Fraction, Fraction], ...]:
        channels = {channel.sensor_id: channel for channel in self.channels}
        return tuple((Fraction(v) - Fraction(e), Fraction(v) + Fraction(e))
                     for sensor in self.sensors
                     for v, e in zip(channels[sensor.sensor_id].values,
                                     channels[sensor.sensor_id].absolute_errors))


@dataclass(frozen=True)
class ConsistencyResult(Record):
    hypothesis: str
    status: ConsistencyStatus
    reason: str
    assumptions: tuple[str, ...]
    # Exact rational parameters or a disjoint interval on a declared coordinate.
    witness: Optional[tuple[str, ...]] = None
    separation: Optional[IntervalSeparation] = None
    affine_model: Optional[AffineModelRecord] = None


@dataclass(frozen=True)
class IntervalSeparation(Record):
    coordinate: tuple[str, str, float]
    predicted: tuple[str, str]
    observed: tuple[str, str]


@dataclass(frozen=True)
class AffineModelRecord(Record):
    """Exact coefficients in measurement coordinate order for certificate replay."""

    offset: tuple[str, ...]
    matrix: tuple[tuple[str, ...], ...]
    bounds: tuple[tuple[str, str], ...]


class PhysicsAdapter(Protocol):
    """Trusted verifier for a declared model and admissible domain.

    The adapter must validate witnesses and prove the prediction enclosure.
    The engine checks result structure and interval separation.
    """

    def check(self, model: HypothesisModel, measurement: MeasurementContract) -> ConsistencyResult:
        ...


@dataclass(frozen=True)
class HypothesisModel:
    name: str
    adapter: Optional[PhysicsAdapter]
    assumptions: tuple[str, ...]


@dataclass(frozen=True)
class DistinguishabilityCertificate(Record):
    feasible: tuple[str, ...]
    excluded: tuple[str, ...]
    indeterminate: tuple[str, ...]
    results: tuple[ConsistencyResult, ...]
    measurement: MeasurementContract
    measurement_issues: tuple[str, ...]


@dataclass(frozen=True)
class DiagnosticDecision(Record):
    status: DecisionStatus
    reason: str
    certificate: DistinguishabilityCertificate
    hypothesis: Optional[str] = None


class WitnessSearch(Protocol):
    def __call__(self, measurement: MeasurementContract) -> Optional[tuple[float, ...]]:
        ...


@dataclass(frozen=True)
class AffineBoxAdapter:
    """Exact reference adapter for y = offset + A theta on a closed parameter box.

    Numeric inputs are interpreted as their exact Python numeric values. The box
    and affine map must cover the entire declared hypothesis for exclusion to apply.
    A supplied search proposes candidates only. Its output is checked independently.
    """

    coordinates: tuple[tuple[str, str, float], ...]
    offset: tuple[float, ...]
    matrix: tuple[tuple[float, ...], ...]
    bounds: tuple[tuple[float, float], ...]
    search: Optional[WitnessSearch] = None

    def check(self, model: HypothesisModel, measurement: MeasurementContract) -> ConsistencyResult:
        assumptions = model.assumptions + ("EXACT_AFFINE_MAP_ON_CLOSED_PARAMETER_BOX",)
        unknown = ConsistencyStatus.INDETERMINATE
        if (self.coordinates != measurement.coordinates() or
                len(self.offset) != len(self.coordinates) or len(self.matrix) != len(self.coordinates) or
                any(len(row) != len(self.bounds) for row in self.matrix) or
                any(lo > hi for lo, hi in self.bounds)):
            return ConsistencyResult(model.name, unknown, "INVALID_MODEL_CONTRACT", assumptions)
        try:
            offset = tuple(map(Fraction, self.offset))
            matrix = tuple(tuple(map(Fraction, row)) for row in self.matrix)
            bounds = tuple((Fraction(lo), Fraction(hi)) for lo, hi in self.bounds)
        except (ValueError, TypeError, OverflowError):
            return ConsistencyResult(model.name, unknown, "INVALID_MODEL_CONTRACT", assumptions)
        model_record = AffineModelRecord(
            tuple(map(str, offset)), tuple(tuple(map(str, row)) for row in matrix),
            tuple((str(lo), str(hi)) for lo, hi in bounds),
        )
        observations = measurement.intervals()
        for coordinate, base, row, observed in zip(self.coordinates, offset, matrix, observations):
            terms = [(a * lo, a * hi) for a, (lo, hi) in zip(row, bounds)]
            lower = base + sum(min(term) for term in terms)
            upper = base + sum(max(term) for term in terms)
            lo, hi = observed
            if upper < lo or lower > hi:
                proof = IntervalSeparation(coordinate, (str(lower), str(upper)), (str(lo), str(hi)))
                return ConsistencyResult(model.name, ConsistencyStatus.EXCLUDED,
                                         "DISJOINT_REACHABLE_INTERVAL", assumptions, separation=proof,
                                         affine_model=model_record)
        try:
            proposed = (tuple((lo + hi) / 2 for lo, hi in bounds) if self.search is None
                        else self.search(measurement))
            if proposed is None:
                return ConsistencyResult(model.name, unknown, "NO_WITNESS_FOUND", assumptions)
            witness = tuple(map(Fraction, proposed))
        except TimeoutError:
            return ConsistencyResult(model.name, unknown, "SOLVER_TIMEOUT", assumptions)
        except (ArithmeticError, RuntimeError, TypeError, ValueError):
            return ConsistencyResult(model.name, unknown, "SOLVER_FAILURE", assumptions)
        if (len(witness) == len(bounds) and
                all(lo <= value <= hi for value, (lo, hi) in zip(witness, bounds)) and
                all(lo <= base + sum(a * value for a, value in zip(row, witness)) <= hi
                    for base, row, (lo, hi) in zip(offset, matrix, observations))):
            return ConsistencyResult(model.name, ConsistencyStatus.FEASIBLE,
                                     "VERIFIED_WITNESS", assumptions, tuple(map(str, witness)),
                                     affine_model=model_record)
        return ConsistencyResult(model.name, unknown, "WITNESS_REJECTED", assumptions)


def _valid_evidence(result: ConsistencyResult, measurement: MeasurementContract) -> bool:
    if result.status is ConsistencyStatus.FEASIBLE:
        return result.witness is not None and result.separation is None
    if result.status is ConsistencyStatus.INDETERMINATE:
        return result.witness is None and result.separation is None
    proof = result.separation
    if result.witness is not None or proof is None or proof.coordinate not in measurement.coordinates():
        return False
    position = measurement.coordinates().index(proof.coordinate)
    lo, hi = measurement.intervals()[position]
    try:
        lower, upper = map(Fraction, proof.predicted)
        return tuple(map(Fraction, proof.observed)) == (lo, hi) and lower <= upper and (
            upper < lo or lower > hi
        )
    except (TypeError, ValueError, ZeroDivisionError):
        return False


def diagnose(measurement: MeasurementContract, models: tuple[HypothesisModel, ...]) -> DiagnosticDecision:
    names = [model.name for model in models]
    if not names or not all(names) or len(set(names)) != len(names):
        raise ValueError("Declare a nonempty hypothesis set with unique nonempty names")
    issues = measurement.issues()
    results = []
    for model in models:
        if issues or model.adapter is None:
            reason = "INVALID_MEASUREMENT" if issues else "UNSUPPORTED_HYPOTHESIS"
            result = ConsistencyResult(model.name, ConsistencyStatus.INDETERMINATE, reason, model.assumptions)
        else:
            try:
                result = model.adapter.check(model, measurement)
            except TimeoutError:
                result = ConsistencyResult(model.name, ConsistencyStatus.INDETERMINATE,
                                           "SOLVER_TIMEOUT", model.assumptions)
            except (ArithmeticError, RuntimeError):
                result = ConsistencyResult(model.name, ConsistencyStatus.INDETERMINATE,
                                           "SOLVER_FAILURE", model.assumptions)
            if (not isinstance(result, ConsistencyResult) or result.hypothesis != model.name or
                    not isinstance(result.status, ConsistencyStatus) or not _valid_evidence(result, measurement)):
                result = ConsistencyResult(model.name, ConsistencyStatus.INDETERMINATE,
                                           "INVALID_ADAPTER_RESULT", model.assumptions)
        results.append(result)
    feasible, excluded, indeterminate = (
        tuple(r.hypothesis for r in results if r.status is status) for status in ConsistencyStatus
    )
    certificate = DistinguishabilityCertificate(feasible, excluded, indeterminate, tuple(results),
                                                measurement, issues)
    if issues or indeterminate or not feasible:
        reason = ("INVALID_MEASUREMENT" if issues else
                  "INDETERMINATE_HYPOTHESES" if indeterminate else "MODEL_MISMATCH")
        return DiagnosticDecision(DecisionStatus.UNRESOLVED, reason, certificate)
    if len(feasible) == 1:
        return DiagnosticDecision(DecisionStatus.SPECIFIC, "UNIQUE_FEASIBLE", certificate, feasible[0])
    return DiagnosticDecision(DecisionStatus.AMBIGUOUS, "MULTIPLE_FEASIBLE", certificate)
