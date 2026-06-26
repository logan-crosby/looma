import unittest
from looma.benchmark import harness
from looma.extraction.extractor import HeuristicExtractor


class BenchmarkTest(unittest.TestCase):
    def test_scoring_matches_paraphrase(self):
        tp, fp, fn = harness._score_kind(
            ["use JWT over opaque tokens for stateless auth"],
            ["use JWT instead of opaque tokens for stateless verification"])
        self.assertEqual((tp, fp, fn), (1, 0, 0))

    def test_prf_perfect_and_empty(self):
        self.assertEqual(harness._prf(3, 0, 0)["f1"], 1.0)
        self.assertEqual(harness._prf(0, 5, 0)["precision"], 0.0)
        self.assertEqual(harness._prf(0, 0, 0)["f1"], 0.0)

    def test_false_positive_counted(self):
        tp, fp, fn = harness._score_kind(["totally unrelated nonsense text here"],
                                         ["use redis for sessions"])
        self.assertEqual((tp, fp, fn), (0, 1, 1))

    def test_paraphrase_with_few_shared_tokens_matches(self):
        # A correct paraphrase of the same bug can share few surface tokens
        # ("memory leak ... listeners" vs the gold's "event listeners ...
        # accumulate ... memory leak"). The matcher must credit it, else one
        # correct extraction is double-penalized as both FP and FN. (V2.1.5)
        self.assertTrue(harness._matches(
            "Memory leak in the worker process due to accumulated EventEmitter listeners",
            "event listeners are never removed after a job completes so they "
            "accumulate causing a memory leak"))

    def test_distinct_facts_do_not_match(self):
        # The fairer matcher must NOT become indiscriminate: different facts,
        # even with shared structure or a shared generic word, stay unmatched.
        NEG = [
            ("ConnectionError: refused on Redis connection",
             "OAuth callback drops the state param on redirect breaking CSRF"),
            ("use JWT instead of opaque tokens for stateless verification",
             "use Redis instead of in-process memory so sessions survive restarts"),
            ("Memory leak from accumulated EventEmitter listeners in the worker",
             "checkout total rounding off by a cent because line items round individually"),
            ("cache entries should expire with a TTL matching the session timeout",
             "the leader election must be idempotent so a re-run is safe"),
        ]
        for p, g in NEG:
            self.assertFalse(harness._matches(p, g), f"should NOT match: {p!r} vs {g!r}")

    def test_run_returns_metrics(self):
        m = harness.run(HeuristicExtractor())
        self.assertEqual(m["extractor"], "heuristic")
        for key in ("precision", "recall", "f1"):
            self.assertIn(key, m["overall"])
            self.assertTrue(0.0 <= m["overall"][key] <= 1.0)
        # heuristic should get a non-trivial F1 on the golden set
        self.assertGreater(m["overall"]["f1"], 0.3)


if __name__ == "__main__":
    unittest.main()
