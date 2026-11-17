"""
CANDIDATE protocol 2.0 helpers (P2-E): development-only operating-target rule. Not used by protocol 1.1.

A coverage target may be registered only if the DEVELOPMENT data can attain it in every inner split. The rule is
fixed before any outer-test evaluation and reads development attainability only:
  target = the largest grid value g with g <= min_split(dev_max_attainable) - margin, and g >= min_target
otherwise NOT_ESTIMABLE_BY_DESIGN (the study then reports non-estimability instead of lowering the bar post hoc).
"""

from __future__ import annotations

from typing import Dict, Iterable, Sequence


def development_target(dev_max_attainable: Iterable[float], grid: Sequence[float] = (0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3),
                       margin: float = 0.05, min_target: float = 0.3) -> Dict:
    vals = [float(v) for v in dev_max_attainable]
    if not vals:
        raise ValueError("no development attainability values")
    if not 0 <= margin < 1 or not 0 < min_target <= 1:
        raise ValueError("invalid margin or min_target")
    floor = min(vals) - margin
    ok = sorted((g for g in grid if g <= floor + 1e-12 and g >= min_target), reverse=True)
    if not ok:
        return {"status": "NOT_ESTIMABLE_BY_DESIGN", "target": None, "min_dev_attainable": min(vals),
                "reason": f"minimum development attainability {min(vals):.3f} minus margin {margin} is below {min_target}"}
    return {"status": "REGISTERABLE", "target": ok[0], "min_dev_attainable": min(vals), "reason": ""}
