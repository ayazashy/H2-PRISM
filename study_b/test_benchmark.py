"""Focused tests for Study B's causal pairing and reported metrics."""
import json
from pathlib import Path
import unittest

import numpy as np

from benchmark import pairs, score


class StudyBTests(unittest.TestCase):
    def test_pairs_exclude_gaps_duplicate_times_counter_resets_and_missing(self):
        time = np.array([0., 1., 3., 3., 4., 5., 6., 7., 8.])
        data = np.column_stack(([1, 2, 3, 4, 5, 6, 1, 2, 3],
                                [5, 6, 7, 8, np.nan, 9, 3, 4, 5],
                                [0, 1, 2, 3, 4, 5, 0, 1, 2]))
        index, current, target = pairs(time, data, [1, 2], .8, 1.2)
        np.testing.assert_array_equal(index, [0, 6, 7])
        np.testing.assert_array_equal(current, data[index, 1:])
        np.testing.assert_array_equal(target, data[index + 1, 1:])

    def test_metrics_use_physical_errors(self):
        mae, rmse = score(np.array([1., 2.]), np.array([0., 5.]))
        self.assertEqual(mae, 2.)
        self.assertAlmostEqual(rmse, np.sqrt(5.))

    def test_frozen_groups_do_not_cross_partitions(self):
        path = Path(__file__).with_name("protocol.json")
        protocol = json.loads(path.read_text(encoding="utf-8-sig"))
        partition, groups = protocol["partition"], protocol["groups"]
        self.assertEqual(set(partition), set(groups))
        development = {groups[n] for n in partition if partition[n] == "development"}
        held_out = {groups[n] for n in partition if partition[n] == "test"}
        self.assertFalse(development & held_out)
        self.assertEqual(groups["26"], groups["27"])
        self.assertEqual(groups["28"], groups["29"])
        self.assertTrue(all(partition[str(n)] == "test" for n in protocol["figure_cases"]))


if __name__ == "__main__":
    unittest.main()

