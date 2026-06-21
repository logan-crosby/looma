import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from looma import cli
from tests.helpers import assistant_edit_rec, user_rec, write_session


def run(argv) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = cli.main(argv)
    return rc, out.getvalue(), err.getvalue()


class CliEmptyStateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.tmp.name) / "looma.db")

    def tearDown(self):
        self.tmp.cleanup()

    def test_init_reports_path(self):
        rc, out, _ = run(["init", "--db", self.db])
        self.assertEqual(rc, 0)
        self.assertIn(self.db, out)
        self.assertIn("Local-first", out)

    def test_status_empty_is_friendly(self):
        run(["init", "--db", self.db])
        rc, out, _ = run(["status", "--db", self.db])
        self.assertEqual(rc, 0)
        self.assertIn("Nothing ingested yet", out)
        self.assertIn("projects:   0", out)

    def test_work_without_project_is_helpful(self):
        run(["init", "--db", self.db])
        rc, out, err = run(["work", "--db", self.db])
        self.assertEqual(rc, 1)
        self.assertIn("No Looma project", err)


class CliResetTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.tmp.name) / "looma.db")
        run(["init", "--db", self.db])

    def tearDown(self):
        self.tmp.cleanup()

    def test_reset_without_confirm_refuses(self):
        rc, out, _ = run(["reset", "--db", self.db])
        self.assertEqual(rc, 1)
        self.assertIn("--confirm", out)
        self.assertTrue(Path(self.db).exists(), "DB must NOT be deleted without --confirm")

    def test_reset_with_confirm_deletes(self):
        rc, out, _ = run(["reset", "--db", self.db, "--confirm"])
        self.assertEqual(rc, 0)
        self.assertFalse(Path(self.db).exists())


class CliDoctorTest(unittest.TestCase):
    def test_doctor_runs_and_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = str(Path(tmp) / "looma.db")
            rc, out, _ = run(["doctor", "--db", db])
            self.assertIn("SQLite FTS5", out)
            self.assertIn("Python version", out)
            self.assertIn("Database", out)
            # FTS5 + python must pass on a supported runtime
            self.assertIn("[ OK ]", out)


if __name__ == "__main__":
    unittest.main()
