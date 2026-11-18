"""Build every Q1 figure, run QA and write the figure manifest.

Usage (repository root):  python 03_results/integrated_validation_v1/publication_q1/scripts/build_figures.py
Options: --only <substring> builds matching functions only (manifest rows of other figures are kept).
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fig_center  # noqa: E402
import fig_hy2res  # noqa: E402
import fig_integrated  # noqa: E402
import fig_mhc  # noqa: E402
from q1style import Q1, setup  # noqa: E402

MODULES = [fig_center, fig_mhc, fig_hy2res, fig_integrated]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--output", type=Path, default=Q1 / "figures")
    a = ap.parse_args()
    font = setup()
    print("font:", font)
    tables = Q1 / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    rows = []
    for mod in MODULES:
        fns = [f for f in mod.FIGURES if a.only in f.__name__]
        if not fns:
            continue
        data = mod.load()
        if mod is fig_center:
            fig_center.export_dy_tables(data, tables)
        for fn in fns:
            r = fn(data, a.output)
            print(f"{r['figure_id']:<10} {r['qa_status']:<9} {r['qa_issues'][:300]}")
            rows.append(r)
    qc = Q1 / "quality_control"
    qc.mkdir(exist_ok=True)
    man = qc / "FIGURE_MANIFEST.csv"
    if not rows:
        print("no figure matched")
        return
    new = pd.DataFrame(rows)
    if a.only and man.exists():
        old = pd.read_csv(man, dtype=str, keep_default_na=False)
        new = pd.concat([old[~old.figure_id.isin(new.figure_id)], new.astype(str)], ignore_index=True)
    new = new.sort_values("figure_id", key=lambda s: s.map(lambda x: ("CBHI".index(x[3]), x)))
    new.to_csv(man, index=False, lineterminator="\n")


if __name__ == "__main__":
    main()
