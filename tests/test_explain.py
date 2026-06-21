import unittest

from looma import explain as explain_mod
from tests.helpers import make_store


class ExplainTest(unittest.TestCase):
    def setUp(self):
        self.store = make_store()
        self.pid = self.store.upsert_project("path:/p", "myapp", None, None)
        self.wid = self.store.insert_work_item(
            self.pid, kind="feature", title="Add OAuth login",
            summary="add oauth login", status="active", lifecycle="active",
            aliases=["add oauth login", "+ const x = 1"], files=["auth/login.ts"],
            confidence=0.5, first_seen="2026-06-18T10:00:00Z", last_active="2026-06-18T12:00:00Z",
        )
        self.store.insert_entity(self.pid, kind="decision", title="Use Auth0 over rolling our own",
                                 work_item_id=self.wid, status="open", confidence=0.5)
        self.store.insert_entity(self.pid, kind="architecture", title="store.set_defaults(x)",
                                 work_item_id=self.wid, status="open", confidence=0.5)
        cid = self.store.upsert_commit(self.pid, {"sha": "deadbeef99", "author": "x",
                                                  "ts": "2026-06-18T11:00:00Z", "message": "wire oauth callback"})
        # link the commit to the work item (IMPLEMENTS edge) so it shows in the story
        wi_node = self.store.work_item_node(self.pid, self.wid)
        self.store.add_edge(self.store.node_id(self.pid, "commit", cid), wi_node, "IMPLEMENTS")
        self.store.commit()

    def test_explain_answers_four_questions(self):
        wi = self.store.get_work_item(self.wid)
        x = explain_mod.build(self.store, self.pid, wi)
        self.assertEqual(x["why"]["title"], "Add OAuth login")
        # code-line alias filtered, prose alias kept
        self.assertIn("add oauth login", x["why"]["aliases"])
        self.assertNotIn("+ const x = 1", x["why"]["aliases"])
        # code-line decision filtered
        dtitles = [d["title"] for d in x["decisions"]]
        self.assertIn("Use Auth0 over rolling our own", dtitles)
        self.assertNotIn("store.set_defaults(x)", dtitles)

        out = explain_mod.format_explain(x)
        for header in ("WHY IT EXISTS", "HOW IT EVOLVED", "DECISIONS THAT SHAPED IT", "WHAT CHANGED"):
            self.assertIn(header, out)
        self.assertIn("Use Auth0 over rolling our own", out)
        self.assertIn("deadbeef9", out)
        self.assertTrue(out.isascii())


if __name__ == "__main__":
    unittest.main()
