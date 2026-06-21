import tempfile
import unittest
from pathlib import Path

from looma import pipeline
from tests.helpers import assistant_edit_rec, make_store, user_rec, write_session


class IngestIdempotentTest(unittest.TestCase):
    def test_double_ingest_stable_message_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            cwd = str(tmp / "proj")
            (tmp / "proj").mkdir()
            projects = tmp / "claude" / "projects"
            write_session(
                projects, "-proj", "sess-1",
                [
                    user_rec("u1", "sess-1", cwd, "feature/auth", "implement oauth login"),
                    assistant_edit_rec("a1", "sess-1", cwd, "feature/auth", f"{cwd}/auth/oauth.py"),
                ],
            )
            store = make_store()
            r1 = pipeline.ingest_messages(store, projects_dir=projects)
            n1 = store.counts()["messages"]
            r2 = pipeline.ingest_messages(store, projects_dir=projects)
            n2 = store.counts()["messages"]

            self.assertEqual(n1, 2)
            self.assertEqual(n1, n2, "re-ingest must not duplicate messages")
            self.assertEqual(r1["new_messages"], 2)
            self.assertEqual(r2["new_messages"], 0)

    def test_rebuild_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            cwd = str(tmp / "proj")
            (tmp / "proj").mkdir()
            projects = tmp / "claude" / "projects"
            write_session(
                projects, "-proj", "sess-1",
                [
                    user_rec("u1", "sess-1", cwd, "feature/auth", "implement oauth login"),
                    assistant_edit_rec("a1", "sess-1", cwd, "feature/auth", f"{cwd}/auth/oauth.py"),
                ],
            )
            store = make_store()
            pipeline.ingest_messages(store, projects_dir=projects)
            pipeline.rebuild(store)
            wi1 = store.counts()["work_items"]
            pipeline.rebuild(store)
            wi2 = store.counts()["work_items"]
            self.assertEqual(wi1, wi2)
            self.assertGreaterEqual(wi1, 1)


if __name__ == "__main__":
    unittest.main()
