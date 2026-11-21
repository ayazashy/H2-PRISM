"""
Independent gas-physics references for validating a future hydrogen network model (RESEARCH MODULE; MATLAB-free).
Specification: 02_methodology/HYDROGEN_MODEL_SPECIFICATION.md.

Contents
  * Gas property models with an explicit interface: PerfectGas (constant properties, as Simscape's perfect-gas
    specification) and TabulatedGas (T x p tables, bilinear interpolation, NO extrapolation). No hydrogen property
    data are embedded: authoritative tables (reference equation of state, e.g. Leachman et al. 2009 for normal
    hydrogen via NIST REFPROP or CoolProp, with version) must be supplied. Only the specific gas constant of H2 is
    computed here, from CODATA R and the IUPAC molar mass.
  * check_gas_properties(): physical-consistency checks (gamma within (1, 5/3], Prandtl within a gas range,
    R consistent with a declared molar mass, Z -> 1 as p -> 0 for tables, positivity) -- fails the released model.
  * Friction factors: laminar 64/Re, Haaland and Colebrook-White (turbulent), linear blend in the transition band.
  * Steady isothermal pipe flow (horizontal, kinetic term neglected and reported via Mach number) by integrating
    dp/dx = -f m|m| / (2 D A^2 rho(p, T)) with RK4; closed form for constant f and ideal gas.
  * Compressible orifice (withdrawal / leak) mass flow, choked and unchoked, for a perfect gas.
  * A steady-state network solver (fixed-pressure supply nodes, junctions, demand sinks, orifice sinks to a back
    pressure, pipes) by Newton iteration on node mass balances; residuals reported.
Purpose: an independent reference against which a Simscape steady state can be compared. It is not a transient
model and does not validate anything by itself.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np
from scipy.optimize import root

R_UNIVERSAL = 8.314462618          # J/(mol K), CODATA 2018 (exact)
M_H2 = 2.01588e-3                  # kg/mol, molar mass of H2 (IUPAC standard atomic weight of H = 1.00794)
R_H2 = R_UNIVERSAL / M_H2          # ~4124.2 J/(kg K)


# ------------------------------------------------------------------------------------------------ gas properties
@dataclass(frozen=True)
class PerfectGas:
    """Constant-property gas: p = Z rho R T, h = cp (T - T_ref) + h_ref, cv = cp - Z R (Simscape perfect-gas form)."""
    R: float          # J/(kg K)
    Z: float
    cp: float         # J/(kg K)
    mu: float         # Pa s
    k: float          # W/(m K)
    name: str = "perfect_gas"

    def z(self, p, T):
        return np.full(np.broadcast(np.asarray(p), np.asarray(T)).shape, self.Z, float)

    def rho(self, p, T):
        return np.asarray(p, float) / (self.Z * self.R * np.asarray(T, float))

    def gamma(self, p=None, T=None):
        return self.cp / (self.cp - self.Z * self.R)

    def props(self, p, T) -> Dict[str, float]:
        return {"Z": self.Z, "cp": self.cp, "mu": self.mu, "k": self.k}


@dataclass
class TabulatedGas:
    """Properties on a (T, p) grid; bilinear interpolation; raises outside the grid (never extrapolates)."""
    R: float
    T: np.ndarray
    p: np.ndarray
    Z: np.ndarray
    cp: np.ndarray
    mu: np.ndarray
    k: np.ndarray
    source: str = "UNSPECIFIED"
    name: str = "tabulated_gas"

    def __post_init__(self):
        self.T, self.p = np.asarray(self.T, float), np.asarray(self.p, float)
        for nm in ("Z", "cp", "mu", "k"):
            a = np.asarray(getattr(self, nm), float)
            if a.shape != (len(self.T), len(self.p)):
                raise ValueError(f"{nm} must have shape (len(T), len(p))")
            setattr(self, nm, a)
        if not (np.all(np.diff(self.T) > 0) and np.all(np.diff(self.p) > 0)):
            raise ValueError("T and p grids must be strictly increasing")

    def _interp(self, tab, p, T):
        p, T = float(p), float(T)
        if not (self.T[0] <= T <= self.T[-1] and self.p[0] <= p <= self.p[-1]):
            raise ValueError(f"(T={T}, p={p}) outside the property table: no extrapolation")
        i = min(np.searchsorted(self.T, T, "right") - 1, len(self.T) - 2)
        j = min(np.searchsorted(self.p, p, "right") - 1, len(self.p) - 2)
        tt = (T - self.T[i]) / (self.T[i + 1] - self.T[i])
        pp = (p - self.p[j]) / (self.p[j + 1] - self.p[j])
        return ((1 - tt) * (1 - pp) * tab[i, j] + tt * (1 - pp) * tab[i + 1, j]
                + (1 - tt) * pp * tab[i, j + 1] + tt * pp * tab[i + 1, j + 1])

    def z(self, p, T):
        return self._interp(self.Z, p, T)

    def rho(self, p, T):
        return float(p) / (self.z(p, T) * self.R * float(T))

    def props(self, p, T) -> Dict[str, float]:
        return {nm: self._interp(getattr(self, nm), p, T) for nm in ("Z", "cp", "mu", "k")}


def check_gas_properties(gas, molar_mass: Optional[float] = None, points: Sequence[Tuple[float, float]] = (),
                         pr_range=(0.5, 1.0), r_rel_tol=1e-3) -> List[str]:
    """Return a list of physical-consistency violations (empty = consistent at the checked points).
    gamma uses the ideal-gas relation cv = cp - Z R (as in Simscape's perfect-gas specification); for tabulated
    real-gas data supply points within the table."""
    v = []
    if molar_mass is not None and abs(gas.R - R_UNIVERSAL / molar_mass) > r_rel_tol * gas.R:
        v.append(f"R = {gas.R:.4g} J/(kg K) inconsistent with molar mass {molar_mass} kg/mol "
                 f"(expected {R_UNIVERSAL / molar_mass:.4g})")
    pts = list(points) or [(1e5, 293.15)]
    for p, T in pts:
        pr = gas.props(p, T)
        if min(pr["cp"], pr["mu"], pr["k"], pr["Z"]) <= 0:
            v.append(f"non-positive property at p={p}, T={T}")
            continue
        cv = pr["cp"] - pr["Z"] * gas.R
        if cv <= 0:
            v.append(f"cv <= 0 at p={p}, T={T}")
            continue
        g = pr["cp"] / cv
        if not (1.0 < g <= 5.0 / 3.0 + 1e-9):
            v.append(f"gamma = {g:.3f} outside (1, 5/3] at p={p}, T={T}")
        prandtl = pr["cp"] * pr["mu"] / pr["k"]
        if not (pr_range[0] <= prandtl <= pr_range[1]):
            v.append(f"Prandtl = {prandtl:.3f} outside {pr_range} at p={p}, T={T}")
    if isinstance(gas, TabulatedGas):
        z_low = gas.Z[:, 0]
        if gas.p[0] <= 2e5 and np.any(np.abs(z_low - 1) > 0.01):
            v.append("Z at the lowest tabulated pressure deviates from 1 by > 1 %")
    return v


# ------------------------------------------------------------------------------------------------ friction
def friction_factor(Re: float, rel_rough: float, model: str = "haaland", re_lam: float = 2000.0,
                    re_tur: float = 4000.0, shape_factor: float = 64.0) -> float:
    """Darcy friction factor. Laminar shape_factor/Re below re_lam; turbulent (Haaland or Colebrook-White) above
    re_tur; linear blend in between (as a transition treatment; must match the Simscape block's documented choice)."""
    Re = abs(float(Re))
    if Re <= 0:
        raise ValueError("Reynolds number must be > 0")

    def turb(r):
        if model == "haaland":
            return (-1.8 * np.log10(6.9 / r + (rel_rough / 3.7) ** 1.11)) ** -2
        if model == "colebrook":
            f = (-1.8 * np.log10(6.9 / r + (rel_rough / 3.7) ** 1.11)) ** -2
            for _ in range(100):
                fn = (-2.0 * np.log10(rel_rough / 3.7 + 2.51 / (r * np.sqrt(f)))) ** -2
                if abs(fn - f) < 1e-14:
                    break
                f = fn
            return fn
        raise ValueError(f"unknown friction model {model}")

    if Re <= re_lam:
        return shape_factor / Re
    if Re >= re_tur:
        return turb(Re)
    w = (Re - re_lam) / (re_tur - re_lam)
    return (1 - w) * shape_factor / re_lam + w * turb(re_tur)


# ------------------------------------------------------------------------------------------------ pipe
@dataclass(frozen=True)
class Pipe:
    a: str
    b: str
    length: float       # m
    diameter: float     # m
    roughness: float    # m
    n_steps: int = 200

    @property
    def area(self):
        return np.pi * self.diameter ** 2 / 4


def pipe_outlet_pressure(pipe: Pipe, p_in: float, mdot: float, T: float, gas, friction_model="haaland",
                         f_const: Optional[float] = None) -> Tuple[float, float]:
    """Isothermal steady flow from a to b (mdot > 0) or b to a (mdot < 0 handled by caller). Returns (p_out, max Mach)."""
    D, A, L = pipe.diameter, pipe.area, pipe.length
    dx = L / pipe.n_steps
    p = float(p_in)
    mach = 0.0

    def dpdx(pp):
        if pp <= 0:
            raise ValueError("pressure became non-positive: flow exceeds what the pipe can carry")
        rho = gas.rho(pp, T)
        mu = gas.props(pp, T)["mu"]
        Re = abs(mdot) * D / (A * mu)
        f = f_const if f_const is not None else friction_factor(Re, pipe.roughness / D, friction_model)
        return -f * mdot * abs(mdot) / (2 * D * A ** 2 * rho)

    for _ in range(pipe.n_steps):
        k1 = dpdx(p)
        k2 = dpdx(p + 0.5 * dx * k1)
        k3 = dpdx(p + 0.5 * dx * k2)
        k4 = dpdx(p + dx * k3)
        p = p + dx * (k1 + 2 * k2 + 2 * k3 + k4) / 6
        if p <= 0:
            raise ValueError("pressure became non-positive along the pipe")
        rho = float(gas.rho(p, T))
        g = gas.gamma() if hasattr(gas, "gamma") else 1.4
        c = np.sqrt(g * p / rho)
        mach = max(mach, abs(mdot) / (rho * A) / c)
    return p, mach


def isothermal_closed_form_dp2(pipe: Pipe, mdot: float, T: float, R: float, Z: float, f: float) -> float:
    """p_in^2 - p_out^2 = f L mdot^2 Z R T / (D A^2)  (ideal/constant-Z gas, constant f, horizontal, no kinetic term)."""
    return f * pipe.length * mdot ** 2 * Z * R * T / (pipe.diameter * pipe.area ** 2)


# ------------------------------------------------------------------------------------------------ orifice
def orifice_mass_flow(p_up: float, p_down: float, T_up: float, area: float, gas: PerfectGas, cd: float = 1.0) -> float:
    """Isentropic compressible flow through an orifice of a perfect gas (choked when p_down/p_up <= critical ratio)."""
    if p_up <= p_down:
        return 0.0
    g = gas.gamma()
    rho0 = gas.rho(p_up, T_up)
    crit = (2 / (g + 1)) ** (g / (g - 1))
    r = max(p_down / p_up, crit)
    term = (2 * g / (g - 1)) * (r ** (2 / g) - r ** ((g + 1) / g))
    return cd * area * np.sqrt(p_up * rho0 * term)


# ------------------------------------------------------------------------------------------------ network
@dataclass
class Network:
    """Steady isothermal network. Nodes with fixed pressure (supplies, compressor discharges as boundaries) or unknown
    pressure (junctions). Sinks: fixed demand (kg/s) or orifice to a back pressure."""
    T: float
    gas: object
    fixed_pressure: Dict[str, float]
    pipes: List[Pipe]
    demands: Dict[str, float] = field(default_factory=dict)                     # node -> kg/s withdrawn
    orifices: Dict[str, Tuple[float, float, float]] = field(default_factory=dict)  # node -> (area m2, cd, p_back Pa)
    friction_model: str = "haaland"

    def nodes(self):
        ns = set(self.fixed_pressure) | set(self.demands) | set(self.orifices)
        for p in self.pipes:
            ns |= {p.a, p.b}
        return sorted(ns)

    def _pipe_flow(self, pipe: Pipe, pa: float, pb: float) -> float:
        """Mass flow a->b that produces outlet pressure pb from inlet pa (bisection on mdot; sign by pa > pb)."""
        if abs(pa - pb) < 1e-9 * max(pa, pb):
            return 0.0
        up, down, sgn = (pa, pb, 1.0) if pa > pb else (pb, pa, -1.0)
        lo, hi = 0.0, 1.0
        while True:
            try:
                out, _ = pipe_outlet_pressure(pipe, up, hi, self.T, self.gas, self.friction_model)
                if out < down:
                    break
            except ValueError:
                break
            hi *= 2.0
            if hi > 1e7:
                raise ValueError("pipe flow bracket not found")
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            try:
                out, _ = pipe_outlet_pressure(pipe, up, mid, self.T, self.gas, self.friction_model)
                ok = out > down
            except ValueError:
                ok = False
            lo, hi = (mid, hi) if ok else (lo, mid)
        return sgn * 0.5 * (lo + hi)

    def solve(self, p_guess: Optional[float] = None, tol: float = 1e-10) -> Dict[str, object]:
        free = [n for n in self.nodes() if n not in self.fixed_pressure]
        p0 = p_guess or min(self.fixed_pressure.values()) * 0.95

        def pressures(x):
            P = dict(self.fixed_pressure)
            P.update({n: float(np.exp(v)) for n, v in zip(free, x)})
            return P

        def residual(x):
            P = pressures(x)
            bal = {n: 0.0 for n in free}
            for pp in self.pipes:
                m = self._pipe_flow(pp, P[pp.a], P[pp.b])
                if pp.a in bal:
                    bal[pp.a] -= m
                if pp.b in bal:
                    bal[pp.b] += m
            for n, d in self.demands.items():
                if n in bal:
                    bal[n] -= d
            for n, (area, cd, pb) in self.orifices.items():
                if n in bal:
                    bal[n] -= orifice_mass_flow(P[n], pb, self.T, area, self.gas, cd)
            scale = max(1.0, sum(abs(v) for v in self.demands.values()))
            return np.array([bal[n] / scale for n in free])

        sol = root(residual, np.full(len(free), np.log(p0)), method="hybr", tol=tol)
        P = pressures(sol.x)
        flows = {f"{pp.a}->{pp.b}": self._pipe_flow(pp, P[pp.a], P[pp.b]) for pp in self.pipes}
        res = residual(sol.x)
        return {"converged": bool(sol.success) and float(np.max(np.abs(res))) < 1e-6, "pressures": P, "flows": flows,
                "max_relative_mass_residual": float(np.max(np.abs(res))) if len(res) else 0.0}
