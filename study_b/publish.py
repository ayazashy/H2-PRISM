"""Generate publication tables and figures from verified frozen outputs."""
from collections import Counter
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from verify_publication import rows, load, ROOT
from benchmark import write_csv

NAVY, BLUE, TEAL, SLATE, WHITE, GRID = "#10263E", "#356CB1", "#007F86", "#64748B", "#F6F5F0", "#D9DFDE"
FIG = ROOT / "figures"
TABLE = ROOT / "tables"


def save(fig, name):
    for ext in ("svg", "pdf", "png"):
        dest = FIG / f"{name}.{ext}"
        fig.savefig(dest, dpi=360, facecolor=WHITE)
        if ext == "svg":
            content = dest.read_text(encoding="utf-8")
            dest.write_text("\n".join(line.rstrip() for line in content.splitlines())+"\n", encoding="utf-8")
    plt.close(fig)


def change(a, b):
    return 100 * (b-a)/a


def tables():
    registry = rows("experiment_registry.csv")
    splits = {r["run"]:r for r in rows("split_manifest.csv")}
    channels = load("channel_map.json")["workbooks"]
    inventory = []
    for r in registry:
        n = r["run"]
        split = splits[n]
        units = channels[n]["units"]
        inventory.append(dict(run=n, role=split["partition"], recording_group=split["recording_group"],
                              eligible=split["partition"]!="outside scope", operation=r["operation"],
                              stage=r["stage"], date=r["date"], material_1=r["material_1"], material_2=r["material_2"],
                              p1_bar=r["p1_bar"], p2_bar=r["p2_bar"], half_cycle_min=r["half_cycle_min"],
                              pressure_unit=units["P-2"], flow_unit=units["MFC-3"],
                              raw_rows=r["raw_rows"], finite_pressure=int(r["raw_rows"])-int(r["invalid_P-2"]),
                              finite_outlet_flow=int(r["raw_rows"])-int(r["invalid_MFC-3"]),
                              eligible_pairs=split["eligible_pairs"],
                              exclusion="" if split["partition"]!="outside scope" else
                              "Physical scope: "+r["operation"], initial_state=r["initial_conditions_and_notes"]))
    write_csv(TABLE/"table_1_eligibility.csv", inventory)
    performance = []
    summary = load("metrics.json")["summary"]
    raw = rows("per_run_metrics.csv")
    for row in raw + [dict(run="Run mean",channel=k,**v) for k,v in summary.items()]:
        result = dict(run=row["run"],channel=row["channel"],unit=row["unit"],pairs=int(row["n"]))
        for metric in ("mae","rmse"):
            a,b = (float(row[f"b{i}_{metric}"]) for i in (0,1))
            result.update({f"b0_{metric}":a,f"b1_{metric}":b,f"{metric}_change_pct":change(a,b),
                           f"{metric}_lower":"B0" if a<b else "B1" if b<a else "Tie"})
        performance.append(result)
    write_csv(TABLE/"table_2_performance.csv", performance)
    return inventory, performance


def design(inventory):
    fig, axes = plt.subplots(1,3,figsize=(13.2,6.0), layout="constrained")
    for ax in axes:
        ax.set(xlim=(0,1),ylim=(0,1))
        ax.set_axis_off()
    ax,b,c=axes
    for a,title in zip(axes,("(a) Workbook eligibility","(b) Recording groups","(c) Causal reference task")):
        a.set_title(title,loc="left",weight="bold",pad=14)
    excluded=Counter(r["operation"] for r in inventory if not r["eligible"])
    ax.text(.04,.88,f"{len(inventory)} workbooks",fontsize=20,weight="bold")
    ax.text(.04,.76,"Physical scope screen",color=SLATE,weight="bold")
    for j,(name,count) in enumerate(excluded.items()):
        ax.text(.09,.68-j*.09,f"{count:>2}  {name.replace(' without hydrogen','')}",fontsize=11)
    ax.plot([.04,.91],[.40,.40],color=GRID)
    ax.text(.04,.31,"8 dual-stage runs",fontsize=19,weight="bold")
    ax.text(.04,.21,"5 development  ·  3 held out",fontsize=11)
    ax.text(.04,.10,"Common P-2 and MFC-3 channels")
    groups={}
    for r in inventory:
        if r["eligible"]:
            groups.setdefault((r["recording_group"],r["role"]),[]).append(r["run"])
    for j,((label,role),runs) in enumerate(groups.items()):
        y=.87-j*.145
        color=BLUE if role=="test" else TEAL
        b.text(.02,y,label,va="center")
        ids=" → ".join(runs) if runs==["26","27"] else " · ".join(runs)
        b.text(.34,y,ids,color=color,va="center",weight="bold",fontsize=13)
        b.text(.70,y,"Held out" if role=="test" else "Development",color=color,va="center")
        b.plot([.02,.98],[y-.062,y-.062],color=GRID,lw=.7)
    b.text(.02,.07,"26 → 27 denotes documented continuation.\nShared apparatus; cross-day carryover unresolved.",
           fontsize=9,color=SLATE,linespacing=1.5)
    c.text(.04,.88,"Recorded at decision time",weight="bold")
    c.text(.04,.77,"P-2 Stage II gauge pressure (barg)\nMFC-3 outlet hydrogen flow (ln/min)",linespacing=1.5)
    c.annotate("",(.06,.59),(.06,.71),arrowprops={"arrowstyle":"->","color":SLATE})
    c.text(.04,.51,"B0  Current observation",color=BLUE,weight="bold")
    c.text(.04,.43,"B1  Current observation + ridge change",color=TEAL,weight="bold")
    c.annotate("",(.06,.26),(.06,.38),arrowprops={"arrowstyle":"->","color":SLATE})
    c.text(.04,.18,"Next measured row · scoring only",weight="bold")
    c.text(.04,.08,"Nominal 1 s · allowed interval 0.8–1.2 s",color=SLATE)
    save(fig,"figure_1_design")


def comparison(inventory,performance):
    fig,axes=plt.subplots(1,3,figsize=(13.2,5.1),gridspec_kw={"width_ratios":[1,1,1.12]},layout="constrained")
    titles=["(a) Stage II pressure","(b) Outlet hydrogen flow"]
    for ax,title,key in zip(axes,titles,("P-2","MFC-3")):
        subset=[r for r in performance if r["channel"]==key]
        for i,r in enumerate(subset):
            a,b=r["b0_mae"],r["b1_mae"]
            ax.plot([a,b],[i,i],color=SLATE,lw=1.4)
            ax.scatter(a,i,color=BLUE,marker="o",s=46,zorder=3)
            ax.scatter(b,i,color=TEAL,marker="D",s=40,zorder=3)
        ax.set(yticks=range(4),yticklabels=["Run 24","Run 28","Run 29","Run mean"],
               xlabel=f'MAE ({subset[0]["unit"]})',xlim=(0,max(r["b1_mae"] for r in subset)*1.14))
        ax.axhline(2.5,color=SLATE,lw=.7,ls="--")
        ax.invert_yaxis()
        ax.grid(axis="x",color=GRID,lw=.7)
        ax.set_title(title,loc="left",weight="bold")
    axes[0].legend(handles=[Line2D([],[],color=c,marker=m,ls="",label=l) for c,m,l in
                            [(BLUE,"o","B0 persistence"),(TEAL,"D","B1 ridge")]],loc="upper left",frameon=False)
    ax=axes[2]
    ax.set(xlim=(0,1),ylim=(0,1))
    ax.axis("off")
    ax.set_title("(c) Run-mean error change",loc="left",weight="bold")
    ax.text(.05,.80,"Target",weight="bold"); ax.text(.47,.80,"MAE",weight="bold"); ax.text(.75,.80,"RMSE",weight="bold")
    for i,r in enumerate(row for row in performance if row["run"]=="Run mean"):
        y=.64-i*.18
        ax.plot([.04,.96],[y+.083,y+.083],color=GRID,lw=.9)
        ax.text(.05,y,r["channel"],weight="bold")
        ax.text(.44,y,f'{r["mae_change_pct"]:+.3f}%',color="#A33F43")
        ax.text(.72,y,f'{r["rmse_change_pct"]:+.3f}%')
    ax.text(.05,.23,"Positive = higher Ridge error",color=SLATE)
    ax.text(.05,.08,"Three workbooks · equal run weighting",color=SLATE)
    save(fig,"figure_3_performance")


def main():
    FIG.mkdir(exist_ok=True)
    TABLE.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10.5,"text.color":NAVY,
                         "axes.labelcolor":NAVY,"axes.facecolor":WHITE,"figure.facecolor":WHITE,
                         "axes.spines.top":False,"axes.spines.right":False,"svg.fonttype":"none","pdf.fonttype":42})
    inventory,performance=tables()
    design(inventory)
    comparison(inventory,performance)
    for ext in ("svg","pdf","png"):
        shutil.copyfile(ROOT/f"figure_2_responses.{ext}", FIG/f"figure_2_responses.{ext}")


if __name__=="__main__":
    main()
