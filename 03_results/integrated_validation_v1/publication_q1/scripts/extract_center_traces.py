"""Extract the two small Center trace windows used by the Q1 response and timing figures.

Reads the accepted captures through the frozen loader (``h2prism.nres.load_pairs``),
which refuses any capture whose raw SHA-256 differs from its acceptance receipt.
Writes exact recorded values (no resampling) for:
  * alternate-profile SID 213 outlet withdrawal pair, 900-1300 s: PS1 (MPa), MFS3 (kg/s);
  * command-issuance timing pair, 0-80 s: PS1 and PS7 (MPa).
Usage: python extract_center_traces.py --workspace <center workspace> --output <csv>
"""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "src"))
from h2prism.nres import load_pairs  # noqa: E402  (frozen, hash-verifying loader)

WINDOWS = {"ALT": (900.0, 1300.0, ("PS1", "MFS3")), "TIMING": (0.0, 80.0, ("PS1", "PS7"))}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workspace", type=Path, default=os.environ.get("H2PRISM_CENTER_WORKSPACE"))
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if a.workspace is None:
        raise SystemExit("pass --workspace or set H2PRISM_CENTER_WORKSPACE")
    t, schema, pairs, hashes = load_pairs(Path(a.workspace))
    names = [s.name for s in schema]
    rows = []
    for pair, (t0, t1, sensors) in WINDOWS.items():
        m = (t >= t0) & (t <= t1)
        control, intervention = pairs[pair]
        for s in sensors:
            c = names.index(s)
            rows.append(pd.DataFrame({"pair": pair, "sensor": s, "unit": "MPa" if s.startswith("PS") else "kg/s",
                                      "time_s": t[m], "control": control.values[m, c],
                                      "intervention": intervention.values[m, c]}))
    out = pd.concat(rows, ignore_index=True)
    out.to_csv(a.output, index=False, lineterminator="\n", float_format="%.12g")
    keys = {"ALT": ("alternate_profile:normal", "alternate_profile:outlet_opening"),
            "TIMING": ("timing:normal", "timing:outlet_opening")}
    meta = {k: {c: hashes[c] for c in v} for k, v in keys.items()}
    meta["output_sha256"] = hashlib.sha256(a.output.read_bytes()).hexdigest()
    a.output.with_suffix(".provenance.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(len(out), "rows")


if __name__ == "__main__":
    main()
