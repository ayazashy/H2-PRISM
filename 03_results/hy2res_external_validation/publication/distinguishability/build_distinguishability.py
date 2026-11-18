from pathlib import Path
import argparse
import hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

here = Path(__file__).resolve().parent
archive = here.parents[1]
parser = argparse.ArgumentParser(description="Rebuild the exploratory HY2RES distinguishability figures.")
parser.add_argument("--output", type=Path, required=True)
out = parser.parse_args().output.resolve()
out.mkdir(parents=True, exist_ok=True)
path = archive.parents[1] / "data/external_validation_data/HY2RES_202404.csv"
assert hashlib.md5(path.read_bytes()).hexdigest() == "9a3c3e3b1668596854b43bfd790d3e0e"
raw = pd.read_csv(path, sep=";")
audit = pd.read_csv(archive / "validity_mask.csv.gz")
t = pd.to_datetime(raw.datetime)
segments = audit.segment_id
assert t.equals(pd.to_datetime(audit.timestamp).rename("datetime"))
same = segments.eq(segments.shift())
assert t.diff()[same].dt.total_seconds().eq(5).all()
p = raw[["P_elec","P_comp","P_pila"]].shift().where(same, axis=0)
known = np.isfinite(p).all(axis=1)
powered = p.gt(0)
print("Power min/max and negative counts", raw[p.columns].agg(["min","max"]), raw[p.columns].lt(0).sum())
label = pd.Series(np.where(~known,"unknown", np.where(powered.sum(axis=1)>1,"multiple_active","electrolyzer_active")))
assert label.equals(audit.operating_regime_at_forecast_origin.rename(None))
print("Known power combinations", powered[known].value_counts())
features = ["pres_buf","pres_comp","h2_flow"]
names = ["Buffer pressure [bar]","Tank pressure [bar]","Electrolyzer H₂ flow [NL/h]"]
states = ["electrolyzer_active","multiple_active"]
labels = ["Electrolyzer only","Electrolyzer + compressor"]
frame = raw[features].shift().where(same, axis=0)
frame = frame.assign(label=label, segment=segments, role=audit.split_role)
usable = np.isfinite(frame[features]).all(axis=1)
dev = frame[frame.role.eq("development") & usable & known].copy()
test = frame[frame.role.eq("test")].copy()
valid = test[usable.loc[test.index] & known.loc[test.index]].copy()
print("SUPPORT", pd.concat([dev,valid]).groupby(["role","label"]).segment.agg(["size","nunique"]))
for table in (dev, valid):
    print("Shared segments", len(set(table[table.label.eq(states[0])].segment) & set(table[table.label.eq(states[1])].segment)))
print("Shared dev/test segment IDs", len(set(dev.segment)&set(valid.segment)))

# Fixed empirical rule: development quartile bins, plus a separate exact-zero flow bin.
# An occupied cell is admissible for a state only if seen in >=2 development segments.
def cell(frame):
    categories = []
    for feature in features:
        values = dev[feature]
        if feature=="h2_flow":
            values = values[values.gt(0)]
        edges = np.unique(values.quantile([.25,.5,.75]).values)
        code = np.searchsorted(edges, frame[feature], side="left")
        if feature=="h2_flow":
            code = np.where(frame[feature].eq(0),-1,code)
        categories.append(code)
    return list(zip(*categories))

dev["cell"] = cell(dev)
counts = dev.groupby(["cell","label"]).segment.nunique().unstack(fill_value=0)
admitted = {key: tuple(state for state in states if row.get(state,0)>=2) for key,row in counts.iterrows()}
# Do not extrapolate beyond the recorded development range of any feature.
inside = test[features].ge(dev[features].min()).all(axis=1) & test[features].le(dev[features].max()).all(axis=1)
test["candidates"] = [admitted.get(key,()) if ok else () for key,ok in zip(cell(test),inside)]
test["decision"] = test.candidates.map(lambda candidates: {(states[0],):"Electrolyzer only",(states[1],):"Both powered",
                                        tuple(states):"Ambiguous",():"Unresolved"}[candidates])
categories = ["Electrolyzer only","Both powered","Ambiguous","Unresolved"]
summary = pd.crosstab(test.label,test.decision).reindex(index=states+["unknown"],columns=categories,fill_value=0)
print("RULE", summary.to_string(), "Out of range or nonfinite", int((~inside).sum()))
for f in features:
    a,b = [valid[valid.label.eq(s)][f] for s in states]
    scores = pd.concat([a,b]).rank().iloc[len(a):]
    auc = (scores.sum()-len(b)*(len(b)+1)/2)/(len(a)*len(b))
    masses = [x.value_counts(normalize=True) for x in (a,b)]
    overlap = pd.concat(masses,axis=1).fillna(0).min(axis=1).sum()
    print(f, "AUC",auc,"exact overlap",overlap)
    print(pd.DataFrame({s:g.quantile([0,.05,.25,.5,.75,.95,1]) for s,g in zip(states,[a,b])}))
for s in states:
    g=test[test.label.eq(s)]
    print(s,"segments by outcome",g.groupby("decision").segment.nunique().to_dict())
print("Cell probabilities overlap",pd.crosstab(pd.Series(cell(valid),index=valid.index).map(str),valid.label,normalize="columns").min(axis=1).sum())

bg,navy,teal,blue,slate,red,grid="#F4F4E9","#10263E","#007F86","#356CB1","#64748B","#A33F43","#D9DFDE"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":11,"svg.fonttype":"none",
                     "figure.facecolor":bg,"axes.facecolor":bg,"savefig.facecolor":bg,
                     "text.color":navy,"axes.labelcolor":navy,"axes.spines.top":False,
                     "axes.spines.right":False,"grid.color":grid})
def title(fig, heading, sub):
    fig.text(.065,.93,heading,fontsize=22,weight="bold")
    fig.text(.065,.87,sub,color=slate)
def emit(fig, name, caption):
    fig.text(.065,.055,caption,fontsize=10,linespacing=1.45)
    fig.savefig(out/f"{name}.png",dpi=400)
    svg = out / f"{name}.svg"
    fig.savefig(svg, metadata={"Date": None})
    lines = svg.read_text(encoding="utf-8").splitlines()
    svg.write_text("\n".join(line.rstrip() for line in lines) + "\n", encoding="utf-8")
    plt.close(fig)
fig,axes=plt.subplots(1,3,figsize=(12,6.75))
fig.subplots_adjust(left=.08,right=.96,bottom=.23,top=.75,wspace=.34)
title(fig,"Pressure–flow signatures of powered states","Exploratory comparison on the previously inspected test period · measurements at the forecast origin")
for i,(axis,f,name) in enumerate(zip(axes,features,names)):
    axis.set_title(f"({chr(97+i)}) {name}",loc="left",fontsize=11,weight="bold")
    for state,lab,color,style in zip(states,labels,[blue,teal],["--","-"]):
        v=valid[valid.label.eq(state)][f].sort_values()
        axis.step(v,np.arange(1,len(v)+1)/len(v),where="post",label=lab,color=color,linestyle=style,lw=2)
    axis.set_ylim(0,1.03)
    axis.grid(axis="y")
axes[0].set_ylabel("Empirical cumulative fraction")
handles,legend=axes[0].get_legend_handles_labels()
fig.legend(handles,legend,loc="lower center",bbox_to_anchor=(.5,.14),ncols=2,frameon=False)
emit(fig,"FIG_01_STATE_SIGNATURES","Power defines the reference labels. Only pressure and hydrogen flow are shown.\nThe two states share measured ranges, and row counts reflect repeated observations within a single pilot record.")

fig,axis=plt.subplots(figsize=(12,6.75))
fig.subplots_adjust(left=.30,right=.94,bottom=.28,top=.74)
title(fig,"Candidate-set decisions by reference state","Exploratory replay · rule fitted only on development observations · equal width per reference group")
left=np.zeros(len(summary))
for col,color in zip(categories,[blue,teal,slate,red]):
    pct=100*summary[col]/summary.sum(axis=1)
    axis.barh(np.arange(len(summary)),pct,left=left,color=color,label=col,height=.48)
    for y,(x,w,n) in enumerate(zip(left,pct,summary[col])):
        if w>=6:
            axis.text(x+w/2,y,f"{n:,}",ha="center",va="center",color="white",weight="bold")
    left+=pct
axis.set(yticks=range(len(summary)),yticklabels=[f"{lab}  (n={n:,})" for lab,n in zip(labels+["Unknown power"],summary.sum(axis=1))],
         xlim=(0,100),xlabel="Share within reference group (%)")
axis.invert_yaxis()
axis.legend(loc="upper center",bbox_to_anchor=(.5,-.2),ncols=4,frameon=False)
emit(fig,"FIG_02_EMPIRICAL_DECISIONS","A singleton is specific under the empirical rule. Two candidates are ambiguous; an empty set is unresolved.\nPower labels describe equipment state. Candidate filtering provides no certified D(Y) exclusion.")
