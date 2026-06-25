import unittest

from looma import weekly as weekly_mod
from tests.helpers import make_store


class WeeklyTest(unittest.TestCase):
    def setUp(self):
        self.store = make_store()

    def _project_with_activity(self, key, name, when="2026-06-18T11:00:00Z"):
        pid = self.store.upsert_project(key, name, None, None)
        sid = self.store.upsert_session(pid, "claude", f"s-{name}", "main", None)
        self.store.update_session_meta(sid, "main", None, when, when, None)
        wid = self.store.insert_work_item(pid, kind="feature", title=f"Build {name}",
                                          summary="x", status="active", lifecycle="active",
                                          aliases=[], files=["a.ts"], confidence=0.4,
                                          first_seen=when, last_active=when)
        return pid, wid

    def test_weekly_aggregates_across_projects(self):
        pid_a, wid_a = self._project_with_activity("path:/a", "alpha")
        self.store.upsert_commit(pid_a, {"sha": "abc1234567", "author": "x",
                                         "ts": "2026-06-18T10:00:00Z", "message": "ship alpha"})
        self.store.insert_entity(pid_a, kind="decision", title="Use Postgres over SQLite",
                                 work_item_id=wid_a, status="open", confidence=0.5)
        self.store.insert_entity(pid_a, kind="todo", title="Wire migrations",
                                 work_item_id=wid_a, status="open", confidence=0.5)
        # a diff-hunk decision that must be filtered
        self.store.insert_entity(pid_a, kind="decision", title="@@ -1,4 +1,6 @@ def f():",
                                 work_item_id=wid_a, status="open", confidence=0.5)
        self._project_with_activity("path:/b", "beta")
        self.store.commit()

        w = weekly_mod.build(self.store, days=3650)
        self.assertFalse(w["empty"])
        names = {p["display_name"] for p in w["projects"]}
        self.assertEqual(names, {"alpha", "beta"})
        self.assertEqual([c["sha"] for c in w["commits"]], ["abc1234567"])
        dtitles = [d["title"] for d in w["decisions"]]
        self.assertIn("Use Postgres over SQLite", dtitles)
        self.assertNotIn("@@ -1,4 +1,6 @@ def f():", dtitles)
        self.assertTrue(any(b["title"] == "Wire migrations" for b in w["blockers"]))

        out = weekly_mod.format_weekly(w)
        for h in ("WORKED ON", "SHIPPED", "DECISIONS", "UNRESOLVED BLOCKERS"):
            self.assertIn(h, out)
        self.assertTrue(out.isascii())

    def test_weekly_drops_completed_blockers_and_meta_decisions(self):
        pid, wid = self._project_with_activity("path:/c", "gamma")
        # blockers that are actually finished work must not read as "unresolved"
        for done in ["Next step done: uploaded PDFs are ingested now",
                     "Final smoke and cleanup checks passed cleanly"]:
            self.store.insert_entity(pid, kind="todo", title=done,
                                     work_item_id=wid, status="open", confidence=0.5)
        self.store.insert_entity(pid, kind="todo", title="Add a timeout to outbound calls",
                                 work_item_id=wid, status="open", confidence=0.5)
        # an ascii-diagram "decision" (Looma's own source) must be filtered
        self.store.insert_entity(pid, kind="decision",
                                 title="Decision --CONSTRAINS--> [ WorkItem ] <--BLOCKS-- Todo",
                                 work_item_id=wid, status="open", confidence=0.5)
        self.store.insert_entity(pid, kind="decision", title="Use Redis over Memcached",
                                 work_item_id=wid, status="open", confidence=0.5)
        self.store.commit()

        w = weekly_mod.build(self.store, days=3650)
        btitles = [b["title"] for b in w["blockers"]]
        self.assertIn("Add a timeout to outbound calls", btitles)
        self.assertNotIn("Next step done: uploaded PDFs are ingested now", btitles)
        self.assertNotIn("Final smoke and cleanup checks passed cleanly", btitles)
        dtitles = [d["title"] for d in w["decisions"]]
        self.assertIn("Use Redis over Memcached", dtitles)
        self.assertNotIn("Decision --CONSTRAINS--> [ WorkItem ] <--BLOCKS-- Todo", dtitles)

    def test_weekly_empty(self):
        w = weekly_mod.build(self.store, days=7)
        self.assertTrue(w["empty"])
        self.assertIn("no activity", weekly_mod.format_weekly(w))


if __name__ == "__main__":
    unittest.main()
