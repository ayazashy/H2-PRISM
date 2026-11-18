"""Focused tests for the Study C evidence enhancement (no source CSV needed)."""
import subprocess
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from analysis import FEATURES, attribute, grid_table, rank_probability  # noqa: E402

RES = HERE / "results" / "analysis"


class EnhancementTests(unittest.TestCase):
    def test_grid_detection_is_exact(self):
        raw = pd.DataFrame({"pres_buf": [28.0, 28.1, 28.3, np.nan], "pres_comp": [100.0, 100.1, 100.15, 100.2],
                            "h2_flow": [0.0, 0.0005, 1.0, 2.0]})
        g = grid_table(raw).set_index("channel")
        self.assertEqual(g.loc["pres_buf", "smallest_positive_step"], 0.1)
        self.assertEqual(g.loc["pres_buf", "missing_rows"], 1)
        self.assertEqual(g.loc["pres_comp", "off_grid_rows"], 1)        # 100.15 is not on the 0.1 grid
        self.assertEqual(g.loc["h2_flow", "smallest_positive_step"], 0.0005)

    def test_rank_probability_ties_and_direction(self):
        self.assertEqual(rank_probability(np.array([0, 0]), np.array([1, 1])), 1.0)
        self.assertEqual(rank_probability(np.array([1, 1]), np.array([1, 1])), 0.5)
        self.assertEqual(rank_probability(np.array([2]), np.array([1])), 0.0)

    def test_reason_precedence_and_nonfinite(self):
        bounds = pd.DataFrame({"dev_min": [28.0, 84.5, 0.0], "dev_max": [34.3, 106.6, 376.9]}, index=FEATURES)
        t = pd.DataFrame({"pres_buf": [30, 35, np.nan, 30, 30], "pres_comp": [110, 110, 105, 105, 105],
                          "h2_flow": [0, 0, 0, 0, 0], "segment": [1, 2, 3, 4, 5],
                          "decision": ["Unresolved"] * 4 + ["Ambiguous"]})
        a = attribute(t, bounds)
        self.assertEqual(list(a.primary_reason[:4]), ["OUT_OF_SUPPORT (pres_comp)", "OUT_OF_SUPPORT (pres_comp)",
                                                      "INVALID_INPUT (nonfinite origin measurement)",
                                                      "EMPTY_CELL (no state with >=2 development segments)"])
        self.assertEqual(a.primary_reason.iloc[4], "—")                 # frozen non-unresolved decision untouched
        self.assertEqual(int(a.n_channels_outside.iloc[1]), 2)          # non-exclusive count keeps the overlap

    @unittest.skipUnless((RES / "unresolved_taxonomy.csv").exists(), "analysis outputs absent")
    def test_counts_reconcile_with_frozen_totals(self):
        tax = pd.read_csv(RES / "unresolved_taxonomy.csv")
        self.assertEqual(int(tax[tax.decision == "Unresolved"].rows.sum()), 32308)
        self.assertEqual(int(tax.rows.sum()), 44397)
        so = pd.read_csv(RES / "state_outcomes.csv").set_index("state")
        self.assertEqual(int(so.rows.sum()), 44397)
        self.assertEqual(int(so.loc["multiple_active", "specific"]), 0)
        self.assertTrue(pd.read_csv(RES / "gate_decision_reproduction.csv").passed.all())
        self.assertTrue(pd.read_csv(RES / "gate_benchmark_reconciliation.csv").passed.all())
        bins = pd.read_csv(RES / "time_bins.csv")
        self.assertEqual(int(bins.rows.sum()), 44397)

    @unittest.skipUnless((RES / "quantization_comparison.csv").exists(), "analysis outputs absent")
    def test_metric_denominators(self):
        q = pd.read_csv(RES / "quantization_comparison.csv").set_index("channel")
        self.assertTrue((q.n == 43168).all() and (q.segments == 409).all())
        self.assertEqual(int(q.loc["pres_buf", "persistence_exact_hits"] + q.loc["pres_buf", "nonzero_step_rows"]), 43168)
        self.assertAlmostEqual(q.loc["pres_comp", "persistence_mae"], 0.025597664936990658, places=15)

    def test_frozen_study_c_files_unchanged(self):
        root = HERE.parents[2]
        try:
            out = subprocess.run(["git", "diff", "--name-only", "6a926de43f3283d9a995fbe0d8381a06c015344f", "--",
                                  "03_results/hy2res_external_validation", ":!03_results/hy2res_external_validation/evidence_enhancement"],
                                 cwd=root, capture_output=True, text=True, check=True).stdout
        except (OSError, subprocess.CalledProcessError):
            self.skipTest("git or frozen commit unavailable")
        self.assertEqual(out.strip(), "")


if __name__ == "__main__":
    unittest.main()
