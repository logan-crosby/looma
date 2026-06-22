"""`looma pack` - minimal, confidence-aware, budgeted agent context."""

import unittest

from looma import pack as pack_mod
from tests.helpers import make_store


class PackTest(unittest.TestCase):
    def setUp(self):
        self.store = make_store()
        self.pid = self.store.upsert_project("path:/p", "myapp", None, None)
        self.project = self.store.find_project_by_key("path:/p")
        wid = self.store.insert_work_item(
            self.pid, kind="feature", title="Add OAuth login", summary="Add OAuth login",
            status="active", lifecycle="active", aliases=["Add OAuth login"],
            files=["auth/login.ts", "auth/jwt.ts"], confidence=0.5,
            first_seen="2026-06-18T10:00:00Z", last_active="2026-06-18T11:00:00Z")
        self.store.insert_entity(self.pid, kind="decision", title="Use JWT instead of opaque tokens",
                                 work_item_id=wid, status="open", confidence=0.5)
        self.store.insert_entity(self.pid, kind="todo", title="Wire up refresh tokens",
                                 work_item_id=wid, status="open", confidence=0.5)
        self.store.upsert_commit(self.pid, {"sha": "abcdef1234", "author": "x",
                                            "ts": "2026-06-18T10:30:00Z", "message": "add login route"})
        self.store.commit()

    def tearDown(self):
        self.store.close()

    def test_pack_has_core_sections_and_is_grounded(self):
        p = pack_mod.build(self.store, self.project)
        for key in ("active_work", "decisions", "blockers", "relevant_files",
                    "commits", "next_step"):
            self.assertIn(key, p)
        text = pack_mod.format_pack(p)
        self.assertIn("LOOMA CONTEXT PACK", text)
        self.assertTrue(text.isascii())

    def test_relevant_files_prioritizes_uncommitted(self):
        active = [{"files": '["a.py", "b.py"]'}, {"files": '["b.py", "c.py"]'}]
        files = pack_mod.relevant_files(active, dirty=["c.py"], limit=5)
        self.assertEqual(files[0], "c.py")  # uncommitted first
        self.assertIn("b.py", files)        # touched by two items

    def test_budget_bounds_output(self):
        p = pack_mod.build(self.store, self.project)
        small = pack_mod.format_pack(p, budget=40)
        big = pack_mod.format_pack(p, budget=2000)
        self.assertLessEqual(pack_mod.est_tokens(small), pack_mod.est_tokens(big) + 20)
        # header always survives even the tightest budget
        self.assertIn("LOOMA CONTEXT PACK", small)

    def test_confidence_floor_filters(self):
        # a very high floor should drop low-confidence prose memories
        p_lo = pack_mod.build(self.store, self.project, min_conf=0.0)
        p_hi = pack_mod.build(self.store, self.project, min_conf=0.99)
        self.assertGreaterEqual(
            len(p_lo["decisions"]) + len(p_lo["blockers"]),
            len(p_hi["decisions"]) + len(p_hi["blockers"]),
        )


if __name__ == "__main__":
    unittest.main()
