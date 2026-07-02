"""Extractor interface + implementations (ARCHITECTURE.md 4, goal Phase B).

An Extractor turns a session's messages into a typed extraction:
    {"memories": [{"kind": decision|todo|bug|architecture, "title": str}],
     "work":     {"label": str|None, "kind": str}}

Both implementations return the SAME schema so they are interchangeable and
benchmarkable. HeuristicExtractor reuses the existing deterministic logic (no
duplication). LocalLLMExtractor talks to a fully-local model server (llama.cpp
llama-server or Ollama) - no hosted API - and falls back to heuristic on any error.

Model detection tries backends in priority order (erebos direct Tailscale HTTP →
erebos SSH tunnel → local Ollama → llama.cpp), so the same code works whether
the model is served from a remote desktop (erebos via Tailscale or SSH tunnel)
or locally on this machine.
"""

import functools
import json
import os
import urllib.request
from typing import Optional

from . import candidates as _cand
from ..resolution import workitems as _wi

MEMORY_KINDS = ("decision", "todo", "bug", "architecture")


class HeuristicExtractor:
    name = "heuristic"

    def extract(self, messages: list[dict]) -> dict:
        mems = [{"kind": c["kind"], "title": c["title"]}
                for c in _cand.extract_candidates(messages)]
        label, kind = _wi._intent(messages)
        return {"memories": mems, "work": {"label": label, "kind": kind}}


# --------------------------------------------------------------------------- #
# Local LLM extractor
# --------------------------------------------------------------------------- #

_PROMPT = """Extract structured project memory from a coding session transcript.
Return ONLY one JSON object, no prose:
{"memories":[{"kind":"...","title":"..."}],"work":{"label":"...","kind":"..."}}

kind meanings (classify carefully):
- decision: a choice made between alternatives ("use X instead of Y", "we decided").
- todo: work still to be done ("we need to", "still need to", "TODO").
- bug: a CONCRETE wrong behavior that was observed (a specific thing returns the
  wrong result, crashes, or does not work). NOT a vague worry or a planned task.
- architecture: a design rule or structural constraint.
work.kind is one of: feature, bugfix, refactor, migration, investigation.

Rules:
- Extract ONLY what the developer EXPLICITLY stated. Do not invent or infer.
- IGNORE the assistant narrating its own actions ("Let me check...", "I'm adding
  tests...", "I'll fix that", "Now I will..."), code, diffs, stack traces, logs,
  lint output, tool results, ascii diagrams, and role-prefixed transcript lines.
  These are NOT memories.
- A todo/bug is OPEN work. Finished work ("done:", "tests pass", "checks passed")
  is NOT a todo or bug.
- No duplicates. At most 5 memories. Choose the correct kind for each.

Example transcript:
[user] Let's switch the API to gRPC. We decided gRPC over REST for lower latency.
[assistant] I'll start. Let me look at the current REST handlers.
[user] There's a bug: the health check returns 200 even when the DB is down. We also need to add a timeout to outbound calls.
Example JSON:
{"memories":[{"kind":"decision","title":"Use gRPC over REST for lower latency"},{"kind":"bug","title":"Health check returns 200 even when the DB is down"},{"kind":"todo","title":"Add a timeout to outbound calls"}],"work":{"label":"Migrate API to gRPC","kind":"migration"}}

Now do the same for this transcript:
[transcript]
{transcript}
[end]
JSON:"""


# Cached model name from the last successful detect_server() probe — so
# _call() uses the same model that detection found, without needing an env var.
_detected_model: Optional[str] = None

# Backend URLs tried in priority order when LOOMA_LLM_URL is not explicitly set.
# Port assignments (compatible with claude-qwen conventions — see ~/.zshrc):
#   desktop-cf5rf9b:11434 — erebos direct HTTP via Tailscale MagicDNS (primary)
#   11334 — Ollama tunneled from erebos (SSH -L 11334:127.0.0.1:11434)
#   11434 — Ollama running locally on this machine (also used by claude-qwen-local)
#   8080  — llama.cpp llama-server (legacy)
_BACKEND_URLS: tuple[str, ...] = (
    "http://desktop-cf5rf9b:11434/v1/chat/completions",  # erebos direct (Tailscale)
    "http://localhost:11334/v1/chat/completions",         # erebos tunnel (SSH -L)
    "http://localhost:11434/v1/chat/completions",         # local Ollama
    "http://localhost:8080/v1/chat/completions",          # llama.cpp (legacy)
)


def _local_url() -> str:
    # Ollama serves on :11434 by default; llama.cpp on :8080.
    # Set LOOMA_LLM_URL explicitly to override the entire probe list.
    return os.environ.get("LOOMA_LLM_URL", "http://localhost:11434/v1/chat/completions")


def _model() -> str:
    # Env override → detected model → sensible default (qwen2.5-coder:7b,
    # the model proven at 0.92 F1 on this benchmark).
    return os.environ.get("LOOMA_LLM_MODEL", _detected_model or "qwen2.5-coder:7b")


def _transcript(messages: list[dict], max_chars: int = 6000) -> str:
    from ..sanitize import strip_injected

    lines = []
    for m in messages:
        if m.get("role") not in ("user", "assistant"):
            continue
        t = strip_injected(m.get("text") or "").strip()
        if t:
            lines.append(f"[{m.get('role')}] {t}")
    blob = "\n".join(lines)
    return blob[:max_chars]


def _extract_json(text: str):
    """Return the first complete JSON value (object OR array), or None."""
    if not text:
        return None
    candidates = [i for i in (text.find("{"), text.find("[")) if i >= 0]
    if not candidates:
        return None
    start = min(candidates)
    open_ch = text[start]
    close_ch = "}" if open_ch == "{" else "]"
    depth = 0
    for i in range(start, len(text)):
        if text[i] == open_ch:
            depth += 1
        elif text[i] == close_ch:
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except (json.JSONDecodeError, ValueError):
                    return None
    return None


def _clean_memories(mems_raw) -> list[dict]:
    """Validate + sanitize raw model memories. Enforces kind/length, ASCII-folds
    titles, drops anything the shared heuristic guard rejects (transcript/agent
    meta, narration, code), and de-dupes - so the LLM path produces the same
    quality of output as the heuristic and cannot reintroduce filtered junk."""
    from ..util import to_ascii

    out, seen = [], set()
    for m in (mems_raw or [])[:8]:
        if not isinstance(m, dict):
            continue
        kind = (m.get("kind") or "").strip().lower()
        title = to_ascii((m.get("title") or "").strip())
        if kind not in MEMORY_KINDS or not (8 <= len(title) <= 200):
            continue
        if _cand.rejects_memory(kind, title):
            continue
        key = (kind, title.lower())
        if key in seen:
            continue
        seen.add(key)
        out.append({"kind": kind, "title": title})
    return out


class LocalLLMExtractor:
    name = "llm"

    def __init__(self, fallback=None, timeout: float = 120.0):
        self.fallback = fallback or HeuristicExtractor()
        self.timeout = timeout

    def _call(self, prompt: str) -> Optional[str]:
        body = json.dumps({
            "model": _model(),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_tokens": 700,
        }).encode()
        req = urllib.request.Request(
            _local_url(), data=body, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                data = json.loads(r.read())
            return data["choices"][0]["message"]["content"]
        except Exception:
            return None

    def extract(self, messages: list[dict]) -> dict:
        transcript = _transcript(messages)
        if not transcript.strip():
            return {"memories": [], "work": {"label": None, "kind": "feature"}}
        raw = self._call(_PROMPT.replace("{transcript}", transcript))
        parsed = _extract_json(raw) if raw else None
        if parsed is None:
            return self.fallback.extract(messages)  # robust local fallback
        # accept either a bare array of memories or the wrapped {memories, work} object
        if isinstance(parsed, list):
            mems_raw, work = parsed, {}
        elif isinstance(parsed, dict):
            mems_raw, work = (parsed.get("memories") or []), (parsed.get("work") or {})
        else:
            return self.fallback.extract(messages)
        mems = _clean_memories(mems_raw)
        label = (str(work.get("label") or "")).strip() or None
        if label and label.lower() in ("null", "none"):
            label = None
        kind = (work.get("kind") or "").strip().lower()
        if kind not in ("feature", "bugfix", "refactor", "migration", "investigation"):
            kind = ""
        # fall back to the heuristic work signal when the LLM omits or botches it
        if not label or not kind:
            hl, hk = _wi._intent(messages)
            label = label or hl
            kind = kind or hk
        return {"memories": mems, "work": {"label": label, "kind": kind}}


def _server_model(data) -> Optional[str]:
    """Model id from a /v1/models payload, or None when no model is loaded.

    A reachable server with an empty or null model list (e.g. llama-server idle,
    or the OpenAI-compatible shim on :8080 returning {"data": null}) must NOT
    count as available - otherwise auto-mode picks the LLM and fails every call.
    """
    if not isinstance(data, dict):
        return None
    items = data.get("data")
    if not isinstance(items, list) or not items:
        return None
    first = items[0] if isinstance(items[0], dict) else {}
    mid = first.get("id")
    if not isinstance(mid, str) or not mid.strip():
        return None
    return mid.split("/")[-1]


@functools.lru_cache(maxsize=8)
def detect_server(base_url: Optional[str] = None):
    """Probe for a reachable local OpenAI-compatible model server WITH a model.

    Returns (ok: bool, model_name | None). Cached per process: a short-lived CLI
    probes once. Pure stdlib (urllib) — no new dependency. Short timeout so the
    zero-dependency default path stays fast when no server is running.

    When `base_url` is explicitly provided (LOOMA_LLM_URL env var), probes only
    that URL. Otherwise tries multiple URLs in priority order: erebos tunnel
    on :11334, local Ollama on :11434, llama.cpp on :8080. The first reachable
    server with a model loaded wins.
    """
def detect_server(base_url: Optional[str] = None):
    """Probe for a reachable local OpenAI-compatible model server WITH a model.

    Returns (ok: bool, model_name | None). Cached per process: a short-lived CLI
    probes once. Pure stdlib (urllib) — no new dependency. Short timeout so the
    zero-dependency default path stays fast when no server is running.

    When `base_url` is explicitly provided (LOOMA_LLM_URL env var), probes only
    that URL. Otherwise tries multiple URLs in priority order: erebos direct
    Tailscale HTTP, erebos SSH tunnel, local Ollama, llama.cpp. The first
    reachable server with a model loaded wins.
    """
    global _detected_model

    urls = (base_url,) if base_url else _BACKEND_URLS

    for url in urls:
        models_url = url.rsplit("/chat/completions", 1)[0].rstrip("/") + "/models"
        try:
            with urllib.request.urlopen(models_url, timeout=0.6) as r:
                data = json.loads(r.read())
        except Exception:
            continue
        name = _server_model(data)
        if name:
            _detected_model = name
            return (True, name)

    _detected_model = None
    return (False, None)


def get_extractor(name: Optional[str] = None):
    """Select an extractor. Modes: auto (default) | heuristic | llm.

    'auto' uses the local LLM when a model server is detected, else the heuristic -
    so the LLM is the best-supported path when available, and the stdlib-only
    heuristic remains the default when it is not.
    """
    name = (name or os.environ.get("LOOMA_EXTRACTOR", "auto")).lower()
    if name == "heuristic":
        return HeuristicExtractor()
    if name == "llm":
        return LocalLLMExtractor()
    # auto
    return LocalLLMExtractor() if detect_server()[0] else HeuristicExtractor()
