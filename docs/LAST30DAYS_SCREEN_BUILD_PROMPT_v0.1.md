# last30days Screen — Build Prompt v0.2
**Date:** 2026-10-06 · **Owner:** David Lowe · **Builder:** Claude Code (sole builder on this repo)
**Status:** David ruled on the v0.1 open items (below). Remaining ASK DAVID items are marked.
**Sibling:** DEEP_RESEARCH_SCREEN_BUILD_PROMPT_v0.1.md — same queue folder, same job UUID, same pill schema.

## Purpose (read this before touching code)
This is the "what is LIVE" arm of Targeted Research. Not a second deep-research engine.
Question it answers, per chapter claim or per whole-case argument: which objections and framings are people
actually using, in whose words, with what engagement, in NAMED PLACES — this subreddit, this forum, this
handle. David's read of what makes it good: it goes to defined, specific places and finds what is there.
The aggregate of many scoped places beats open web search. Build for that.
Consumers: (1) the battleground map, (2) prior_art in the Deep Research screen (fresh forks). Feeds
fork-finder; does not replace it.

## Engine (as found, doctor --json probed live 2026-10-07 04:11 UTC)
- last30days v3.23.1, `apps/last30days-skill/skills/last30days/scripts/last30days.py`.
  UPSTREAM.md: "modified local copy of D:\GitHub\last30days-skill" — treat D:\GitHub as source.
- `START_LAST30DAYS.bat` WORKS (uv → CPython 3.13). Saves to `C:\Users\David\Documents\Last30Days`
  (8 briefs). Config `C:\Users\David\.config\last30days\.env`.
- WORKING: reddit (public + ScrapeCreators backfill), hackernews, polymarket, github, youtube, library.
- KEYED, UNVERIFIED: tiktok, instagram, web via serper.
- X: "will use: bird" but no AUTH_TOKEN/CT0 today. The Sept 23 run HAD X — cookies have since lapsed
  or came from the host env.
- NO REASONING PROVIDER configured. Runs differ by HOST, not engine: Sept 8 "Arguments for God" via the
  bare .bat = 13 clusters, all off-topic (Deltarune, GTA6, DLSS). Sept 23 "resurrection evidence" under
  a hosting model = Habermas 61K, @Sean_McDowell, maklelan 28K, r/Christianity "500 witnesses" thread.
  Same engine. The host IS the product. STRUCTURAL: no planner slot = the Sept 8 run.
- Window is NOT fixed at 30: `--days N` and `--as-of YYYY-MM-DD` exist. Sliding windows backfill history.
- Missing CLIs: arxiv/techmeme/digg (`npx -y @mvanhorn/printing-press-library@0.1.16 install arxiv --cli-only`).
- Noise: `jobs` source fires on apologetics topics. `EXCLUDE_SOURCES=jobs`.

## RULED by David (2026-10-06)
- X: browser cookies, same as last time → `setup --allow-browser-cookies` (Firefox per config).
- Planner: DeepSeek through the engine's OpenRouter client path if it works; else a real OpenRouter key;
  else other APIs. Do not stall on it.
- Discovery domains: not every domain; the list will grow. NOT the priority.
- **PRIORITY #1 = FORUMS.** Reddit proves the engine can do forums. Replicate the Reddit part for many
  more forums. The forum list is the thing that should always be growing and always getting better.
- Window: more than 30 days at the front end (--days is already there; expose it).
- Frontend: redo it; same look as the rest of the hub. Simple case by default — one thing in, it goes
  through, defaults everywhere. A second expanding interface for the specifics when you need depth.

## What we keep, and what we do NOT inherit
KEEP: the engine; `--emit=json`; `library search` / `library feed`; topic queue (`queue list/cover`);
`--corpus <dir>` (vault lane, offline); `doctor --postmortem` (per-source outcome = read receipt);
Discovery three-leg protocol + checkpoint files (a receipts chain); `--days` / `--as-of`.
DO NOT INHERIT: the 2,300-line SKILL.md host contract (Claude Code as hosting brain — LAWs, badge,
wizard, upsell). The hub replaces the hosting brain with the planner slot.

## Build order
### 0. Planner slot + X   ← first; nothing below is worth testing on the deterministic path
- `lib/providers.py` OpenRouterClient is plain chat-completions and honors `OPENROUTER_BASE_URL`:
  `LAST30DAYS_REASONING_PROVIDER=openrouter`, `OPENROUTER_API_KEY=<DEEPSEEK key>`,
  `OPENROUTER_BASE_URL=https://api.deepseek.com/chat/completions`,
  `LAST30DAYS_PLANNER_MODEL=deepseek-chat`, `LAST30DAYS_RERANK_MODEL=deepseek-chat`. UNTESTED.
  Verify on one topic: stderr no longer says "deterministic fallback"; clusters carry `why_relevant`.
  Fallback: real OpenRouter key (Jev runs on one). Never the `openai` path (Responses API).
  Note: `schema.ProviderRuntime.reasoning_provider` Literal omits "openrouter"; runtime doesn't enforce
  it, but fix the Literal so a type checker doesn't lie later.
- X: `setup --allow-browser-cookies`, then one run to confirm bird sees the pair. Re-run when it lapses;
  doctor's `x_browser_cookies` is the tell.
### 1. FORUMS adapter (the always-growing source)   ← David's #1
- Contract to hit: `schema.SourceItem` (item_id, source, title, body, url, author, container,
  published_at, engagement{}, metadata{}). Reddit is 7 modules (rss, listing, arctic, shreddit, public,
  keyless, enrich) hand-built for one site. Do NOT do that per forum.
- Build ONE `lib/forums.py` with platform DRIVERS and a REGISTRY:
  - `data/forums.yaml` — one entry per forum: name, base_url, platform, lanes (search|latest|rss),
    search_path override, date_format, tags[] (apologetics, physics, theology, atheism, ...), enabled.
  - Drivers by platform, in this order of yield-per-effort:
    1. **Discourse** — JSON API free: `/search.json?q=`, `/latest.json`, `/t/<id>.json` gives posts +
       likes + replies. Many modern forums (incl. several theology/physics communities) run it.
    2. **Stack Exchange** — API v2.3 (`/search/advanced`, `/questions/{id}/answers`), votes native.
       Philosophy.SE, Christianity.SE, Physics.SE, Biblical Hermeneutics.SE, History.SE.
    3. **RSS/Atom generic** — any forum exposing a feed (phpBB, XenForo, vBulletin, Invision all do).
       Dates + titles + first body; comments require lane 4.
    4. **HTML thread scraper** — platform-aware selectors for phpBB/XenForo/vBulletin thread pages:
       post text, author, date, like/thanks count. Last resort, most maintenance.
  - `container` = forum name (what `r/sub` is for Reddit). `source` = "forum". Engagement normalized to
    {replies, likes, views} so clustering treats a 40-reply TheologyWeb thread like a 40-comment subreddit.
  - Register `forum` as a source in the planner's source list and in doctor (one probe per enabled forum:
    HTTP 200 on its latest/feed lane). Doctor must show per-forum WORKING / NOT WORKING.
  - Seed list: David does NOT have one and the arguments are "meta-Christian" — they cut across
    communities. So the list is DISCOVERED, not supplied (same rule as the discovery grammar):
    a) Day-one coverage with no list at all: Stack Exchange is enumerable via API — Philosophy,
       Christianity, Biblical Hermeneutics, Physics, History, Skeptics. Six sites, votes native, zero scraping.
    b) `forum-finder` job: for each whole-case argument, run the web lane (Serper) with "forum" +
       argument phrasing, collect domains, fingerprint platform (Discourse `/latest.json`; phpBB
       `/viewforum.php`; XenForo `/threads/`; vBulletin `/showthread.php`; Invision `/topic/`), write
       CANDIDATE rows to `data/forums.yaml` with `enabled: false`. David flips enabled. Re-run monthly;
       the registry grows because the finder runs, not because anyone remembers to add.
    c) Modern "forums" are Discord servers and Telegram channels. Telegram lane exists (needs
       TELEGRAM_SOURCES). Discord has no lane and no public API — note it, don't build it now.
- Growth rule: adding a forum = one YAML entry + doctor probe green. No code. If a forum needs code,
  it is a new platform driver, not a new forum.
### 2. Job type in the SAME queue folder
- `data/jobs/<job>.yaml`, `job_type: last30`. Same runner, UUID, `done/`. Fields: topic, chapter,
  days (default 30), as_of, subreddits[], forums[] (names from registry, or tag:apologetics), x_handle,
  x_related[], github_repo, discover_domain, depth, corpus[], save_dir. Runner builds the flag list.
- Output per job: `--emit=json` + raw .md + `doctor --postmortem --json` beside it (the receipt).
### 3. Pills → fork-finder
- Clusters → cluster pills: name, score, items[] (url, date, engagement, source, container),
  top_comments[] (author, votes, url, text). TOPIC-grouped. Position split is fork-finder's job:
  feed items into `gpt_researcher/skills/fork_finder.py` as a second feeder (same (url, raw_content)
  shape). One fork-finder, two feeders.
### 4. Discovery (later, not now)
- `--discover "<domain>"` monthly over a short list; judge legs call the planner slot to write the
  judgments file; drop podcast/x_article angles. Topic queue `queue cover` = already answered.
### 5. Screen — two tiers, same shell as every other hub screen
- TIER 1 (default): one text box. Topic in → runs with every default (30 days, all enabled sources,
  all enabled forums, planner on) → cluster pills + receipt. Nothing else visible.
- TIER 2 (expand): the YAML fields from §2 as controls — days/as-of, source toggles, forum picker by
  tag, subreddits, handles, corpus folders, depth, discover. Expanding never changes a default; it
  only overrides this run. Run log pane streams stderr `[narrate] step=` lines (receipts stream).
- Library view: render `library feed` index.html read-only.
- Frontend tech: ASK DAVID (same open question as Deep Research — static, Next.js, or the hub shell).

## Classes
1. Giveaway: the skill as-is (MIT, multi-harness). Nothing to build.
2. Ours: planner slot + forums adapter + queue + cluster pills → fork-finder + vault corpus lane.

## ASK DAVID
- Forum seed list (names). Everything else in §1 can be built without you.
- Frontend tech, once, for the whole hub.

## Next after this: Lean — recompile the remaining eight GOD_IS files live.
