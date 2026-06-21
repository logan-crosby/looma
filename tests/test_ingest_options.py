import tempfile
import unittest
from pathlib import Path

from looma import pipeline
from tests.helpers import make_store, user_rec, write_session


def _two_projects(projects: Path, tmp: Path):
    a = tmp / "proj-a"; a.mkdir()
    b = tmp / "proj-b"; b.mkdir()
    write_session(projects, "-a", "s-a",
                  [user_rec("u", "s-a", str(a), "main", "implement alpha feature")])
    write_session(projects, "-b", "s-b",
                  [user_rec("u", "s-b", str(b), "main", "implement beta feature")])
    return str(a), str(b)


class IngestOptionsTest(unittest.TestCase):
    def test_limit_caps_sessions(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            projects = tmp / "claude"
            _two_projects(projects, tmp)
            store = make_store()
            res = pipeline.ingest_messages(store, projects_dir=projects, limit=1)
            self.assertEqual(res["sessions"], 1)
            self.assertEqual(store.counts()["sessions"], 1)

    def test_project_filter_only_ingests_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            projects = tmp / "claude"
            a, b = _two_projects(projects, tmp)
            from looma import identity
            key_a = identity.resolve(a)["canonical_key"]

            store = make_store()
            res = pipeline.ingest_messages(store, projects_dir=projects, project_filter=key_a)
            self.assertEqual(res["sessions"], 1)
            self.assertGreaterEqual(res["skipped"], 1)
            projs = store.list_projects()
            self.assertEqual(len(projs), 1)
            self.assertEqual(projs[0]["canonical_key"], key_a)


if __name__ == "__main__":
    unittest.main()
