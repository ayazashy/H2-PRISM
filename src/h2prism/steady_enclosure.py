"""Outward rational quadrature for a fixed-isotherm, no-leak capillary junction."""
from dataclasses import dataclass
from fractions import Fraction as Q
from math import ceil, floor

from .certified_evidence import Record


@dataclass(frozen=True)
class Isotherm(Record):
    """Decimal values are exact for the declared table interpolant."""

    pressure_pa: tuple[str, ...]
    z: tuple[str, ...]
    viscosity_pa_s: tuple[str, ...]
    gas_constant: str
    temperature_k: str

    def integrals(self, lower, upper, panels=64):
        grid, z, mu = (tuple(map(Q, values)) for values in (self.pressure_pa, self.z, self.viscosity_pa_s))
        start, stop = Q(lower), Q(upper)
        if (len(grid) < 2 or len(grid) != len(z) or len(grid) != len(mu) or
                any(b <= a for a, b in zip(grid, grid[1:])) or
                not all(x > 0 for x in (*z, *mu, grid[0])) or
                not grid[0] <= start <= stop <= grid[-1] or panels < 1):
            raise ValueError("outside the positive, ordered property-table domain")
        rt = Q(self.gas_constant) * Q(self.temperature_k)
        if Q(self.gas_constant) <= 0 or Q(self.temperature_k) <= 0:
            raise ValueError("invalid gas constant or temperature")
        scale = 10**12
        lo = hi = 0
        for i, (a, b) in enumerate(zip(grid, grid[1:])):
            left, right = max(start, a), min(stop, b)
            if left >= right:
                continue
            delta = (right - left) / panels
            zz, mm = (z[i+1] - z[i]) / (b-a), (mu[i+1] - mu[i]) / (b-a)
            for j in range(panels):
                x, y = left + j * delta, left + (j+1) * delta
                zx, zy = z[i] + (x-a)*zz, z[i] + (y-a)*zz
                mx, my = mu[i] + (x-a)*mm, mu[i] + (y-a)*mm
                numerator = scale * (x+y)*delta / (2*rt)
                lo += floor(numerator / (max(zx, zy)*max(mx, my)))
                hi += ceil(numerator / (min(zx, zy)*min(mx, my)))
        return Q(lo, scale), Q(hi, scale)


def junction_bracket(table: Isotherm, supply, sink, ratio, panels=64, steps=25):
    """Bracket a steady NORMAL root for all positive outlet/inlet conductance ratios."""
    supply, sink = Q(supply), Q(sink)
    rlo, rhi = map(Q, ratio)
    if supply <= sink or not 0 < rlo <= rhi or steps < 1:
        raise ValueError("invalid boundary order or conductance domain")

    def residual(p):
        a, b = table.integrals(p, supply, panels)
        c, d = table.integrals(sink, p, panels)
        return a-rhi*d, b-rlo*c

    # The exact residual for each fixed ratio is strictly decreasing. A strict
    # sign witness is sufficient even if the computed interval is inconclusive.
    def edge(lower_edge):
        left, right = sink, supply
        for _ in range(steps):
            p = (left + right) / 2
            lo, hi = residual(p)
            keep_left = lo > 0 if lower_edge else hi >= 0
            if keep_left:
                left = p
            else:
                right = p
        return left if lower_edge else right

    return edge(True), edge(False)
