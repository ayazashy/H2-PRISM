#!/usr/bin/env python3
"""
H2-PRISM forensic audit of the recorded runs (read-only; no model is trained, no protocol value is changed).

It reproduces R2's test-time D(x) neighbourhoods EXACTLY (asserting identity with the stored D and flags) and traces
neighbour identities, source simulation models and scenario ancestry. Every table is DIAGNOSTIC evidence for the
forensic report; none is a registered estimand.

Outputs (03_results/diagnostics/forensics/):
  source_model_attribution.csv     every manifest run -> simulation model inferred from sensor evidence
  simulation_model_sensors.csv     sensors logged by each MATLAB/Simscape model (.slx) in the source package
  padded_channel_evidence.csv      zero-variance (padded) channels per release folder
  neighbour_trace_summary.csv      D(x) neighbourhoods by held-out topology x class (same-model share, ancestry)
  pseudo_independent_support.csv   flag-free windows whose ">= 2 families" support is ONE scenario ancestor
  dx_classifier_agreement.csv      D(x) top class vs classifier label among flag-free windows
  rq2_error_anatomy.csv            the wrong SPECIFIC decisions at exploratory coverage 0.25 (why eligible)
  tie_structure.csv                score resolution and share of matched selection decided by the PA-1 tie key
  independence_units.csv           windows -> runs -> families -> scenario ancestors per class
Usage:
  python tools/experiments/forensic_audit.py --raw-parent data/raw
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy.spatial.distance import cdist

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from h2prism.experiments import primary_protocol as pp  # noqa: E402

CONFIG = REPO / "06_audit_preparation" / "FINAL_EXPERIMENT_CONFIG.yaml"
MANIFEST = REPO / "06_audit_preparation" / "phase6_resolution" / "CANDIDATE_MANIFEST_V02.csv"
CLASSES = ["NORMAL", "LEAK", "COMPRESSOR_FAULT", "COMPRESSOR_DELAY"]
EXTENDED = ("PS11", "PS12", "MFS4")
EXPECTED_MODEL = {"Center": "center_model", "Downstream": "down_model", "Upstream": "up_model"}


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def ancestor(scenario_id: str) -> str:
    """Scenario stem without the topology token (CS_<TOPOLOGY>_<stem>)."""
    return "_".join(scenario_id.split("_")[2:])


def model_sensors(raw: Path) -> pd.DataFrame:
    rows = []
    for f in sorted((raw / "H2-SimNet-Dataset" / "MATLAB_SIMSCAPE_Simulation").rglob("*.slx")):
        z = zipfile.ZipFile(f)
        xml = "".join(z.read(n).decode("utf-8", "ignore") for n in z.namelist() if n.endswith(".xml"))
        ws = sorted(set(re.findall(r"(pressure_sensor\d+|flow_sensor\d+)", xml)), key=lambda s: (s[0], int(re.sub(r"\D", "", s))))
        rows.append({"model_file": f.relative_to(raw).as_posix(), "sha256": _sha(f), "n_logged_sensors": len(ws),
                     "has_PS11_PS12_MFS4": {"pressure_sensor11", "pressure_sensor12", "flow_sensor4"} <= set(ws),
                     "logged_sensors": "|".join(ws)})
    return pd.DataFrame(rows)


def source_attribution(raw: Path) -> tuple:
    man = pd.read_csv(MANIFEST)
    rows, pad = [], []
    for r in man.itertuples():
        f = raw / r.file_noise_added
        df = pd.read_parquet(f)
        df.columns = [str(c).strip() for c in df.columns]
        num = df.apply(pd.to_numeric, errors="coerce")
        sd = {c: float(num[c].std()) for c in EXTENDED if c in num}
        mu = {c: float(num[c].mean()) for c in ("PS4", "PS8", "PS9") + EXTENDED if c in num}
        ext_active = any(v > 1e-9 for v in sd.values())
        d8, d9 = abs(mu["PS4"] - mu["PS8"]), abs(mu["PS4"] - mu["PS9"])
        model = "down_model" if ext_active else ("center_model" if d8 < d9 else "up_model")
        folder = Path(r.file_noise_added).parent.parent.name if "anom" in r.file_noise_added else Path(r.file_noise_added).stem
        rows.append({"Scenario_ID": r.Scenario_ID, "manifest_topology": r.topology, "label_mapped": r.label_mapped,
                     "eligible_primary": r.eligible_primary, "source_folder_or_file": folder, "file_sha256": _sha(f),
                     "extended_sensors_active": ext_active, "abs_PS4_minus_PS8": round(d8, 4), "abs_PS4_minus_PS9": round(d9, 4),
                     "inferred_source_model": model, "expected_model_for_manifest_topology": EXPECTED_MODEL[r.topology],
                     "consistent": model == EXPECTED_MODEL[r.topology]})
        pad.append({"Scenario_ID": r.Scenario_ID, "source_folder_or_file": folder,
                    **{f"{c}_mean": round(mu.get(c, np.nan), 4) for c in EXTENDED}, **{f"{c}_std": sd.get(c, np.nan) for c in EXTENDED}})
    return pd.DataFrame(rows), pd.DataFrame(pad)


def neighbour_trace(cfg, ft: pd.DataFrame, preds: pd.DataFrame, model_of: dict) -> pd.DataFrame:
    feats = pp.model_feature_columns(ft)
    ext_idx = np.array([i for i, f in enumerate(feats) if f.split("__")[0] in EXTENDED])
    k = int(cfg["distinguishability"]["k"])
    rows = []
    for held in sorted(ft.topology.unique()):
        dev = ft[ft.topology != held].reset_index(drop=True)
        test = ft[ft.topology == held].reset_index(drop=True)
        sup = pp._support(cfg, dev, test, feats, CLASSES)
        st = preds.loc[test.window_id]
        if not np.allclose(sup.D.to_numpy(float), st.D.to_numpy(float), equal_nan=True) or \
                not (sup.support_flags.fillna("").to_numpy() == st.support_flags.fillna("").to_numpy()).all():
            raise SystemExit(f"REFUSED: D(x)/flags not reproduced for held-out {held}")
        es = pp.EmpiricalSupport(pp._dconfig(cfg)).fit(dev[feats].to_numpy(float), dev.label_mapped, dev.Scenario_Family_ID,
                                                       dev.Scenario_ID, CLASSES)
        Zq = (test[feats].to_numpy(float) - es.mu_) / es.sigma_
        dmod = dev.Scenario_ID.map(model_of).to_numpy()
        dfam, dsid, dy = dev.Scenario_Family_ID.to_numpy(), dev.Scenario_ID.to_numpy(), dev.label_mapped.to_numpy()
        danc = np.array([ancestor(s) for s in dsid])
        for c0 in range(0, len(test), 512):
            dist = cdist(Zq[c0:c0 + 512], es.Z_)
            for i in range(dist.shape[0]):
                q = c0 + i
                avail = dfam != test.Scenario_Family_ID.iloc[q]
                dav = dist[i][avail]
                kth = np.partition(dav, k - 1)[k - 1]
                idx = np.flatnonzero(avail)[dav <= kth + 1e-12]
                top = sup.top_class.iloc[q]
                tm = dy[idx] == top
                d2 = (Zq[q][None, :] - es.Z_[idx]) ** 2
                rows.append({"window_id": test.window_id.iloc[q], "held_out": held, "y_true": test.label_mapped.iloc[q],
                             "query_model": model_of[test.Scenario_ID.iloc[q]], "D": float(sup.D.iloc[q]), "top_class": top,
                             "support_flags": "" if pd.isna(sup.support_flags.iloc[q]) else str(sup.support_flags.iloc[q]),
                             "top_families": len(set(dfam[idx][tm])), "top_ancestors": len(set(danc[idx][tm])),
                             "top_runs": "|".join(sorted(set(dsid[idx][tm]))),
                             "share_nb_same_model": float((dmod[idx] == model_of[test.Scenario_ID.iloc[q]]).mean()),
                             "share_dist2_extended_channels": float(d2[:, ext_idx].sum() / max(d2.sum(), 1e-12))})
    T = pd.DataFrame(rows)
    yh = np.array(CLASSES)[preds.loc[T.window_id, [f"p_cal_{c}" for c in CLASSES]].to_numpy(float).argmax(1)]
    T["y_pred"], T["unflagged"] = yh, T["support_flags"] == ""
    T["classifier_correct"], T["dx_top_correct"] = T.y_pred == T.y_true, T.top_class == T.y_true
    T["dx_agrees_with_classifier"] = T.top_class == T.y_pred
    T["pseudo_independent"] = T.unflagged & (T.top_families >= 2) & (T.top_ancestors < 2)
    return T


def rq2_anatomy(cfg, preds: pd.DataFrame, T: pd.DataFrame) -> pd.DataFrame:
    salt = str(pp._matched_cfg(cfg)["tie_break_salt"])
    pol = pp._policies(cfg)["primary"]
    rows = []
    Ti = T.set_index("window_id")
    for f, pf in preds.reset_index().groupby("fold"):
        pf = pf.reset_index(drop=True)
        av = pp._available(np.zeros(len(pf)), pf.support_flags.fillna(""), pol)
        mk, info = pp.exact_count_selection(pf.score_s_C.to_numpy(float), av & np.isfinite(pf.score_s_C), pf.window_id.to_numpy(), 0.25, salt)
        if mk is None:
            continue
        sel = pf[mk]
        tr = Ti.loc[sel.window_id]
        wrong = tr.y_pred.to_numpy() != tr.y_true.to_numpy()
        for (yt, yp), g in tr[wrong].groupby(["y_true", "y_pred"]):
            rows.append({"held_out": pf.topology.iloc[0], "coverage": 0.25, "n_available_unflagged": int(av.sum()),
                         "n_selected": int(mk.sum()), "share_of_available_selected": float(mk.sum() / av.sum()),
                         "true_class": yt, "predicted_class": yp, "n_wrong_specific": len(g),
                         "dx_top_class": "|".join(sorted(g.top_class.unique())), "mean_D": float(g.D.mean()),
                         "median_top_families": float(g.top_families.median()), "median_top_ancestors": float(g.top_ancestors.median()),
                         "supporting_runs": "; ".join(g.top_runs.value_counts().head(2).index),
                         "mean_share_nb_same_model": float(g.share_nb_same_model.mean()),
                         "mean_s_C_percentile_in_fold": float(pf.score_s_C.rank(pct=True)[sel.index[wrong]].mean())})
    return pd.DataFrame(rows)


ROOT_PRIORITY = (("FLAG:", "UNRESOLVED_BY_SUPPORT_FLAG"), ("FLAG_BLOCKS_SPECIFIC", "SPECIFIC_BLOCKED_BY_SUPPORT_FLAG"),
                 ("SCORE_BELOW_THRESHOLD", "SCORE_BELOW_MATCHED_COVERAGE_CUT"), ("SET_TOO_BROAD", "AMBIGUITY_SET_TOO_BROAD"),
                 ("ALL_CLASS_SET_PREVENTED", "AMBIGUITY_SET_TOO_BROAD"), ("SPECIFIC_REJECTED_SINGLE_CANDIDATE", "SINGLE_CANDIDATE_REJECTED"))


def root_reason(code: str) -> str:
    """Causal root of a compound policy reason code. The runner's decision_reasons.csv keeps only the FIRST token,
    which is the policy's last consequence (e.g. SPECIFIC_REJECTED_SINGLE_CANDIDATE), not the blocking cause."""
    code = str(code or "")
    if code.startswith("ACCEPTED"):
        return "ACCEPTED"
    for key, label in ROOT_PRIORITY:
        if key in code:
            return label
    return "OTHER"


def decision_root_causes(run: Path) -> pd.DataFrame:
    d = pd.read_parquet(run / "decisions.parquet", columns=["window_id", "method", "variant", "mode", "target", "topology",
                                                            "y_true", "policy_outcome", "reason_code"])
    d = d[(d.method == "s_C") & (d.variant == "primary") & (d["mode"] == "rank_matched")]
    d = d.assign(first_token=d.reason_code.fillna("").str.split(";").str[0].str.split(":").str[0],
                 root_cause=d.reason_code.map(root_reason))
    return (d.groupby(["target", "topology", "y_true", "policy_outcome", "first_token", "root_cause"]).size()
            .rename("n").reset_index())


def tie_structure(run: Path, preds: pd.DataFrame) -> pd.DataFrame:
    e = pd.read_csv(run / "estimability.csv")
    e = e[(e.status == "ESTIMABLE") & (e.variant == "primary")]
    rows = []
    for r in e.itertuples():
        pf = preds[preds.fold == r.fold]
        rows.append({"fold": r.fold, "held_out": pf.topology.iloc[0], "method": r.method, "target": r.target,
                     "requested_count": r.requested_count, "n_tied_at_boundary": r.n_tied_at_boundary,
                     "n_selected_by_tie_key": r.n_tied_selected, "share_selected_by_tie_key": r.n_tied_selected / r.requested_count,
                     "distinct_score_values_in_fold": int(pf[f"score_{r.method}"].nunique()),
                     "share_windows_at_max_score": float((pf[f"score_{r.method}"] == pf[f"score_{r.method}"].max()).mean())})
    return pd.DataFrame(rows)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=Path, default=REPO / "03_results/primary_protocol/PRIMARY")
    ap.add_argument("--raw-parent", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=REPO / "03_results/diagnostics/forensics")
    a = ap.parse_args(argv)
    raw = a.raw_parent.resolve()
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    man = json.loads((a.run / "run_manifest.json").read_text(encoding="utf-8"))
    preds = pd.read_parquet(a.run / "predictions.parquet").set_index("window_id")
    out = a.out
    out.mkdir(parents=True, exist_ok=True)

    def w(df, name):
        df.to_csv(out / name, index=False, lineterminator="\n", float_format="%.6g")

    w(model_sensors(raw), "simulation_model_sensors.csv")
    attr, pad = source_attribution(raw)
    w(attr, "source_model_attribution.csv")
    w(pad.groupby("source_folder_or_file").agg(**{f"{c}_{s}": (f"{c}_{s}", "max") for c in EXTENDED for s in ("mean", "std")}).reset_index(),
      "padded_channel_evidence.csv")
    ft, summ = pp.build_features(cfg, REPO, raw, "noise_added")
    if summ["feature_table_sha256"] != man["features"]["feature_table_sha256"]:
        raise SystemExit("REFUSED: rebuilt feature table differs from the run's")
    model_of = dict(zip(attr.Scenario_ID, attr.inferred_source_model))
    T = neighbour_trace(cfg, ft, preds, model_of)
    g = T.groupby(["held_out", "y_true"])
    w(g.agg(n=("window_id", "size"), mean_D=("D", "mean"), share_unflagged=("unflagged", "mean"),
            mean_share_nb_same_model=("share_nb_same_model", "mean"), mean_share_dist2_extended=("share_dist2_extended_channels", "mean"),
            median_top_families=("top_families", "median"), median_top_ancestors=("top_ancestors", "median"),
            classifier_accuracy=("classifier_correct", "mean"), dx_top_class_accuracy=("dx_top_correct", "mean")).reset_index(),
      "neighbour_trace_summary.csv")
    u = T[T.unflagged]
    w(u.groupby(["held_out", "y_true"]).agg(n_unflagged=("window_id", "size"), n_pseudo_independent=("pseudo_independent", "sum"),
                                           share=("pseudo_independent", "mean"), classifier_correct=("classifier_correct", "mean")).reset_index(),
      "pseudo_independent_support.csv")
    w(u.groupby(["held_out", "dx_agrees_with_classifier", "classifier_correct"]).agg(n=("window_id", "size"),
                                                                                   dx_top_correct=("dx_top_correct", "sum")).reset_index(),
      "dx_classifier_agreement.csv")
    w(rq2_anatomy(cfg, preds, T), "rq2_error_anatomy.csv")
    w(tie_structure(a.run, preds.reset_index()), "tie_structure.csv")
    w(decision_root_causes(a.run), "decision_root_causes.csv")
    p = preds.reset_index()
    w(p.assign(anc=p.Scenario_ID.map(ancestor)).groupby("y_true").agg(windows=("window_id", "size"), runs=("Scenario_ID", "nunique"),
                                                                       families=("Scenario_Family_ID", "nunique"),
                                                                       scenario_ancestors=("anc", "nunique")).reset_index(),
      "independence_units.csv")
    T.drop(columns=["top_runs"]).to_parquet(out / "neighbour_trace.parquet")  # window level: kept out of Git
    files = sorted(out.glob("*.csv"))
    (out / "FORENSICS_MANIFEST.json").write_text(json.dumps({
        "source_run_key": man["run_key"], "config_sha256": _sha(CONFIG), "manifest_sha256": _sha(MANIFEST),
        "feature_table_sha256": summ["feature_table_sha256"], "dx_and_flags_reproduced_exactly": True,
        "command": "python tools/experiments/forensic_audit.py --raw-parent data/raw", "status": "DIAGNOSTIC - not a registered estimand",
        "outputs": {f.name: _sha(f) for f in files}}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out": "03_results/diagnostics/forensics", "files": len(files),
                      "inconsistent_runs": int((~attr.consistent).sum())}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
