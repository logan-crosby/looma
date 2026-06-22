"""Project identity resolution (ARCHITECTURE.md section 3).

First hit wins: normalized git remote -> git root path -> raw path. The returned
canonical_key is the cross-agent join key.
"""

import os
import re
from typing import Optional

from . import gitutil

# Roots that are not a project: the filesystem root, OS temp/scratch dirs, and
# config/cache homes. A session whose only cwd is one of these does not "belong"
# to a repository - it is routed to the shared unsorted bucket instead of minting
# a junk project named "tmp" or "/". (V2 Phase 2 identity hygiene.)
_EPHEMERAL_ROOT = re.compile(
    r"^/$"                                            # filesystem root
    r"|^/(?:private/)?tmp/?$"                         # the temp root itself
    r"|^/var/tmp/?$"
    r"|^/(?:private/)?var/folders/[^/]+/[^/]+/[A-Z]/?$"  # macOS per-user scratch root (.../T, .../C)
    r"|/\.(?:claude|codex|cursor|config|cache)(?:/|$)"   # config/cache homes
)


def _is_ephemeral(path: str) -> bool:
    # match both the raw and symlink-resolved form (/tmp vs /private/tmp on macOS)
    if _EPHEMERAL_ROOT.search(path) or _EPHEMERAL_ROOT.search(os.path.realpath(path)):
        return True
    # the user's home directory itself (not a subdir of it) is too broad
    return os.path.abspath(path) == os.path.abspath(os.path.expanduser("~"))


def resolve(root: Optional[str]) -> Optional[dict]:
    """Resolve a directory to a project identity dict, or None if no root.

    Returns None for missing, ephemeral, or degenerate roots (temp dirs, the
    filesystem root, config homes) so the caller buckets the session rather than
    creating a meaningless project.
    """
    if not root:
        return None
    root = os.path.abspath(os.path.expanduser(root))

    git_root = gitutil.repo_root(root) or root
    # an ephemeral *git root* is still ephemeral; a real repo under /tmp is rare
    # and not worth a permanent identity
    if _is_ephemeral(git_root):
        return None
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
