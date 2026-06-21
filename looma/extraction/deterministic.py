"""Deterministic extraction - files, commits, commands (ARCHITECTURE.md 4.1).

No model involved. High precision: file paths come from tool-call arguments
(ground truth for what the agent touched), commit SHAs are validated with
`git cat-file`, commands come from Bash tool calls.
"""

import functools
import json
import os
import re
from typing import Optional

from .. import gitutil

FILE_TOOLS = {"Edit", "Write", "Read", "MultiEdit", "NotebookEdit", "Update", "Create"}
_SHA_RE = re.compile(r"\b[0-9a-f]{7,40}\b")
_PATH_RE = re.compile(r"[\w./-]+\.[A-Za-z][\w]{0,7}")
# SHAs in recognizable git output ("commit <sha>", "[branch <sha>]", "HEAD is now at <sha>")
_GIT_OUTPUT_SHA = re.compile(
    r"(?im)^\s*(?:commit\s+|HEAD is now at\s+|\[[^\]]*\s)([0-9a-f]{7,40})\b"
)
_GIT_CMD_HINT = re.compile(r"\bgit\b|\bcommit\b|\bcherry-pick\b|\brebase\b|\bHEAD\b")


@functools.lru_cache(maxsize=100000)
def _cached_commit_exists(root: str, sha: str) -> bool:
    return gitutil.commit_exists(sha, root)


def _rel_under_root(path: str, root: Optional[str]) -> Optional[str]:
    if not path:
        return None
    if not root:
        # no repo context: accept path-ish tokens with an extension
        return path if ("/" in path and "." in os.path.basename(path)) else None
    try:
        ap = os.path.abspath(path if os.path.isabs(path) else os.path.join(root, path))
    except (OSError, ValueError):
        return None
    root_abs = os.path.abspath(root)
    if ap == root_abs or ap.startswith(root_abs + os.sep):
        return os.path.relpath(ap, root_abs)
    return None


def _tool_calls(message: dict) -> list[dict]:
    raw = message.get("tool_calls")
    if not raw:
        return []
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return []
    return raw if isinstance(raw, list) else []


def session_artifacts(messages: list[dict], project_root: Optional[str], validate=None) -> dict:
    """Return {'files': [...], 'commands': [...], 'shas': [...]} for a session.

    `validate(sha) -> bool` lets the caller supply a persistent cache; defaults to a
    per-process lru-cached `git cat-file`. SHA candidates are only collected from git
    commands or recognizable git output - never arbitrary hex tokens in logs.
    """
    files: set[str] = set()
    commands: list[str] = []
    raw_shas: set[str] = set()

    for m in messages:
        for call in _tool_calls(m):
            name = call.get("name")
            inp = call.get("input") or {}
            if name in FILE_TOOLS:
                for key in ("file_path", "notebook_path", "path"):
                    p = inp.get(key)
                    rel = _rel_under_root(p, project_root) if p else None
                    if rel:
                        files.add(rel)
            if name == "Bash":
                cmd = inp.get("command")
                if cmd:
                    commands.append(cmd.strip()[:200])
                    if _GIT_CMD_HINT.search(cmd):
                        raw_shas.update(_SHA_RE.findall(cmd))
        text = m.get("text") or ""
        # path tokens mentioned in prose, validated against the tree (only when we
        # have a real root on disk - rootless projects skip the existence check)
        if project_root:
            for tok in _PATH_RE.findall(text):
                rel = _rel_under_root(tok, project_root)
                if rel and os.path.exists(os.path.join(project_root, rel)):
                    files.add(rel)
        # SHAs from recognizable git output only
        for m2 in _GIT_OUTPUT_SHA.finditer(text):
            raw_shas.add(m2.group(1))

    if validate is None:
        def validate(sha):
            return bool(project_root) and _cached_commit_exists(project_root, sha)

    shas: list[str] = []
    seen = set()
    for sha in raw_shas:
        if len(sha) < 7 or sha in seen:
            continue
        seen.add(sha)
        if validate(sha):
            shas.append(sha)

    return {"files": sorted(files), "commands": commands, "shas": shas}
