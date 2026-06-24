import unittest

from looma import pipeline
from tests.helpers import make_store


class ReconcileProjectsTest(unittest.TestCase):
    def _proj(self, store, key, name, root, remote):
        return store.upsert_project(key, name, root, remote)

    def test_orphan_path_project_folds_into_same_repo_remote(self):
        store = make_store()
        remote_pid = self._proj(
            store, "github.com/donandrade/shb_database", "shb_database",
            "/Users/x/GitHub/shb_database", "github.com/donandrade/shb_database",
        )
        orphan_pid = self._proj(
            store, "path:/Users/x/Desktop/shb_database", "shb_database",
            "/Users/x/Desktop/shb_database", None,
        )
        store.upsert_session(orphan_pid, "claude", "s1", None, None)
        store.commit()

        merged = pipeline.reconcile_projects(store)
        self.assertEqual(merged, 1)
        self.assertIsNone(store.find_project_by_key("path:/Users/x/Desktop/shb_database"))
        # the orphan's session now belongs to the remote project
        self.assertEqual(len(store.project_sessions(remote_pid)), 1)

    def test_distinct_names_are_not_merged(self):
        store = make_store()
        self._proj(store, "github.com/devyrpauli/portfolio", "portfolio",
                   "/Users/x/portfolio", "github.com/devyrpauli/portfolio")
        orphan = self._proj(store, "path:/Users/x/yash-portfolio", "yash-portfolio",
                            "/Users/x/yash-portfolio", None)
        store.upsert_session(orphan, "claude", "s2", None, None)
        store.commit()
        self.assertEqual(pipeline.reconcile_projects(store), 0)
        self.assertIsNotNone(store.find_project_by_key("path:/Users/x/yash-portfolio"))

    def test_ambiguous_remote_match_is_left_alone(self):
        store = make_store()
        self._proj(store, "github.com/a/app", "app", "/Users/x/a/app", "github.com/a/app")
        self._proj(store, "github.com/b/app", "app", "/Users/x/b/app", "github.com/b/app")
        orphan = self._proj(store, "path:/Users/x/c/app", "app", "/Users/x/c/app", None)
        store.upsert_session(orphan, "claude", "s3", None, None)
        store.commit()
        # two remotes share the basename "app" -> ambiguous -> no merge
        self.assertEqual(pipeline.reconcile_projects(store), 0)


if __name__ == "__main__":
    unittest.main()
