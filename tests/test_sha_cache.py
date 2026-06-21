import unittest

from looma.extraction import deterministic
from tests.helpers import make_store


class ShaCacheTest(unittest.TestCase):
    def test_store_cache_roundtrip(self):
        store = make_store()
        self.assertIsNone(store.sha_cached("/repo", "abc1234"))
        store.cache_sha("/repo", "abc1234", True)
        store.cache_sha("/repo", "deadbee", False)
        self.assertIs(store.sha_cached("/repo", "abc1234"), True)
        self.assertIs(store.sha_cached("/repo", "deadbee"), False)

    def test_validate_called_once_per_sha(self):
        calls = []

        def validate(sha):
            calls.append(sha)
            return True

        msgs = [
            {"role": "assistant", "text": "ran it",
             "tool_calls": [{"name": "Bash", "input": {"command": "git show 1234abc"}}]},
            {"role": "assistant", "text": "again",
             "tool_calls": [{"name": "Bash", "input": {"command": "git log 1234abc"}}]},
        ]
        arts = deterministic.session_artifacts(msgs, "/repo", validate=validate)
        # same sha appears twice but is validated once (deduped before validate)
        self.assertEqual(calls.count("1234abc"), 1)
        self.assertIn("1234abc", arts["shas"])

    def test_non_git_hex_not_validated(self):
        called = []

        def validate(sha):
            called.append(sha)
            return True

        # hex token only in prose / non-git command -> must NOT be validated
        msgs = [
            {"role": "user", "text": "the uuid is deadbeefcafe1234 in the logs",
             "tool_calls": [{"name": "Bash", "input": {"command": "ls -la deadbeefcafe1234"}}]},
        ]
        arts = deterministic.session_artifacts(msgs, "/repo", validate=validate)
        self.assertEqual(called, [])
        self.assertEqual(arts["shas"], [])

    def test_git_output_sha_is_collected(self):
        seen = []

        def validate(sha):
            seen.append(sha)
            return True

        msgs = [{"role": "assistant", "text": "commit 9f3a1c2bd0\nAuthor: x", "tool_calls": []}]
        arts = deterministic.session_artifacts(msgs, "/repo", validate=validate)
        self.assertIn("9f3a1c2bd0", arts["shas"])


if __name__ == "__main__":
    unittest.main()
