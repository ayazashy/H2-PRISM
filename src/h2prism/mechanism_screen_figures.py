"""Summarize open-set screening on completed controlled records."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
import pandas as pd

from .mechanism_screen import WITHDRAWAL


def render(out):
    x=pd.read_csv(out/"rankings.csv")
    x["mechanism_match"]=x.mechanism==x.truth
    x["withdrawal"]=x.truth==WITHDRAWAL
    x["withdrawal_retained"]=x.withdrawal & x.eligible
    x["nearest_mechanism_wrong_route"]=~x.withdrawal & (x.mechanism==WITHDRAWAL)
    summary=x.groupby(["scope","subset","offset_s"]).agg(
        settings=("query","size"),withdrawal_settings=("withdrawal","sum"),
        mechanism_matches=("mechanism_match","sum"),forced_nonwithdrawal=("forced_nonwithdrawal","sum"),
        incorrect_route=("incorrect_route","sum"),nearest_mechanism_wrong_route=("nearest_mechanism_wrong_route","sum"),withdrawal_retained=("withdrawal_retained","sum"),
        suppressed_withdrawal=("suppressed_withdrawal","sum"),
        median_latency_ms=("latency_ms","median"),p95_latency_ms=("latency_ms",lambda a:a.quantile(.95)))
    summary.to_csv(out/"coverage.csv")
    focus=x[x.scope=="controlled"]
    fig,axes=plt.subplots(1,2,figsize=(10,4),layout="constrained")
    counts=focus.groupby("seconds")[["forced_nonwithdrawal","nearest_mechanism_wrong_route","incorrect_route"]].sum()
    counts.plot(ax=axes[0],marker="o")
    axes[0].set(xlabel="Observed prefix (s)",ylabel="Wrong non-withdrawal routes per prefix")
    axes[0].legend(fontsize=7)
    refs=pd.read_csv(out/"reference_feasibility.csv")
    refs.pivot(index="query",columns="reference",values="all_rms").plot.bar(ax=axes[1])
    axes[1].set(xlabel="Controlled observation",ylabel="Normalized reference mismatch RMS")
    axes[1].legend(fontsize=7)
    fig.savefig(out/"routing_and_reference.png",dpi=220)
    plt.close(fig)

    selected=x[(x.scope=="controlled")&(x.seconds==30)&(x["subset"]=="all")&(x.offset_s==1)]
    selected[["query","self_template","truth","mechanism","forced_location","eligible","location_ranked",
              "reason","mechanism_margin","location_margin"]].to_csv(out/"thirty_second_summary.csv",index=False)
    held=selected[~selected.self_template]
    details=dict(settings=len(x),scenarios=int(x["query"].nunique()),independent_families=0,
                thirty_second_controlled=dict(
                    nonwithdrawal_forced=int(selected.forced_nonwithdrawal.sum()),
                    nonwithdrawal_routed=int(selected.incorrect_route.sum()),
                    withdrawals_routed=int(selected.withdrawal_retained.sum()),
                    withdrawals_total=int(selected.withdrawal.sum()),
                    held_out_withdrawals=int(held.withdrawal.sum())),
                all_controlled=dict(
                    nonwithdrawal_forced=int(focus.forced_nonwithdrawal.sum()),
                    nonwithdrawal_nearest_mechanism=int(focus.nearest_mechanism_wrong_route.sum()),
                    nonwithdrawal_routed=int(focus.incorrect_route.sum()),
                    withdrawals_retained=int(focus.withdrawal_retained.sum()),
                    withdrawals_total=int(focus.withdrawal.sum())),
                reference_status="BLOCKED_REFERENCE / UNRESOLVED",
                decision="REVISE_OR_REJECT",
                formal="12/12 UNRESOLVED, zero qualified exclusions, L0")
    (out/"results_register.json").write_text(json.dumps(details,indent=2),encoding="utf8")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("output",type=Path)
    render(p.parse_args().output)
