import unittest

from looma.promotion import promote


class PromotionTest(unittest.TestCase):
    def test_commit_linked_promotes(self):
        self.assertTrue(promote.should_promote(commit_linked=True, work_item_active=False, n_sessions=1))

    def test_active_work_item_promotes(self):
        self.assertTrue(promote.should_promote(commit_linked=False, work_item_active=True, n_sessions=1))

    def test_multi_session_promotes(self):
        self.assertTrue(promote.should_promote(commit_linked=False, work_item_active=False, n_sessions=2))

    def test_single_session_weak_stays_candidate(self):
        self.assertFalse(promote.should_promote(commit_linked=False, work_item_active=False, n_sessions=1))

    def test_force_reject_overrides_everything(self):
        self.assertFalse(
            promote.should_promote(commit_linked=True, work_item_active=True, n_sessions=9, force_reject=True)
        )

    def test_force_promote_overrides_weak(self):
        self.assertTrue(
            promote.should_promote(commit_linked=False, work_item_active=False, n_sessions=1, force_promote=True)
        )

    def test_kind_to_relation_map(self):
        self.assertEqual(promote.KIND_REL["decision"], "CONSTRAINS")
        self.assertEqual(promote.KIND_REL["todo"], "BLOCKS")
        self.assertEqual(promote.KIND_REL["bug"], "AFFECTS")
        self.assertEqual(promote.KIND_REL["architecture"], "CONSTRAINS")


if __name__ == "__main__":
    unittest.main()
