import unittest

from looma.resolution import workitems as wi


def _sig(sid, branch, files, msgs, model="claude-opus-4-8", started="2026-06-18T10:00:00Z",
         ended="2026-06-18T11:00:00Z"):
    session = {"id": sid, "branch": branch, "agent_model": model,
               "started_at": started, "ended_at": ended}
    messages = [{"role": "user", "text": m} for m in msgs]
    return wi.build_session_signal(session, messages, files)


class WorkItemCreationTest(unittest.TestCase):
    def test_intent_label_and_kind(self):
        s = _sig(1, "feature/auth", ["auth/oauth.py"], ["please implement oauth login for the app"])
        self.assertEqual(s["kind"], "feature")
        self.assertIn("oauth login", s["label"])

        s2 = _sig(2, "fix/cb", ["auth/cb.py"], ["fix the callback validation bug"])
        self.assertEqual(s2["kind"], "bugfix")

    def test_same_files_and_branch_merge(self):
        sigs = [
            _sig(1, "feature/auth", ["auth/oauth.py", "auth/routes.py"], ["implement oauth login"]),
            _sig(2, "feature/auth", ["auth/oauth.py", "auth/routes.py"], ["continue google auth work"]),
        ]
        items = wi.resolve(sigs)
        self.assertEqual(len(items), 1, "shared files + branch should resolve to one WorkItem")
        self.assertEqual(len(items[0]["members"]), 2)
        self.assertGreaterEqual(len(items[0]["aliases"]), 1)

    def test_unrelated_efforts_stay_separate(self):
        sigs = [
            _sig(1, "feature/auth", ["auth/oauth.py"], ["implement oauth login"]),
            _sig(2, "feature/cache", ["cache/redis.py"], ["add redis session cache"]),
        ]
        items = wi.resolve(sigs)
        self.assertEqual(len(items), 2)

    def test_title_from_files_when_no_intent(self):
        s = _sig(1, "HEAD", ["billing/invoice.py", "billing/tax.py"], ["here is some output"])
        items = wi.resolve([s])
        self.assertEqual(len(items), 1)
        self.assertIn("billing", items[0]["title"].lower())

    def test_title_prettifies_acronyms(self):
        s = _sig(1, "feature/auth", ["auth/oauth.py"], ["implement oauth login"])
        items = wi.resolve([s])
        self.assertIn("OAuth", items[0]["title"])


if __name__ == "__main__":
    unittest.main()
