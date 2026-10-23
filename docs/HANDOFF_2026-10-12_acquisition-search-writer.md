# Handoff 2026-10-12: Acquisition, search engine, labeler, research to Writer

Companion to `docs/SESSION_2026-10-12.md`, written by an earlier session that day: hub runs, Writer story import and rewrites. This note covers what came after. Read both.

David's working style: short voice-typed messages, act first, keep moving. He wants things running, not plans.

---

## 1. State right now

**Services under the hub** (http://127.0.0.1:2828, started from bash as `./hub/target/debug/drh-hub.exe` in the repo root):

| proc | launch id | port |
|---|---|---|
| 11 | gptr.server (GPT Researcher) | 8000 |
| 12 | axiom.navigator | 8774 |
| 13 | openwriter.server | 5050 |
| 14 | deepcrawl.server (new) | 8080 |

The hub was rebuilt and restarted this session to add the new param kinds. All four services were stopped and relaunched through the hub. API keys (`DEEPSEEK_API_KEY`, `TAVILY_API_KEY`, `OPENAI_API_KEY`, `OPENROUTER_API_KEY`) are Windows *user* env vars, so a restart keeps them. `MARGINALIA_API_KEY` and `CRAWLAB_TOKEN` are **not set**.

**Running outside the hub:** the CocoIndex labeler in live mode on `\\192.168.2.50\h_hp\Documents\axiom dump` (see §4). It was started from a Claude session and probably dies with it. Restart it with the command in §4.

**Nothing is committed.** `git status` shows about 80 entries, from this session and the earlier one. This session's files are listed in §7. Do not commit until David says so.

---

## 2. Acquisition screen: built (Screen 3)

`web/src/screens/acquire/index.jsx`, registered in `App.jsx`. Tabs:

- **Scrape:** one page to markdown.
- **Links:** internal plus external links (POST to `/links`; GET ignores `includeExternal`) and the site tree.
- **Crawl:** same-host breadth-first walk with page and depth limits.
- **Search:** Marginalia result links.

Output goes to `data/crawl/`, `data/links/` and `data/search/`.

- **Deepcrawl:** cloned to `apps/deepcrawl` (fork YellowKidokc/deepcrawl).
  - Only the v0 API worker is installed: `pnpm install --filter "deepcrawl-worker-v0..."`.
  - Local config is `apps/workers/v0/wrangler.local.jsonc`: `AUTH_MODE=none`, local KV/D1, no auth worker, no rate limit. D1 migrations were applied locally.
  - The hub script is `apps/deepcrawl/drh_crawl.py` (stdlib).
  - Quirk: deepcrawl strips `www.`, so a few sites 404 (Gutenberg).
  - `apps/deepcrawl` **still contains its own `.git`**. Remove it before committing if it should be tracked like the other apps.
- **Marginalia:** `apps/MarginaliaSearch/drh_search.py` calls the official API v2 (`https://api2.marginalia-search.com/search`, header `API-Key`).
  - The shared `public` key hit **"Daily Limit Exceeded"**, so the script stops with a clear message.
  - Needs a personal key (free for non-commercial use, email kontakt@marginalia.nu) set as `MARGINALIA_API_KEY`, then a hub restart.
  - The Java engine in the clone is not runnable here (needs Linux, JDK 25, its own index).
- **Hub param kinds added** in `hub/src/procs.rs`:
  - `web_url`: http(s) only, no whitespace.
  - `query`: 1–300 characters, never starting with `-`.
- **Launch entries added** to `hub/launch.json`: `deepcrawl.server`, `acquire.scrape`, `acquire.links`, `acquire.crawl`, `search.marginalia`.
- README has a new "Screen 3" section.

---

## 3. David's real search engine: discovered, not yet integrated

David's search UI is `\\192.168.2.50\h_hp\Desktop\Documents\search2.index.html` ("Theophysics Research Search, combined interface v2"; `search.index.html` is v1). It is **already live** at **http://192.168.1.177:8017/**. 192.168.1.177 is another machine; this PC is 192.168.2.51 / 192.168.1.76.

- **The 8017 backend** is FastAPI (title "Theophysics Research Search" 0.1.0).
  - Routes: `GET/POST /api/search` (q, mode, limit, providers), `/api/history`, `/api/feedback`, `/api/transition`, `/api/crawl`, `/dork`, `/health`.
  - Search returns ranked results with `score`, `components` and `explanation`, from Serper (Google), CrossRef and OpenAlex.
  - **Its source code is not on this PC or the NAS**; it lives only on .177.
- **Routes the page calls that 404:** `/api/crawler/search`, `/api/markdown`, `/api/semantic/search`, `/api/intake`, `/api/draft`.
  - The page refuses Marginalia (it needs a server-side key).
  - Its "DeepCrawl worker" option calls `/scrape`, but deepcrawl's route is `/read`.
  - Its deepcrawl endpoint is David's deployed `https://deepcrawl-worker-v0.davidokc28.workers.dev`, which answers.
  - No SearXNG exists anywhere on the LAN.
- **Hister** (browsing history) is at 192.168.2.50:4433 and 192.168.1.177:4433.
- **Crawlab** v0.6.3 is at http://192.168.1.177:7622. It shows the default `admin/admin` login, and the API returns 401 without login.
  - Claude must not enter credentials. David logs in himself, or creates a token (Settings → Tokens) and sets `CRAWLAB_TOKEN`.
- **Proposed, not built** (David didn't answer yet): a local companion on :8017 that serves search2, proxies existing routes to .177, and implements the missing routes:
  - Marginalia via server key
  - `/api/markdown` and links via local deepcrawl
  - `/api/crawler/search` over `data/crawl`
  - intake to files
  - Crawlab as crawl backend

  It would become the hub's "Search Engine" screen (Screen 4). The alternative is to add the routes on .177 directly, if David gives access.

---

## 4. Labeler: CocoIndex pipeline (`apps/cocoindex/examples/theophysics_labeler/`)

`main.py` (CocoIndex 1.0.24 app) does three steps:

1. **Labels every file** with the Convergence Tagger engine (`C:\Theophysics_Tagger`) and writes a **`.fistag` JSON sidecar** beside each one. It uses fistag.py's own format and codes (`NO.AXM · RUN · --`) plus label fields. David rejected `.fmeta`.
2. **Duplicates report.**
3. **Empty-folders report.**

It is incremental: memo on path + size + mtime + registry, and deleting a file deletes its sidecar.

- **Ran on `\\192.168.2.50\h_hp\Documents\axiom dump`:**
  - 3,608 files labeled.
  - **1,035 duplicate copies (316.6 MB)**, 995 of them in `_GEMINI_DELETE`.
  - 133 same-text groups.
  - 1,147 empty folders, of which **1,095 were removed** (`--remove-empty`; completely empty only). The rest hold `.obsidian`/`node_modules`, and the report was fixed to stop listing them.
- **Duplicates NOT moved.** The permission classifier blocked it. `quarantine_duplicates.py` is ready: it re-verifies sha256, moves to `axiom dump__DUPLICATES_QUARANTINE` with a manifest, and has `--undo`. David must run it himself or grant permission. Never hard-delete on the NAS (no recycle bin).
- Run from PowerShell, not Git Bash: bash mangles `\\server` paths.

  ```
  python main.py run --live
  ```

  Reports go to `state/reports/`.

---

## 5. Research to Writer pipeline: working, first article done

- **Question:** "the best argument that numbers are from God, not man-made."
- **Research:** 20 queries through the .177:8017 engine, 300 results, and 13 sources pulled via deepcrawl (PDFs via PyMuPDF). Everything is in `data/research/numbers-from-god/`: `ARGUMENT.md`, `sources/`, `search_results.json`, `queries.json`.
  - Quotes were checked against the pulled text, except the Gödel 1964 line (marked unverified) and an Augustine paraphrase (unquoted).
  - Key nuance: Craig is an anti-Platonist, so the claim is split into (A) discovered and (B) grounded in God.
- **Stack to the Writer:** copied to `data/deep_research/numbers-from-god/`. That is a "dropped collection" with no `run.json`, so every `.md` becomes a research card in OpenWriter's right rail.
- **New API Layer set:** `prompts/S_synthesize.json` plus `prompts/S_synthesize/RULES.md`.
  - Slot 1 `stack_to_page` (DeepSeek `deepseek-chat`) turns a record into a 900–1,300-word article: quotes verbatim, nothing invented, contested premises flagged.
  - `run_slot.py` gained `--out`.
- **Result:** `data/writer/drafts/numbers-are-from-god.md`, created in OpenWriter via `POST /api/documents {title, content: markdown}` as the doc **"Numbers Are From God, Not Made by Man"**.
  - Small nit: its Sources list names two works the article doesn't cite.
- **Pipeline for the next topic:**

  ```
  python prompts/run_slot.py S 1 --file <record.md> --out data/writer/drafts/<name>.md
  ```

  Then POST it to `http://127.0.0.1:5050/api/documents`.
- **Offered, not built:** a one-click hub button for this. Not yet in `prompts/README.md`'s table, so add `S_synthesize` there.

---

## 6. Elsewhere today (outside this repo)

- **Theophysics Convergence Tagger v3:** `C:\Theophysics_Tagger\tools\tagger3.py` plus `tagger3_gui.py` and `START_TAGGER.bat`.
  - It merges filetagger (PDF/DOCX/HTML, catalog, duplicates, sidecars, folder markers, watch) onto tagger2's engine.
  - Same `tagger.db` and registry hash as v2: 84/84 identical tags.
  - Registry tuning still needed: "Setup", "evidence" and "Tagging" fire everywhere.
- **AI Hub on Cloudflare:** a message board for AIs (MCP plus REST plus UI) at https://ai-hub.davidokc28.workers.dev (Worker + D1, account davidokc28@gmail.com).
  - Its source and **`tokens.local.json`** are in the first Claude session's *scratch folder* (`…\scratch-2026-10-12-fdc482\ai-hub`), which is deleted with that session. **Move it somewhere permanent.**
  - Planned next: relay worker for @mentions to GPT/Gemini, and Durable Objects push.

---

## 7. This session's files in this repo

Modified:
- `README.md`
- `hub/launch.json`
- `hub/src/procs.rs`
- `web/src/App.jsx`
- `prompts/run_slot.py`
- `apps/MarginaliaSearch/UPSTREAM.md`

New:
- `web/src/screens/acquire/`
- `apps/deepcrawl/` (incl. `drh_crawl.py`, `wrangler.local.jsonc`, `UPSTREAM.md`)
- `apps/MarginaliaSearch/drh_search.py`
- `apps/cocoindex/examples/theophysics_labeler/`
- `prompts/S_synthesize*`
- `data/research/numbers-from-god/` (git-ignored)
- `data/deep_research/numbers-from-god/` (git-ignored)
- `data/writer/drafts/` (git-ignored)
- this file

The other modified/untracked files (openwriter, W_* prompts, R_web bias prompts, docs/*_v0.x.md) belong to the earlier session.

## 8. Next steps, in David's likely order

1. Get the duplicates quarantined (David runs `quarantine_duplicates.py`) and a Marginalia personal key.
2. Decide on the :8017 companion vs editing .177. Then make search2 fully work and make it Screen 4.
3. Hub button for "stack to page", and a "Send to Writer" action on research runs.
4. Fold the paywalled sources into the numbers article: Steiner 1998; *J. Phil.* 2023 "God and the Numbers"; the 2021 applicability chapter; the 2025 Wigner/God paper. DOIs are in `ARGUMENT.md`.
5. Commit, in logical chunks, once David approves.
