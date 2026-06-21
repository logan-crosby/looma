"""Git ground-truth helpers. All best-effort; absence of git degrades gracefully."""

import re
import subprocess
from typing import Optional


def _run(args: list[str], cwd: Optional[str]) -> Optional[str]:
    try:
        out = subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return out.stdout.strip()


def normalize_remote(url: Optional[str]) -> Optional[str]:
    """git@github.com:org/repo.git | https://github.com/org/repo -> github.com/org/repo."""
    if not url:
        return None
    url = url.strip()
    # scp-like: git@host:org/repo(.git)
    m = re.match(r"^[\w.+-]+@([^:]+):(.+)$", url)
    if m:
        host, path = m.group(1), m.group(2)
    else:
        m = re.match(r"^[a-zA-Z][\w+.-]*://(?:[^@/]+@)?([^/]+)/(.+)$", url)
        if m:
            host, path = m.group(1), m.group(2)
        else:
            return None
    path = re.sub(r"\.git$", "", path).strip("/")
    return f"{host}/{path}".lower()


def remote_url(cwd: Optional[str]) -> Optional[str]:
    return _run(["git", "remote", "get-url", "origin"], cwd)


def repo_root(cwd: Optional[str]) -> Optional[str]:
    return _run(["git", "rev-parse", "--show-toplevel"], cwd)


def head_sha(cwd: Optional[str]) -> Optional[str]:
    return _run(["git", "rev-parse", "HEAD"], cwd)


def current_branch(cwd: Optional[str]) -> Optional[str]:
    b = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd)
    if b == "HEAD":  # detached
        return None
    return b


def dirty_files(cwd: Optional[str]) -> list[str]:
    out = _run(["git", "status", "--porcelain"], cwd)
    if not out:
        return []
    files = []
    for line in out.splitlines():
        # format: "XY path" (path may be quoted/renamed); take last token best-effort
        parts = line[3:].strip()
        if " -> " in parts:
            parts = parts.split(" -> ")[-1]
        files.append(parts.strip().strip('"'))
    return files


def commit_exists(sha: str, cwd: Optional[str]) -> bool:
    return _run(["git", "cat-file", "-e", f"{sha}^{{commit}}"], cwd) is not None


def commit_info(sha: str, cwd: Optional[str]) -> Optional[dict]:
    out = _run(["git", "show", "-s", "--format=%H%n%an%n%aI%n%s", sha], cwd)
    if not out:
        return None
    lines = out.splitlines()
    if len(lines) < 4:
        return None
    return {"sha": lines[0], "author": lines[1], "ts": lines[2], "message": lines[3]}


def commit_files(sha: str, cwd: Optional[str]) -> list[str]:
    out = _run(["git", "show", "--name-only", "--format=", sha], cwd)
    if not out:
        return []
    return [l.strip() for l in out.splitlines() if l.strip()]
