"""Certified joint membership for the three-sample Phase 3 network domain."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as Q

from .certified_evidence import (
    ConsistencyResult, ConsistencyStatus as Status, HypothesisModel, MeasurementContract,
    PolynomialCell, PolynomialExclusion, PolynomialResult,
)
from .network_reference import NetworkHypothesis, choked_factor, nodal_rates


def product(a, b):
    out = [Q(0)] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i + j] += x * y
    return out


def difference(left, right):
    size = max(len(left), len(right))
    return tuple((left[i] if i < len(left) else 0) - (right[i] if i < len(right) else 0)
                 for i in range(size))


def polynomial(coeffs, x):
    value = Q(0)
    for coefficient in reversed(coeffs):
        value = value * x + coefficient
    return value


def constraints(initial, injection, observations):
    """Pairwise lower <= upper inequalities after eliminating one shared rate."""
    lo, hi = injection
    lower = [((lo,), (1,))]
    upper = [((hi,), (1,))]
    if observations is not None:
        first, second = observations[1:]
        lower += [((first[0], -initial), (1,)), ((second[0], 0, -initial), (1, 1))]
        upper += [((first[1], -initial), (1,)), ((second[1], 0, -initial), (1, 1))]
    inequalities = [difference(product(a, d), product(c, b))
                    for a, b in lower for c, d in upper]
    return inequalities, lower


def polynomial_floor(coeffs, a, b):
    # r >= 0. Each monomial has a monotone range, summed with its coefficient sign.
    return sum(c * (a if c >= 0 else b) ** i for i, c in enumerate(coeffs))


def solve_retention(domain, inequalities, budget):
    """Return a rational witness, a covering exclusion, or a resource-limit result."""
    pending = [domain]
    rejected = []
    while pending and budget > 0:
        budget -= 1
        a, b = pending.pop()
        violated = next((p for p in inequalities if polynomial_floor(p, a, b) > 0), None)
        if violated is not None:
            rejected.append(PolynomialCell(str(a), str(b), tuple(map(str, violated))))
            continue
        middle = (a + b) / 2
        for point in dict.fromkeys((middle, a, b)):
            if all(polynomial(p, point) <= 0 for p in inequalities):
                return point, None
        if a == b:
            return None, None
        pending.extend(((middle, b), (a, middle)))
    if pending:
        return None, None
    return None, PolynomialExclusion(tuple(map(str, domain)),
                                     tuple(sorted(rejected, key=lambda cell: Q(cell.lower))))


@dataclass(frozen=True)
class JointNetwork:
    model: NetworkHypothesis
    max_cells: int = 256

    def check(self, hypothesis: HypothesisModel, measurement: MeasurementContract) -> ConsistencyResult:
        assumptions = hypothesis.assumptions + ("JOINT_THREE_SAMPLE_EXACT_RATIONAL",)
        # Reuse the original mass, regime and topology domain checks and its
        # inexpensive valid coordinate exclusions. Overlap is never a witness.
        direct = self.model.check(hypothesis, measurement)
        if direct.status is Status.EXCLUDED or direct.reason.startswith("NETWORK_DOMAIN:"):
            return direct
        if len(measurement.timestamps_s) != 3:
            return ConsistencyResult(hypothesis.name, Status.INDETERMINATE, "JOINT_WINDOW_UNSUPPORTED", assumptions)
        network, region = self.model.network, self.model.region
        domain = network.domain
        initial = [s.initial_mass.exact("kg", domain) for s in network.storage]
        flows = [t.rate.exact("kg/s", domain) for t in network.transfers]
        if any(lo != hi for lo, hi in initial + flows):
            return ConsistencyResult(hypothesis.name, Status.INDETERMINATE, "JOINT_INPUT_DOMAIN_UNSUPPORTED", assumptions)
        dt = Q(network.step_s)
        rates = [s.external_rate.exact("kg/s", domain) for s in network.storage]
        transfers = nodal_rates(network.topology, [Q(0)] * len(rates), [a for a, _ in flows])
        observations = measurement.intervals()
        pressure = {}
        for i, sensor in enumerate(measurement.sensors):
            # Fixed flow constraints are already enforced by the coordinate check.
            if sensor.quantity == "pressure":
                pressure.setdefault(sensor.location_id, []).append(observations[3 * i:3 * i + 3])
        masses, injections, factors = [], [], []
        retention_domain = (Q(1), Q(1))
        area = cd = None
        for s, (mass, _), (lo, hi), transfer in zip(network.storage, initial, rates, transfers):
            gain = Q(network.gas.R) * network.temperature_k / s.volume_m3
            # Multiple sensors on one storage constrain the same latent pressure.
            series = pressure.get(s.node, [])
            observed = (tuple((max(c[k][0] for c in series) / gain, min(c[k][1] for c in series) / gain)
                              for k in range(3)) if series else None)
            tests, lower = constraints(mass, (dt * (lo + transfer), dt * (hi + transfer)), observed)
            if observed is not None:
                tests.extend((a - b,) for a, b in observed)
                tests.extend(((observed[0][0] - mass,), (mass - observed[0][1],)))
            masses.append(mass)
            leak = region is not None and s.node == region.storage_node
            if leak:
                area = region.area.exact("m2", domain)
                cd = region.discharge_coefficient.exact("1", domain)
                factor = dt * gain * choked_factor(network.gas, network.temperature_k)
                retention_domain = (1 - factor * area[1] * cd[1], 1 - factor * area[0] * cd[0])
                factors.append(factor)
            injections.append((leak, tests, lower, transfer, observed))
        tests = [p if leak else (polynomial(p, Q(1)),)
                 for leak, polynomials, _, _, _ in injections for p in polynomials]
        retention, proof = solve_retention(retention_domain, tests, self.max_cells)
        if proof is not None:
            return PolynomialResult(hypothesis.name, Status.EXCLUDED, "JOINT_CONSTRAINTS_DISJOINT", assumptions,
                                    joint_proof=proof)
        if retention is None:
            return ConsistencyResult(hypothesis.name, Status.INDETERMINATE, "JOINT_SEARCH_LIMIT", assumptions)
        external = []
        for i, (leak, _, lower, transfer, observed) in enumerate(injections):
            r = retention if leak else Q(1)
            added = max(polynomial(a, r) / polynomial(b, r) for a, b in lower)
            values = (masses[i], r * masses[i] + added, r * (r * masses[i] + added) + added)
            if observed and not all(a <= v <= b for v, (a, b) in zip(values, observed)):
                return ConsistencyResult(hypothesis.name, Status.INDETERMINATE, "JOINT_WITNESS_REJECTED", assumptions)
            external.append(added / dt - transfer)
        leak_parameters = ()
        if area is not None:
            effective = (1 - retention) / factors[0]
            opening = max(area[0], effective / cd[1])
            coefficient = effective / opening if opening else cd[0]
            if not (area[0] <= opening <= area[1] and cd[0] <= coefficient <= cd[1]):
                return ConsistencyResult(hypothesis.name, Status.INDETERMINATE, "JOINT_WITNESS_REJECTED", assumptions)
            leak_parameters = (opening, coefficient)
        witness = tuple(masses) + tuple(external) + tuple(a for a, _ in flows) + leak_parameters
        return ConsistencyResult(hypothesis.name, Status.FEASIBLE, "VERIFIED_JOINT_TRAJECTORY", assumptions,
                                 tuple(map(str, witness)))
