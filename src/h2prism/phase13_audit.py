"""Independent audit of the frozen Phase 13 five-model benchmark."""
import argparse
import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score

from .data.loader import load_scenario
from .features import FEATURE_FUNCTIONS
from .phase13_benchmark import counts, estimators, fit, predict
from .phase13_ml import CLASSES, FEATURES, SAMPLES, SEED
from .simnet_independence import build_graph, split_issues
from .simnet_study import annotation, archive_path, catalog_tables


def permute_groups(train, rng):
    """Exchange label blocks only among equal-size dependency components."""
    result = train.copy()
    sizes = {}
    for _, group in train.sort_values("Scenario_ID").groupby("Scenario_Family_ID"):
        sizes.setdefault(len(group), []).append(group.index)
    for blocks in sizes.values():
        for target, source in zip(blocks, rng.permutation(len(blocks))):
            result.loc[target, "label_mapped"] = train.loc[blocks[source], "label_mapped"].to_numpy()
    return result


def check_replay(original, replay):
    a, b = [json.loads((p/"benchmark.json").read_text(encoding="utf8")) for p in (original,replay)]
    for key in ("versions","seed","folds","input_sha256","features","model_settings","alternate_xgboost","alternate_svm"):
        if a[key] != b[key]:
            raise ValueError(f"Replay differs in {key}")
    keys = ["variant","model","fold","Scenario_ID"]
    cols = keys + ["truth","prediction"]
    tables = [pd.read_csv(p/"predictions.csv")[cols].sort_values(keys).reset_index(drop=True)
              for p in (original,replay)]
    pd.testing.assert_frame_equal(*tables)
    return len(tables[0])


def audit(previous, original, replay, out):
    replay_rows = check_replay(original,replay)
    meta = json.loads((original/"benchmark.json").read_text(encoding="utf8"))
    table = pd.read_csv(previous/"features.csv",float_precision="round_trip")
    cols = meta["features"]["full"]
    signals = list(dict.fromkeys(c.split("__")[0] for c in cols))
    manifest, _ = catalog_tables()
    graph = build_graph(manifest)
    groups = {s:g for g,members in graph["conservative_components"].items() for s in members}
    records = {r.Scenario_ID:r for r in manifest.itertuples(index=False)}
    trajectories, clocks, windows, anchors = {}, {}, {}, {}
    for row in table.itertuples(index=False):
        record = records[row.Scenario_ID]
        frame = load_scenario(archive_path(record))
        labels, issues = annotation(frame,record)
        start = labels["onset_s"] if labels["onset_s"] is not None else 1000
        assert not issues and row.label_mapped == record.label_mapped
        assert row.start_time == start and row.Scenario_Family_ID == groups[row.Scenario_ID]
        x = frame.loc[start:start+SAMPLES-1,signals]
        assert len(x) == SAMPLES
        values = {f"{name}__{feat}":FEATURE_FUNCTIONS[feat](x[name].to_numpy(),x.index.to_numpy())
                  for name in signals for feat in FEATURES}
        np.testing.assert_allclose([getattr(row,c) for c in cols],[values[c] for c in cols],
                                   rtol=1e-15,atol=1e-15)
        trajectories[row.Scenario_ID] = frame[signals].to_numpy()
        clocks[row.Scenario_ID] = frame.index.to_numpy()
        windows[row.Scenario_ID] = x.to_numpy()
        anchors[row.Scenario_ID] = start
    # Relative RMS is computed per channel without fitting a shared scaler.
    distances = []
    for a,b in combinations(trajectories,2):
        if groups[a] == groups[b] or not np.array_equal(clocks[a],clocks[b]):
            continue
        x,y = trajectories[a],trajectories[b]
        scale = np.maximum(np.maximum(np.sqrt(np.mean(x*x,axis=0)),np.sqrt(np.mean(y*y,axis=0))),1e-15)
        delta = ((x-y)/scale)**2
        distance = float(np.sqrt(np.mean(delta)))
        prefix = clocks[a] < min(anchors[a], anchors[b])
        wx, wy = windows[a],windows[b]
        window_distance = float(np.sqrt(np.mean(((wx-wy)/scale)**2)))
        distances.append(dict(a=a,b=b,relative_rms=distance,window_relative_rms=window_distance,
                              exact=np.array_equal(x,y),window_exact=np.array_equal(wx,wy),
                              common_preevent_samples=int(prefix.sum()),
                              preevent_rms=float(np.sqrt(np.mean(delta[prefix]))) if prefix.any() else None))
    pairs = pd.DataFrame(distances)
    fold_rows, diagnostics, controls, removals = [], [], [], []
    saved = pd.read_csv(original/"predictions.csv")
    frozen = saved[saved.variant=="full"]
    for fold in meta["folds"]:
        group = fold["group"]
        mask = table.Scenario_Family_ID == group
        train, test = table[~mask],table[mask]
        train_ids, test_ids = set(train.Scenario_ID),set(test.Scenario_ID)
        assignments = {**dict.fromkeys(train_ids,"train"),**dict.fromkeys(test_ids,"test")}
        crossing = pairs[(pairs.a.isin(train_ids)&pairs.b.isin(test_ids)) |
                         (pairs.b.isin(train_ids)&pairs.a.isin(test_ids))]
        related = [e for e in graph["edges"] if {assignments.get(e[k]) for k in ("a","b")}=={"train","test"}]
        fold_rows.append(dict(fold=group,status=fold["status"],train_rows=len(train),test_rows=len(test),
                              train_classes=counts(train.label_mapped),test_classes=counts(test.label_mapped),
                              scenario_overlap=len(train_ids&test_ids),
                              group_overlap=len(set(train.Scenario_Family_ID)&set(test.Scenario_Family_ID)),
                              graph_split_issues=split_issues(graph,assignments),known_edges_crossing=len(related),
                              exact_crossing=int(crossing.exact.sum()),exact_aligned_windows=int(crossing.window_exact.sum()),
                              comparable_pairs=len(crossing),
                              near_full_0_1pct=int((crossing.relative_rms<=.001).sum()),
                              near_window_0_1pct=int((crossing.window_relative_rms<=.001).sum()),
                              near_preevent_0_1pct=int((crossing.preevent_rms<=.001).sum()),
                              exact_preevent=int((crossing.preevent_rms==0).sum()),
                              min_relative_rms=float(crossing.relative_rms.min()),
                              source_history="INCONCLUSIVE: producing histories unavailable"))
        if fold["status"] != "scored":
            continue
        controls.append(dict(fold=group,model="constant",control="always_LEAK",seed=SEED,hits=len(test),cases=len(test)))
        for name,model in estimators().items():
            fit(model,name,train,cols)
            train_prediction = predict(model,name,train,cols)
            pred = frozen[(frozen.fold==group)&(frozen.model==name)]
            leak = train.label_mapped == "LEAK"
            diagnostics.append(dict(fold=group,model=name,train=len(train),
                                    train_accuracy=float(np.mean(train_prediction==train.label_mapped)),
                                    train_balanced_accuracy=balanced_accuracy_score(train.label_mapped,train_prediction),
                                    train_leak_recall=float(np.mean(train_prediction[leak]=="LEAK")),
                                    test_leak_recall=float((pred.prediction=="LEAK").mean())))
            for removed in sorted(train.Scenario_Family_ID.unique()):
                subset = train[train.Scenario_Family_ID!=removed]
                if set(subset.label_mapped)!=set(CLASSES):
                    removals.append(dict(fold=group,model=name,removed=removed,status="class lost"))
                    continue
                fit(model,name,subset,cols)
                prediction = predict(model,name,test,cols)
                removals.append(dict(fold=group,model=name,removed=removed,status="scored",
                                     hits=int((prediction=="LEAK").sum()),cases=len(test)))
        for seed in (42,43,44):
            permuted = permute_groups(train,np.random.default_rng(seed))
            assert counts(permuted.label_mapped)==counts(train.label_mapped)
            for name,model in estimators().items():
                fit(model,name,permuted,cols)
                control_prediction = predict(model,name,test,cols)
                controls.append(dict(fold=group,model=name,control="component_block_label_permutation",
                                     seed=seed,hits=int((control_prediction=="LEAK").sum()),cases=len(test),
                                     changed_labels=int((permuted.label_mapped!=train.label_mapped).sum())))
        # A proxy control uses extraction start only, with neither identifiers nor sensor inputs.
        model = estimators()["logistic"]
        fit(model,"logistic",train,["start_time"])
        controls.append(dict(fold=group,model="logistic",control="onset_metadata_only",seed=SEED,
                             hits=int((predict(model,"logistic",test,["start_time"])=="LEAK").sum()),cases=len(test)))
    out.mkdir(parents=True)
    for name, data in (("trajectory_pairs",pairs),("fold_audit",pd.DataFrame(fold_rows)),
                       ("train_test",pd.DataFrame(diagnostics)),("negative_controls",pd.DataFrame(controls)),
                       ("component_removal",pd.DataFrame(removals))):
        data.to_csv(out/f"{name}.csv",index=False)
    (out/"audit.json").write_text(json.dumps(dict(replay_rows=replay_rows,
        reconstructed_feature_scenarios=len(table),graph=graph,folds=fold_rows),indent=2),encoding="utf8")


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ("previous","original","replay","output"):
        p.add_argument(arg,type=Path)
    args = p.parse_args()
    audit(args.previous, args.original, args.replay, args.output)
