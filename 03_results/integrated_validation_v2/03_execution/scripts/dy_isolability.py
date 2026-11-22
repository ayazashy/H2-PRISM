"""Structural vs bound-limited isolability on the Center formal D(Y) (H4/H5; template level, hypothetical bounds).

I1 Isolability onset.  Two hypotheses are template-isolable at bounds eps iff for EVERY pair of admissible shifts
   some channel/time has |h_a - h_b| > 2 eps(kind).  Scaling eps = lambda * eps_REF (REF = solver-refinement delta),
   the pair is isolable iff lambda < lambda* = min over shift pairs of max over (t, c) of |h_a - h_b| / (2 eps_REF(c)).
   lambda* = 0 means some admissible shifts make the two templates identical on the chosen channels: INTRINSIC
   (structural) non-isolability. 0 < lambda* < 1 means isolable only with bounds tighter than REF: BOUND-LIMITED.
I2 Structural incidence matrix: per hypothesis template and channel, peak |template| over the window and its ratio
   to 2*eps_REF(kind); incidence = ratio > 1 (the channel responds detectably at REF bounds).
I3 Unidentifiable-pair register at REF for all / pressure-only / flow-only channel sets, with the limiting reason.
Usage: python dy_isolability.py --workspace <Center workspace>
"""
from __future__ import annotations

import argparse
import itertools
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

V2 = Path(__file__).resolve().parents[2]
REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "src"))
from h2prism import center_enhancement as ce  # noqa: E402

HYPS = {"HN": ("NORMAL_ZERO",), "H213": ("SID213", "ALT"), "H312": ("SID312",), "H215": ("SID215",),
        "HP55": ("PRESSURE",), "HT59": ("TIMING",)}
REF = {"pressure": ce.SOLVER_DELTA["pressure_MPa"], "mass_flow": ce.SOLVER_DELTA["flow_kg_s"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", default=os.environ.get("H2PRISM_CENTER_WORKSPACE"))
    a = ap.parse_args()
    d = ce.load(Path(a.workspace))
    allidx = np.arange(len(d.names))
    eref = np.array([REF[k] for k in d.kinds])
    stacks = {h: np.concatenate([ce.shifted_windows(d, t, allidx, 1.0) for t in ts]) for h, ts in HYPS.items()}
    configs = {"all": allidx, "pressure_only": np.array([i for i, k in enumerate(d.kinds) if k == "pressure"]),
               "flow_only": np.array([i for i, k in enumerate(d.kinds) if k == "mass_flow"])}
    out = V2 / "04_results/analysis"
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for ha, hb in itertools.combinations(HYPS, 2):
        diff = np.abs(stacks[ha][:, None] - stacks[hb][None, :]).max(axis=2)         # (Sa, Sb, C) max over time
        for cfg, idx in configs.items():
            ratio = diff[:, :, idx] / (2 * eref[idx])                                   # (Sa, Sb, |idx|)
            best = ratio.max(axis=2)                                                    # per shift pair
            k = np.unravel_index(best.argmin(), best.shape)
            lam = float(best.min())
            limiting = d.names[idx[int(ratio[k].argmax())]]
            raw = float(diff[:, :, idx].max(axis=2).min())
            reason = ("ISOLABLE_AT_REF" if lam > 1 else "INTRINSIC_IDENTICAL_UNDER_ADMISSIBLE_SHIFTS" if raw == 0
                      else "BOUND_LIMITED")
            rows.append(dict(hyp_a=ha, hyp_b=hb, channels=cfg, lambda_star=lam,
                             onset_eps_pressure_MPa=lam * REF["pressure"], onset_eps_flow_kg_s=lam * REF["mass_flow"],
                             min_over_shift_pairs_of_max_abs_difference=raw, limiting_channel_at_worst_shift_pair=limiting,
                             worst_shift_pair_s=f"{(k[0] - 5) * ce.STEP_S:+.1f}/{(k[1] - 5) * ce.STEP_S:+.1f}"
                             if stacks[ha].shape[0] == 11 and stacks[hb].shape[0] == 11 else f"index {k[0]}/{k[1]}",
                             isolable_at_REF=lam > 1, reason=reason))
    I1 = pd.DataFrame(rows)
    I1.to_csv(out / "i1_isolability_onset.csv", index=False, lineterminator="\n")
    I1[~I1.isolable_at_REF].to_csv(out / "i3_unidentifiable_pair_register_REF.csv", index=False, lineterminator="\n")
    inc = []
    for h, ts in HYPS.items():
        for t in ts:
            v, i = d.templates[t]
            w = v[i:i + ce.N]
            for c, (n, k) in enumerate(zip(d.names, d.kinds)):
                pk = float(np.abs(w[:, c]).max())
                inc.append(dict(hypothesis=h, template=t, channel=n, kind=k, peak_abs=pk, ratio_to_2epsREF=pk / (2 * REF[k]),
                                incidence_at_REF=pk > 2 * REF[k]))
    I2 = pd.DataFrame(inc)
    I2.to_csv(out / "i2_structural_incidence.csv", index=False, lineterminator="\n")
    print(I1[["hyp_a", "hyp_b", "channels", "lambda_star", "reason", "limiting_channel_at_worst_shift_pair"]].to_string())
    print(I2.pivot_table(index=["hypothesis", "template"], columns="channel", values="incidence_at_REF", aggfunc="first")
          .reindex(columns=list(d.names)).astype(int).to_string())


if __name__ == "__main__":
    main()
