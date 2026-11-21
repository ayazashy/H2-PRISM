"""Frozen replay of the accepted Study B Ridge benchmark at observation level.

Reuses the frozen functions in ``study_b/benchmark.py`` (``read_run``, ``pairs``,
``score``) and the frozen ``protocol.json``. It does not modify the protocol, split,
features, alpha or metric definitions, and it never selects anything on test data.
The replay passes only if every frozen per-run metric is reproduced within the
tolerance declared below *before* comparison.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import numpy as np

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
sys.path.insert(0, str(STUDY))

from benchmark import SIGNALS, pairs, read_run, score  # noqa: E402  (frozen implementation)
from verify_source import inventory  # noqa: E402

# Declared before any comparison. Persistence is a copy of recorded values and must match exactly.
TOLERANCE = {"persistence_abs": 0.0, "ridge_abs": 1e-12, "ridge_rel": 1e-9}


def load_protocol():
    return json.loads((STUDY / "protocol.json").read_text(encoding="utf-8-sig"))


def frozen_metrics():
    with (STUDY / "per_run_metrics.csv").open(encoding="utf-8-sig", newline="") as stream:
        return {(int(r["run"]), r["channel"]): r for r in csv.DictReader(stream)}


def protocol_text(book, run):
    """All non-empty cells above the data header of the raw sheet (source notes, verbatim)."""
    raw = book[f"Cycle Definition Exp.{run}"]
    lines = []
    for row in raw.iter_rows(max_row=85, max_col=15, values_only=True):
        if row[:3] == ("Date", "Time", "Seconds"):
            break
        cells = [str(v) for v in row if v is not None]
        if cells:
            lines.append(" ".join(cells))
    return lines


def replay(archive: Path):
    source = inventory(archive)                          # Gate A: size, MD5, safe members
    protocol = load_protocol()
    partitions = {int(r): p for r, p in protocol["partition"].items()}
    channels = protocol["targets"]
    columns = [list(SIGNALS).index(k) + 1 for k in channels]
    records, notes, dates, units = {}, {}, {}, {}
    with ZipFile(archive) as z:
        for run in partitions:
            book = load_workbook_bytes(z.read(source["experiments"][run]))
            _, _, unit_map, run_dates, time, data, _ = read_run(book, run)
            notes[run] = protocol_text(book, run)
            book.close()
            records[run] = (time, data)
            dates[run] = sorted({d for d in run_dates if d})
            units[run] = {k: unit_map.get(k) for k in ("Seconds", *channels)}
            if any(units[run][k] != SIGNALS[k] for k in channels):
                raise ValueError(f"unit mismatch in run {run}")
    examples = {n: pairs(*records[n], columns, *protocol["interval_s"]) for n in partitions}
    training = [(x, y) for run, (_, x, y) in examples.items() if partitions[run] == "development"]
    x, y = (np.concatenate(a) for a in zip(*training))
    from sklearn.linear_model import Ridge
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    model = make_pipeline(StandardScaler(), Ridge(alpha=protocol["ridge_alpha"]))
    model.fit(x, y - x)
    rows, gate = [], []
    frozen = frozen_metrics()
    for run, (index, current, actual) in examples.items():
        if partitions[run] != "test":
            continue
        estimate = current + model.predict(current)
        time = records[run][0]
        counter = records[run][1][:, 0]
        for j, i in enumerate(index):
            for c, key in enumerate(channels):
                rows.append(dict(run=run, channel=key, unit=SIGNALS[key], seconds_counter=int(counter[i + 1]),
                                 target_time_s=float(time[i + 1]), y_prev=float(current[j, c]),
                                 y_true=float(actual[j, c]), persistence=float(current[j, c]),
                                 ridge=float(estimate[j, c])))
        for c, key in enumerate(channels):
            b0 = score(actual[:, c], current[:, c])
            b1 = score(actual[:, c], estimate[:, c])
            f = frozen[(run, key)]
            for model_name, metric, value, ref in (("persistence", "mae", b0[0], f["b0_mae"]),
                                                   ("persistence", "rmse", b0[1], f["b0_rmse"]),
                                                   ("ridge", "mae", b1[0], f["b1_mae"]),
                                                   ("ridge", "rmse", b1[1], f["b1_rmse"])):
                ref = float(ref)
                diff = abs(value - ref)
                rel = diff / abs(ref) if ref else 0.0
                ok = (diff <= TOLERANCE["persistence_abs"] if model_name == "persistence" else
                      diff <= TOLERANCE["ridge_abs"] or rel <= TOLERANCE["ridge_rel"])
                gate.append(dict(run=run, channel=key, model=model_name, metric=metric, frozen=ref, replayed=value,
                                 abs_diff=diff, rel_diff=rel, n_frozen=int(f["n"]), n_replayed=len(index),
                                 passed=bool(ok and int(f["n"]) == len(index))))
    meta = dict(source_sha256=source.get("sha256"), source_md5=source.get("md5"),
                development_pairs=int(len(x)), coefficients=model[-1].coef_.tolist(),
                intercept=model[-1].intercept_.tolist(), scaler_mean=model[0].mean_.tolist(),
                scaler_scale=model[0].scale_.tolist(), tolerance=TOLERANCE, units=units, dates=dates,
                protocol_sha256=hashlib.sha256((STUDY / "protocol.json").read_bytes()).hexdigest())
    eligible = {run: len(examples[run][0]) for run in partitions}
    return rows, gate, meta, notes, eligible, records


def load_workbook_bytes(blob):
    from openpyxl import load_workbook
    return load_workbook(BytesIO(blob), read_only=True, data_only=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("archive", type=Path)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    rows, gate, meta, notes, eligible, _ = replay(a.archive)
    with (a.output / "gate_frozen_replay.csv").open("w", newline="", encoding="utf-8") as s:
        w = csv.DictWriter(s, fieldnames=list(gate[0]), lineterminator="\n")
        w.writeheader(), w.writerows(gate)
    passed = all(g["passed"] for g in gate)
    meta.update(gate_passed=passed, eligible_pairs=eligible, source_notes=notes)
    (a.output / "replay_manifest.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n",
                                                  encoding="utf-8", newline="\n")
    if not passed:
        raise SystemExit("FROZEN REPLAY GATE FAILED: dependent error analyses are blocked")
    import gzip
    with gzip.open(a.output / "replayed_predictions.csv.gz", "wt", newline="", encoding="utf-8") as s:
        w = csv.DictWriter(s, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader(), w.writerows(rows)
    print(json.dumps(dict(gate_passed=passed, checks=len(gate), rows=len(rows)), indent=2))


if __name__ == "__main__":
    main()
