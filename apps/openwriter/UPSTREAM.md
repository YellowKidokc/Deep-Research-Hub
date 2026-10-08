fresh clone from https://github.com/travsteward/openwriter.git at e6fa497dce9f499eaaf069b3e6d4cb3b5a563aac (2026-10-06, v0.46.0 line) on 2026-10-07; copied unchanged via git archive (no .git)

## Changes made in this repo

### 2026-10-07 — Story tab (the Writer's right column)

- `plugins/drh/` (new, `@openwriter/plugin-drh`): routes `/api/drh/status`, `/api/drh/checklist` (GET, POST), `/api/drh/research`. Reads the Deep Research Hub's plain files: `prompts/W_story_checklist.json`, `data/deep_research/`, `data/youtube/`; saves ticks to `data/writer/checklists/<docId>.json`. Hub root from `DRH_ROOT` or found by walking up from the plugin.
- `packages/openwriter/src/right-rail/tabs/StoryTab.tsx` + `StoryTab.css` (new): story checklist (green when done), paragraph word/sentence counts against the checklist's band (opening checked on its own), research cards matched on the doc's heading (editable topic).
- `packages/openwriter/src/right-rail/tabs.tsx`, `types.ts`, `icons.tsx`: one registry entry, the `'story'` tab id, and its icon.
- `package-lock.json`: the new workspace's entry (`npm install`; `check:lockfile` passes).

Checks: frontend and server `tsc --noEmit` clean; `turbo run build` 7/7; `npm test` 4 passed, 0 failed, 5 skipped (PowerShell suites) with `OPENWRITER_PRIVACY_NO_DENYLIST=1` (the privacy gate otherwise wants the upstream author's denylist).

### 2026-10-07 — Story tab: extras in the loop, outlines

- `plugins/drh/src/index.ts`: POST `/api/drh/checklist` also accepts an outline section (`<outline>.<section>`) and `_outline` with `{ value }` (the outline this doc follows, `''` = none); both validated against the checklist file.
- `StoryTab.tsx` + `StoryTab.css`: core items as before; optional techniques under "Extras in the loop", one collapsed group per source video, each with an "around mm:ss" link to where it is taught; an outline picker (None / PPP / CART) whose sections tick green like items.

Checks: `turbo run build` 7/7; `tsc --noEmit` clean; Chromium run ticked a core item, an extra and an outline section, and the outline and ticks survived a reload; bad section ids and unknown outlines get 400.

Upstream behaviour noticed, not changed: a plugin enabled while the server runs only serves its routes after a restart (its routes are added after the app's catch-all). The Story tab says so when the plugin's routes are missing.
