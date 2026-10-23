# API Pipeline Universal Prep Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` (native) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn `000_QUICK_CALL` into the mandatory `00_PREP` gate so every API pipeline item gets UUID, classification, master equation, knowledge graph, tags, naming, and DEBATE_MAP matching before downstream stations run; add a master JSON aggregator.

**Architecture:** Refactor `000_QUICK_CALL/quick_call.py` into a reusable `prep_lib.py`, add an engine-native `00_prep.py`, add DEBATE_MAP indexing + matching helpers in `_system/engine/`, add the aggregator in `_system/tools/`, and wire `041_STORIES` as the pilot dependent station.

**Tech Stack:** Python 3.12, existing engine framework, DeepSeek API, YAML/JSON sidecars.

**Spec:** `docs/superpowers/specs/2026-10-20-api-prep-gate-design.md`

## Global Constraints

- Work on the `work` branch; one-line commits.
- No absolute paths in code; use `_system/config/paths.json` for `debate_map`.
- `INBOX`/`OUTBOX` content and `paths.json` are not committed.
- Every station front folder must contain `BACKSIDE/station.json`, script, `PROMPT.md`, `FOCUS.md`, `README.md`.
- Scripts find `_system` by walking up; never hard-code folder position.
- Add tests to `_system/tests/test_prep.py` using `unittest`.

## Review Focus

- Prep runs idempotently: same bytes → same UUID, no duplicate registry entries.
- Sidecar YAML is valid and complete even when AI calls fail.
- DEBATE_MAP matching returns reasonable questions for resurrection/fine-tuning/moral-law samples.
- `041_STORIES` reads the prep header and re-runs when prep changes.
- Aggregator builds a master JSON that includes prep + story outputs.
- The legacy ad-hoc prompt still works via `--call QUICK_CALL`.

---

## File Structure

| File | Responsibility |
|---|---|
| `000_QUICK_CALL/BACKSIDE/station.json` | Updated metadata: label `00_PREP`, goals, script `00_prep.py`. |
| `_system/config/stations.json` | Number `00` row renamed to PREP. |
| `_system/config/paths.json` + `path_keys.json` | New `debate_map` key. |
| `000_QUICK_CALL/BACKSIDE/prep_lib.py` | Identity, NABLA, YAML sidecar, master-equation helpers. |
| `000_QUICK_CALL/BACKSIDE/00_prep.py` | Engine-native prep station script. |
| `000_QUICK_CALL/BACKSIDE/00_quick_call.py` | Legacy ad-hoc prompt (unchanged, invoked via `--call QUICK_CALL`). |
| `000_QUICK_CALL/BACKSIDE/PROMPT.md` | Prep prompt (NABLA + master equation + DEBATE_MAP). |
| `000_QUICK_CALL/BACKSIDE/FOCUS.md` | Station focus. |
| `000_QUICK_CALL/BACKSIDE/README.md` | What the station does now. |
| `_system/engine/debate_map_index.py` | Build + cache question index; keyword pre-filter. |
| `_system/tools/aggregate_api_results.py` | Walk station runs and build `_data/master/<uuid>/master.json`. |
| `_system/tests/test_prep.py` | Unit + smoke tests. |
| `041_STORIES/BACKSIDE/station.json` | Add `"depends_on": ["00_PREP"]`. |

---

### Task 1: Add `debate_map` config key

**Files:**
- Modify: `D:/GitHub/pipeline-workflows/API/_system/config/paths.json`
- Modify: `D:/GitHub/pipeline-workflows/API/_system/config/paths.example.json`
- Modify: `D:/GitHub/pipeline-workflows/API/_system/config/path_keys.json`
- Test: `D:/GitHub/pipeline-workflows/API/_system/tests/test_prep.py`

**Interfaces:**
- Consumes: existing `paths.configured()` / `paths.external()`
- Produces: `debate_map` key available to engine code

- [ ] **Step 1: Write the failing test**

```python
import json
import os
import tempfile
import unittest
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]

class TestDebateMapPath(unittest.TestCase):
    def test_debate_map_key_is_configurable(self):
        from engine import paths
        # With a temp override, debate_map resolves
        with tempfile.TemporaryDirectory() as td:
            cfg = Path(td) / "paths.json"
            cfg.write_text(json.dumps({"debate_map": td}), encoding="utf-8")
            os.environ["ONE_MENU_PATHS_FILE"] = str(cfg)
            paths._cached_paths = None
            self.assertTrue(paths.configured("debate_map"))
            del os.environ["ONE_MENU_PATHS_FILE"]
            paths._cached_paths = None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest _system/tests/test_prep.py::TestDebateMapPath::test_debate_map_key_is_configurable -v`
Expected: FAIL because `debate_map` is not in `path_keys.json` / `paths.json`.

- [ ] **Step 3: Add the config key**

Add to `_system/config/paths.json`:
```json
  "debate_map": "C:/Users/David/Documents/faiththruphysics.com/Canon/DEBATE_MAP"
```

Add to `_system/config/paths.example.json`:
```json
  "debate_map": ""
```

Add to `_system/config/path_keys.json`:
```json
  "debate_map": {
    "what": "Canon DEBATE_MAP folder (Pxx_*/Qx_*) used by 00_PREP to match items to questions",
    "fingerprint": null
  }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest _system/tests/test_prep.py::TestDebateMapPath::test_debate_map_key_is_configurable -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add _system/config/paths.json _system/config/paths.example.json _system/config/path_keys.json _system/tests/test_prep.py
git commit -m "config: add debate_map path key for prep gate"
```

---

### Task 2: Create DEBATE_MAP indexer

**Files:**
- Create: `D:/GitHub/pipeline-workflows/API/_system/engine/debate_map_index.py`
- Test: `D:/GitHub/pipeline-workflows/API/_system/tests/test_prep.py`

**Interfaces:**
- Consumes: `paths.external("debate_map")`
- Produces: `list[dict]` with keys `id`, `section`, `question`, `keywords`

- [ ] **Step 1: Write the failing test**

```python
import tempfile
import unittest
from pathlib import Path

class TestDebateMapIndex(unittest.TestCase):
    def test_index_scans_question_folders(self):
        from engine import debate_map_index
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "P07_JESUS" / "07_Q-JESUS-RESURRECTION").mkdir(parents=True)
            (root / "P07_JESUS" / "07_Q-JESUS-RESURRECTION" / "README.md").write_text(
                "# Q-JESUS-RESURRECTION\n\n**Question:** Did Jesus rise from the dead?\n", encoding="utf-8")
            idx = debate_map_index.build_index(root)
            self.assertEqual(1, len(idx))
            self.assertEqual("07_Q-JESUS-RESURRECTION", idx[0]["id"])
            self.assertIn("Did Jesus rise from the dead?", idx[0]["question"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest _system/tests/test_prep.py::TestDebateMapIndex::test_index_scans_question_folders -v`
Expected: FAIL — module not defined.

- [ ] **Step 3: Implement the indexer**

```python
"""DEBATE_MAP question index for 00_PREP matching."""
from __future__ import annotations

import json
import re
from pathlib import Path

from .paths import external


def _read_question(folder: Path) -> str:
    readme = folder / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"\*\*Question:\*\*\s*(.+)", text)
        if m:
            return m.group(1).strip()
    q = folder / "QUESTION.md"
    if q.exists():
        text = q.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^#\s+(.+)$", text, re.M)
        if m:
            return m.group(1).strip()
    return folder.name


def _keywords(question: str, folder_name: str) -> list[str]:
    text = f"{question} {folder_name}".lower()
    tokens = re.findall(r"[a-z0-9']+", text)
    stop = {"did", "the", "a", "an", "is", "are", "was", "were", "from", "of", "in", "to", "and", "or", "for",
            "with", "as", "by", "it", "that", "this", "these", "those", "what", "how", "why", "when", "where",
            "who", "which", "q", "jesus", "god"}
    return sorted({t for t in tokens if t not in stop and len(t) > 2})


def build_index(root: Path | None = None) -> list[dict]:
    root = root or external("debate_map")
    out = []
    for qfolder in sorted(root.rglob("Q-*")):
        if not qfolder.is_dir():
            continue
        section = qfolder.parent.name
        question = _read_question(qfolder)
        out.append({
            "id": qfolder.name,
            "section": section,
            "question": question,
            "keywords": _keywords(question, qfolder.name),
            "path": str(qfolder),
        })
    return out


def keyword_score(index: list[dict], text: str, top_n: int = 10) -> list[dict]:
    words = set(re.findall(r"[a-z0-9']+", text.lower()))
    scored = []
    for entry in index:
        hits = words.intersection(entry["keywords"])
        if hits:
            scored.append({**entry, "keyword_hits": sorted(hits),
                           "keyword_score": len(hits) / max(len(entry["keywords"]), 1)})
    scored.sort(key=lambda x: x["keyword_score"], reverse=True)
    return scored[:top_n]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest _system/tests/test_prep.py::TestDebateMapIndex::test_index_scans_question_folders -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add _system/engine/debate_map_index.py _system/tests/test_prep.py
git commit -m "feat: DEBATE_MAP question indexer"
```

---

### Task 3: Refactor `quick_call.py` into `prep_lib.py`

**Files:**
- Create: `D:/GitHub/pipeline-workflows/API/000_QUICK_CALL/BACKSIDE/prep_lib.py`
- Keep: `D:/GitHub/pipeline-workflows/API/000_QUICK_CALL/quick_call.py` (legacy wrapper)
- Test: `D:/GitHub/pipeline-workflows/API/_system/tests/test_prep.py`

**Interfaces:**
- Consumes: `identity.py`, `nabla.py`
- Produces: `mint_identity(source_path)`, `classify_nabla(text)`, `write_sidecar(item_folder, data)`

- [ ] **Step 1: Write the failing test**

```python
import tempfile
import unittest
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]
API = HOME.parent

class TestPrepLib(unittest.TestCase):
    def test_mint_identity_creates_uuid(self):
        import sys
        sys.path.insert(0, str(API / "000_QUICK_CALL" / "BACKSIDE"))
        import prep_lib
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "paper.md"
            src.write_text("# Test\n", encoding="utf-8")
            reg = Path(td) / "registry.json"
            result = prep_lib.mint_identity(src, registry_path=reg)
            self.assertEqual(36, len(result["paper_uuid"]))
            self.assertTrue(reg.exists())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest _system/tests/test_prep.py::TestPrepLib::test_mint_identity_creates_uuid -v`
Expected: FAIL — `prep_lib` not defined.

- [ ] **Step 3: Implement `prep_lib.py`**

Move identity/classification/YAML helpers from `quick_call.py`:

```python
"""Shared helpers for the 00_PREP gate."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import identity
import nabla


def _central(key: str) -> str | None:
    try:
        cfg = json.load(open(Path(__file__).resolve().parents[2] / "_system" / "config" / "paths.json",
                            encoding="utf-8"))
        return cfg.get(key) or None
    except Exception:
        return None


def originals_root() -> Path:
    raw = os.environ.get("API_ORIGINALS") or _central("originals_root")
    if raw:
        return Path(raw).expanduser()
    # fallback relative to API home (for tests)
    return Path(__file__).resolve().parents[2] / "_data" / "originals"


def yaml_dump(o, ind=0):
    pad = "  " * ind
    out = []
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, (dict, list)) and v:
                out.append(f"{pad}{k}:")
                out.append(yaml_dump(v, ind + 1))
            else:
                out.append(f"{pad}{k}: {json.dumps(v, ensure_ascii=False) if v not in ({}, []) else ('{}' if v == {} else '[]')}")
    else:
        for v in o:
            if isinstance(v, (dict, list)):
                out.append(f"{pad}-")
                out.append(yaml_dump(v, ind + 1))
            else:
                out.append(f"{pad}- {json.dumps(v, ensure_ascii=False)}")
    return "\n".join(out)


def mint_identity(source_path: Path, *, parent_uuid: str | None = None,
                  registry_path: Path | None = None) -> dict:
    source_path = Path(source_path)
    raw = source_path.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    stem = source_path.stem
    reg = identity.Registry(str(registry_path or (Path(__file__).resolve().parent / "UUID_REGISTRY.json")))
    pid, new = reg.resolve(sha, stem, parent_uuid)
    reg.save()
    originals = originals_root()
    originals.mkdir(parents=True, exist_ok=True)
    orig = originals / f"{stem}__{sha[:12]}{source_path.suffix}"
    if not orig.exists():
        shutil.copy2(source_path, orig)
    paper = reg.data["papers"][pid]
    version = next(v for v in paper["versions"] if v["sha256"] == sha)
    return {
        "paper_uuid": pid,
        "version_uuid": identity.version_uuid(sha),
        "version_n": version["n"],
        "source_sha256": sha,
        "source_file": source_path.name,
        "original_copy": str(orig),
        "new_version": new,
    }


def ask_ai(text: str, system_prompt: str) -> dict:
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        raise RuntimeError("DEEPSEEK_API_KEY not set")
    url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/") + "/chat/completions"
    body = {
        "model": "deepseek-chat",
        "response_format": {"type": "json_object"},
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text[:60000]},
        ],
    }
    req = urllib.request.Request(url, json.dumps(body).encode(),
                                 {"Content-Type": "application/json", "Authorization": "Bearer " + key})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(json.loads(r.read())["choices"][0]["message"]["content"])


def classify_nabla(text: str) -> dict:
    try:
        p = ask_ai(text, nabla.ENCODER_PROMPT)
        v = {k: int(p["vector"][k]) for k in nabla.ORDER}
        errs = nabla.validate(p["filing"], v)
        conf = p.get("confidence", {})
        return {
            "status": "VALID" if not errs else "INVALID",
            "errors": errs,
            "address": nabla.address(p["filing"], v) if not errs else None,
            "filing": p["filing"],
            "vector": nabla.vector_str(v),
            "hash": nabla.semantic_hash(v),
            "confidence": conf,
            "review_flags": p.get("review_flags", []) + [f"low confidence {k}" for k, c in conf.items() if float(c) < 0.75],
            "minimal_decode": p.get("minimal_decode"),
            "truth_modes": p.get("truth_modes", []),
            "operators": p.get("operators", []),
            "proposed_by": "deepseek-chat (semantic, AI-proposed)",
            "validated_by": "nabla.py (deterministic)",
        }
    except Exception as e:
        return {"status": "FAILED", "error": str(e)}


def propose_master_equation(text: str, nabla_address: str | None) -> str:
    prompt = (
        "Propose a short MASTER_EQUATION_ID for this artifact. "
        "Return ONLY JSON: {\"master_equation_id\": \"ME-UPPER_SNAKE\"}. "
        "Use the NABLA address and a one-sense decode to pick a canonical pill if possible.\n\n"
        f"NABLA: {nabla_address or 'unknown'}\n\n{text[:4000]}"
    )
    try:
        return ask_ai(text, prompt).get("master_equation_id", "ME-UNKNOWN")
    except Exception:
        return "ME-UNKNOWN"


def build_sidecar(identity_block: dict, nabla_block: dict, me_id: str | None,
                  knowledge_graph: dict, debate_matches: list, naming: dict | None = None) -> dict:
    if naming is None:
        naming = {"stem": identity_block["source_file"].rsplit(".", 1)[0]}
    return {
        "record_type": "QUICK_CALL_HEADER",
        "schema": "00_PREP v0.1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "identity": identity_block,
        "naming": naming,
        "branch": {"series": None, "position": None, "of": None},
        "master_equation_id": me_id or "ME-UNKNOWN",
        "nabla": nabla_block,
        "knowledge_graph": knowledge_graph,
        "debate_map_matches": debate_matches,
        "tags": {
            "domain": [nabla_block.get("filing", {}).get("D", "UNKNOWN")] if isinstance(nabla_block.get("filing"), dict) else [],
            "topics": [],
            "move": nabla_block.get("filing", {}).get("U", "UNKNOWN") if isinstance(nabla_block.get("filing"), dict) else "UNKNOWN",
            "standing": "DRAFT",
        },
        "lifecycle": {"current_stage": "prep", "stations_done": ["00_PREP"], "stations_skipped": []},
        "ladder": {
            "1_uuid": "which object",
            "2_nabla_title": "what kind / read it?",
            "3_lossless_summary": "1/20 compaction - pending",
            "4_paper": "source",
        },
    }


def write_sidecar(item_folder: Path, data: dict) -> Path:
    path = item_folder / "00_PREP.yaml"
    path.write_text("# Sidecar - tied to the paper, never inside it. Header for every API call.\n" + yaml_dump(data) + "\n",
                    encoding="utf-8")
    return path
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest _system/tests/test_prep.py::TestPrepLib::test_mint_identity_creates_uuid -v`
Expected: PASS

- [ ] **Step 5: Update `quick_call.py` to use `prep_lib`**

Keep `quick_call.py` as a thin CLI wrapper that imports from `prep_lib.py`. (Minimal changes; preserve existing CLI.)

- [ ] **Step 6: Commit**

```bash
git add 000_QUICK_CALL/BACKSIDE/prep_lib.py 000_QUICK_CALL/quick_call.py _system/tests/test_prep.py
git commit -m "refactor: extract prep_lib from quick_call"
```

---

### Task 4: Implement `00_prep.py` engine-native station

**Files:**
- Create: `D:/GitHub/pipeline-workflows/API/000_QUICK_CALL/BACKSIDE/00_prep.py`
- Modify: `D:/GitHub/pipeline-workflows/API/000_QUICK_CALL/BACKSIDE/station.json`
- Modify: `D:/GitHub/pipeline-workflows/API/_system/config/stations.json`
- Create/Modify: `D:/GitHub/pipeline-workflows/API/000_QUICK_CALL/BACKSIDE/PROMPT.md`, `FOCUS.md`, `README.md`
- Test: `D:/GitHub/pipeline-workflows/API/_system/tests/test_prep.py`

**Interfaces:**
- Consumes: `prep_lib`, `debate_map_index`, engine `Station`/`Context`
- Produces: `00_PREP.yaml` sidecar + engine bundle

- [ ] **Step 1: Write the failing smoke test**

```python
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]
API = HOME.parent

class Test00PrepSmoke(unittest.TestCase):
    def test_dry_run_lists_items(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = root / "paths.json"
            cfg.write_text(json.dumps({
                "papers_root": str(root / "papers"),
                "debate_map": str(root / "debate"),
                "originals_root": str(root / "originals"),
            }), encoding="utf-8")
            (root / "debate").mkdir()
            script = API / "000_QUICK_CALL" / "BACKSIDE" / "00_prep.py"
            env = {**os.environ, "ONE_MENU_PATHS_FILE": str(cfg), "PYTHONIOENCODING": "utf-8"}
            env.pop("DEEPSEEK_API_KEY", None)
            src = root / "paper.md"
            src.write_text("# Test\n\nResurrection and identity.\n", encoding="utf-8")
            r = subprocess.run([sys.executable, str(script), str(src), "--dry-run"],
                               cwd=API, env=env, capture_output=True, text=True, timeout=60)
            self.assertEqual(0, r.returncode, r.stdout + r.stderr)
            self.assertIn("00_PREP", r.stdout)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest _system/tests/test_prep.py::Test00PrepSmoke::test_dry_run_lists_items -v`
Expected: FAIL — `00_prep.py` does not exist.

- [ ] **Step 3: Implement `00_prep.py`**

```python
"""00_PREP: universal preprocessing gate for every API pipeline item."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prep_lib  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_system"))
from engine import debate_map_index  # noqa: E402
from engine.station import Context, ItemResult, Station  # noqa: E402

HERE = Path(__file__).resolve().parent
LABEL = "00_PREP"


def q7_dimension(nabla_filing: dict) -> str | None:
    domain = (nabla_filing or {}).get("D", "")
    entity = (nabla_filing or {}).get("N", "")
    keywords = f"{domain} {entity}".lower()
    mapping = {
        "P01_EXISTENCE": ["cause", "cosmological", "begin", "existence", "naturalism"],
        "P02_ORDER": ["fine", "fine-tuning", "order", "intelligibility", "multiverse"],
        "P03_LIFE": ["life", "abiogenesis", "information", "evolution"],
        "P04_MIND": ["mind", "consciousness", "reason", "agency", "soul", "identity"],
        "P05_MORAL_LAW": ["moral", "ethics", "euthyphro", "objective", "sacrifice"],
        "P06_FOUNDATION": ["god", "coherence", "islam", "religion", "exclusive"],
        "P07_JESUS": ["jesus", "resurrection", "incarnation", "atonement", "trinity"],
        "P08_SCRIPTURE": ["bible", "scripture", "canon", "contradiction", "prophecy"],
        "P09_HARD_QUESTIONS": ["evil", "hell", "doubt", "slavery", "violence"],
        "P10_PEOPLE": ["church", "hypocrisy", "experience", "prayer", "personal"],
        "P00_GROUND_RULES": ["method", "science", "authority", "disconfirmation"],
    }
    scores = {dim: sum(1 for k in keys if k in keywords) for dim, keys in mapping.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else None


def debate_match_prompt(item_text: str, title: str, candidates: list[dict]) -> str:
    lines = [f"- {c['id']}: {c['question']} (keyword hits: {', '.join(c.get('keyword_hits', []))})" for c in candidates]
    return (
        "You are matching a source artifact to canonical debate questions. "
        "Return ONLY JSON: {\"matches\": [{\"question_id\": \"...\", \"score\": 0.0-1.0, \"reason\": \"...\"}]}. "
        "Include 0-5 matches. Score >= 0.8 only when the artifact actually addresses the question.\n\n"
        f"TITLE: {title}\n\nARTIFACT (first 2000 chars):\n{item_text[:2000]}\n\n"
        f"CANDIDATES:\n" + "\n".join(lines)
    )


def run_prep(ctx: Context) -> ItemResult:
    item = ctx.item
    text = ctx.text
    title = item.title

    ctx.step("prep: mint identity")
    reg = HERE / "UUID_REGISTRY.json"
    identity_block = prep_lib.mint_identity(item.source, registry_path=reg)

    ctx.step("prep: classify NABLA")
    nab = prep_lib.classify_nabla(text)

    ctx.step("prep: master equation")
    me_id = ctx.item.meta.get("master_equation_id") or prep_lib.propose_master_equation(text, nab.get("address"))

    ctx.step("prep: knowledge graph slot")
    kg = {
        "node_type": None,
        "q7_dimension": q7_dimension(nab.get("filing")),
        "edge_types": [],
        "canonical_claims": [],
    }

    ctx.step("prep: DEBATE_MAP matching")
    matches = []
    try:
        index = debate_map_index.build_index()
        candidates = debate_map_index.keyword_score(index, f"{title}\n{text}", top_n=10)
        if candidates:
            reply = ctx.call_json("debate_match", debate_match_prompt(text, title, candidates))
            if isinstance(reply, dict):
                for m in reply.get("matches", []):
                    qid = m.get("question_id", "")
                    entry = next((c for c in candidates if c["id"] == qid), None)
                    matches.append({
                        "question_id": qid,
                        "question_text": entry["question"] if entry else qid,
                        "score": float(m.get("score", 0)),
                        "reason": m.get("reason", ""),
                    })
    except Exception as e:
        ctx.warnings.append(f"debate_map matching skipped: {e}")

    ctx.step("prep: write sidecar")
    naming = {"stem": item.source.stem, "std_title": title}
    sidecar = prep_lib.build_sidecar(identity_block, nab, me_id, kg, matches, naming)
    prep_lib.write_sidecar(item.folder, sidecar)

    md = f"# Prep: {title}\n\n- UUID: `{identity_block['paper_uuid']}`\n- NABLA: `{nab.get('address') or nab.get('status')}`\n- ME: `{me_id}`\n- Q7: `{kg['q7_dimension']}`\n- Matches: {len(matches)}\n"
    html = f"<h1>Prep: {title}</h1><ul><li>UUID: {identity_block['paper_uuid']}</li><li>NABLA: {nab.get('address') or nab.get('status')}</li><li>ME: {me_id}</li><li>Q7: {kg['q7_dimension']}</li><li>Matches: {len(matches)}</li></ul>"
    return ItemResult({"sidecar": sidecar}, html, markdown=md)


def main() -> int:
    station = Station(LABEL, prompt_files=["PROMPT.md", "FOCUS.md"])
    return station.run(run_prep)


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Update `000_QUICK_CALL/BACKSIDE/station.json`**

```json
{
  "number": "00",
  "name": "PREP",
  "label": "00_PREP",
  "kind": "native",
  "items": "files",
  "uses_api": true,
  "description": "Universal preprocessing gate: UUID, classification, master equation, knowledge graph, tags, naming, DEBATE_MAP matching. Use --call QUICK_CALL for the legacy ad-hoc prompt.",
  "options": ["workers", "focus", "redo", "outbox"],
  "goals": [
    {"id": "API-00.1", "title": "MINT_IDENTITY", "task": "identity", "asks": "paper_uuid, version_uuid, naming, original_copy"},
    {"id": "API-00.2", "title": "CLASSIFY_NABLA", "task": "nabla", "asks": "domain, entity, vector, address, confidence, tags"},
    {"id": "API-00.3", "title": "MASTER_EQUATION", "task": "master_equation", "asks": "master_equation_id or propose one"},
    {"id": "API-00.4", "title": "KNOWLEDGE_BANK", "task": "knowledge_bank", "asks": "knowledge_graph node_type, q7_dimension, edge_types"},
    {"id": "API-00.5", "title": "DEBATE_MAP_MATCH", "task": "debate_match", "asks": "matched question IDs with scores and evidence"}
  ]
}
```

- [ ] **Step 5: Update `_system/config/stations.json` row for number `00`**

Change name to `PREP`, label to `00_PREP`, script to `00_prep.py`. Keep folder `../000_QUICK_CALL/BACKSIDE`.

- [ ] **Step 6: Add required BACKSIDE files**

Create `PROMPT.md`:
```markdown
# 00_PREP

Run the universal preprocessing gate: mint UUID, classify with NABLA, propose master equation, set knowledge-graph slot, match to DEBATE_MAP questions.
```

Create `FOCUS.md`:
```markdown
# Focus

- Be deterministic: same source bytes → same UUID.
- Never manufacture confidence.
- Keep master_equation_id short and canonical.
```

Create `README.md`:
```markdown
# 00_PREP

Mandatory first station for every API pipeline item. Writes `00_PREP.yaml` inside the item folder.

Legacy ad-hoc prompt: `python 00_quick_call.py --call QUICK_CALL ...`
```

- [ ] **Step 7: Run test to verify it passes**

Run: `python -m pytest _system/tests/test_prep.py::Test00PrepSmoke::test_dry_run_lists_items -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add 000_QUICK_CALL/BACKSIDE/00_prep.py 000_QUICK_CALL/BACKSIDE/station.json 000_QUICK_CALL/BACKSIDE/PROMPT.md 000_QUICK_CALL/BACKSIDE/FOCUS.md 000_QUICK_CALL/BACKSIDE/README.md _system/config/stations.json _system/tests/test_prep.py
git commit -m "feat: 00_PREP engine-native station"
```

---

### Task 5: Implement master JSON aggregator

**Files:**
- Create: `D:/GitHub/pipeline-workflows/API/_system/tools/aggregate_api_results.py`
- Test: `D:/GitHub/pipeline-workflows/API/_system/tests/test_prep.py`

**Interfaces:**
- Consumes: item folders (`paper.json`/`video.json`), `02_RUNS/*/`, `00_PREP.yaml`
- Produces: `_data/master/<paper_uuid>/master.json`

- [ ] **Step 1: Write the failing test**

```python
import json
import sys
import tempfile
import unittest
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]

class TestAggregator(unittest.TestCase):
    def test_aggregator_builds_master_json(self):
        sys.path.insert(0, str(HOME / "tools"))
        import aggregate_api_results as agg
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            item = root / "papers" / "ABCD_test"
            item.mkdir(parents=True)
            (item / "paper.json").write_text(json.dumps({"id": "ABCD", "source_hash": "sha"}), encoding="utf-8")
            (item / "00_PREP.yaml").write_text("identity:\n  paper_uuid: uuid-123\n", encoding="utf-8")
            runs = item / "02_RUNS" / "00_PREP" / "20261020_120000"
            runs.mkdir(parents=True)
            (runs / "00_PREP.json").write_text(json.dumps({"header": "prep"}), encoding="utf-8")
            out = agg.build_master(item, root / "master")
            self.assertTrue(out.exists())
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual("uuid-123", data["paper_uuid"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest _system/tests/test_prep.py::TestAggregator::test_aggregator_builds_master_json -v`
Expected: FAIL — module not defined.

- [ ] **Step 3: Implement the aggregator**

```python
"""Aggregate every station's output into one master JSON per paper UUID."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from engine import items


def _load_yaml(path: Path) -> dict:
    """Minimal YAML loader for the 00_PREP sidecar (no external deps)."""
    import yaml
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _uuid_from_sidecar(sidecar: dict) -> str | None:
    return (sidecar.get("identity") or {}).get("paper_uuid")


def build_master(item_folder: Path, master_root: Path) -> Path:
    meta = json.loads((item_folder / ("paper.json" if (item_folder / "paper.json").exists() else "video.json")).read_text(encoding="utf-8"))
    sidecar_path = item_folder / "00_PREP.yaml"
    sidecar = _load_yaml(sidecar_path) if sidecar_path.exists() else {}
    paper_uuid = _uuid_from_sidecar(sidecar) or meta.get("id")
    out_folder = master_root / paper_uuid
    out_folder.mkdir(parents=True, exist_ok=True)

    stations: dict[str, dict] = {}
    for station_dir in sorted((item_folder / "02_RUNS").glob("*")):
        if not station_dir.is_dir():
            continue
        latest = None
        for run in sorted(station_dir.iterdir(), reverse=True):
            if run.is_dir():
                latest = run
                break
        if not latest:
            continue
        json_file = latest / f"{station_dir.name}.json"
        if json_file.exists():
            stations[station_dir.name] = {
                "latest_run": str(latest.relative_to(item_folder)),
                "data": json.loads(json_file.read_text(encoding="utf-8")),
            }

    master = {
        "paper_uuid": paper_uuid,
        "identity": sidecar.get("identity", {}),
        "naming": sidecar.get("naming", {}),
        "nabla": sidecar.get("nabla", {}),
        "master_equation_id": sidecar.get("master_equation_id"),
        "knowledge_graph": sidecar.get("knowledge_graph", {}),
        "debate_map_matches": sidecar.get("debate_map_matches", []),
        "tags": sidecar.get("tags", {}),
        "stations": stations,
        "aggregated_at": datetime.now(timezone.utc).isoformat(),
    }
    out = out_folder / "master.json"
    out.write_text(json.dumps(master, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def aggregate_all(master_root: Path | None = None) -> list[Path]:
    master_root = master_root or items.external("papers_root").parent / "master"
    made: list[Path] = []
    for kind in ("papers", "videos"):
        try:
            for item in items.all_items(kind):
                made.append(build_master(item.folder, master_root))
        except Exception:
            continue
    return made


if __name__ == "__main__":
    import sys
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    for path in aggregate_all(root):
        print(path)
```

Note: if `PyYAML` is not available, replace `_load_yaml` with a tiny parser or add PyYAML to requirements. Check first: `python -c "import yaml"`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest _system/tests/test_prep.py::TestAggregator::test_aggregator_builds_master_json -v`
Expected: PASS (install PyYAML if needed).

- [ ] **Step 5: Commit**

```bash
git add _system/tools/aggregate_api_results.py _system/tests/test_prep.py
git commit -m "feat: aggregate API results into master JSON"
```

---

### Task 6: Wire `041_STORIES` to depend on `00_PREP`

**Files:**
- Modify: `D:/GitHub/pipeline-workflows/API/041_STORIES/BACKSIDE/station.json`
- Test: `D:/GitHub/pipeline-workflows/API/_system/tests/test_prep.py`

**Interfaces:**
- Consumes: `00_PREP.yaml` in item folder
- Produces: `depends_on` declaration

- [ ] **Step 1: Write the failing test**

```python
import json
import unittest
from pathlib import Path

class TestDependency(unittest.TestCase):
    def test_story_station_depends_on_prep(self):
        station = Path(__file__).resolve().parents[2] / "041_STORIES" / "BACKSIDE" / "station.json"
        data = json.loads(station.read_text(encoding="utf-8"))
        self.assertIn("00_PREP", data.get("depends_on", []))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest _system/tests/test_prep.py::TestDependency::test_story_station_depends_on_prep -v`
Expected: FAIL.

- [ ] **Step 3: Add dependency**

Edit `041_STORIES/BACKSIDE/station.json` to add:
```json
"depends_on": ["00_PREP"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest _system/tests/test_prep.py::TestDependency::test_story_station_depends_on_prep -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add 041_STORIES/BACKSIDE/station.json _system/tests/test_prep.py
git commit -m "feat: 041_STORIES depends on 00_PREP"
```

---

### Task 7: End-to-end smoke run

**Files:**
- Run existing test suite: `_system/tests/test_engine.py` + `_system/tests/test_prep.py`

- [ ] **Step 1: Run the full test suite**

Run:
```bash
python -m pytest _system/tests/test_prep.py _system/tests/test_engine.py -v --tb=short 2>&1 | tail -60
```

Expected: `test_prep.py` passes; `test_engine.py` should not have new failures caused by our changes. (It already has a pre-existing failure around a missing `PROMPT.md`; confirm that failure is unchanged.)

- [ ] **Step 2: Manual dry-run smoke test**

Create a temp paper and run `00_PREP` dry-run:
```bash
# From API_HOME
python 000_QUICK_CALL/BACKSIDE/00_prep.py /path/to/test_paper.md --dry-run
```

Expected: prints the item and exits 0.

- [ ] **Step 3: Commit any test fixes**

```bash
git add _system/tests/test_prep.py
git commit -m "test: prep gate smoke tests"
```

---

## Self-Review Checklist

- [ ] Spec coverage: every section of `2026-10-20-api-prep-gate-design.md` maps to a task above.
- [ ] Placeholder scan: no TBD/TODO/"implement later" in the plan.
- [ ] Type consistency: `paper_uuid`, `master_equation_id`, `q7_dimension`, `debate_map_matches` names match across `prep_lib.py`, `00_prep.py`, aggregator, and tests.
- [ ] Review focus: each failure mode has a test (idempotency, AI failure, no matches, dependency, aggregator, legacy prompt).
