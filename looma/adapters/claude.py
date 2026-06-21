"""Claude Code adapter.

Reads ~/.claude/projects/<encoded-cwd>/<sessionId>.jsonl. Each line is one JSON
record. We parse defensively (bad lines skipped, never fatal), preserve raw_json,
and emit NormalizedEvents for user/assistant/system turns. Project root and git
branch come from the records' own `cwd`/`gitBranch` fields (reliable), with the
encoded directory name as a fallback.
"""

import glob
import hashlib
import json
import os
from pathlib import Path
from typing import Iterator, Optional

from ..models import NormalizedEvent, SessionHandle

SOURCE = "claude"
_MESSAGE_TYPES = {"user", "assistant", "system"}


def _event_hash(session_id: str, uuid: Optional[str], line_no: int, line: str) -> str:
    basis = uuid or f"{session_id}:{line_no}:{line}"
    return hashlib.sha1(f"{SOURCE}:{session_id}:{basis}".encode("utf-8")).hexdigest()


def decode_encoded_cwd(dirname: str) -> Optional[str]:
    """Best-effort: '-Users-alice-code-myapp' -> a real path if it exists.

    The encoding is lossy (dir hyphens vs path separators), so we only return a
    path we can confirm on disk; otherwise None and the caller relies on record cwd.
    """
    if not dirname.startswith("-"):
        return None
    parts = [p for p in dirname.split("-") if p != ""]
    # greedily rebuild, merging segments that only exist when joined by '-'
    path = "/"
    i = 0
    while i < len(parts):
        candidate = os.path.join(path, parts[i])
        j = i
        while not os.path.exists(candidate) and j + 1 < len(parts):
            j += 1
            candidate = os.path.join(path, "-".join(parts[i : j + 1]))
        path = candidate
        i = j + 1
    return path if os.path.exists(path) else None


def _flatten_content(content) -> tuple[str, list[dict]]:
    """Return (text, tool_calls) from a Claude message content (str or block list)."""
    if isinstance(content, str):
        return content, []
    if not isinstance(content, list):
        return "", []
    texts, tools = [], []
    for block in content:
        if not isinstance(block, dict):
            continue
        bt = block.get("type")
        if bt == "text":
            texts.append(block.get("text", ""))
        elif bt == "thinking":
            texts.append(block.get("thinking", ""))
        elif bt == "tool_use":
            tools.append({"name": block.get("name"), "input": block.get("input") or {}})
        elif bt == "tool_result":
            c = block.get("content")
            if isinstance(c, str):
                texts.append(c)
            elif isinstance(c, list):
                for sub in c:
                    if isinstance(sub, dict) and sub.get("type") == "text":
                        texts.append(sub.get("text", ""))
    return "\n".join(t for t in texts if t), tools


class ClaudeAdapter:
    id = SOURCE

    def __init__(self, projects_dir: Path):
        self.projects_dir = Path(projects_dir)

    def discover(self) -> Iterator[SessionHandle]:
        if not self.projects_dir.exists():
            return
        for path in sorted(glob.glob(str(self.projects_dir / "*" / "*.jsonl"))):
            native_id = Path(path).stem
            yield SessionHandle(source=SOURCE, native_id=native_id, path=path)

    def read(self, handle: SessionHandle) -> Iterator[NormalizedEvent]:
        encoded_dir = Path(handle.path).parent.name
        fallback_root = decode_encoded_cwd(encoded_dir)
        seq = 0
        try:
            fh = open(handle.path, "r", encoding="utf-8", errors="replace")
        except OSError:
            return
        with fh:
            for line_no, line in enumerate(fh):
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    # malformed line: skip, never fatal
                    continue
                if not isinstance(rec, dict):
                    continue
                rtype = rec.get("type")
                if rtype not in _MESSAGE_TYPES:
                    continue
                msg = rec.get("message") or {}
                if not isinstance(msg, dict):
                    msg = {}
                text, tools = _flatten_content(msg.get("content"))
                role = msg.get("role") or rtype
                uuid = rec.get("uuid")
                seq += 1
                yield NormalizedEvent(
                    event_hash=_event_hash(handle.native_id, uuid, line_no, line),
                    source=SOURCE,
                    session_native_id=handle.native_id,
                    project_root=rec.get("cwd") or fallback_root,
                    git_remote=None,  # resolved later from project_root
                    git_branch=rec.get("gitBranch"),
                    seq=seq,
                    ts=rec.get("timestamp"),
                    role=role,
                    agent_model=msg.get("model"),
                    text=text,
                    tool_calls=tools,
                    raw_json=line,
                )
