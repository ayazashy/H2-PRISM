"""HY2RES Level-A adapter: port the frozen development-only candidate-set rule into certified_evidence.diagnose
and test decision equivalence with the frozen rule (H6 generalization; EXPLORATORY, previously inspected test).

Step 1 rebuilds the frozen rule exactly as publication/distinguishability/build_distinguishability.py does (same
checksum-verified CSV, validity mask, development quartile cells, >=2-segment admission, no extrapolation) and checks
its decision counts against the table in the frozen TECHNICAL_REPORT.md (parsed, not retyped).
Step 2 wraps the same admitted regions as an engine adapter, one HypothesisModel per power state:
  FEASIBLE      the origin observation lies in an admitted cell inside the development range (witness = cell);
  EXCLUDED      some single channel lies strictly outside the closed hull of that state's admitted region
                (IntervalSeparation certificate, re-verified by diagnose);
  INDETERMINATE otherwise (inside the hull, but in a cell the rule does not admit: no single-coordinate certificate).
Observation half-widths are ZERO (HY2RES declares no measurement uncertainty): certification is relative to the
recorded values only, a hypothetical assumption, not a qualified bound. Flow NL/h is expressed as m3/s (normal) for
the unit contract; the monotone conversion can only weaken, never create, a strict separation.
Usage: python hy2res_dy_adapter.py --data <HY2RES_202404.csv>
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd

V2 = Path(__file__).resolve().parents[2]
REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "src"))
from h2prism.certified_evidence import (Channel, ConsistencyResult, ConsistencyStatus, HypothesisModel,  # noqa: E402
                                        IntervalSeparation, MeasurementContract, diagnose)
from h2prism.data_contracts import SensorRecord  # noqa: E402

ARCH = REPO / "03_results/hy2res_external_validation"
MD5 = "9a3c3e3b1668596854b43bfd790d3e0e"
FEATURES = ["pres_buf", "pres_comp", "h2_flow"]
STATES = ["electrolyzer_active", "multiple_active"]
DEC = {(STATES[0],): "Electrolyzer only", (STATES[1],): "Both powered", tuple(STATES): "Ambiguous", (): "Unresolved"}
FLOW = 1 / 3.6e6          # NL/h -> normal m3/s
UNIT = {"pres_buf": ("pressure", "bar", 1.0), "pres_comp": ("pressure", "bar", 1.0), "h2_flow": ("volumetric_flow", "m3/s", FLOW)}


def frozen(data):
    assert hashlib.md5(Path(data).read_bytes()).hexdigest() == MD5
    raw = pd.read_csv(data, sep=";")
    audit = pd.read_csv(ARCH / "validity_mask.csv.gz")
    seg = audit.segment_id
    same = seg.eq(seg.shift())
    p = raw[["P_elec", "P_comp", "P_pila"]].shift().where(same, axis=0)
    known = np.isfinite(p).all(axis=1)
    label = pd.Series(np.where(~known, "unknown", np.where(p.gt(0).sum(axis=1) > 1, "multiple_active", "electrolyzer_active")))
    assert label.equals(audit.operating_regime_at_forecast_origin.rename(None))
    frame = raw[FEATURES].shift().where(same, axis=0).assign(label=label, segment=seg, role=audit.split_role)
    usable = np.isfinite(frame[FEATURES]).all(axis=1)
    dev = frame[frame.role.eq("development") & usable & known].copy()
    test = frame[frame.role.eq("test")].copy()
    edges = {}
    for f in FEATURES:
        v = dev[f][dev[f].gt(0)] if f == "h2_flow" else dev[f]
        edges[f] = np.unique(v.quantile([.25, .5, .75]).values)

    def cell(fr):
        cats = []
        for f in FEATURES:
            code = np.searchsorted(edges[f], fr[f], side="left")
            if f == "h2_flow":
                code = np.where(fr[f].eq(0), -1, code)
            cats.append(code)
        return list(zip(*cats))

    dev["cell"] = cell(dev)
    counts = dev.groupby(["cell", "label"]).segment.nunique().unstack(fill_value=0)
    admitted = {k: tuple(s for s in STATES if r.get(s, 0) >= 2) for k, r in counts.iterrows()}
    lo, hi = dev[FEATURES].min(), dev[FEATURES].max()
    inside = test[FEATURES].ge(lo).all(axis=1) & test[FEATURES].le(hi).all(axis=1)
    test["cell"] = cell(test)
    test["inside"] = inside
    test["candidates"] = [admitted.get(k, ()) if ok else () for k, ok in zip(test.cell, inside)]
    test["frozen_decision"] = test.candidates.map(DEC.get)
    return test, admitted, edges, lo, hi


def published_table():
    txt = (ARCH / "publication/distinguishability/TECHNICAL_REPORT.md").read_text(encoding="utf-8")
    rows = {}
    for name in ("Electrolyzer only", "Electrolyzer + compressor", "Unknown"):
        m = re.search(rf"^\| {re.escape(name)} \|([^\n]+)\|$", txt, re.M)
        rows[name] = [int(x.strip().replace(",", "")) for x in m.group(1).split("|")]
    return pd.DataFrame(rows, index=["Electrolyzer only", "Both powered", "Ambiguous", "Unresolved"]).T


class CellRegionAdapter:
    def __init__(self, state, admitted, edges, lo, hi):
        self.cells = {k for k, v in admitted.items() if state in v}
        self.lo, self.hi, self.edges = lo, hi, edges
        self.hull = {}
        for j, f in enumerate(FEATURES):
            ivs = [self._interval(f, k[j]) for k in self.cells]
            self.hull[f] = (min(a for a, _ in ivs), max(b for _, b in ivs))

    def _interval(self, f, code):
        e = self.edges[f]
        if f == "h2_flow" and code == -1:
            return 0.0, 0.0
        a = self.lo[f] if code == 0 else e[code - 1]
        b = self.hi[f] if code == len(e) else e[code]
        return max(a, self.lo[f]), min(b, self.hi[f])

    def check(self, model, m):
        coords, obs = m.coordinates(), m.intervals()
        for j, f in enumerate(FEATURES):
            s = UNIT[f][2]
            a, b = Fraction(self.hull[f][0] * s), Fraction(self.hull[f][1] * s)
            o_lo, o_hi = obs[j]
            if b < o_lo or a > o_hi:
                return ConsistencyResult(model.name, ConsistencyStatus.EXCLUDED, "OUTSIDE_ADMITTED_HULL", model.assumptions,
                                         separation=IntervalSeparation(coords[j], (str(a), str(b)), (str(o_lo), str(o_hi))))
        if self.row_inside and self.row_cell in self.cells:
            return ConsistencyResult(model.name, ConsistencyStatus.FEASIBLE, "ADMITTED_CELL", model.assumptions,
                                     witness=("cell", str(self.row_cell)))
        return ConsistencyResult(model.name, ConsistencyStatus.INDETERMINATE, "NOT_ADMITTED_NO_SINGLE_COORDINATE_SEPARATION",
                                 model.assumptions)


def contract(row):
    sensors = tuple(SensorRecord(f, "HY2RES", "node", f, UNIT[f][0], UNIT[f][1], 5.0) for f in FEATURES)
    chans = tuple(Channel(f, UNIT[f][1], (0.0,), "HY2RES datetime column (forecast origin)", (float(row[f]) * UNIT[f][2],), (0.0,))
                  for f in FEATURES)
    return MeasurementContract(sensors, (0.0,), chans, f"HY2RES row {row.name}", f"segment {row.segment}", "HY2RES_202404",
                               "HYPOTHETICAL zero half-width: no declared measurement uncertainty", 0.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    a = ap.parse_args()
    test, admitted, edges, lo, hi = frozen(a.data)
    states_order = ["electrolyzer_active", "multiple_active", "unknown"]
    cols = ["Electrolyzer only", "Both powered", "Ambiguous", "Unresolved"]
    fz = pd.crosstab(test.label, test.frozen_decision).reindex(index=states_order, columns=cols, fill_value=0)
    pub = published_table()
    reproduced = bool((fz.to_numpy() == pub.to_numpy()).all())
    adapters = {s: CellRegionAdapter(s, admitted, edges, lo, hi) for s in STATES}
    models = tuple(HypothesisModel(s, adapters[s], ("HY2RES development-only empirical cell rule; hypothetical zero bounds",))
                   for s in STATES)
    out = []
    for _, row in test.iterrows():
        for ad in adapters.values():
            ad.row_cell, ad.row_inside = row.cell, bool(row.inside)
        d = diagnose(contract(row), models)
        st = {r.hypothesis: r.status.value for r in d.certificate.results}
        out.append(dict(label=row.label, frozen_decision=row.frozen_decision, certified_status=d.status.value,
                        certified_reason=d.reason, certified_hypothesis=d.hypothesis or "",
                        status_electrolyzer_active=st[STATES[0]], status_multiple_active=st[STATES[1]]))
    R = pd.DataFrame(out)
    dst = V2 / "04_results/analysis"
    R.groupby(["label", "frozen_decision", "certified_status", "certified_reason", "certified_hypothesis",
               "status_electrolyzer_active", "status_multiple_active"]).size().rename("rows").reset_index() \
        .to_csv(dst / "h1_hy2res_certified_vs_frozen.csv", index=False, lineterminator="\n")
    eq = pd.DataFrame([dict(frozen_rule_reproduced_vs_published_table=reproduced, test_rows=len(R),
                            frozen_specific=int(R.frozen_decision.isin(cols[:2]).sum()),
                            certified_specific=int((R.certified_status == "SPECIFIC").sum()),
                            certified_specific_agrees_with_frozen=int(((R.certified_status == "SPECIFIC") &
                                                                       (R.certified_hypothesis.map({STATES[0]: cols[0], STATES[1]: cols[1]})
                                                                        == R.frozen_decision)).sum()),
                            frozen_ambiguous=int((R.frozen_decision == "Ambiguous").sum()),
                            certified_ambiguous=int((R.certified_status == "AMBIGUOUS").sum()),
                            certified_specific_wrong_vs_power_label=int(((R.certified_status == "SPECIFIC") &
                                                                         (R.certified_hypothesis != R.label)).sum()),
                            bound_basis="HYPOTHETICAL zero half-width", status="EXPLORATORY (previously inspected test)")])
    eq.to_csv(dst / "h2_hy2res_equivalence_summary.csv", index=False, lineterminator="\n")
    fz.to_csv(dst / "h0_hy2res_frozen_rule_reproduction.csv", lineterminator="\n")
    print(fz.to_string()); print(pd.crosstab(R.frozen_decision, R.certified_status + "|" + R.certified_hypothesis).to_string())
    print(eq.T.to_string())


if __name__ == "__main__":
    main()
