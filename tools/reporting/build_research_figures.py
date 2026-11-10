#!/usr/bin/env python3
"""
H2-PRISM research figure builder (Task A13 -- Ahmed; metric meaning verified by Faisal).

STATUS: IMPLEMENTED + TESTED (fixture-based). Consumes saved, machine-readable result
tables only. It never refits models, selects thresholds, resamples families or
computes new experimental statistics; plotted values are the input values.

Routing (cannot be overridden by the figure config):
  * evidence_status VALIDATED/FROZEN and no illustrative data -> <out>/final/
  * any other evidence_status                                 -> <out>/preliminary/ + watermark
  * input with data_status in {ILLUSTRATIVE, FIXTURE, SYNTHETIC, DEMO}
                                                              -> <out>/illustrative/ + watermark
Each output gets a row in FIGURE_BUILD_MANIFEST.csv with input/config/output SHA-256.

Supported kinds: risk_coverage (method, coverage, selective_risk),
                 reliability (mean_confidence, accuracy, n)

Usage:
  python tools/reporting/build_research_figures.py --config configs/reporting_figures.yaml --out-dir 05_documentation/figures
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import ReportingInputError, classify, load_config, load_input, sha256_path  # noqa: E402

plt.rcParams["svg.hashsalt"] = "h2prism-a13"
PNG_META = {"Software": None}
SVG_META = {"Date": None}


def _watermark(fig, text: str) -> None:
    if text:
        fig.text(0.5, 0.5, text, ha="center", va="center", rotation=25, fontsize=14,
                 color="red", alpha=0.35, transform=fig.transFigure)


def plot_risk_coverage(df: pd.DataFrame, spec: Dict):
    fig, ax = plt.subplots(figsize=(6, 4.2))
    for method, d in df.groupby("method", sort=True):
        d = d.sort_values("coverage")
        ax.plot(d["coverage"], d["selective_risk"], marker=".", label=str(method))
    ax.set_xlabel(spec.get("xlabel", "Coverage (fraction of eligible windows issued SPECIFIC)"))
    ax.set_ylabel(spec.get("ylabel", "Selective risk (error rate among SPECIFIC)"))
    ax.set_xlim(0, 1)
    ax.legend(frameon=False)
    ax.set_title(spec.get("title", ""))
    return fig


def plot_reliability(df: pd.DataFrame, spec: Dict):
    fig, ax = plt.subplots(figsize=(4.8, 4.8))
    d = df.dropna(subset=["mean_confidence", "accuracy"])
    ax.plot([0, 1], [0, 1], ls="--", lw=1, color="grey")
    ax.plot(d["mean_confidence"], d["accuracy"], marker="o")
    for _, r in d.iterrows():
        ax.annotate(str(int(r["n"])), (r["mean_confidence"], r["accuracy"]), fontsize=7)
    ax.set_xlabel("Mean top-label confidence")
    ax.set_ylabel("Empirical accuracy")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title(spec.get("title", ""))
    return fig


KINDS = {"risk_coverage": (plot_risk_coverage, ["method", "coverage", "selective_risk"]),
         "reliability": (plot_reliability, ["mean_confidence", "accuracy", "n"])}


def build(config_path: Path, out_dir: Path, root: Path) -> pd.DataFrame:
    cfg, cfg_hash = load_config(config_path)
    rows: List[Dict] = []
    errors: List[str] = []
    for spec in cfg.get("figures", []):
        kind = spec.get("kind")
        if kind not in KINDS:
            errors.append(f"[{spec.get('id')}] unsupported kind {kind}")
            continue
        fn, req = KINDS[kind]
        spec = {**spec, "required_columns": list(dict.fromkeys(req + spec.get("required_columns", [])))}
        try:
            df = load_input(root, spec)
        except ReportingInputError as exc:
            errors.append(str(exc))
            rows.append({"figure_id": spec.get("id"), "status": "NOT_BUILT_MISSING_EVIDENCE", "reason": str(exc)})
            continue
        dest, wm = classify(spec, df)
        fig = fn(df, spec)
        _watermark(fig, wm)
        if spec.get("caption"):
            fig.text(0.01, 0.005, f"Source: {spec['input']} | experiment: {spec.get('source_experiment', 'UNSPECIFIED')}",
                     fontsize=6, color="dimgray")
        fig.tight_layout()
        d = out_dir / dest
        d.mkdir(parents=True, exist_ok=True)
        stem = d / spec["id"]
        fig.savefig(stem.with_suffix(".png"), dpi=int(cfg.get("dpi", 300)), metadata=PNG_META)
        fig.savefig(stem.with_suffix(".svg"), metadata=SVG_META)
        plt.close(fig)
        for ext in (".png", ".svg"):
            rows.append({
                "figure_id": spec["id"], "status": f"BUILT_{dest.upper()}", "reason": wm,
                "output_file": stem.with_suffix(ext).as_posix(), "output_sha256": sha256_path(stem.with_suffix(ext)),
                "input_file": spec["input"], "input_sha256": sha256_path(root / spec["input"]),
                "config_file": config_path.as_posix(), "config_sha256": cfg_hash,
                "source_experiment": spec.get("source_experiment", "UNSPECIFIED"),
                "evidence_status": spec.get("evidence_status", "UNDECLARED"),
                "research_question": spec.get("research_question", ""), "caption": spec.get("caption", ""),
            })
    man = pd.DataFrame(rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    man.to_csv(out_dir / "FIGURE_BUILD_MANIFEST.csv", index=False, lineterminator="\n")
    if errors and cfg.get("fail_on_missing", True):
        raise ReportingInputError("; ".join(errors))
    return man


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--root", type=Path, default=Path("."))
    a = ap.parse_args(argv)
    try:
        build(a.config, a.out_dir, a.root)
    except ReportingInputError as exc:
        print(f"FAILED (mandatory evidence absent or invalid): {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
