import unittest

from looma import confidence


class ConfidenceTest(unittest.TestCase):
    def test_zero_signal_is_zero(self):
        self.assertEqual(
            confidence.score(file_overlap=0, has_commit=False, n_sessions=1, n_agents=1, span_days=0),
            0.0,
        )

    def test_weights_sum_to_components(self):
        # full file overlap + commit only
        c = confidence.score(file_overlap=1.0, has_commit=True, n_sessions=1, n_agents=1, span_days=0)
        self.assertAlmostEqual(c, 0.55, places=4)  # 0.30 + 0.25

    def test_commit_linkage_weight(self):
        base = confidence.score(0, False, 1, 1, 0)
        withc = confidence.score(0, True, 1, 1, 0)
        self.assertAlmostEqual(withc - base, 0.25, places=4)

    def test_more_sessions_increases_confidence(self):
        c1 = confidence.score(0, False, 1, 1, 0)
        c2 = confidence.score(0, False, 2, 1, 0)
        c3 = confidence.score(0, False, 5, 1, 0)
        self.assertLess(c1, c2)
        self.assertLess(c2, c3)

    def test_multi_agent_increases_confidence(self):
        c1 = confidence.score(0, False, 2, 1, 0)
        c2 = confidence.score(0, False, 2, 2, 0)
        self.assertLess(c1, c2)

    def test_clamped_to_one(self):
        c = confidence.score(1.0, True, 99, 99, 999)
        self.assertLessEqual(c, 1.0)

    def test_cohesion(self):
        self.assertEqual(confidence.cohesion([]), 0.0)
        self.assertAlmostEqual(confidence.cohesion([{"a", "b"}]), 0.3)
        # identical sets -> jaccard 1
        self.assertAlmostEqual(confidence.cohesion([{"a"}, {"a"}]), 1.0)
        # disjoint -> 0
        self.assertAlmostEqual(confidence.cohesion([{"a"}, {"b"}]), 0.0)


if __name__ == "__main__":
    unittest.main()
