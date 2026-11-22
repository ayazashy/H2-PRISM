"""Quasi-steady, laminar hydrogen-capillary reference; numerical, not certified."""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, pi, sqrt

from scipy.integrate import quad
from scipy.optimize import brentq

from .gas_physics import PerfectGas, Pipe, TabulatedGas, orifice_mass_flow


@dataclass(frozen=True)
class CapillaryReference:
    gas: TabulatedGas
    temperature_k: float = 300
    pressure_domain_pa: tuple[float, float] = (100000, 220000)
    reynolds_limit: float = 1000
    mach_limit: float = 0.05

    def state(self, pressure):
        if not isfinite(pressure) or not self.pressure_domain_pa[0] <= pressure <= self.pressure_domain_pa[1]:
            raise ValueError("pressure outside the reference domain")
        properties = self.gas.props(pressure, self.temperature_k)
        density = self.gas.rho(pressure, self.temperature_k)
        if any(not isfinite(v) or v <= 0 for v in (*properties.values(), density)):
            raise ValueError("invalid gas properties")
        return density, properties

    def rate(self, pipe: Pipe, p_a: float, p_b: float, quadrature_tol: float = 1e-9):
        """Signed integral of rho/mu from the inertia-free Poiseuille closure."""
        if (not all(map(isfinite, (pipe.diameter, pipe.length, quadrature_tol))) or
                not 0 < 100 * pipe.diameter <= pipe.length or quadrature_tol <= 0):
            raise ValueError("invalid or insufficiently slender capillary")
        lo, hi = sorted((p_a, p_b))
        self.state(lo)
        self.state(hi)
        pressure_knots = [float(x) for x in self.gas.p if lo < x < hi]

        def integrand(p):
            density, props = self.state(p)
            return density / props["mu"]

        integral, _ = quad(integrand, lo, hi, points=pressure_knots, epsabs=quadrature_tol,
                           epsrel=quadrature_tol)
        rate = pi * pipe.diameter ** 4 / (128 * pipe.length) * integral
        props = [self.state(point)[1] for point in [lo, *pressure_knots, hi]]
        mu_min = min(p["mu"] for p in props)
        z_max = max(p["Z"] for p in props)
        # At fixed temperature each property interpolant is piecewise linear.
        density_min = lo / (z_max * self.gas.R * self.temperature_k)
        reynolds = 4 * rate / (pi * pipe.diameter * mu_min)
        # sqrt(RT) is an engineering screen speed, not real-gas acoustic validation.
        mach_screen = rate / (pipe.area * density_min * sqrt(self.gas.R * self.temperature_k))
        if reynolds > self.reynolds_limit or mach_screen > self.mach_limit:
            raise ValueError("laminar or low-velocity screening limit exceeded")
        return {"kg_s": rate if p_a >= p_b else -rate, "reynolds_upper_screen": reynolds,
                "mach_reference_upper_screen": mach_screen}

    def leak(self, upstream, ambient, opening_m2, cd):
        if (not all(map(isfinite, (opening_m2, cd))) or opening_m2 < 0 or not 0 < cd <= 1):
            raise ValueError("invalid opening or discharge coefficient")
        _, p = self.state(upstream)
        self.state(ambient)
        if upstream < ambient:
            raise ValueError("reverse orifice flow outside the declared model")
        gas = PerfectGas(self.gas.R, 1, p["cp"], p["mu"], p["k"], "local ideal orifice approximation")
        gamma = gas.gamma()
        if not 1 < gamma < 2:
            raise ValueError("invalid local heat-capacity ratio")
        cutoff = (2 / (gamma + 1)) ** (gamma / (gamma - 1))
        regime = ("CLOSED" if opening_m2 == 0 or upstream == ambient else
                  "CHOKED" if ambient / upstream <= cutoff else "UNCHOKED")
        return {"kg_s": float(orifice_mass_flow(upstream, ambient, self.temperature_k, opening_m2, gas, cd)),
                "regime": regime, "critical_ratio": cutoff, "gamma_approx": gamma,
                "ideal_density_relative_to_table": p["Z"] - 1}

    def branch(self, inlet: Pipe, outlet: Pipe, supply, sink, opening_m2=0.0, cd=0.75, ambient=100000,
               volume_m3=1e-3, tolerance_pa=1e-7, quadrature_tol=1e-9):
        if (not all(map(isfinite, (volume_m3, tolerance_pa))) or volume_m3 <= 0 or
                tolerance_pa <= 0 or not ambient <= sink < supply):
            raise ValueError("invalid branch boundaries, volume or tolerance")

        def fluxes(p):
            incoming = self.rate(inlet, supply, p, quadrature_tol)
            outgoing = self.rate(outlet, p, sink, quadrature_tol)
            loss = self.leak(p, ambient, opening_m2, cd)
            return incoming, outgoing, loss

        def residual(p):
            a, b, leak = fluxes(p)
            return a["kg_s"] - b["kg_s"] - leak["kg_s"]

        p = brentq(residual, sink, supply, xtol=tolerance_pa)
        a, b, leak = fluxes(p)
        density, props = self.state(p)
        return {"pressure_pa": p, "density_kg_m3": density, "inventory_kg": volume_m3 * density,
                "viscosity_pa_s": props["mu"], "inlet": a, "outlet": b, "leak": leak,
                "balance_residual_kg_s": residual(p)}
