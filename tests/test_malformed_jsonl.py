import tempfile
import unittest
from pathlib import Path

from looma import pipeline
from looma.adapters.claude import ClaudeAdapter
from looma.models import SessionHandle
from tests.helpers import make_store


class MalformedJsonlTest(unittest.TestCase):
    def _write(self, projects, lines):
        d = projects / "-proj"
        d.mkdir(parents=True, exist_ok=True)
        p = d / "sess-bad.jsonl"
        p.write_text("\n".join(lines) + "\n")
        return p

    def test_bad_lines_skipped_good_kept(self):
        with tempfile.TemporaryDirectory() as tmp:
            projects = Path(tmp) / "claude" / "projects"
            lines = [
                '{"type":"user","uuid":"u1","sessionId":"s","cwd":"/p","message":{"role":"user","content":"hello implement auth"}}',
                "{ this is not valid json",            # malformed
                "",                                     # blank
                "not json at all",                      # garbage
                '{"type":"assistant","uuid":"a1","sessionId":"s","cwd":"/p","message":{"role":"assistant","content":[{"type":"text","text":"ok"}]}}',
                '{"type":"summary","leafUuid":"x"}',    # non-message type, ignored
            ]
            path = self._write(projects, lines)
            adapter = ClaudeAdapter(projects)
            handle = SessionHandle("claude", "sess-bad", str(path))
            events = list(adapter.read(handle))
            self.assertEqual(len(events), 2, "only the 2 well-formed message records survive")
            self.assertEqual(events[0].role, "user")
            self.assertEqual(events[1].role, "assistant")

    def test_pipeline_survives_malformed(self):
        with tempfile.TemporaryDirectory() as tmp:
            projects = Path(tmp) / "claude" / "projects"
            self._write(
                projects,
                [
                    '{"type":"user","uuid":"u1","sessionId":"s","cwd":"/p","message":{"role":"user","content":"build login"}}',
                    "<<<corrupt>>>",
                ],
            )
            store = make_store()
            # must not raise
            pipeline.ingest_messages(store, projects_dir=projects)
            pipeline.rebuild(store)
            self.assertEqual(store.counts()["messages"], 1)


if __name__ == "__main__":
    unittest.main()
