"""
Versioned gas-composition interface (Master Execution Directive, gas architecture; issues A-07/A-08 via action X20).
RESEARCH MODULE. It routes a declared composition to a property provider that is VALID for it and refuses otherwise.

Rules enforced here (tested in tests/test_gas_composition.py):
  * A composition is a set of mole fractions over named species, summing to 1 within 1e-9; it carries a schema version.
  * Pure-hydrogen tables (H2Net v1, CoolProp/Leachman) serve ONLY compositions with x_H2 >= 1 - PURE_TOL. They are
    never extrapolated to blends: an H2-CH4 composition is refused, however small the CH4 fraction.
  * Out-of-table (T, p) is refused by gas_physics.TabulatedGas (no extrapolation).
  * Mixture properties (H2-CH4) have NO provider: MixtureProviderUnavailable records why (a mixture equation of state,
    e.g. GERG-2008, must first be evaluated and new tables authorized). Nothing here approximates a blend.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Mapping, Optional, Sequence, Tuple

COMPOSITION_SCHEMA_VERSION = "gas_composition/0.1"
PURE_TOL = 1e-6                      # max total impurity mole fraction accepted as "pure" by a pure-species provider
KNOWN_SPECIES = ("H2", "CH4", "N2", "CO2", "C2H6", "C3H8", "O2", "H2O", "AIR_LIKE")


class CompositionNotSupported(ValueError):
    """The provider is not valid for this composition."""


@dataclass(frozen=True)
class GasComposition:
    mole_fractions: Tuple[Tuple[str, float], ...]
    version: str = COMPOSITION_SCHEMA_VERSION

    @classmethod
    def of(cls, **x: float) -> "GasComposition":
        return cls(tuple(sorted((k, float(v)) for k, v in x.items() if float(v) != 0.0)))

    def __post_init__(self):
        if self.version != COMPOSITION_SCHEMA_VERSION:
            raise ValueError(f"unsupported composition schema {self.version!r}")
        if not self.mole_fractions:
            raise ValueError("empty composition")
        names = [k for k, _ in self.mole_fractions]
        if len(set(names)) != len(names):
            raise ValueError("duplicate species")
        unknown = set(names) - set(KNOWN_SPECIES)
        if unknown:
            raise ValueError(f"unknown species {sorted(unknown)}")
        if any(not (0.0 <= v <= 1.0) for _, v in self.mole_fractions):
            raise ValueError("mole fractions must lie in [0, 1]")
        if abs(sum(v for _, v in self.mole_fractions) - 1.0) > 1e-9:
            raise ValueError("mole fractions must sum to 1")

    def x(self, species: str) -> float:
        return dict(self.mole_fractions).get(species, 0.0)

    def is_pure(self, species: str, tol: float = PURE_TOL) -> bool:
        return self.x(species) >= 1.0 - tol

    def as_record(self) -> Dict[str, object]:
        return {"version": self.version, "mole_fractions": dict(self.mole_fractions)}


@dataclass
class PureHydrogenTableProvider:
    """Serves the hash-verified H2Net v1 tables, for pure hydrogen only."""
    loader: Callable[[], object]
    provider_id: str = "H2NET_V1_PURE_H2_TABLES"
    _gas: Optional[object] = field(default=None, repr=False)

    def supports(self, comp: GasComposition) -> bool:
        return comp.is_pure("H2")

    def gas_for(self, comp: GasComposition):
        if not self.supports(comp):
            raise CompositionNotSupported(
                f"{self.provider_id} is valid only for pure H2 (impurity <= {PURE_TOL}); got {dict(comp.mole_fractions)}."
                " Pure-H2 tables are not extrapolated to blends.")
        if self._gas is None:
            self._gas = self.loader()
        return self._gas


@dataclass(frozen=True)
class MixtureProviderUnavailable:
    """Placeholder that refuses every multi-component composition and states the blocker."""
    provider_id: str = "H2_CH4_MIXTURE"
    status: str = "NOT_AVAILABLE"
    blocker: str = ("No validated mixture property source is authorized: GERG-2008 (or equivalent) H2-CH4 properties and"
                    " mixture transport must be evaluated (feasibility note 02_methodology/GAS_COMPOSITION_INTERFACE.md)"
                    " and new tables generated under a scoped authorization.")

    def supports(self, comp: GasComposition) -> bool:
        return False

    def gas_for(self, comp: GasComposition):
        raise CompositionNotSupported(f"{self.provider_id}: {self.status}. {self.blocker}")


def resolve_provider(comp: GasComposition, providers: Sequence[object]):
    """First provider valid for the composition; otherwise refuse (never fall back to an invalid one)."""
    for p in providers:
        if p.supports(comp):
            return p
    blockers = "; ".join(getattr(p, "blocker", f"{p.provider_id} not valid") for p in providers)
    raise CompositionNotSupported(f"no valid property provider for {dict(comp.mole_fractions)}: {blockers}")
