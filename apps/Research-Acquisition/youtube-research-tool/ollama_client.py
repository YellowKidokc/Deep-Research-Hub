"""Minimal Ollama client — local models do the language work.

No API key, no per-run cost, nothing leaves the machine. Everything here
degrades gracefully: if Ollama isn't running, callers get None and can fall
back to heuristics rather than crashing.

Models are chosen per job, not one-size-fits-all:
  FAST_MODEL  — per-video classification, run many times, needs to be quick
  SMART_MODEL — synthesis of a side's best case, run a few times, needs depth
  EMBED_MODEL — claim clustering by meaning rather than shared keywords
"""

from __future__ import annotations

import json
import math
import os
import urllib.error
import urllib.request

HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
FAST_MODEL = os.environ.get("OLLAMA_FAST_MODEL", "qwen3:4b-instruct")
SMART_MODEL = os.environ.get("OLLAMA_SMART_MODEL", "gemma4:latest")
EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")

# Synthesis over a long transcript is slow on CPU; don't cut it off mid-thought.
TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "600"))


class OllamaError(RuntimeError):
    """Ollama was reachable but could not satisfy the request."""


def use_fast_everywhere() -> None:
    """Collapse SMART_MODEL onto FAST_MODEL.

    Synthesis quality drops, but on CPU-only hardware a 9GB model costs
    minutes per call — enough to turn a 12-video run into an afternoon.
    """
    global SMART_MODEL
    SMART_MODEL = FAST_MODEL


def _post(path: str, payload: dict, timeout: int | None = None) -> dict:
    req = urllib.request.Request(
        f"{HOST}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout or TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def is_available() -> bool:
    """True if the Ollama daemon answers. Never raises."""
    try:
        req = urllib.request.Request(f"{HOST}/api/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False


def installed_models() -> list[str]:
    try:
        req = urllib.request.Request(f"{HOST}/api/tags")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return [m.get("name", "") for m in data.get("models", [])]
    except Exception:
        return []


def resolve_model(preferred: str) -> str | None:
    """Fall back to any installed model rather than failing on an exact tag."""
    models = installed_models()
    if not models:
        return None
    if preferred in models:
        return preferred
    stem = preferred.split(":")[0]
    for m in models:
        if m.split(":")[0] == stem:
            return m
    return None


def generate(prompt: str, model: str | None = None, system: str | None = None,
             temperature: float = 0.2, timeout: int | None = None) -> str | None:
    """Plain text completion. Returns None if Ollama is unreachable."""
    chosen = resolve_model(model or FAST_MODEL)
    if not chosen:
        return None
    payload: dict = {
        "model": chosen,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature},
    }
    if system:
        payload["system"] = system
    try:
        return _post("/api/generate", payload, timeout).get("response", "").strip()
    except Exception:
        return None


def generate_json(prompt: str, model: str | None = None, system: str | None = None,
                  temperature: float = 0.1, timeout: int | None = None):
    """Completion constrained to JSON. Returns the parsed object, or None.

    Ollama's format=json still occasionally wraps output in prose or a fenced
    block, so the raw text is salvaged before giving up.
    """
    chosen = resolve_model(model or FAST_MODEL)
    if not chosen:
        return None
    payload: dict = {
        "model": chosen,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": temperature},
    }
    if system:
        payload["system"] = system
    try:
        raw = _post("/api/generate", payload, timeout).get("response", "")
    except Exception:
        return None
    return _salvage_json(raw)


def _salvage_json(raw: str):
    if not raw:
        return None
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    if "```" in raw:
        chunk = raw.split("```")[1]
        chunk = chunk[4:] if chunk.lower().startswith("json") else chunk
        try:
            return json.loads(chunk.strip())
        except json.JSONDecodeError:
            pass
    # Last resort: the outermost brace/bracket span.
    for opener, closer in (("{", "}"), ("[", "]")):
        start, end = raw.find(opener), raw.rfind(closer)
        if start != -1 and end > start:
            try:
                return json.loads(raw[start:end + 1])
            except json.JSONDecodeError:
                continue
    return None


def embed(text: str, model: str | None = None) -> list[float] | None:
    chosen = resolve_model(model or EMBED_MODEL)
    if not chosen:
        return None
    try:
        data = _post("/api/embeddings", {"model": chosen, "prompt": text}, timeout=120)
    except Exception:
        return None
    vec = data.get("embedding")
    return vec if vec else None


def embed_many(texts: list[str], model: str | None = None) -> list[list[float] | None]:
    return [embed(t, model) for t in texts]


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0
