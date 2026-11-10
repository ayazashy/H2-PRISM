"""
H2-PRISM primary protocol runner core (Phase 8). CLI: tools/experiments/run_primary_protocol.py

Orchestrates the existing tested modules exactly as FINAL_EXPERIMENT_CONFIG.yaml specifies:

  preflight (fail-closed) -> feature table (one realization) -> for each outer fold:
     development stage  [outer-train only; inner leave-one-topology-out]
        RF selection (macro-F1) -> calibration feasibility + selection -> cross-fitted calibrated OOF
        -> D(x) with reference = other inner topology -> comparators -> cross-fitted s_C / s_C-D
        -> development thresholds per method x target x policy variant (NOT_ESTIMABLE if unattainable)
     outer stage        [only in modes synthetic / execute; never in preflight]
        refit on all development data -> calibrate -> D(x) with development reference -> scores
        -> policy with frozen thresholds (threshold transfer) and label-free rank matching
  -> aggregation: coverage/risk, estimability, RQ1 paired comparison, RQ2 outcome summary,
     family-level paired effects, topology-stratified family bootstrap.

Modes / artifact classes
  preflight  -> PREFLIGHT_ONLY      (no model fitting; works on real data)
  synthetic  -> SYNTHETIC_TEST      (full pipeline; config status must be SYNTHETIC_TEST_CONFIG;
                                     output may not be written under 03_results/)
  execute    -> PRIMARY_EXPERIMENT / ROBUSTNESS_EXPERIMENT (requires an authorization file whose
                                     config_sha256 matches; never used in Phase 8)
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import subprocess
from dataclasses import replace
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yaml

from ..baseline import GroupedRunConfig, _aligned_proba, make_random_forest, select_on_development
from ..calibration import calibration_feasibility, fit_calibrator, select_calibration
from ..combined_score import CombinedScoreConfig, apply_combined_score, fit_combined_score
from ..comparators import compute_comparators
from ..distinguishability import ALL_FLAGS, DConfig, EmpiricalSupport
from ..feature_table import build_feature_table, normalize_manifest_columns
from ..features import model_feature_columns, table_sha256
from ..io import SENSOR_CHANNELS
from ..metrics import AMBIGUITY_SET, SPECIFIC, UNRESOLVED, ambiguity_summary, coverage_and_risk
from ..policy import PolicyConfig, apply_policy
from ..splits import assert_group_disjoint, validate_outer_folds
from ..uncertainty import paired_stratified_bootstrap
from ..windows import WindowConfig

METHODS = ("s_C", "s_C_minus_D", "confidence", "margin", "neg_entropy", "D_only")
# RQ1 paired comparisons (plan F10): C vs C-D is primary; C vs B (confidence) and the other indicators secondary
COMPARISONS = (("s_C_minus_D", "PRIMARY"), ("confidence", "SECONDARY_C_VS_B"), ("margin", "SECONDARY"),
               ("neg_entropy", "SECONDARY"), ("D_only", "SECONDARY"))
MODES = {"preflight": "PREFLIGHT_ONLY", "synthetic": "SYNTHETIC_TEST"}
EXECUTE_CLASSES = {"PRIMARY_EXPERIMENT": "noise_added", "ROBUSTNESS_EXPERIMENT": "clean", "SENSITIVITY_EXPERIMENT": None}
# Registered sensitivity analyses (config `sensitivity_analyses`). Each is ONE pre-specified deviation from the
# primary protocol, read off its registered name; nothing else changes. Values are fixed here, not tuned.
SENSITIVITY_OVERRIDES: Dict[str, Dict[str, object]] = {
    "clean_realization": {"dataset.realization_primary": "clean"},
    "windows_60_60": {"windows.stride_s": 60},
    "pre_event_label_normal": {"windows.pre_event_policy": "label_normal"},
    "offset_invariant_features": {"features.statistics": ["std", "range", "last_minus_first", "slope", "mean_abs_diff"]},
    "k_10": {"distinguishability.k": 10},
    "k_50": {"distinguishability.k": 50},
    "prior_correction": {"distinguishability.prior_correction": True},
    "extended_family_map": {"dataset.family_column": "family_extended_sensitivity"},
    "policy_warning_only": {},  # produced inside EVERY run as policy variant "warning_only"; no separate run
}
EMBEDDED_SENSITIVITIES = {"policy_warning_only"}


def apply_sensitivity(cfg: Dict, name: Optional[str]) -> Dict:
    """Return a deep copy of ``cfg`` with the registered override for ``name`` applied (fail closed otherwise)."""
    import copy
    if name is None:
        return cfg
    if name not in (cfg.get("sensitivity_analyses") or []):
        raise PreflightError(f"sensitivity '{name}' is not registered in config sensitivity_analyses")
    if name not in SENSITIVITY_OVERRIDES:
        raise PreflightError(f"sensitivity '{name}' has no implemented override")
    if name in EMBEDDED_SENSITIVITIES:
        raise PreflightError(f"sensitivity '{name}' is produced by every run (variant column); no separate run")
    out = copy.deepcopy(cfg)
    for path, val in SENSITIVITY_OVERRIDES[name].items():
        a, b = path.split(".")
        if b not in out.get(a, {}) and a != "dataset":
            raise PreflightError(f"override target {path} missing in config")
        out[a][b] = copy.deepcopy(val)
    out["sensitivity_applied"] = {"name": name, "override": SENSITIVITY_OVERRIDES[name]}
    return out
REAL_STATUS = "PROTOCOL_SELECTED_PENDING_EXECUTION"
# Execution-blocking governance items (FINAL_GOVERNANCE_AND_GATE_RECORD.md): each must be attested or waived
REQUIRED_CLEARANCES = ("F-D15", "F-D16", "A-D10", "PA-1")
SYNTH_STATUS = "SYNTHETIC_TEST_CONFIG"
MANIFEST_COLS = ["Scenario_ID", "Scenario_Family_ID", "topology", "label_mapped", "eligible_primary",
                 "file_noise_added", "sha256_noise_added", "file_clean", "sha256_clean"]
PROHIBITED_CLAIMS = ["industrial deployment readiness", "field validation", "generalisation beyond the evaluated simulated topologies",
                     "physical identifiability", "metric leak localisation", "pure-hydrogen performance",
                     "a verified hydrogen blend percentage", "superiority of D(x) beyond the reported effect sizes"]


class PreflightError(RuntimeError):
    pass


class AuthorizationError(RuntimeError):
    pass


# ----------------------------------------------------------------------------- io helpers
def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def write_csv(df: pd.DataFrame, p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(df.to_csv(index=False, lineterminator="\n", float_format="%.10g").encode("utf-8"))


def write_json(obj, p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes((json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n").encode("utf-8"))


def _code_sha256() -> str:
    """Hash of the runner and the library modules it orchestrates (resume keys change when code changes)."""
    pkg = Path(__file__).resolve().parents[1]
    h = hashlib.sha256()
    for f in sorted(pkg.rglob("*.py")):
        h.update(f.relative_to(pkg).as_posix().encode())
        h.update(f.read_bytes().replace(b"\r\n", b"\n"))
    return h.hexdigest()


def _git_commit(root: Path) -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
    except Exception:  # noqa: BLE001
        return "UNKNOWN"


# ----------------------------------------------------------------------------- preflight
def preflight(cfg: Dict, root: Path, raw_parent: Path, realization: str, expected_status: str) -> Dict:
    checks: List[Dict] = []

    def chk(name, ok, detail=""):
        checks.append({"check": name, "ok": bool(ok), "detail": str(detail)})
        return ok

    chk("config_status", cfg.get("status") == expected_status, f"{cfg.get('status')} (expected {expected_status})")
    for path in [("dataset", "manifest"), ("splits", "outer"), ("dataset", "label_mapping"), ("splits", "inner"), ("features", "register")]:
        item = cfg.get(path[0], {}).get(path[1])
        if isinstance(item, dict) and "file" in item and "sha256" in item:
            p = root / item["file"]
            chk(f"hash:{item['file']}", p.exists() and sha256_file(p) == item["sha256"], "missing" if not p.exists() else "")
    for key in ("windows", "features", "model", "distinguishability", "policy_primary", "thresholds", "seeds"):
        chk(f"config_section:{key}", key in cfg)
    if not all(c["ok"] for c in checks):
        raise PreflightError(_fmt(checks))
    man = pd.read_csv(root / cfg["dataset"]["manifest"]["file"])
    miss = [c for c in MANIFEST_COLS if c not in man.columns]
    if not chk("manifest_columns", not miss, f"missing {miss}"):
        raise PreflightError(_fmt(checks))
    el = man[man.eligible_primary.astype(bool)]
    chk("eligible_count", len(el) == int(cfg["dataset"]["eligible_runs"]), f"{len(el)} vs {cfg['dataset']['eligible_runs']}")
    chk("unique_scenarios", el.Scenario_ID.is_unique)
    chk("classes", set(el.label_mapped) == set(cfg["dataset"]["classes"]), sorted(set(el.label_mapped)))
    chk("exclusions_have_reasons", (man.loc[~man.eligible_primary.astype(bool), "exclusion_reason"].fillna("").str.len() > 0).all())
    famcol = cfg["dataset"].get("family_column", "Scenario_Family_ID")
    if not chk("family_column_present", famcol in el.columns, famcol):
        raise PreflightError(_fmt(checks))
    el = el.assign(Scenario_Family_ID=el[famcol])  # the family map in force (primary or registered sensitivity map)
    chk("families_nest_in_topology", el.groupby("Scenario_Family_ID").topology.nunique().max() == 1)
    folds = pd.read_csv(root / cfg["splits"]["outer"]["file"])
    topo_of = dict(zip(el.Scenario_ID, el.topology))
    fam_of = dict(zip(el.Scenario_ID, el.Scenario_Family_ID))
    ok_sets = all(set(d.Scenario_ID) == set(el.Scenario_ID) for _, d in folds.groupby("outer_fold_id"))
    chk("folds_cover_eligible_runs_exactly", ok_sets)
    f2 = folds.assign(Scenario_Family_ID=folds.Scenario_ID.map(fam_of), topology=folds.Scenario_ID.map(topo_of))
    res = validate_outer_folds(f2, required_train_classes=cfg["dataset"]["classes"])
    chk("fold_family_isolation", res.passed, res.issues_frame().to_dict("records"))
    one_topo = all(d[d.split_role == "test"].topology.nunique() == 1 for _, d in f2.groupby("outer_fold_id"))
    topo_disjoint = all(not (set(d[d.split_role == "test"].topology) & set(d[d.split_role == "train"].topology))
                        for _, d in f2.groupby("outer_fold_id"))
    chk("fold_topology_isolation", one_topo and topo_disjoint)
    inner = cfg.get("splits", {}).get("inner")
    if isinstance(inner, dict) and "file" in inner:  # pinned inner record must equal the splits the runner derives
        ins = pd.read_csv(root / inner["file"])
        ins = ins[ins.scheme == "LOTO_within_train"]
        same = True
        for k, d in f2.groupby("outer_fold_id"):
            tr = d[d.split_role == "train"]
            derived = {frozenset(g.Scenario_ID) for _, g in tr.groupby("topology")}
            pinned = {frozenset(str(v).split(";")) for v in ins[ins.outer_fold_id == k].val_scenarios}
            same &= derived == pinned
        chk("inner_folds_match_runner", same and len(ins) > 0)
    fcol, hcol = ("file_noise_added", "sha256_noise_added") if realization == "noise_added" else ("file_clean", "sha256_clean")
    bad = [r.Scenario_ID for r in el.itertuples() if not (raw_parent / getattr(r, fcol)).exists()
           or sha256_file(raw_parent / getattr(r, fcol)) != getattr(r, hcol)]
    chk(f"raw_files_present_and_unmodified[{realization}]", not bad, bad[:5])
    flags = set(cfg["policy_primary"]["unresolved_flags"]) | set(cfg["policy_primary"]["specific_blocking_flags"])
    chk("policy_flags_known", flags <= set(ALL_FLAGS), sorted(flags - set(ALL_FLAGS)))
    chk("thresholds_from_development", cfg["thresholds"]["source"] == "development")
    mc = cfg["thresholds"].get("matched_coverage") or {}
    chk("matched_coverage_rule_prespecified", mc.get("selection") == "exact_count" and bool(mc.get("tie_break_salt"))
        and mc.get("tie_break_key") == "sha256(salt|window_id)", mc)
    if not all(c["ok"] for c in checks):
        raise PreflightError(_fmt(checks))
    return {"checks": checks, "eligible_runs": len(el), "folds": int(folds.outer_fold_id.nunique())}


def _fmt(checks):
    return "; ".join(f"{c['check']}: {c['detail']}" for c in checks if not c["ok"])


# ----------------------------------------------------------------------------- features
def build_features(cfg: Dict, root: Path, raw_parent: Path, realization: str) -> Tuple[pd.DataFrame, Dict]:
    man = normalize_manifest_columns(pd.read_csv(root / cfg["dataset"]["manifest"]["file"]))
    w = cfg["windows"]
    wc = WindowConfig(w["window_s"], w["stride_s"], w["min_samples"], w["label_mode"], w["pre_event_policy"])
    out = build_feature_table(man, raw_parent, realization, cfg["dataset"]["family_column"], wc, cfg["features"]["statistics"])
    ft = out["features"]
    wm = out["window_manifest"].set_index("window_id")
    ft = ft.join(wm[["start_time", "end_time", "file_id"]], on="window_id")
    ft["realization"] = realization
    ft["feature_version"] = f"{cfg.get('version')}|{','.join(cfg['features']['statistics'])}"
    el = man[man.eligible_primary_candidate.astype(bool)]
    per_run = ft.groupby("Scenario_ID").size().reindex(el.Scenario_ID, fill_value=0)
    if (per_run == 0).any():  # no silent drops: a run without eligible windows is a hard failure
        raise PreflightError(f"runs without eligible windows: {per_run[per_run == 0].index.tolist()}")
    cls_of = dict(zip(el.Scenario_ID, el.candidate_primary_class))
    n_post_dropped = 0
    if w["pre_event_policy"] == "label_normal":
        # registered sensitivity relabels only PRE-event rows; windows.py would also keep post-event NORMAL rows,
        # which the protocol excludes (post-delay rows) -> drop them so exactly one choice differs from primary
        post = ft.window_id.map(wm["boundary_status"]) == "POST_EVENT"
        n_post_dropped = int(post.sum())
        ft = ft[~post].reset_index(drop=True)
        out["feature_table_sha256"] = table_sha256(ft.drop(columns=["start_time", "end_time", "file_id", "realization",
                                                                    "feature_version"]))
    run_cls = ft.Scenario_ID.map(cls_of)
    ok = ft.label_mapped == run_cls
    if w["pre_event_policy"] == "label_normal":
        ok |= (ft.label_mapped == "NORMAL") & (ft.window_id.map(wm["boundary_status"]) == "PRE_EVENT")
    wrong = ft[~ok]
    if len(wrong):  # windows must carry the run's class (pre/post-event and boundary windows were excluded)
        raise PreflightError(f"{len(wrong)} eligible windows carry a label different from their run class")
    if set(ft.label_mapped) - set(cfg["dataset"]["classes"]):
        raise PreflightError(f"invalid event labels {sorted(set(ft.label_mapped) - set(cfg['dataset']['classes']))}")
    summary = {"n_windows": len(ft), "n_post_event_windows_dropped": n_post_dropped, "feature_table_sha256": out["feature_table_sha256"],
               "window_manifest_sha256": out["window_manifest_sha256"], "n_features": len(model_feature_columns(ft)),
               "windows_per_class": ft.label_mapped.value_counts().sort_index().to_dict(),
               "windows_per_topology_class": {f"{a}|{b}": int(v) for (a, b), v in ft.groupby(["topology", "label_mapped"]).size().items()}}
    return ft, summary


# ----------------------------------------------------------------------------- stages
def _grid(cfg) -> List[Dict]:
    g = cfg["model"]["grid"]
    return [dict(zip(g, v)) for v in itertools.product(*g.values())]


def _dconfig(cfg, oos=None) -> DConfig:
    d = {k: v for k, v in cfg["distinguishability"].items() if k in DConfig.__dataclass_fields__}
    return DConfig(**d, out_of_support_distance=oos)


def _support(cfg, ref: pd.DataFrame, query: pd.DataFrame, feats, classes) -> pd.DataFrame:
    """D(x) for query rows with a reference built only from ``ref`` (OOS threshold fitted on ref)."""
    es = EmpiricalSupport(_dconfig(cfg)).fit(ref[feats].to_numpy(float), ref.label_mapped, ref.Scenario_Family_ID,
                                             ref.Scenario_ID, classes)
    thr = es.fit_out_of_support_threshold(cfg["distinguishability"]["out_of_support_quantile"])
    es2 = EmpiricalSupport(_dconfig(cfg, thr)).fit(ref[feats].to_numpy(float), ref.label_mapped, ref.Scenario_Family_ID,
                                                   ref.Scenario_ID, classes)
    out = es2.compute(query[feats].to_numpy(float), query_families=query.Scenario_Family_ID.to_numpy())
    out.index = query.index
    return out


def _policies(cfg) -> Dict[str, Dict]:
    prim = cfg["policy_primary"]
    warn = dict(prim)
    warn.update(cfg.get("policy_sensitivity_warning_only", {}).get("same_as_primary_except", {}))
    return {"primary": prim, "warning_only": warn}


def _targets(cfg) -> List[float]:
    t = cfg["thresholds"]
    return [float(t["target_coverage_primary"])] + [float(x) for x in t.get("target_coverage_secondary", [])]


def _available(scores, flags, pol) -> np.ndarray:
    blocked = set(pol["unresolved_flags"]) | set(pol["specific_blocking_flags"])
    fl = [set(str(f).split("|")) - {""} for f in flags]
    return np.isfinite(scores) & np.array([not (f & blocked) for f in fl])


def _required_count(target: float, n: int) -> int:
    """Number of SPECIFIC decisions a target coverage requires; denominator = all eligible windows of the evaluated set."""
    return 0 if n == 0 else int(math.ceil(float(target) * n - 1e-9))


def _rank_threshold(scores, avail, target) -> Tuple[Optional[float], float]:
    """Development threshold (threshold-transfer rule): the score of the m-th best available row.

    Ties at this value are all accepted when the threshold is transferred (a deployable threshold
    cannot split ties); realized coverage is reported separately. Returns (None, max_cov) if unattainable.
    """
    n = len(scores)
    max_cov = float(avail.mean()) if n else 0.0
    m = _required_count(target, n)
    if n == 0 or m > int(avail.sum()) or m == 0:
        return None, max_cov
    return float(np.sort(scores[avail])[::-1][m - 1]), max_cov


def tie_keys(window_ids, salt: str) -> np.ndarray:
    """Label-free, platform-independent tie-break keys: SHA-256 of '<salt>|<window_id>' (UTF-8).

    A salted hash is used instead of the raw window_id so that the tie order is not aligned with run,
    topology or class ordering that may be encoded in identifiers.
    """
    return np.array([hashlib.sha256(f"{salt}|{w}".encode("utf-8")).hexdigest() for w in window_ids], dtype=object)


def exact_count_selection(scores, avail, window_ids, target: float, salt: str) -> Tuple[Optional[np.ndarray], Dict]:
    """Primary matched-coverage rule (protocol amendment PA-1).

    Select exactly m = ceil(target * n) rows, n = all rows of the evaluated set, from the eligible rows
    (``avail``: finite score and no unresolved/specific-blocking flag), ordered by score (descending)
    then by ``tie_keys`` (ascending). Never uses labels. If fewer than m rows are eligible the target is
    not attainable and ``None`` is returned (never forced).
    """
    scores = np.asarray(scores, dtype=float)
    avail = np.asarray(avail, dtype=bool) & np.isfinite(scores)
    window_ids = np.asarray(window_ids).astype(str)
    if len(set(window_ids)) != len(window_ids):
        raise ValueError("window_id must be unique for deterministic tie resolution")
    n, n_av = len(scores), int(avail.sum())
    m = _required_count(target, n)
    info = {"denominator_n": n, "requested_count": m, "n_eligible_for_specific": n_av,
            "max_attainable_coverage": (n_av / n) if n else 0.0}
    if n == 0 or m > n_av:
        return None, {**info, "realized_count": None, "realized_coverage": None}
    idx = np.flatnonzero(avail)
    order = np.lexsort((tie_keys(window_ids[idx], salt), -scores[idx]))
    sel = idx[order[:m]]
    mask = np.zeros(n, dtype=bool)
    mask[sel] = True
    if m:
        boundary = scores[idx[order[m - 1]]]
        tied = scores[idx] == boundary
        info.update(boundary_score=float(boundary), n_tied_at_boundary=int(tied.sum()),
                    n_tied_selected=int((scores[sel] == boundary).sum()))
    else:
        info.update(boundary_score=None, n_tied_at_boundary=0, n_tied_selected=0)
    return mask, {**info, "realized_count": m, "realized_coverage": m / n}


def _matched_cfg(cfg) -> Dict:
    mc = cfg["thresholds"].get("matched_coverage")
    if not mc:
        raise PreflightError("thresholds.matched_coverage (tie rule) must be prespecified in the config")
    return mc


def _scores_frame(P, D, sC, sCmD) -> pd.DataFrame:
    comp = compute_comparators(P, D)
    return pd.DataFrame({"s_C": sC, "s_C_minus_D": sCmD, "confidence": comp.C.to_numpy(), "margin": comp.M.to_numpy(),
                         "neg_entropy": comp.neg_H.to_numpy(), "D_only": comp.D.to_numpy()})


def development_stage(cfg, dev: pd.DataFrame, feats: List[str]) -> Dict:
    classes = list(cfg["dataset"]["classes"])
    seed = int(cfg["seeds"]["global"])
    topo = dev.topology.to_numpy()
    n_t = len(set(topo))
    X, y = dev[feats].to_numpy(float), dev.label_mapped.to_numpy()
    yidx = np.array([classes.index(v) for v in y])
    rcfg = GroupedRunConfig(classes=classes, param_grid=_grid(cfg), inner_n_splits=n_t, seed=seed,
                            model_name="random_forest_primary", independence_col="topology")
    _, params, P_oof, sel_rows = select_on_development(X, y, topo, make_random_forest, rcfg)
    feas = calibration_feasibility(yidx, topo, len(classes), int(cfg["calibration"]["feasibility_rule"]["min_groups_per_class"]))
    methods = [m for m in cfg["calibration"]["candidates"] if m in feas["allowed_methods"]]
    if methods == ["none"] or not methods:
        cal_method, cal_table = "none", None
    else:
        sel = select_calibration(P_oof, yidx, topo, len(classes), n_splits=n_t, criterion=cfg["calibration"]["criterion"], methods=methods)
        cal_method, cal_table = sel["selected_method"], sel["table"]
    P_cal = np.zeros_like(P_oof)
    for t in sorted(set(topo)):  # cross-fitted calibrated development probabilities
        m = topo == t
        P_cal[m] = fit_calibrator(cal_method, P_oof[~m], yidx[~m], len(classes)).transform(P_oof[m])
    sup = pd.concat([_support(cfg, dev[dev.topology != t], dev[dev.topology == t], feats, classes) for t in sorted(set(topo))])
    sup = sup.loc[dev.index]
    D = sup.D.to_numpy(float)
    correct = (P_cal.argmax(1) == yidx).astype(int)
    csc = dict(n_splits=n_t, seed=seed, C=float(cfg.get("combined_scores", {}).get("fit", {}).get("C", 1.0)))
    fitC = fit_combined_score(P_cal, correct, topo, CombinedScoreConfig(include_D=True, **csc), D)
    fitCmD = fit_combined_score(P_cal, correct, topo, CombinedScoreConfig(include_D=False, **csc), D)
    S = _scores_frame(P_cal, D, fitC["oof_scores"], fitCmD["oof_scores"])
    thr = []
    for vname, pol in _policies(cfg).items():
        av = _available(np.zeros(len(S)), sup.support_flags.fillna(""), pol)  # flags only; method finiteness below
        for meth in METHODS:
            avm = av & np.isfinite(S[meth].to_numpy())
            for tg in _targets(cfg):
                sc = S[meth].to_numpy()
                tau, max_cov = _rank_threshold(sc, avm, tg)
                thr.append({"variant": vname, "method": meth, "target": tg, "tau": tau, "dev_max_attainable_coverage": max_cov,
                            "dev_realized_coverage_at_tau": float((avm & (sc >= tau)).mean()) if tau is not None else None,
                            "dev_status": "ESTIMABLE" if tau is not None else "NOT_ESTIMABLE_UNDER_PRIMARY_PROTOCOL"})
    return {"params": params, "selection": pd.DataFrame(sel_rows), "cal_method": cal_method,
            "cal_feasibility": feas, "cal_table": cal_table, "P_oof": P_oof, "y_idx": yidx,
            "fitC": fitC, "fitCmD": fitCmD, "thresholds": pd.DataFrame(thr),
            "dev_flags": sup.support_flags.fillna("").value_counts().to_dict()}


def _decide(P, scores, flags, classes, pol, tau):
    pc = PolicyConfig(config_id="protocol", tau_accept=tau, ambiguity_mass=float(pol["ambiguity_mass"]),
                      max_set_size=int(pol["max_set_size"]), singleton_handling=pol["singleton_handling"],
                      threshold_source="development", unresolved_flags=tuple(pol["unresolved_flags"]),
                      specific_blocking_flags=tuple(pol["specific_blocking_flags"]))
    return apply_policy(P, scores, classes, pc, flags=list(flags))


def outer_stage(cfg, dev: pd.DataFrame, test: pd.DataFrame, feats: List[str], devres: Dict) -> Tuple[pd.DataFrame, pd.DataFrame]:
    classes = list(cfg["dataset"]["classes"])
    est = make_random_forest(devres["params"], int(cfg["seeds"]["global"])).fit(dev[feats].to_numpy(float), dev.label_mapped.to_numpy())
    P_raw = _aligned_proba(est, test[feats].to_numpy(float), classes)
    cal = fit_calibrator(devres["cal_method"], devres["P_oof"], devres["y_idx"], len(classes))
    P = cal.transform(P_raw)
    sup = _support(cfg, dev, test, feats, classes)
    D = sup.D.to_numpy(float)
    S = _scores_frame(P, D, apply_combined_score(devres["fitC"], P, D, True), apply_combined_score(devres["fitCmD"], P, D, False))
    pred = test[["window_id", "Scenario_ID", "Scenario_Family_ID", "topology", "label_mapped"]].rename(columns={"label_mapped": "y_true"}).reset_index(drop=True)
    for j, c in enumerate(classes):
        pred[f"p_raw_{c}"], pred[f"p_cal_{c}"] = P_raw[:, j], P[:, j]
    for c in ("D", "support_flags", "top_class_n_families", "n_distinct_scenarios"):
        pred[c] = sup[c].to_numpy()
    for c in S.columns:
        pred[f"score_{c}"] = S[c].to_numpy()
    rows, tie_rows = [], []
    th = devres["thresholds"]
    mc = _matched_cfg(cfg)
    salt = str(mc["tie_break_salt"])
    n_sens = int(mc.get("tie_sensitivity", {}).get("n_alternative_salts", 0))
    wid = pred.window_id.to_numpy()
    flags = pred.support_flags.fillna("")
    y_hat = np.array(classes, dtype=object)[np.argmax(P, axis=1)]  # same argmax/lowest-index rule as the policy
    for vname, pol in _policies(cfg).items():
        av = _available(np.zeros(len(S)), flags, pol)  # flags only; method finiteness below
        av &= np.isfinite(P).all(axis=1)
        for meth in METHODS:
            sc = S[meth].to_numpy()
            avm = av & np.isfinite(sc)
            for tg in _targets(cfg):
                tau_dev = th[(th.variant == vname) & (th.method == meth) & (th.target == tg)].tau.iloc[0]
                # threshold transfer: development threshold applied unchanged (ties at tau all accepted)
                base = {"variant": vname, "method": meth, "target": tg, "mode": "threshold_transfer",
                        "test_max_attainable_coverage": float(avm.mean()) if len(avm) else 0.0}
                if tau_dev is None or (isinstance(tau_dev, float) and not np.isfinite(tau_dev)):
                    rows.append({**base, "status": "NOT_ESTIMABLE_UNDER_PRIMARY_PROTOCOL"})
                else:
                    d = _decide(P, np.where(np.isfinite(sc), sc, np.nan), flags, classes, pol, float(tau_dev))
                    rows.append({**base, "status": "ESTIMABLE", "tau": float(tau_dev), "decisions": d.assign(window_id=wid)})
                # rank matched (primary RQ1 rule, PA-1): exact count, deterministic label-free tie key
                mask, info = exact_count_selection(sc, avm, wid, tg, salt)
                base = {"variant": vname, "method": meth, "target": tg, "mode": "rank_matched",
                        "test_max_attainable_coverage": info["max_attainable_coverage"],
                        **{k: info.get(k) for k in ("denominator_n", "requested_count", "realized_count", "realized_coverage",
                                                   "n_tied_at_boundary", "n_tied_selected", "boundary_score")}}
                if mask is None:
                    rows.append({**base, "status": "NOT_ESTIMABLE_UNDER_PRIMARY_PROTOCOL"})
                    continue
                eff = np.where(mask, 1.0, np.where(np.isfinite(sc), -1.0, np.nan))  # selected <=> SPECIFIC-eligible
                d = _decide(P, eff, flags, classes, pol, 0.0)
                n_spec = int((d.policy_outcome == SPECIFIC).sum())
                if n_spec != info["realized_count"]:
                    raise AssertionError(f"rank_matched selected {info['realized_count']} but policy issued {n_spec} SPECIFIC")
                rows.append({**base, "status": "ESTIMABLE", "tau": info["boundary_score"], "decisions": d.assign(window_id=wid)})
                if vname == "primary" and meth in ("s_C", "s_C_minus_D"):
                    for j in range(n_sens):  # tie-order sensitivity: alternative salts (secondary, labelled)
                        mj, _ = exact_count_selection(sc, avm, wid, tg, f"{salt}|sensitivity|{j}")
                        for fam, idx in pred.groupby("Scenario_Family_ID").indices.items():
                            s = mj[idx]
                            tie_rows.append({"target": tg, "salt_index": j, "method": meth, "Scenario_Family_ID": fam,
                                             "topology": pred.topology.iloc[idx[0]], "n_selected": int(s.sum()),
                                             "n_errors": int((y_hat[idx][s] != pred.y_true.to_numpy()[idx][s]).sum())})
    return pred, rows, pd.DataFrame(tie_rows)


# ----------------------------------------------------------------------------- aggregation
def reliability_bins(preds: pd.DataFrame, classes: List[str], n_bins: int = 10) -> pd.DataFrame:
    """Top-label reliability on outer-test windows (raw and calibrated), 10 equal-width bins; empty bins omitted."""
    rows = []
    if not all(f"p_{k}_{c}" in preds.columns for k in ("raw", "cal") for c in classes):
        return pd.DataFrame(rows)  # unit-test inputs without probabilities
    y = preds.y_true.to_numpy()
    for kind in ("raw", "cal"):
        P = preds[[f"p_{kind}_{c}" for c in classes]].to_numpy(float)
        conf = P.max(axis=1)
        correct = np.array(classes, dtype=object)[P.argmax(axis=1)] == y
        b = np.minimum((conf * n_bins).astype(int), n_bins - 1)
        for i in range(n_bins):
            m = b == i
            if m.any():
                rows.append({"probability": kind, "bin": i, "bin_low": i / n_bins, "bin_high": (i + 1) / n_bins,
                             "mean_confidence": float(conf[m].mean()), "accuracy": float(correct[m].mean()), "n": int(m.sum())})
    return pd.DataFrame(rows)


def aggregate(cfg, preds: pd.DataFrame, dec_rows: List[Dict], artifact_class: str,
              tie_counts: Optional[pd.DataFrame] = None, analysis: str = "primary") -> Dict[str, object]:
    classes = list(cfg["dataset"]["classes"])
    y_of = dict(zip(preds.window_id, preds.y_true))
    fam_of = dict(zip(preds.window_id, preds.Scenario_Family_ID))
    top_of = dict(zip(preds.window_id, preds.topology))
    cov, est, longd = [], [], []
    for r in dec_rows:
        key = {k: r[k] for k in ("fold", "variant", "method", "target", "mode")}
        est.append({**key, "status": r["status"], "test_max_attainable_coverage": r["test_max_attainable_coverage"],
                    **{k: r.get(k) for k in ("requested_count", "realized_count", "realized_coverage", "n_tied_at_boundary",
                                            "n_tied_selected", "tau")}})
        if r["status"] != "ESTIMABLE":
            continue
        d = r["decisions"].copy()
        for k, v in key.items():
            d[k] = v
        longd.append(d)
    D = pd.concat(longd, ignore_index=True) if longd else pd.DataFrame()
    if len(D):
        D["y_true"] = D.window_id.map(y_of)
        D["Scenario_Family_ID"] = D.window_id.map(fam_of)
        D["topology"] = D.window_id.map(top_of)
        # RQ2 consistency checks (fail loudly if violated)
        sets = D.ambiguity_set.fillna("")
        bad_sets = D[(D.policy_outcome == AMBIGUITY_SET) & ~sets.apply(lambda s: 2 <= len(s.split("|")) <= len(classes) - 1)]
        if len(bad_sets):
            raise AssertionError(f"{len(bad_sets)} invalid ambiguity sets")
        if (D[D.policy_outcome != SPECIFIC].y_pred_specific.notna()).any():
            raise AssertionError("non-SPECIFIC outcome carries a specific prediction")
        for (v, m, t, mo), g in D.groupby(["variant", "method", "target", "mode"]):
            r = coverage_and_risk(g.policy_outcome, g.y_pred_specific, g.y_true)
            a = ambiguity_summary(g.policy_outcome, g.ambiguity_set.fillna(""), g.y_true, len(classes))
            assert r["n_specific"] + r["n_ambiguity"] + r["n_unresolved"] == r["n_eligible"]
            cov.append({"variant": v, "method": m, "target": t, "mode": mo, "folds_estimable": g.fold.nunique(),
                        "n_families": int(g.Scenario_Family_ID.nunique()), **r,
                        **{f"ambiguity_{k}": val for k, val in a.items()}})
    n_folds = preds.fold.nunique() if "fold" in preds else 0
    est_df = pd.DataFrame(est)
    rq1 = []
    for mb, role in COMPARISONS:
        pair = est_df[est_df.method.isin(["s_C", mb])] if len(est_df) else est_df
        if not len(pair) or pair.method.nunique() < 2:
            continue  # comparator not part of this run (only possible in unit tests; real runs score all METHODS)
        combos = sorted({(r.variant, r.target, r.mode) for r in pair.itertuples()})
        Dp = D[D.method.isin(["s_C", mb])] if len(D) else D
        for v, t, mo in combos:  # every registered comparison gets a row; nothing is silently omitted
          key = {"comparison_a": "s_C", "comparison_b": mb, "comparison_role": role, "variant": v, "target": t, "mode": mo}
          ok = pair[(pair.variant == v) & (pair.target == t) & (pair["mode"] == mo)]
          g = Dp[(Dp.variant == v) & (Dp.target == t) & (Dp["mode"] == mo)] if len(Dp) else Dp
          if (ok.status != "ESTIMABLE").any() or not len(g) or g.fold.nunique() < n_folds:
              rq1.append({**key, "status": "NOT_ESTIMABLE_UNDER_PRIMARY_PROTOCOL",
                          "folds_estimable": int((ok[ok.status == "ESTIMABLE"].groupby("fold").method.nunique() == 2).sum()),
                          "n_folds": n_folds})
              continue
          units = []
          for fam, gf in g.groupby("Scenario_Family_ID"):
              a, b = gf[gf.method == "s_C"], gf[gf.method == mb]
              assert set(a.window_id) == set(b.window_id)  # aligned evaluation units
              spec = lambda x: x[x.policy_outcome == SPECIFIC]
              units.append({"unit": fam, "stratum": gf.topology.iloc[0],
                            "num_a": int((spec(a).y_pred_specific != spec(a).y_true).sum()), "den_a": len(spec(a)),
                            "num_b": int((spec(b).y_pred_specific != spec(b).y_true).sum()), "den_b": len(spec(b))})
          U = pd.DataFrame(units)
          u = cfg.get("evaluation", {}).get("uncertainty", {})
          bs = paired_stratified_bootstrap(U, int(u.get("n_boot", 2000)), int(u.get("seed", 0)))
          cov_a = float((g[g.method == "s_C"].policy_outcome == SPECIFIC).mean())
          cov_b = float((g[g.method == mb].policy_outcome == SPECIFIC).mean())
          if mo == "rank_matched":  # PA-1: exact-count matching must give identical coverage per fold
              for _, gk in g.groupby("fold"):
                  na = int((gk[gk.method == "s_C"].policy_outcome == SPECIFIC).sum())
                  nb = int((gk[gk.method == mb].policy_outcome == SPECIFIC).sum())
                  if na != nb:
                      raise AssertionError(f"rank_matched coverage not matched ({na} vs {nb})")
          rq1.append({**key, "status": "ESTIMABLE",
                      "realized_coverage_a": cov_a, "realized_coverage_b": cov_b,
                      "coverage_gap_a_minus_b": cov_a - cov_b,  # 0 by construction in rank_matched; reported for threshold_transfer
                      **{k: bs[k] for k in ("estimate_a", "estimate_b", "difference", "ci_low", "ci_high", "n_units", "n_boot_undefined")},
                      "comparison": f"selective risk s_C minus {mb} (negative = lower risk for s_C)",
                      "interpretation": bs["interpretation"]})
    rq2 = []
    per_class = cfg.get("evaluation", {}).get("per_class_reporting", {})
    if len(D):
        for (v, m, t, mo), g in D[D.method == "s_C"].groupby(["variant", "method", "target", "mode"]):
            for c, gc in g.groupby("y_true"):
                rq2.append({"variant": v, "target": t, "mode": mo, "class": c, "n": len(gc),
                            **{o.lower(): float((gc.policy_outcome == o).mean()) for o in (SPECIFIC, AMBIGUITY_SET, UNRESOLVED)},
                            "reporting": per_class.get(c, "UNSPECIFIED")})
    tie = []
    if tie_counts is not None and len(tie_counts):
        prim = {(r["target"]): r for r in rq1 if r["variant"] == "primary" and r["mode"] == "rank_matched"
                and r["comparison_b"] == "s_C_minus_D" and r["status"] == "ESTIMABLE"}
        for (t, j), g in tie_counts.groupby(["target", "salt_index"]):
            if t not in prim:
                continue  # sensitivity only where the primary comparison is estimable in every fold
            a, b = g[g.method == "s_C"], g[g.method == "s_C_minus_D"]
            ra = a.n_errors.sum() / a.n_selected.sum() if a.n_selected.sum() else float("nan")
            rb = b.n_errors.sum() / b.n_selected.sum() if b.n_selected.sum() else float("nan")
            tie.append({"target": t, "salt_index": int(j), "pooled_risk_a": ra, "pooled_risk_b": rb, "difference": ra - rb,
                        "primary_difference": prim[t]["difference"], "role": "TIE_ORDER_SENSITIVITY_SECONDARY"})
    tag = lambda df: df.assign(analysis=analysis, artifact_class=artifact_class) if len(df) else df
    return {"coverage_risk": tag(pd.DataFrame(cov)), "estimability": tag(est_df), "rq1": tag(pd.DataFrame(rq1)),
            "rq2": tag(pd.DataFrame(rq2)), "tie_sensitivity": tag(pd.DataFrame(tie)),
            "calibration_reliability": tag(reliability_bins(preds, classes)), "decisions": tag(D)}


# ----------------------------------------------------------------------------- orchestration
def check_authorization(path: Optional[Path], config_sha: str, artifact_class: str) -> Dict:
    if path is None or not Path(path).exists():
        raise AuthorizationError("outer-test execution requires an authorization file (none given)")
    a = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    problems = []
    if a.get("authorized") is not True:
        problems.append("authorized must be true")
    if a.get("scope") != artifact_class:
        problems.append(f"scope must be {artifact_class}")
    if a.get("config_sha256") != config_sha:
        problems.append("config_sha256 does not match the config being run")
    for k in ("authorized_by", "date"):
        if not a.get(k):
            problems.append(f"{k} missing")
    gc = a.get("governance_clearance") or {}
    if not isinstance(gc, dict):
        gc = {}
    for item in REQUIRED_CLEARANCES:  # human attestations or written waivers; the runner never infers them
        v = str(gc.get(item, "")).strip()
        if not (v.startswith("ATTESTED") or v.startswith("WAIVED")):
            problems.append(f"governance_clearance.{item} must start with ATTESTED or WAIVED")
    if problems:
        raise AuthorizationError("; ".join(problems))
    return a


def run(config_path: Path, root: Path, raw_parent: Path, out_dir: Path, mode: str,
        artifact_class: Optional[str] = None, authorization: Optional[Path] = None,
        stop_after_fold: Optional[int] = None, sensitivity: Optional[str] = None) -> Dict:
    config_path, root, raw_parent, out_dir = map(lambda p: Path(p).resolve(), (config_path, root, raw_parent, out_dir))
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    cfg_sha = sha256_file(config_path)
    if mode == "execute" and (artifact_class == "SENSITIVITY_EXPERIMENT") != (sensitivity is not None):
        raise AuthorizationError("SENSITIVITY_EXPERIMENT requires --sensitivity NAME and vice versa")
    cfg = apply_sensitivity(cfg, sensitivity)
    derived_sha = hashlib.sha256(json.dumps(cfg, sort_keys=True, default=str).encode()).hexdigest() if sensitivity else cfg_sha
    if mode == "preflight":
        artifact_class, status = "PREFLIGHT_ONLY", (SYNTH_STATUS if cfg.get("status") == SYNTH_STATUS else REAL_STATUS)
        realization = cfg["dataset"]["realization_primary"]
    elif mode == "synthetic":
        artifact_class, status, realization = "SYNTHETIC_TEST", SYNTH_STATUS, cfg["dataset"]["realization_primary"]
        results_dir = (Path(__file__).resolve().parents[3] / "03_results").resolve()
        if str(out_dir).startswith(str(results_dir)):
            raise PreflightError("synthetic outputs may not be written under 03_results/ (genuine results directory)")
    elif mode == "execute":
        if artifact_class not in EXECUTE_CLASSES:
            raise AuthorizationError(f"artifact_class must be one of {sorted(EXECUTE_CLASSES)}")
        status = REAL_STATUS
        scope = f"SENSITIVITY_EXPERIMENT:{sensitivity}" if sensitivity else artifact_class
        check_authorization(authorization, cfg_sha, scope)
        realization = EXECUTE_CLASSES[artifact_class] or cfg["dataset"]["realization_primary"]
    else:
        raise ValueError(f"unknown mode {mode}")

    pre = preflight(cfg, root, raw_parent, realization, status)
    ft, fsum = build_features(cfg, root, raw_parent, realization)
    feats = [c for c in model_feature_columns(ft) if "__" in c]
    expected = [f"{ch}__{s}" for ch in SENSOR_CHANNELS for s in cfg["features"]["statistics"]]
    if sorted(feats) != sorted(expected):  # only registered sensor statistics may be model inputs
        raise PreflightError(f"feature set mismatch: unexpected {sorted(set(feats) - set(expected))[:5]}, missing {sorted(set(expected) - set(feats))[:5]}")
    n_nonfinite = int((~np.isfinite(ft[feats].to_numpy(float))).sum())
    if n_nonfinite:  # D(x) standardisation and RF inputs require finite features; no silent imputation
        raise PreflightError(f"{n_nonfinite} non-finite feature values in the eligible feature table")
    fsum["n_nonfinite_feature_values"] = 0
    if not ft.window_id.is_unique:
        raise PreflightError("window_id is not unique (required for deterministic tie resolution)")
    folds = pd.read_csv(root / cfg["splits"]["outer"]["file"])
    code_sha = _code_sha256()
    run_key = hashlib.sha256(f"{derived_sha}|{fsum['feature_table_sha256']}|{realization}|{mode}|{code_sha}".encode()).hexdigest()
    prev = out_dir / "run_manifest.json"
    if prev.exists():  # never mix outputs of different runs in one directory (fail closed)
        old = json.loads(prev.read_text(encoding="utf-8"))
        if old.get("run_key") != run_key:
            raise PreflightError(f"output directory holds a different run (run_key {str(old.get('run_key'))[:12]}...); use a new --out")
    manifest = {"artifact_class": artifact_class, "mode": mode, "status": "RUNNING", "run_key": run_key,
                "config_sha256": cfg_sha, "config_file": config_path.name, "realization": realization, "code_sha256": code_sha,
                "git_commit": _git_commit(root), "seed": cfg["seeds"]["global"], "preflight": pre, "features": fsum,
                "input_sha256": {k: cfg[a][b]["sha256"] for k, (a, b) in
                                 {"manifest": ("dataset", "manifest"), "outer_folds": ("splits", "outer"), "inner_folds": ("splits", "inner"),
                                  "label_mapping": ("dataset", "label_mapping"), "feature_register": ("features", "register")}.items()
                                 if isinstance(cfg.get(a, {}).get(b), dict) and "sha256" in cfg[a][b]},
                "prohibited_claims": PROHIBITED_CLAIMS,
                "sensitivity": cfg.get("sensitivity_applied"), "effective_config_sha256": derived_sha}
    write_json(manifest, out_dir / "run_manifest.json")
    if mode == "preflight":
        classes = cfg["dataset"]["classes"]
        share = ft.groupby("topology").label_mapped.value_counts(normalize=True).unstack(fill_value=0)
        manifest["structural_class_share_per_topology"] = share.round(6).to_dict(orient="index")
        manifest["status"] = "PREFLIGHT_PASSED"
        write_json(manifest, out_dir / "run_manifest.json")
        return manifest

    preds, dec_rows, cal_records, ties = [], [], [], []
    for k, d in folds.groupby("outer_fold_id", sort=True):
        fdir = out_dir / "folds" / f"fold_{k}"
        done = fdir / "DONE.json"
        tr_ids, te_ids = set(d[d.split_role == "train"].Scenario_ID), set(d[d.split_role == "test"].Scenario_ID)
        dev, test = ft[ft.Scenario_ID.isin(tr_ids)].copy(), ft[ft.Scenario_ID.isin(te_ids)].copy()
        assert_group_disjoint(dev.Scenario_Family_ID, test.Scenario_Family_ID, "family")
        assert_group_disjoint(dev.topology, test.topology, "topology")
        assert_group_disjoint(dev.Scenario_ID, test.Scenario_ID, "run")
        if done.exists() and json.loads(done.read_text(encoding="utf-8")).get("run_key") == run_key:
            p = pd.read_csv(fdir / "predictions.csv")
            rows = json.loads((fdir / "decision_index.json").read_text(encoding="utf-8"))
            for r in rows:
                if r["status"] == "ESTIMABLE":
                    r["decisions"] = pd.read_csv(fdir / r["decisions_file"], keep_default_na=False).replace({"y_pred_specific": {"": None}})
            preds.append(p)
            dec_rows += rows
            cal_records.append(json.loads((fdir / "calibration.json").read_text(encoding="utf-8")))
            tp = fdir / "tie_sensitivity_counts.csv"
            ties.append(pd.read_csv(tp) if tp.stat().st_size > 1 else pd.DataFrame())
            continue
        devres = development_stage(cfg, dev, feats)
        pred, rows, tie_df = outer_stage(cfg, dev, test, feats, devres)
        write_csv(tie_df.assign(fold=k), fdir / "tie_sensitivity_counts.csv")
        ties.append(tie_df.assign(fold=k))
        pred["fold"] = k
        cal = {"fold": int(k), "method": devres["cal_method"], "feasibility": devres["cal_feasibility"],
               "params": devres["params"], "dev_support_flags": devres["dev_flags"]}
        write_csv(pred.assign(artifact_class=artifact_class), fdir / "predictions.csv")
        write_csv(devres["thresholds"].assign(fold=k, artifact_class=artifact_class), fdir / "thresholds.csv")
        write_csv(devres["selection"].assign(fold=k), fdir / "selection.csv")
        if devres["cal_table"] is not None:  # F6 CALIBRATION_RESULTS: development comparison of candidate methods
            write_csv(devres["cal_table"].assign(fold=k, selected=devres["cal_method"]), fdir / "calibration_selection.csv")
        write_json(cal, fdir / "calibration.json")
        index = []
        for i, r in enumerate(rows):
            r["fold"] = int(k)
            entry = {kk: vv for kk, vv in r.items() if kk != "decisions"}
            if r["status"] == "ESTIMABLE":
                entry["decisions_file"] = f"decisions_{i:03d}.csv"
                write_csv(r["decisions"], fdir / entry["decisions_file"])
            index.append(entry)
        write_json(index, fdir / "decision_index.json")
        write_json({"run_key": run_key, "fold": int(k)}, done)
        preds.append(pred)
        dec_rows += rows
        cal_records.append(cal)
        if stop_after_fold is not None and int(k) == int(stop_after_fold):
            raise InterruptedError(f"stopped after fold {k} (simulated interruption)")
    P = pd.concat(preds, ignore_index=True)
    T = pd.concat([t for t in ties if len(t)], ignore_index=True) if any(len(t) for t in ties) else pd.DataFrame()
    agg = aggregate(cfg, P, dec_rows, artifact_class, T, analysis=sensitivity or "primary")
    for name in ("coverage_risk", "estimability", "rq1", "rq2", "tie_sensitivity", "calibration_reliability"):
        write_csv(agg[name], out_dir / f"{name}.csv")
    write_json(cal_records, out_dir / "calibration_records.json")
    manifest["status"] = "COMPLETED"
    manifest["n_test_windows"] = len(P)
    write_json(manifest, out_dir / "run_manifest.json")
    return {**manifest, **{k: v for k, v in agg.items() if k != "decisions"}}
