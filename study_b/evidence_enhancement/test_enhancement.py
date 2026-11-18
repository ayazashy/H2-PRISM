"""Focused tests for the Study B evidence enhancement (no archive needed)."""
import csv
import gzip
import subprocess
import sys
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

from analysis import assign_bin, observed_increment, representative_windows, tail_share  # noqa: E402
from benchmark import score  # noqa: E402  (frozen metric definition)

RESULTS = HERE / "results"


class EnhancementTests(unittest.TestCase):
    def test_observed_increment_is_smallest_recorded_step(self):
        self.assertEqual(observed_increment(np.array([0.0, 0.2, 0.4, 1.0, 1.0])), 0.2)
        self.assertEqual(observed_increment(np.array([0.0, 0.01, 0.03])), 0.01)

    def test_change_bins_are_increment_decades(self):
        labels = assign_bin(np.array([0, 1, 2, 10, 11, 100, 101, 1.0000001]))
        self.assertEqual(list(labels), ["no change", "1 increment", "2–10 increments", "2–10 increments",
                                        "11–100 increments", "11–100 increments", ">100 increments", "1 increment"])

    def test_tail_share_uses_ceiling_count_and_model_total(self):
        sq = np.array([100.0, 1.0, 1.0, 1.0] + [0.0] * 996)
        k, share = tail_share(sq, 0.001)
        self.assertEqual(k, 1)
        self.assertAlmostEqual(share, 100 / 103)

    def test_representative_window_parsing(self):
        notes = {"24": ["14:00:00 switch-over Start: 14:30:00 =VLOOKUP(...)", "End: 15:00:00 =VLOOKUP"]}
        self.assertEqual(representative_windows(notes), {24: ("14:30:00", "15:00:00")})

    @unittest.skipUnless((RESULTS / "replay/replayed_predictions.csv.gz").exists(), "replay outputs absent")
    def test_saved_predictions_reproduce_frozen_metrics_exactly(self):
        with gzip.open(RESULTS / "replay/replayed_predictions.csv.gz", "rt", encoding="utf-8") as s:
            rows = list(csv.DictReader(s))
        with (HERE.parent / "per_run_metrics.csv").open(encoding="utf-8-sig", newline="") as s:
            frozen = {(r["run"], r["channel"]): r for r in csv.DictReader(s)}
        for (run, channel), ref in frozen.items():
            sel = [r for r in rows if r["run"] == run and r["channel"] == channel]
            y = np.array([float(r["y_true"]) for r in sel])
            b0 = score(y, np.array([float(r["persistence"]) for r in sel]))
            b1 = score(y, np.array([float(r["ridge"]) for r in sel]))
            self.assertEqual(len(sel), int(ref["n"]))
            self.assertEqual(b0[0], float(ref["b0_mae"]))
            self.assertEqual(b0[1], float(ref["b0_rmse"]))
            self.assertLessEqual(abs(b1[0] - float(ref["b1_mae"])), 1e-12)
            self.assertLessEqual(abs(b1[1] - float(ref["b1_rmse"])), 1e-12)

    @unittest.skipUnless((RESULTS / "replay/gate_frozen_replay.csv").exists(), "replay outputs absent")
    def test_gate_recorded_all_pass(self):
        with (RESULTS / "replay/gate_frozen_replay.csv").open(encoding="utf-8") as s:
            gate = list(csv.DictReader(s))
        self.assertEqual(len(gate), 24)
        self.assertTrue(all(g["passed"] == "True" for g in gate))

    def test_frozen_study_b_files_unchanged(self):
        frozen = [str(p.relative_to(HERE.parents[1]).as_posix()) for p in HERE.parent.iterdir()
                  if p.name != "evidence_enhancement"]
        try:
            out = subprocess.run(["git", "diff", "--name-only", "2f36d156f4fab9d00c1030b214039afe4b97175a", "--",
                                  *frozen], cwd=HERE.parents[1], capture_output=True, text=True, check=True).stdout
        except (OSError, subprocess.CalledProcessError):
            self.skipTest("git or frozen commit unavailable")
        self.assertEqual(out.strip(), "")


if __name__ == "__main__":
    unittest.main()
