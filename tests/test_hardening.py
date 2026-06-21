import sqlite3, unittest
from looma import db, health


class MigrationTest(unittest.TestCase):
    def test_migrate_adds_missing_columns_to_old_db(self):
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE TABLE work_items(id INTEGER PRIMARY KEY, title TEXT)")  # pre-v1
        db.migrate(conn)
        cols = {r[1] for r in conn.execute("PRAGMA table_info(work_items)")}
        for c in ("branch", "name_locked", "confidence"):
            self.assertIn(c, cols)

    def test_migrate_idempotent(self):
        conn = sqlite3.connect(":memory:")
        db.migrate(conn)
        db.migrate(conn)  # must not raise
        self.assertTrue({r[1] for r in conn.execute("PRAGMA table_info(entities)")})


class HealthWarningsTest(unittest.TestCase):
    def test_degradation_warnings(self):
        h = {"conversion_rate": 0.05, "merge_rate": 0.1, "false_positive_rate": 0.3,
             "avg_work_item_size": 1.0, "orphan_candidates": 5,
             "unresolved_related_items": 100, "_raw": {"work_items": 50, "candidates": 100}}
        w = " | ".join(health.warnings(h))
        self.assertIn("fragmentation", w)
        self.assertIn("correction rate", w)
        self.assertIn("under-merging", w)
        self.assertIn("low promotion", w)

    def test_healthy_graph_no_warnings(self):
        h = {"conversion_rate": 0.4, "merge_rate": 0.5, "false_positive_rate": 0.02,
             "avg_work_item_size": 2.5, "orphan_candidates": 0,
             "unresolved_related_items": 3, "_raw": {"work_items": 50, "candidates": 100}}
        self.assertEqual(health.warnings(h), [])


if __name__ == "__main__":
    unittest.main()
