"""Audit the verified MHC archive and run the frozen Study B benchmark."""
import argparse
import csv
import hashlib
from datetime import datetime
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile

import numpy as np
from openpyxl import load_workbook
from openpyxl.utils.datetime import from_excel
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from verify_source import inventory

HERE = Path(__file__).resolve().parent
SIGNALS = {"P-1": "barg", "P-2": "barg", "MFC-1": "ln/min",
           "MFC-2": "ln/min", "MFC-3": "ln/min",
           "T_HTF-1": "°C", "T_HTF-2": "°C"}


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)
                    + "\n", encoding="utf-8")


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def numeric(value):
    return float(value) if type(value) in (int, float) else np.nan


def read_run(book, run):
    raw = book[f"Cycle Definition Exp.{run}"]
    preview = list(raw.iter_rows(max_row=85, max_col=15, values_only=True))
    header_row, header = next((i, row) for i, row in enumerate(preview, 1)
                              if row[:3] == ("Date", "Time", "Seconds"))
    cycle_name = next((name for name in book.sheetnames if name.lower().startswith("cycle data")), None)
    mapping = {}
    if cycle_name:
        units, keys = book[cycle_name].iter_rows(min_row=10, max_row=11, max_col=15, values_only=True)
        mapping = dict(zip(keys, units))
    columns = [header.index(key) if key in header else None for key in SIGNALS]
    date = []
    time = []
    readings = []
    for row in raw.iter_rows(min_row=header_row + 1, max_col=15, values_only=True):
        if all(value is None for value in row):
            continue
        stamp = row[0]
        if type(stamp) in (int, float):
            try:
                stamp = (datetime.strptime(str(int(stamp)), "%Y%m%d")
                         if stamp >= 10_000_000 else from_excel(stamp, book.epoch))
            except (OverflowError, ValueError):
                stamp = None
        if type(row[1]) in (int, float) and 0 <= row[1] < 1:
            row = (*row[:1], from_excel(row[1], book.epoch), *row[2:])
        clock = row[1]
        date.append(stamp.isoformat()[:10] if isinstance(stamp, datetime) else "")
        time.append((datetime.combine(stamp.date(), clock) - datetime(1970, 1, 1)).total_seconds()
                    if isinstance(stamp, datetime) and hasattr(clock, "hour") else np.nan)
        readings.append([numeric(row[2]), *(numeric(row[c]) if c is not None else np.nan for c in columns)])
    notes = " | ".join(str(row[0]) for row in preview[3:8] if row[0] is not None)
    return header_row, cycle_name, mapping, date, np.array(time), np.array(readings), notes


def pairs(time, data, columns, lower, upper):
    values = data[:, columns]
    dt = np.diff(time)
    valid = ((np.diff(data[:, 0]) == 1) & (dt >= lower) & (dt <= upper)
             & np.isfinite(values[:-1]).all(axis=1) & np.isfinite(values[1:]).all(axis=1))
    index = np.flatnonzero(valid)
    return index, values[index], values[index + 1]


def audit(path, out):
    source = inventory(path)
    rows, layouts, records = [], {}, {}
    with ZipFile(path) as archive:
        overview = load_workbook(BytesIO(archive.read(source["overview"])),
                                 read_only=True, data_only=True)
        meta = {r[0]: r for r in overview.active.values if type(r[0]) is int}
        overview.close()
        for run in sorted(meta):
            book = load_workbook(BytesIO(archive.read(source["experiments"][run])),
                                 read_only=True, data_only=False)
            header, cycle_name, units, dates, time, data, notes = read_run(book, run)
            dt = np.diff(time)
            info = meta[run]
            rows.append(dict(run=run, stage=info[1], material_1=info[2], material_2=info[3],
                             operation=info[4], p1_bar=info[5], p2_bar=info[6],
                             half_cycle_min=info[7], date=next((d for d in dates if d), ""),
                             raw_rows=len(data), duration_s=round(float(time[np.isfinite(time)][-1]
                                                        -time[np.isfinite(time)][0]), 3),
                             median_interval_s=round(float(np.nanmedian(dt)), 4),
                             invalid_time=int(np.count_nonzero(~np.isfinite(time))),
                             duplicate_timestamps=int(np.count_nonzero(np.isfinite(time))
                                                  - len(np.unique(time[np.isfinite(time)]))),
                             irregular_intervals=int(np.count_nonzero(~((dt >= .8) & (dt <= 1.2)))),
                             **{f"invalid_{key}": int(np.count_nonzero(~np.isfinite(data[:, i])))
                                for i, key in enumerate(SIGNALS, 1)},
                             initial_conditions_and_notes=notes))
            layouts[str(run)] = dict(raw_sheet=f"Cycle Definition Exp.{run}", header_row=header,
                                     sheets=book.sheetnames, units_sheet=cycle_name,
                                     units={key: units.get(key) for key in ["Seconds", *SIGNALS]},
                                     unit_row=10, channel_row=11)
            book.close()
            records[run] = (time, data)
            print(f"Audited workbook {run}", flush=True)
    dump(out / "source_manifest.json", source)
    dump(out / "channel_map.json", {"signals": SIGNALS, "workbooks": layouts})
    write_csv(out / "experiment_registry.csv", rows)
    return records


def score(actual, predicted):
    error = predicted - actual
    return float(np.mean(np.abs(error))), float(np.sqrt(np.mean(error ** 2)))


def evaluate(records, protocol, out):
    partitions = {int(run): split for run, split in protocol["partition"].items()}
    channels = protocol["targets"]
    columns = [list(SIGNALS).index(key) + 1 for key in channels]
    maps = json.loads((out / "channel_map.json").read_text(encoding="utf-8"))["workbooks"]
    for run in partitions:
        if any(maps[str(run)]["units"][key] != SIGNALS[key] for key in channels):
            raise ValueError(f"Unverified target units for run {run}")
    examples = {n: pairs(*records[n], columns, *protocol["interval_s"])
                for n in partitions}
    groups = protocol["groups"]
    for group in set(groups.values()):
        if len({partitions[int(n)] for n in groups if groups[n] == group}) != 1:
            raise ValueError(f"Recording group crosses partitions: {group}")
    write_csv(out / "split_manifest.csv", [
        dict(run=run, partition=partitions.get(run, "outside scope"),
             recording_group=groups.get(str(run), ""),
             eligible_pairs=len(examples[run][0]) if run in examples else 0)
        for run in sorted(records)
    ])
    training = [(x, y) for run, (_, x, y) in examples.items() if partitions[run] == "development"]
    if any(len(index) == 0 for index, _, _ in examples.values()):
        raise ValueError("A frozen run has no eligible adjacent pairs")
    x, y = (np.concatenate(arrays) for arrays in zip(*training))
    candidate = make_pipeline(StandardScaler(), Ridge(alpha=protocol["ridge_alpha"]))
    candidate.fit(x, y - x)
    metrics, predictions = [], {}
    for run, (index, current, actual) in examples.items():
        if partitions[run] != "test":
            continue
        estimates = current + candidate.predict(current)
        predictions[run] = (records[run][0][index + 1], actual, current, estimates)
        for i, key in enumerate(channels):
            b0_mae, b0_rmse = score(actual[:, i], current[:, i])
            b1_mae, b1_rmse = score(actual[:, i], estimates[:, i])
            metrics.append(dict(run=run, channel=key, unit=SIGNALS[key], n=len(index),
                                adjacent_rows=len(records[run][0]) - 1,
                                b0_mae=b0_mae, b0_rmse=b0_rmse,
                                b1_mae=b1_mae, b1_rmse=b1_rmse,
                                delta_mae_b1_minus_b0=b1_mae-b0_mae))
    write_csv(out / "per_run_metrics.csv", metrics)
    summary = {}
    for key in channels:
        group = [row for row in metrics if row["channel"] == key]
        summary[key] = dict(unit=SIGNALS[key], n=sum(r["n"] for r in group), runs=len(group),
                            **{metric: float(np.mean([r[metric] for r in group]))
                               for metric in ("b0_mae", "b0_rmse", "b1_mae", "b1_rmse",
                                              "delta_mae_b1_minus_b0")})
    dump(out / "metrics.json", {"aggregation": "unweighted mean of per-run metrics",
                               "protocol_sha256": hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest(),
                               "development_pairs": len(x), "summary": summary})
    from figures import render
    render(out, protocol, metrics, predictions)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--out", type=Path, default=HERE)
    parser.add_argument("--audit-only", action="store_true")
    parser.add_argument("--verified-cache", action="store_true",
                        help="Reuse this run's completed local audit after checking provenance")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if args.verified_cache:
        if json.loads(json.dumps(inventory(args.archive))) != json.loads((args.out / "source_manifest.json").read_text()):
            raise ValueError("Audit cache source manifest differs")
        with np.load(args.out / "audit_cache.npz") as cache:
            records = {n: (cache[f"time_{n}"], cache[f"data_{n}"]) for n in range(1, 30)}
    else:
        records = audit(args.archive, args.out)
    if args.audit_only and not args.verified_cache:
        np.savez(args.out / "audit_cache.npz",
                 **{f"time_{n}": t for n, (t, _) in records.items()},
                 **{f"data_{n}": d for n, (_, d) in records.items()})
    if not args.audit_only:
        protocol = json.loads((HERE / "protocol.json").read_text(encoding="utf-8-sig"))
        evaluate(records, protocol, args.out)


if __name__ == "__main__":
    main()

