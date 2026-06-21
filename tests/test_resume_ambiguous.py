import unittest

from looma.retrieval import resume as resume_mod
from tests.helpers import make_store


def _add_wi(store, pid, title, aliases, conf, files=None):
    wid = store.insert_work_item(
        pid, kind="feature", title=title, summary=" ".join(aliases),
        status="active", lifecycle="active", aliases=aliases, files=files or [],
        confidence=conf, first_seen="2026-06-18T10:00:00Z", last_active="2026-06-18T11:00:00Z",
    )
    store.update_work_item(wid, confidence=conf)
    store.index_work_item_fts(store.get_work_item(wid))
    return wid


class ResumeAmbiguityTest(unittest.TestCase):
    def setUp(self):
        self.store = make_store()
        self.pid = self.store.upsert_project("path:/p", "p", None, None)
        self.project = self.store.find_project_by_key("path:/p")

    def test_ambiguous_when_two_close_below_high(self):
        _add_wi(self.store, self.pid, "Authentication Login", ["build authentication login"], 0.60)
        _add_wi(self.store, self.pid, "Authentication Service Cache", ["add authentication service"], 0.55)
        self.store.commit()
        res = resume_mod.resume(self.store, self.project, "authentication")
        self.assertEqual(res["mode"], resume_mod.AMBIGUOUS)
        self.assertTrue(res["alternatives"], "alternatives must be surfaced, not collapsed")

    def test_confident_when_one_clear_high(self):
        _add_wi(self.store, self.pid, "Authentication Login", ["build authentication login"], 0.90)
        _add_wi(self.store, self.pid, "Billing Export", ["export billing report"], 0.50)
        self.store.commit()
        res = resume_mod.resume(self.store, self.project, "authentication")
        self.assertEqual(res["mode"], resume_mod.CONFIDENT)
        self.assertFalse(res["alternatives"])
        self.assertEqual(res["bundle"]["work_item"]["title"], "Authentication Login")

    def test_cold_when_no_match(self):
        _add_wi(self.store, self.pid, "Authentication Login", ["build authentication login"], 0.90)
        self.store.commit()
        res = resume_mod.resume(self.store, self.project, "zzzznomatch")
        self.assertEqual(res["mode"], resume_mod.COLD)
        self.assertEqual(res.get("reason"), "no_match")

    def test_low_confidence_high_relevance_surfaces(self):
        # Phase 1 fix: resume gates on match RELEVANCE, not the item's intrinsic
        # confidence. A clearly-relevant item must surface even when its
        # confidence is low (the common solo-dev case), not collapse to COLD.
        _add_wi(self.store, self.pid, "Authentication Login", ["build authentication login"], 0.20)
        self.store.commit()
        res = resume_mod.resume(self.store, self.project, "authentication")
        self.assertEqual(res["mode"], resume_mod.CONFIDENT)
        self.assertEqual(res["bundle"]["work_item"]["title"], "Authentication Login")

    def test_weak_only_match_is_not_confident(self):
        # An item that matches the goal only weakly (one stemmed/partial token)
        # must not be asserted as the answer; it surfaces as AMBIGUOUS at most.
        _add_wi(self.store, self.pid, "Authentication Login", ["authentication login"], 0.90)
        self.store.commit()
        res = resume_mod.resume(self.store, self.project, "authn review notes draft pass two")
        self.assertNotEqual(res["mode"], resume_mod.CONFIDENT)

    def test_no_goal_picks_most_recent(self):
        _add_wi(self.store, self.pid, "Authentication Login", ["build authentication login"], 0.60)
        self.store.commit()
        res = resume_mod.resume(self.store, self.project, "")
        self.assertEqual(res["mode"], resume_mod.NO_GOAL)
        self.assertIn("work_item", res["bundle"])


if __name__ == "__main__":
    unittest.main()
