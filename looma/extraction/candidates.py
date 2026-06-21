"""Heuristic candidate-memory extraction (ARCHITECTURE.md 4.2/F).

Phase 1 uses pattern heuristics rather than a local LLM. Each detected line
becomes a CandidateMemory of a typed kind. These are staging-tier facts; only
promotion (section 5) moves corroborated ones into the graph.
"""

import re
from typing import Optional

from ..sanitize import is_noise, strip_injected

# Ordered so the strongest/most-specific kind wins when several match a line.
_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("decision", re.compile(r"(?i)\bwe (?:decided|chose|went with|agreed)\b")),
    ("decision", re.compile(r"(?i)\bdecision\b\s*[:\-]")),
    ("decision", re.compile(r"(?i)\buse\s+\S.+\s+instead of\s+\S")),
    ("decision", re.compile(r"(?i)\b(?:use|prefer|choose|going with)\s+\S.+\s+over\s+\S")),
    ("decision", re.compile(r"(?i)\blet'?s use\b")),
    ("bug", re.compile(r"(?i)\b(?:bug|regression|broken|crash(?:es|ed)?)\b")),
    ("bug", re.compile(r"(?i)\b(?:failing|fails|failed)\b")),
    ("bug", re.compile(r"(?i)\b(?:error|exception|traceback)\b")),
    ("architecture", re.compile(r"(?i)\b(?:architecture|design decision|constraint|trade-?off)\b")),
    ("todo", re.compile(r"(?i)\bTODO\b")),
    ("todo", re.compile(r"^\s*[-*]\s*\[\s\]\s+")),
    ("todo", re.compile(r"(?i)\b(?:we (?:need to|should)|still need to|next step)\b")),
    ("bug", re.compile(r"(?i)\b(?:fix(?:ed|es|ing)?)\b")),  # weakest, last
]

_MAX_LINE = 180
_MAX_PER_SESSION = 40
# lines that are mostly noise/log/caveat boilerplate
_SKIP = re.compile(
    r"(?i)(local-command|system-reminder|caveat:|stdout|stderr|\bnpm (?:warn|err)\b|"
    r"traceback|most recent call last|@typescript-eslint)"
)
# code / diff / log fragments that should never be a "memory"
_CODE = re.compile(
    r"(^\d+\s)|(^[0-9a-f]{7,40}\b)|[{}]|=>|;|`|</|/>|::|==|!=|\)\s*\{|<[A-Za-z][\w-]*[\s/>]|className=|"
    r"\b(?:const|let|await|function|return|def|import|class|console|npm|git)\b|\b\w+\([^)]*\)\s*[:{]"
)
_ALPHA_WORD = re.compile(r"[A-Za-z]{2,}")


def _clean(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip()


def _classify(line: str) -> Optional[str]:
    for kind, pat in _PATTERNS:
        if pat.search(line):
            return kind
    return None


def extract_candidates(messages: list[dict]) -> list[dict]:
    """Return candidate dicts: {kind, title, body, ts, message_id, role}."""
    out: list[dict] = []
    seen: set[str] = set()
    for m in messages:
        role = m.get("role")
        if role not in ("user", "assistant"):
            continue
        text = strip_injected(m.get("text") or "")
        for raw_line in text.splitlines():
            line = _clean(raw_line)
            if not (12 <= len(line) <= _MAX_LINE):
                continue
            if _SKIP.search(line) or is_noise(line):
                continue
            if _CODE.search(line) or line.count("*") >= 2:
                # code/diff fragments and markdown-bolded instruction/spec text
                continue
            if len(_ALPHA_WORD.findall(line)) < 4:
                continue
            kind = _classify(line)
            if not kind:
                continue
            key = (kind, line.lower())
            if key in seen:
                continue
            seen.add(key)
            out.append(
                {
                    "kind": kind,
                    "title": line,
                    "body": line,
                    "ts": m.get("ts"),
                    "message_id": m.get("id"),
                    "role": role,
                }
            )
            if len(out) >= _MAX_PER_SESSION:
                return out
    return out
