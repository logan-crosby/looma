"""Project identity resolution (ARCHITECTURE.md section 3).

First hit wins: normalized git remote -> git root path -> raw path. The returned
canonical_key is the cross-agent join key.
"""

import os
from typing import Optional

from . import gitutil


def resolve(root: Optional[str]) -> Optional[dict]:
    """Resolve a directory to a project identity dict, or None if no root."""
    if not root:
        return None
    root = os.path.abspath(os.path.expanduser(root))

    git_root = gitutil.repo_root(root) or root
    remote = gitutil.normalize_remote(gitutil.remote_url(root))

    if remote:
        canonical_key = remote
    elif git_root:
        canonical_key = f"path:{git_root}"
    else:
        canonical_key = f"path:{root}"

    display = os.path.basename(git_root.rstrip("/")) or git_root
    return {
        "canonical_key": canonical_key,
        "display_name": display,
        "root_path": git_root,
        "git_remote": remote,
    }
