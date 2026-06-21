import unittest

from looma.extraction import deterministic


class RootlessArtifactsTest(unittest.TestCase):
    def test_no_crash_when_project_root_is_none(self):
        # Rootless projects (unknown buckets, path-keys not on disk) must not crash
        # the rebuild. Regression for os.path.join(None, rel) (caused ingest rc=1).
        msgs = [
            {"role": "user", "text": "please update src/app.ts and run git status",
             "ts": "2026-06-18T10:00:00Z", "tool_calls": []},
        ]
        arts = deterministic.session_artifacts(msgs, None, validate=lambda s: False)
        self.assertEqual(arts["files"], [])
        self.assertEqual(arts["shas"], [])


if __name__ == "__main__":
    unittest.main()
