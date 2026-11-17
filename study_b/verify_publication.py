"""Verify the frozen results without fitting or replaying Ridge."""
import argparse
import csv
from io import BytesIO
import json
import math
from pathlib import Path
from zipfile import ZipFile

import numpy as np
from openpyxl import load_workbook

from benchmark import read_run
from verify_source import inventory

ROOT = Path(__file__).resolve().parent


def rows(name):
    with (ROOT / name).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8-sig"))


def verify(archive):
    source = inventory(archive)
    assert json.loads(json.dumps(source)) == load("source_manifest.json")
    metrics = rows("per_run_metrics.csv")
    summary = load("metrics.json")["summary"]
    protocol = load("protocol.json")
    split = rows("split_manifest.csv")
    registry = rows("experiment_registry.csv")
    assert len(registry) == len(split) == len(source["experiments"]) == 29
    assert {r["run"] for r in registry if r["operation"] == "Dual stage compression"} == set(protocol["partition"])
    assert {g for n,g in protocol["groups"].items() if protocol["partition"][n]=="test"}.isdisjoint(
        {g for n,g in protocol["groups"].items() if protocol["partition"][n]=="development"})
    results = []
    with ZipFile(archive) as zip_file:
        for run, partition in protocol["partition"].items():
            book = load_workbook(BytesIO(zip_file.read(source["experiments"][int(run)])),
                                 read_only=True, data_only=False)
            _, _, units, dates, clock, samples, notes = read_run(book, int(run))
            book.close()
            assert units["Seconds"] == "s" and units["P-2"] == "barg" and units["MFC-3"] == "ln/min"
            assert len({d for d in dates if d}) == 1
            if run == "27":
                assert "27 directly following 26" in notes
            delta = np.diff(clock)
            valid = [i for i, duration in enumerate(delta)
                     if .8 <= duration <= 1.2 and samples[i+1,0] == samples[i,0]+1
                     and all(math.isfinite(v) for v in samples[i:i+2][:,[2,5]].ravel())]
            saved = next(r for r in split if r["run"] == run)
            assert saved["partition"] == partition and int(saved["eligible_pairs"]) == len(valid)
            if partition != "test":
                continue
            results.append({"run": int(run), "raw_rows": len(samples), "pairs": len(valid),
                            "interval_min_s": round(float(min(delta[valid])), 6),
                            "interval_max_s": round(float(max(delta[valid])), 6),
                            "elapsed_span_min": round(float((clock[-1]-clock[valid[0]+1])/60), 4),
                            "excluded_wallclock_s": [round(float(delta[i]),6)
                                                       for i in sorted(set(range(len(delta)))-set(valid))]})
            for key, column in (("P-2", 2), ("MFC-3", 5)):
                row = next(r for r in metrics if r["run"]==run and r["channel"]==key)
                assert row["unit"] == units[key] and int(row["n"]) == len(valid)
                assert int(row["adjacent_rows"]) == len(samples)-1
                errors = [float(samples[i+1,column]-samples[i,column]) for i in valid]
                assert math.isclose(math.fsum(map(abs,errors))/len(errors), float(row["b0_mae"]), abs_tol=1e-14)
                assert math.isclose(math.sqrt(math.fsum(x*x for x in errors)/len(errors)),
                                    float(row["b0_rmse"]), abs_tol=1e-14)
    for channel, aggregate in summary.items():
        subset = [r for r in metrics if r["channel"]==channel]
        assert aggregate["runs"] == len(subset) == 3
        assert aggregate["n"] == sum(int(r["n"]) for r in subset) == 15885
        for name in ("b0_mae","b1_mae","b0_rmse","b1_rmse","delta_mae_b1_minus_b0"):
            assert math.isclose(aggregate[name], math.fsum(float(r[name]) for r in subset)/len(subset))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    verify(parser.parse_args().archive)
