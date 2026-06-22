import os
import tempfile
import unittest

from looma import identity
from looma.gitutil import normalize_remote


class ProjectIdentityTest(unittest.TestCase):
    def test_normalize_remote_variants(self):
        cases = {
            "git@github.com:devYRPauli/looma.git": "github.com/devyrpauli/looma",
            "https://github.com/devYRPauli/looma.git": "github.com/devyrpauli/looma",
            "https://github.com/devYRPauli/looma": "github.com/devyrpauli/looma",
            "ssh://git@gitlab.com/group/sub/repo.git": "gitlab.com/group/sub/repo",
        }
        for url, expected in cases.items():
            self.assertEqual(normalize_remote(url), expected, url)

    def test_normalize_remote_none(self):
        self.assertIsNone(normalize_remote(None))
        self.assertIsNone(normalize_remote("not a url"))

    def test_resolve_falls_back_to_path_key_without_git(self):
        with tempfile.TemporaryDirectory() as tmp:
            ident = identity.resolve(tmp)
            self.assertIsNotNone(ident)
            # not a git repo -> path: key anchored on the abspath
            self.assertTrue(ident["canonical_key"].startswith("path:"))
            self.assertEqual(ident["display_name"], os.path.basename(ident["root_path"]))

    def test_resolve_none_for_missing_root(self):
        self.assertIsNone(identity.resolve(None))

    def test_ephemeral_and_degenerate_roots_rejected(self):
        # V2 Phase 2: temp/scratch/config/degenerate roots are not projects
        for junk in ["/", "/tmp", "/private/tmp", "/var/tmp",
                     "/private/var/folders/sm/abcd1234567890/T",
                     os.path.expanduser("~/.claude/projects"),
                     os.path.expanduser("~")]:
            self.assertIsNone(identity.resolve(junk), junk)

    def test_deep_temp_subdir_still_resolves(self):
        # a real project that happens to live under a temp dir (pytest fixtures)
        # must still resolve - only the scratch ROOT itself is ephemeral
        with tempfile.TemporaryDirectory() as tmp:
            sub = os.path.join(tmp, "myproject")
            os.makedirs(sub)
            self.assertIsNotNone(identity.resolve(sub))


if __name__ == "__main__":
    unittest.main()
