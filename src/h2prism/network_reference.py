"""Exact discrete conservation and choked-discharge benchmark in SI units."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as Q
from math import isqrt
from typing import Optional

from .certified_evidence import (
    ConsistencyResult, ConsistencyStatus as Status, DiagnosticDecision, DecisionStatus,
    HypothesisModel, IntervalSeparation, MeasurementContract, Record, diagnose,
)
from .data_contracts import NetworkRecord, SensorRecord
from .gas_physics import PerfectGas
from .physical_reference import Bound


@dataclass(frozen=True)
class Storage(Record):
    node: str
    volume_m3: int
    initial_mass: Bound
    # Positive net external injection. Negative values are withdrawals.
    external_rate: Bound


@dataclass(frozen=True)
class Transfer(Record):
    pipe: str
    upstream: str
    downstream: str
    rate: Bound


@dataclass(frozen=True)
class Region(Record):
    name: str
    pipe: str
    storage_node: str
    # A normalized, lumped pipe region. Position within it is unobservable.
    interval: tuple[float, float]
    area: Bound
    discharge_coefficient: Bound
    ambient_pressure_pa: int


def nodal_rates(network: NetworkRecord, external, transfers):
    rates = list(external)
    indices = {node: i for i, node in enumerate(network.nodes)}
    for (_, origin, destination), value in zip(network.edges, transfers):
        rates[indices[origin]] -= value
        rates[indices[destination]] += value
    return tuple(rates)


def choked_factor(gas: PerfectGas, temp: int) -> Q:
    """Exact supported specialization of the ideal-gas isentropic orifice law."""
    r, cp = Q(gas.R), Q(gas.cp)
    if r <= 0 or Q(gas.Z) != 1 or cp != 3 * r / 2 or temp <= 0:
        raise ValueError("requires ideal gas with gamma=3 and positive temperature")
    square = Q(3) / (r * temp)
    n, d = isqrt(square.numerator), isqrt(square.denominator)
    if n * n != square.numerator or d * d != square.denominator:
        raise ValueError("choked coefficient has no exact rational square root")
    return Q(n, 2 * d)


@dataclass(frozen=True)
class NetworkReference(Record):
    topology: NetworkRecord
    storage: tuple[Storage, ...]
    transfers: tuple[Transfer, ...]
    sensors: tuple[SensorRecord, ...]
    gas: PerfectGas
    temperature_k: int
    step_s: float
    max_samples: int
    domain: str
    clock_error: Bound
    discrepancy: Bound

    def evaluate(self, measurement: MeasurementContract, region: Optional[Region]):
        net = self.topology
        if (not net.composition or tuple(s.node for s in self.storage) != net.nodes or
                len(set(net.nodes)) != len(net.nodes) or not net.nodes or
                tuple((t.pipe, t.upstream, t.downstream) for t in self.transfers) != net.edges or
                len({e[0] for e in net.edges}) != len(net.edges) or
                any(u == v or u not in net.nodes or v not in net.nodes for _, u, v in net.edges)):
            raise ValueError("invalid network topology or missing gas evidence")
        dt = Q(self.step_s)
        times = tuple(map(Q, measurement.timestamps_s))
        if not 2 <= len(times) <= self.max_samples or dt <= 0 or any(
                end - start != dt for start, end in zip(times, times[1:])):
            raise ValueError("observation grid outside certified discrete model")
        if self.clock_error.exact("s", self.domain) != (0, 0) or self.discrepancy.exact("Pa", self.domain) != (0, 0):
            raise ValueError("reference needs exact timing and zero discrepancy")
        if (len({s.sensor_id for s in self.sensors}) != len(self.sensors) or
                any(s not in self.sensors for s in measurement.sensors)):
            raise ValueError("sensor mapping incompatible with network")
        index = {node: i for i, node in enumerate(net.nodes)}
        edges = {edge[0]: i for i, edge in enumerate(net.edges)}
        if any(s.network_id != net.network_id or
               (s.quantity, s.unit, s.location_kind) not in
               {("pressure", "Pa", "node"), ("mass_flow", "kg/s", "edge")} or
               s.location_id not in (index if s.quantity == "pressure" else edges)
               for s in measurement.sensors):
            raise ValueError("invalid sensor target or units")
        if any(s.volume_m3 <= 0 for s in self.storage):
            raise ValueError("nonpositive storage volume")
        factor = choked_factor(self.gas, self.temperature_k)
        gains = tuple(Q(self.gas.R) * self.temperature_k / s.volume_m3 for s in self.storage)
        masses = tuple(s.initial_mass.exact("kg", self.domain) for s in self.storage)
        external = tuple(s.external_rate.exact("kg/s", self.domain) for s in self.storage)
        flow = tuple(t.rate.exact("kg/s", self.domain) for t in self.transfers)
        lows, highs = [a for a, _ in external], [b for _, b in external]
        for (_, u, v), (a, b) in zip(net.edges, flow):
            lows[index[u]] -= b
            highs[index[u]] -= a
            lows[index[v]] += a
            highs[index[v]] += b
        midpoint = lambda pair: (pair[0] + pair[1]) / 2
        centers = tuple(map(midpoint, masses))
        center_flow = tuple(map(midpoint, flow))
        rates = nodal_rates(net, tuple(map(midpoint, external)), center_flow)
        decay_lo = decay_hi = decay_center = Q(0)
        leak_node = None
        leak_witness = ()
        if region is not None:
            edge = net.edges[edges[region.pipe]] if region.pipe in edges else None
            if (edge is None or region.storage_node != edge[2] or not 0 <= region.interval[0] < region.interval[1] <= 1 or
                    Q(region.ambient_pressure_pa) < 0):
                raise ValueError("invalid lumped leak region")
            leak_node = index[region.storage_node]
            area = region.area.exact("m2", self.domain)
            cd = region.discharge_coefficient.exact("1", self.domain)
            if area[0] < 0 or not 0 < cd[0] <= cd[1] <= 1:
                raise ValueError("inadmissible leak opening or discharge coefficient")
            gain = gains[leak_node] * factor
            decay_lo, decay_hi = gain * area[0] * cd[0], gain * area[1] * cd[1]
            decay_center = gain * midpoint(area) * midpoint(cd)
            leak_witness = (midpoint(area), midpoint(cd))
            if dt * decay_hi > 1:
                raise ValueError("Euler retention is outside the monotone domain")
        boxes, path = [], []
        for tick in range(len(times)):
            if any(lo <= 0 for lo, _ in masses):
                raise ValueError("certified box intersects nonpositive stored mass")
            if leak_node is not None and decay_hi > 0:
                p_low = masses[leak_node][0] * gains[leak_node]
                # gamma=3 critical pressure ratio = (1/2)^(3/2); compare squares exactly.
                if 8 * Q(region.ambient_pressure_pa) ** 2 > p_low ** 2:
                    raise ValueError("possible unchoked discharge")
            boxes.append(masses)
            path.append(centers)
            if tick + 1 == len(times):
                break
            masses = tuple(((1 - dt * (decay_hi if i == leak_node else 0)) * lo + dt * lows[i],
                            (1 - dt * (decay_lo if i == leak_node else 0)) * hi + dt * highs[i])
                           for i, (lo, hi) in enumerate(masses))
            centers = tuple((1 - dt * (decay_center if i == leak_node else 0)) * m + dt * rates[i]
                            for i, m in enumerate(centers))
        predicted, witness_response = [], []
        for sensor in measurement.sensors:
            if sensor.quantity == "pressure":
                i = index[sensor.location_id]
                predicted.extend((lo * gains[i], hi * gains[i]) for lo, hi in (box[i] for box in boxes))
                witness_response.extend(row[i] * gains[i] for row in path)
            else:
                i = edges[sensor.location_id]
                predicted.extend([flow[i]] * len(times))
                witness_response.extend([center_flow[i]] * len(times))
        witness = tuple(map(midpoint, boxes[0])) + tuple(map(midpoint, external)) + center_flow + leak_witness
        return predicted, witness_response, witness, path


@dataclass(frozen=True)
class NetworkHypothesis(Record):
    network: NetworkReference
    region: Optional[Region]

    def check(self, model: HypothesisModel, measurement: MeasurementContract) -> ConsistencyResult:
        assumptions = model.assumptions + (
            self.network.domain, "EXACT_RATIONAL_DISCRETE_EULER", "PRESCRIBED_SIGNED_TRANSFERS",
            "ISOTHERMAL_CHOKED_IDEAL_GAS_GAMMA_3", "COORDINATE_OUTER_ENCLOSURE",
        )
        try:
            if self.region is not None and self.region.name != model.name:
                raise ValueError("region and declared hypothesis differ")
            bounds, response, witness, _ = self.network.evaluate(measurement, self.region)
        except (ValueError, TypeError, ArithmeticError) as error:
            return ConsistencyResult(model.name, Status.INDETERMINATE, f"NETWORK_DOMAIN: {error}", assumptions)
        observation = measurement.intervals()
        for key, (lo, hi), (a, b) in zip(measurement.coordinates(), bounds, observation):
            if hi < a or lo > b:
                proof = IntervalSeparation(key, (str(lo), str(hi)), (str(a), str(b)))
                return ConsistencyResult(model.name, Status.EXCLUDED, "DISJOINT_NETWORK_ENCLOSURE", assumptions,
                                         separation=proof)
        if all(lo <= value <= hi for (lo, hi), value in zip(observation, response)):
            return ConsistencyResult(model.name, Status.FEASIBLE, "EXACT_NETWORK_WITNESS", assumptions,
                                     tuple(map(str, witness)))
        return ConsistencyResult(model.name, Status.INDETERMINATE, "NO_VERIFIED_JOINT_WITNESS", assumptions)


@dataclass(frozen=True)
class Localization(Record):
    level: str
    candidates: tuple[str, ...]
    conditional: bool
    reason: str


def localize(decision: DiagnosticDecision, regions: tuple[str, ...]) -> Localization:
    cert = decision.certificate
    declared = cert.feasible + cert.excluded + cert.indeterminate
    if not regions or not (set(declared) - set(regions)) or len(set(regions)) != len(regions) or any(r not in declared for r in regions):
        raise ValueError("all candidate regions must be declared")
    candidates = tuple(r for r in regions if r not in cert.excluded)
    feasible = tuple(r for r in candidates if r in cert.feasible)
    leak_established = bool(feasible) and all(h in cert.excluded for h in declared if h not in regions)
    if not leak_established:
        return Localization("L0", candidates, True, "LEAK_EVENT_NOT_ESTABLISHED")
    if any(r in cert.indeterminate for r in candidates):
        return Localization("L0", candidates, True, "REGION_INDETERMINATE")
    if len(feasible) > 1:
        return Localization("L1", feasible, False, "MULTIPLE_COMPATIBLE_REGIONS")
    if decision.status is DecisionStatus.SPECIFIC and len(feasible) == 1:
        return Localization("L2", feasible, False, "UNIQUE_COMPATIBLE_REGION")
    return Localization("L0", candidates, True, "REGION_UNRESOLVED")
