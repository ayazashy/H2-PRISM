"""Retrospective stream playback on a fixed, causal schedule."""
import argparse
import json
import platform
from pathlib import Path
import time

import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import balanced_accuracy_score, confusion_matrix, f1_score, matthews_corrcoef
from sklearn.dummy import DummyClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from xgboost import XGBClassifier, __version__ as xgb_version

from .baseline import make_random_forest
from .data.loader import load_scenario
from .secondary_baseline import make_logistic_regression
from .simnet_independence import build_graph, edge, groups, POTENTIAL
from .simnet_study import annotation, archive_path, catalog_tables

CHANNELS = tuple([f"PS{i}" for i in range(1,13)] + [f"MFS{i}" for i in range(1,5)])
STRIDE = 120
LENGTH = 5
SEED = 42
MODES = ("clean","white_noise","correlated_noise","drift","stuck","delayed")


def causal_features(clock, samples, deadline, columns=CHANNELS):
    if tuple(columns) != CHANNELS:
        raise ValueError("unexpected channel order or metadata column")
    clock = np.asarray(clock)
    if (len(clock) != LENGTH or clock[-1] != deadline or not np.all(np.diff(clock) == 1)
            or samples.shape != (LENGTH,len(CHANNELS)) or not np.isfinite(samples).all()):
        raise ValueError("invalid, incomplete or noncausal window")
    return np.concatenate((samples.mean(axis=0),samples.std(axis=0),samples[-1]-samples[0],
                           np.arange(-2,3) @ samples / 10))


def mapped_window_features(frame, deadline, channel_map, units):
    """Map stated units and named sensors to the specific trained input schema."""
    if set(channel_map) != set(CHANNELS) or len(set(channel_map.values())) != len(CHANNELS):
        raise ValueError("incomplete or ambiguous channel mapping")
    pressure = {"Pa":1e-6,"kPa":1e-3,"MPa":1.0,"bar":.1}
    flow = {"kg/s":1.0,"g/s":.001}
    columns = []
    for channel in CHANNELS:
        source = channel_map[channel]
        scales = pressure if channel.startswith("PS") else flow
        if source not in frame or units.get(source) not in scales:
            raise ValueError(f"missing sensor or unsupported units: {source}")
        columns.append(frame[source].to_numpy(dtype=float)*scales[units[source]])
    return causal_features(frame.index,np.column_stack(columns),deadline)


def stream_windows(frame):
    # Sensor data and clock only. Annotation lookup is a separate scoring operation.
    if not set(CHANNELS) <= set(frame):
        raise ValueError("missing required sensor")
    x = frame.loc[:,CHANNELS].to_numpy(dtype=float)
    clock = frame.index.to_numpy(dtype=float)
    if not np.isfinite(clock).all() or not np.all(np.diff(clock) == 1):
        raise ValueError("unsupported source clock")
    ends = np.arange(LENGTH-1,len(clock),STRIDE)
    rng = np.random.default_rng(SEED)
    relative = np.maximum(abs(x[0]), 1e-8)
    white = rng.normal(size=x.shape)*relative*.01
    correlated = white.copy()
    for i in range(1,len(x)):
        correlated[i] += .8*correlated[i-1]
    drift = x + np.linspace(0,.02,len(x))[:,None]*relative
    stuck = x.copy()
    stuck[:,0] = x[0,0]
    delayed = x.copy()
    delayed[2:,0] = x[:-2,0]
    delayed[:2,0] = x[0,0]
    variants = dict(clean=x,white_noise=x+white,correlated_noise=x+correlated,
                    drift=drift,stuck=stuck,delayed=delayed)
    features = {k:np.stack([causal_features(clock[end-LENGTH+1:end+1], v[end-LENGTH+1:end+1],
                                           clock[end]) for end in ends]) for k,v in variants.items()}
    return ends,features


def models():
    return {
        "majority":DummyClassifier(strategy="most_frequent"),
        "always_event":DummyClassifier(strategy="constant",constant=1),
        "logistic":make_logistic_regression({"C":1},SEED),
        "random_forest":make_random_forest(dict(n_estimators=60,min_samples_leaf=5,max_features="sqrt"),SEED),
        "xgboost":XGBClassifier(objective="binary:logistic",n_estimators=100,max_depth=2,
                                  learning_rate=.05,min_child_weight=2,reg_lambda=5,
                                  n_jobs=1,tree_method="hist",random_state=SEED),
        "linear_svm":make_pipeline(StandardScaler(),SVC(kernel="linear",class_weight="balanced",C=.1)),
        "rbf_svm":make_pipeline(StandardScaler(),SVC(kernel="rbf",class_weight="balanced",C=1)),
    }


def make_groups(manifest, flagged):
    graph = build_graph(manifest)
    additional = [edge(r.a,r.b,POTENTIAL,"AUDIT_NEAR_PREEVENT_PREFIX","trajectory_pairs.csv",
                       {"samples":int(r.common_preevent_samples),"relative_rms":r.preevent_rms})
                  for r in flagged.itertuples() if r.common_preevent_samples >= 2500 and r.preevent_rms <= .001]
    graph["added_development_edges"] = additional
    graph["development_components"] = groups(graph["nodes"],graph["edges"]+additional,True)
    return graph


def scores(rows):
    y,p = rows.truth,rows.prediction
    tn,fp,fn,tp = confusion_matrix(y,p,labels=[0,1]).ravel()
    # Each positive decision on a known negative evaluation knot is a false alarm opportunity.
    return dict(n=len(rows),tn=int(tn),fp=int(fp),fn=int(fn),tp=int(tp),
                balanced_accuracy=balanced_accuracy_score(y,p),macro_f1=f1_score(y,p,average="macro"),
                mcc=matthews_corrcoef(y,p),fpr=float(fp/(tn+fp)),fnr=float(fn/(tp+fn)),
                event_precision=float(tp/(tp+fp)) if tp+fp else None,event_recall=float(tp/(tp+fn)),
                normal_precision=float(tn/(tn+fn)) if tn+fn else None,normal_recall=float(tn/(tn+fp)))


def main(audit, output):
    manifest,_ = catalog_tables()
    graph = make_groups(manifest,pd.read_csv(audit/"trajectory_pairs.csv"))
    lookup = {s:g for g,items in graph["development_components"].items() for s in items}
    arrays = {k:[] for k in MODES}
    records, manifest_rows, excluded = [], [], {}
    for run in manifest.itertuples():
        sid = run.Scenario_ID
        if run.eligible_primary != "True":
            excluded[sid] = "manifest-excluded"
            continue
        frame = load_scenario(archive_path(run))
        try:
            ends, features = stream_windows(frame)
        except ValueError as exc:
            excluded[sid] = str(exc)
            continue
        label, issues = annotation(frame,run)
        if issues:
            excluded[sid] = list(issues)
            continue
        for k in arrays:
            arrays[k].append(features[k])
        for i in ends:
            records.append(dict(scenario=sid,group=lookup[sid],truth=int(frame.label_anomaly.iloc[i]),
                                decision_s=float(frame.index[i])))
        manifest_rows.append(dict(scenario=sid,group=lookup[sid],archive_sha256=run.sha256_clean,
                                  topology=run.topology_source_model,event=run.label_mapped,**label))
    data = pd.DataFrame(records)
    arrays = {k:np.concatenate(v) for k,v in arrays.items()}
    folds,predictions = [],[]
    for group in sorted(data.group.unique()):
        test = data.group==group
        train = ~test
        support = data.loc[train,"truth"].value_counts().to_dict()
        if set(support) != {0,1}:
            folds.append(dict(group=group,status="blocked",train_counts=support))
            continue
        folds.append(dict(group=group,status="scored",train_counts=support,
                          test_counts=data.loc[test,"truth"].value_counts().to_dict(),
                          train_groups=sorted(set(data.group[train])),train_scenarios=sorted(set(data.scenario[train])),
                          test_scenarios=sorted(set(data.scenario[test]))))
        for name,model in models().items():
            start = time.perf_counter()
            model.fit(arrays["clean"][train],data.truth[train])
            fit_s = time.perf_counter()-start
            for mode in MODES:
                start = time.perf_counter()
                prediction = model.predict(arrays[mode][test])
                predict_s = time.perf_counter()-start
                predictions.append(data[test].assign(model=name,mode=mode,prediction=prediction,
                                                     fit_s=fit_s,batch_predict_s=predict_s))
    table = pd.concat(predictions,ignore_index=True)
    cases = pd.DataFrame(manifest_rows).set_index("scenario")
    metrics,event_rows = [],[]
    for (model,mode),rows in table.groupby(["model","mode"]):
        metrics.append(dict(model=model,mode=mode,**scores(rows)))
        for sid,r in rows.groupby("scenario"):
            event = cases.loc[sid]
            flagged = r[(r.truth==1)&(r.prediction==1)]
            onset = event.onset_s
            event_rows.append(dict(model=model,mode=mode,scenario=sid,event=event.event,
                                   positive_knots=int(r.truth.sum()),detected=bool(len(flagged)),
                                   delay_s=float(flagged.decision_s.min()-onset) if len(flagged) else None,
                                   false_positive_knots=int(((r.truth==0)&(r.prediction==1)).sum())))
    output.mkdir(parents=True)
    table.to_csv(output/"predictions.csv",index=False)
    pd.DataFrame(metrics).to_csv(output/"metrics.csv",index=False)
    pd.DataFrame(event_rows).to_csv(output/"events.csv",index=False)
    cases.to_csv(output/"provenance.csv")
    (output/"method.json").write_text(json.dumps(dict(
        scope="Retrospective causal playback; producing-run independence remains unresolved.",
        schema=CHANNELS,window_samples=LENGTH,stride_seconds=STRIDE,
        earliest_decision="first stored time plus 4 seconds",seed=SEED,folds=folds,excluded=excluded,
        noise="1% of absolute initial per-channel value white; AR(1) coefficient 0.8; drift up to 2%; PS1 stuck or 2 s late",
        versions=dict(python=platform.python_version(),sklearn=sklearn.__version__,xgboost=xgb_version,
                      numpy=np.__version__,pandas=pd.__version__),graph=graph),indent=2),encoding="utf8")
    summarize(output)


def summarize(output):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    metrics = pd.read_csv(output/"metrics.csv")
    events = pd.read_csv(output/"events.csv")
    observed = events[events.event != "NORMAL"]
    summary = observed.groupby(["model","mode","event"]).agg(
        detected=("detected","sum"), events=("detected","size"), median_delay_s=("delay_s","median"))
    summary.to_csv(output/"event_class_results.csv")
    timings = pd.read_csv(output/"predictions.csv",usecols=["model","mode","group","fit_s","batch_predict_s"])
    clean = timings[timings["mode"]=="clean"].drop_duplicates(["model","group"])
    clean.groupby("model")[["fit_s","batch_predict_s"]].median().to_csv(output/"timings.csv")
    chart = metrics.pivot(index="model",columns="mode",values="balanced_accuracy")
    chart = chart.loc[["logistic","random_forest","xgboost","linear_svm","rbf_svm"],list(MODES)]
    ax = chart.T.plot(marker="o",figsize=(9,4),color=["#143253","#078781","#3678af","#5f677d","#557fb4"])
    ax.set_ylabel("Binary balanced accuracy")
    ax.set_xlabel("Held-out playback condition")
    ax.tick_params(axis="x",rotation=25)
    ax.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(output/"sensor_stress.png",dpi=240)
    plt.close()


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audit",type=Path)
    parser.add_argument("output",type=Path)
    args=parser.parse_args()
    main(args.audit,args.output)
