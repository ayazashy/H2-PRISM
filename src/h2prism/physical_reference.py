"""Exact, isothermal, well-mixed control volume with constant signed boundary rates."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction

from .certified_evidence import (
    AffineBoxAdapter, ConsistencyResult, ConsistencyStatus, HypothesisModel, MeasurementContract, Record,
)
from .data_contracts import NetworkRecord
from .gas_physics import PerfectGas


class EvidenceCategory(str, Enum):
    SOURCE = "SOURCE_CONFIRMED"
    OBSERVED = "DATASET_OBSERVED"
    LITERATURE = "LITERATURE_SUPPORTED"
    ENGINEERING = "ENGINEERING_ASSUMPTION"
    UNKNOWN = "UNKNOWN"


class BoundStatus(str, Enum):
    VERIFIED = "VERIFIED_BOUND"
    ASSUMED = "ASSUMED_BOUND"
    UNKNOWN = "UNKNOWN_BOUND"
    UNSUPPORTED = "UNSUPPORTED_BOUND"


@dataclass(frozen=True)
class Evidence(Record):
    identifier: str
    value: object
    unit: str
    reference: str
    category: EvidenceCategory
    status: str
    scope: str
    domain: str
    dependencies: tuple[str, ...] = ()
    limitations: str = ""


@dataclass(frozen=True)
class EvidenceLedger(Record):
    entries: tuple[Evidence, ...]
    version: str = "physical-evidence/1"

    def require(self, identifier: str, unit: str) -> Evidence:
        matches = [entry for entry in self.entries if entry.identifier == identifier]
        if len(matches) != 1:
            raise ValueError(f"{identifier}: expected exactly one evidence entry")
        entry = matches[0]
        if (entry.value is None or entry.category == EvidenceCategory.UNKNOWN or
                not all((entry.reference, entry.scope, entry.status, entry.domain))):
            raise ValueError(f"{identifier}: required evidence unavailable")
        if entry.unit != unit:
            raise ValueError(f"{identifier}: expected {unit}, got {entry.unit}")
        return entry


@dataclass(frozen=True)
class Bound(Record):
    interval: tuple[float, float] | None
    unit: str
    status: BoundStatus
    reference: str
    domain: str

    def exact(self, unit: str, domain: str) -> tuple[Fraction, Fraction]:
        if self.status not in (BoundStatus.VERIFIED, BoundStatus.ASSUMED) or self.interval is None:
            raise ValueError("uncertainty bound unavailable")
        if self.unit != unit or self.domain != domain or not self.reference:
            raise ValueError("uncertainty unit, domain or provenance mismatch")
        lo, hi = map(Fraction, self.interval)
        if lo > hi:
            raise ValueError("inverted uncertainty interval")
        return lo, hi


@dataclass(frozen=True)
class Uncertainty(Record):
    initial_mass: Bound
    inlet: Bound
    outlet: Bound
    leak: Bound
    clock_error: Bound
    model_discrepancy: Bound


@dataclass(frozen=True)
class ControlVolume(Record):
    network: NetworkRecord
    model_id: str
    node: str
    pressure_sensor: str
    volume_m3: float
    temperature_k: float
    gas: PerfectGas
    uncertainty: Uncertainty
    ledger: EvidenceLedger
    boundary_convention: str
    max_duration_s: float
    # Inputs are constant over the window. Inlet/outlet exclude the separate leak.
    solver: str = "EXACT_RATIONAL_AFFINE"
    role: str = "ANALYTICAL_REFERENCE"

    def check(self, model: HypothesisModel, measurement: MeasurementContract) -> ConsistencyResult:
        assumptions = model.assumptions + (
            self.role, self.model_id, self.network.network_id, self.network.source_model,
            self.solver, self.boundary_convention,
            *(f"{b.status.value} {b.reference} [{b.domain}]" for b in vars(self.uncertainty).values()),
            *(f"{e.identifier} {e.reference}" for e in self.ledger.entries),
        )
        try:
            adapter = self.affine(measurement)
        except (ValueError, TypeError, OverflowError) as exc:
            return ConsistencyResult(model.name, ConsistencyStatus.INDETERMINATE,
                                     f"PHYSICS_CONTRACT_INVALID: {exc}", assumptions)
        return adapter.check(HypothesisModel(model.name, adapter, assumptions), measurement)

    def affine(self, measurement: MeasurementContract) -> AffineBoxAdapter:
        if self.role != "ANALYTICAL_REFERENCE" or self.solver != "EXACT_RATIONAL_AFFINE":
            raise ValueError("unsupported physical adapter domain")
        if self.boundary_convention != "NONNEGATIVE_INLET_OUTLET_SEPARATE_LEAK":
            raise ValueError("unsupported boundary sign convention")
        if not self.network.composition:
            raise ValueError("missing gas composition")
        if self.network.nodes != (self.node,) or self.network.edges:
            raise ValueError("expected one lumped volume")
        if len(measurement.sensors) != 1:
            raise ValueError("expected one pressure sensor")
        sensor = measurement.sensors[0]
        if (sensor.sensor_id, sensor.network_id, sensor.location_kind, sensor.location_id,
                sensor.quantity, sensor.unit) != (
                self.pressure_sensor, self.network.network_id, "node", self.node, "pressure", "Pa"):
            raise ValueError("pressure sensor mapping or SI units mismatch")
        times = measurement.timestamps_s
        if len(times) < 2:
            raise ValueError("insufficient observation duration")
        elapsed = tuple(Fraction(t) - Fraction(times[0]) for t in times)
        if elapsed[-1] <= 0 or elapsed[-1] > Fraction(self.max_duration_s):
            raise ValueError("observation duration outside the model domain")
        volume, temp, gas_r, z = map(Fraction, (self.volume_m3, self.temperature_k, self.gas.R, self.gas.Z))
        if min(volume, temp, gas_r, z, Fraction(self.gas.mu), Fraction(self.gas.k)) <= 0:
            raise ValueError("nonpositive physical parameter")
        if Fraction(self.gas.cp) <= z * gas_r:
            raise ValueError("inconsistent gas heat capacities")
        for identifier, unit, value in (
            ("volume", "m3", volume), ("temperature", "K", temp), ("specific_gas_constant", "J/(kg K)", gas_r),
            ("compressibility", "1", z),
        ):
            if Fraction(self.ledger.require(identifier, unit).value) != value:
                raise ValueError(f"{identifier}: configuration differs from ledger")
        domain = self.model_id
        u = self.uncertainty
        if u.clock_error.exact("s", domain) != (0, 0) or u.model_discrepancy.exact("Pa", domain) != (0, 0):
            raise ValueError("reference adapter requires exact clocks and zero model discrepancy")
        bounds = (u.initial_mass.exact("kg", domain), u.inlet.exact("kg/s", domain),
                  u.outlet.exact("kg/s", domain), u.leak.exact("kg/s", domain))
        if any(lo < 0 for lo, _ in bounds):
            raise ValueError("negative mass or directional flow bound")
        if bounds[0][0] + min(0, elapsed[-1] * (bounds[1][0] - bounds[2][1] - bounds[3][1])) <= 0:
            raise ValueError("box includes nonpositive stored mass")
        # Invert PerfectGas.rho algebraically, keeping the declared numeric inputs exact.
        gain = z * gas_r * temp / volume
        rows = tuple((gain, gain * dt, -gain * dt, -gain * dt) for dt in elapsed)
        return AffineBoxAdapter(measurement.coordinates(), (0,) * len(rows), rows, bounds)
