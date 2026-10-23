# API Pipeline Universal Prep Gate — Design Spec

**Date:** 2026-10-20  
**Topic:** `pipeline-workflows/API` preprocessing layer  
**Status:** design ready for implementation plan

## 1. Intent

Every item that enters the `pipeline-workflows/API` pipeline must carry a single, authoritative header before any downstream station runs. The header survives renames, moves, and re-runs and is the source of truth for identity, classification, naming, and argument mapping.

The prep gate also matches each item to the canonical questions in the DEBATE_MAP vault (configured in `_system/config/paths.json` under key `debate_map`), and an aggregator collects every station's output into one master JSON per item.

## 2. Scope

**In scope for this cycle:**
- Repurpose `000_QUICK_CALL` as the `00_PREP` gate; keep its ad-hoc prompt as `--call QUICK_CALL`.
- Reuse of the existing `identity.py` UUID registry and `nabla.py` classification logic.
- Sidecar YAML with all required universal fields.
- DEBATE_MAP keyword pre-filter + API confirmation matcher.
- `paper.json` / `00_PREP.json` header emitted for downstream stations.
- Aggregator script `_system/tools/aggregate_api_results.py` that builds `_data/master/<paper_uuid>/master.json`.
- Dependency wiring for one pilot downstream station (`041_STORIES`).

**Out of scope / later:**
- Rewriting all downstream stations to depend on `00_PREP` (done station-by-station after pilot).
- Full semantic embedding index for DEBATE_MAP (the API + keyword hybrid is the v1).
- Auto-routing items to specific downstream stations (the gate enriches; routing stays manual or station-driven).

## 3. Shared understanding

- A "paper" means any source item: markdown paper, YouTube transcript, script, argument note, etc.
- UUIDs are minted once by `identity.py` and never change.
- The sidecar YAML lives inside the item folder (`00_PREP.yaml`), not inside the source file.
- Downstream stations read the sidecar + `paper.json`; they do not re-mint identity.
- `DEBATE_MAP` folder names carry the canonical question ID (e.g., `07_Q-JESUS-RESURRECTION`).

## 4. Components

### 4.1 `00_PREP` station

We repurpose the existing `000_QUICK_CALL` front folder as the prep gate. It already holds the UUID registry (`identity.py`), the NABLA classifier (`nabla.py`), and the existing sidecar-writing code (`quick_call.py`). The ad-hoc DeepSeek prompt remains available as a sub-call.

Location: `D:\GitHub\pipeline-workflows\API\000_QUICK_CALL` (folder name kept; station label becomes `00_PREP`)

Folder shape (per `API/AGENTS.md`):
```
000_QUICK_CALL/
  1 RUN HERE.bat
  2 RUN ON FOLDER.bat
  INBOX/
  OUTBOX/
  BACKSIDE/
    station.json
    00_prep.py
    00_quick_call.py   (legacy ad-hoc prompt, invoked via --call QUICK_CALL)
    PROMPT.md
    FOCUS.md
    README.md
    identity.py
    nabla.py
    calls/
      QUICK_CALL/...
```

`station.json`:
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

### 4.2 `00_prep.py` stages

`000_QUICK_CALL/BACKSIDE/00_prep.py` uses the engine-native `Station` / `Context` framework (`_system/engine/station.py`).

**Stage 1 — Identity (`identity`)**
- Call `identity.Registry.resolve(sha256, stem, parent_uuid)`.
- Copy original to `ORIGINALS/` if not already present.
- Result: `paper_uuid`, `version_uuid`, `version_n`, `source_sha256`, `original_copy`.

**Stage 2 — NABLA classification (`nabla`)**
- If the sidecar already has a valid NABLA block and `--redo` is not set, reuse it.
- Otherwise call DeepSeek with `nabla.ENCODER_PROMPT` and validate with `nabla.validate`.
- Result: filing, vector, address, confidence, review flags, truth modes, operators, tags.

**Stage 3 — Master equation (`master_equation`)**
- If `--me-id` was passed or the sidecar already has one, keep it.
- Otherwise ask DeepSeek to propose a `master_equation_id` based on the NABLA classification and a one-sentence decode.
- Result: `master_equation_id` string.

**Stage 4 — Knowledge bank / graph (`knowledge_bank`)**
- Populate a structured slot:
  ```yaml
  knowledge_graph:
    node_type: null          # filled later by CKG
    q7_dimension: null       # e.g., P07_JESUS
    edge_types: []
    canonical_claims: []
  ```
- If the text clearly maps to a Q7 area (e.g., resurrection, fine-tuning, moral law), set `q7_dimension` via API + keyword fallback.

**Stage 5 — DEBATE_MAP matching (`debate_match`)**
- Build a lightweight index of all `**/Q-*` folders under DEBATE_MAP: id, question text, section, keywords.
- Keyword pre-filter: score each question by overlap of stemmed keywords from question text + README + folder name.
- API confirmation: send the top 10 keyword hits plus the item's title and first 2,000 chars to DeepSeek; ask it to return the best 0-5 matches with scores (0-1) and a one-line reason.
- Result: list of `{question_id, question_text, score, reason}`.

**Write outputs**
- Sidecar YAML: `00_PREP.yaml` inside the item folder (next to `paper.json`/`video.json`). This is the living header every station reads.
- Engine bundle: `02_RUNS/00_PREP/<run>/00_PREP.json`, `00_PREP.html`, `00_PREP.run.json` (engine standard).
- Receipt: `00_PREP.run.json`.
- UUID registry: `000_QUICK_CALL/UUID_REGISTRY.json` (reused from existing `identity.py`).

### 4.3 Sidecar YAML schema

```yaml
record_type: QUICK_CALL_HEADER
schema: 00_PREP v0.1
created_at: 2026-10-20T...
identity:
  paper_uuid: uuid4
  version_uuid: uuid5
  version_n: 1
  source_sha256: sha256
  source_file: filename.md
  original_copy: /path/to/ORIGINALS/...
  new_version: true
naming:
  stem: filename
  std_title: "..."
  series: "..."
  series_code: "..."
  part: 0
  previous_names: []
branch:
  series: null
  position: null
  of: null
master_equation_id: ME-...
nabla:
  status: VALID
  address: "..."
  filing:
    D: RELIGION
    N: RESURRECTION_IDENTITY
    V: W
    A: PUBLIC_RESEARCH
    U: T
    R: R2
  vector: G3M0E0S3T0K3R0Q0F3C0
  hash: "[G·C][M·F][K·S][...]"
  confidence: {G: 0.92, ...}
  review_flags: []
  minimal_decode: "..."
  truth_modes: [HISTORICAL_RECORD, ...]
  operators: [source, identity_preserving_transformation]
knowledge_graph:
  node_type: null
  q7_dimension: P07_JESUS
  edge_types: []
  canonical_claims: []
debate_map_matches:
  - question_id: 07_Q-JESUS-RESURRECTION
    question_text: "Did Jesus rise from the dead?"
    score: 0.91
    reason: "..."
tags:
  domain: [RELIGION, HISTORY]
  topics: [RESURRECTION, IDENTITY]
  move: ARGUMENT
  standing: DRAFT
lifecycle:
  current_stage: prep
  stations_done: [00_PREP]
  stations_skipped: []
ladder:
  1_uuid: which object
  2_nabla_title: what kind / read it?
  3_lossless_summary: 1/20 compaction - pending
  4_paper: source
```

### 4.4 `paper.json` header

A flat, JSON-only version of the sidecar, written by the engine's `write_bundle`, so downstream stations can do:
```python
from engine.station import latest_data
header = latest_data(item, "00_PREP")
```

### 4.5 Aggregator: `_system/tools/aggregate_api_results.py`

Walks:
- `_data/master/` for existing master JSONs.
- Every station run folder under each item's `02_RUNS/<station>/`.
- `00_PREP` OUTBOX sidecars.

Produces `_data/master/<paper_uuid>/master.json`:
```json
{
  "paper_uuid": "...",
  "identity": {...},
  "naming": {...},
  "nabla": {...},
  "master_equation_id": "ME-...",
  "knowledge_graph": {...},
  "debate_map_matches": [...],
  "tags": {...},
  "stations": {
    "00_PREP": {"latest_run": "...", "data": {...}},
    "41_STORY": {"latest_run": "...", "data": {...}}
  },
  "aggregated_at": "2026-10-20T..."
}
```

The aggregator is idempotent: re-running overwrites the file with the latest data from each station.

## 5. Data flow

```
Source file
    │
    ▼
item folder (paper.json / video.json + 00_SOURCE/)
    │
    ▼
000_QUICK_CALL / 00_PREP (identity → classify → master equation → knowledge bank → DEBATE_MAP match)
    │
    ├── 00_PREP.yaml sidecar (inside item folder)
    ├── 02_RUNS/00_PREP/<run>/00_PREP.json
    └── 000_QUICK_CALL/UUID_REGISTRY.json
    │
    ▼
Downstream station (e.g., 041_STORIES)
    │
    ├── reads 00_PREP.yaml for UUID + tags
    ├── runs its own analysis
    └── writes its own run.json
    │
    ▼
aggregate_api_results.py
    │
    └── _data/master/<paper_uuid>/master.json
```

## 6. Integration with downstream stations

A downstream station declares the dependency in `station.json`:
```json
"depends_on": ["00_PREP"]
```

The engine's `Station.upstream()` and `_run_item()` already check `depends_on`: if the prep run is newer than the downstream run, the item is due again.

Pilot: add the dependency to `041_STORIES/BACKSIDE/station.json` after `000_QUICK_CALL` / `00_PREP` is working.

## 7. Error handling

- Identity minting never fails; it is local.
- NABLA AI call failure sets `nabla.status: FAILED` and records the error; the sidecar is still written so the item is tracked.
- DEBATE_MAP matching failure leaves `debate_map_matches: []` and a warning.
- A item with `nabla.status == FAILED` is still eligible for downstream stations; downstream stations may choose to skip it via their own gates.

## 8. Testing plan

1. Update `000_QUICK_CALL/BACKSIDE/station.json` and `_system/config/stations.json` to label the station `00_PREP`.
2. Create one paper item from a markdown source (engine will make its item folder under `papers_root`).
3. Run `000_QUICK_CALL` / `00_PREP` on that item.
4. Verify `00_PREP.yaml` inside the item folder contains UUID, NABLA, master_equation_id, knowledge_graph, debate_map_matches.
5. Run `041_STORIES` on the same item and confirm it reads `00_PREP.yaml`.
6. Run the aggregator and inspect `_data/master/<uuid>/master.json`.
7. Remove test files before committing.

## 9. Open questions / future work

- Should the aggregator run automatically at the end of every `button.py` run, or only on demand?
- Should downstream stations also append their outputs to the master JSON directly, or keep the aggregator as the single writer?
- Should `00_PREP` propose a series/part based on filename prefixes (e.g., `bgl-02`)?
- Should we eventually rename the `000_QUICK_CALL` front folder to `000_PREP` (high disruption; deferred)?
