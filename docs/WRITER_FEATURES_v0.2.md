# The Writer — feature backlog v0.2

**Date:** 2026-10-12 · **Owner:** David Lowe · **Status:** DRAFT. Build order below is a proposal, not a commitment — David decides what goes next. Extends `docs/WRITER_v0.1.md` (the screen's design).

The Writer's right column now has the checklist, story import, craft-on-demand and rewrite-by-selection. These are the next five features, smallest and most reusable first.

---

## 1. Truth nodes — BUILT (this pass)

A snippet library of passages worth keeping: a fact with its receipt, a sentence that landed, an argument worth reusing. Select text in the doc → right-click → "Save as truth node", or paste one straight into the Story tab. Nodes are searchable (text, note, tags), insertable at the cursor, and deletable. They live in `data/writer/nodes.json` so any future screen can read them.

- **Plugs in:** drh plugin routes (`GET`/`POST`/`DELETE /api/drh/nodes`), one `contextMenuItems` entry, a "Truth nodes" section in the Story tab.
- **Dependencies:** none — plain files, no model call.

## 2. Doc metadata rail (left side)

A left-rail panel that says what the system knows about this doc: which series it belongs to, its keywords, whether its schema.org markup checks out, which axioms it touches, and where it sits in the outline order. This is the doc-level counterpart of the Story tab — the right rail helps write the piece, the left rail places it in the body of work.

- **Plugs in:** a new left-sidebar panel in `packages/openwriter/src` (recorded in `UPSTREAM.md`, like the right rail was); a `GET /api/drh/doc-meta?docId=` route in the drh plugin reading `data/` classification records and a new `data/writer/docmeta/` folder for edits.
- **Dependencies:** the classification records from screen 1/2; an axiom list (from the Faith Through Physics material); a schema.org checker (can start as a shape check, no network).

## 3. Templates, both ways

Two directions. **From doc:** take a finished piece and save its shape (span structure, outline, which checklist items it leaned on) as a named template. **To doc:** pick a template when starting a blank doc and get a skeleton — headings and empty spans, ready to fill. This extends the outline picker (None / PPP / CART) from a checklist into something generative.

- **Plugs in:** `data/writer/templates/` folder; drh routes `GET`/`POST /api/drh/templates`; a template picker beside the story picker in the Story tab.
- **Dependencies:** the story JSON format (spans + anchors) already built; outline definitions in `prompts/W_story_checklist.json`.

## 4. SEO compare against high-ranking pages

Take the doc's target keyword, pull what already ranks for it, and show a side-by-side: their headings, word counts, questions answered, schema — against this doc. The point is not to copy; it is to see the gaps the piece is supposed to fill and check it actually fills them. Sits naturally beside the metadata rail (feature 2) since both ask "how does this doc stand up, outside itself".

- **Plugs in:** a `GET /api/drh/seo-compare?docId=&kw=` route; results rendered in the Story tab or the metadata rail.
- **Dependencies:** a SERP source (one of the seo-* skills' data paths, or a saved `data/seo/` snapshot per keyword — snapshots first, live fetch later, so the hub stays plain-files-first).

## 5. Voice total-rewrite with split view

Rewrite the whole doc in one voice, not just a selection. The result opens in a split view — original left, rewrite right — with up to four versions kept, each switchable, none committed until the person says so. This is the rewrite-by-selection machinery scaled up: same OpenRouter plumbing, same accept/reject discipline, bigger canvas.

- **Plugs in:** a new `POST /api/drh/rewrite-doc` route (whole-doc slots in `prompts/W_rewrite_doc.json`); a versions panel, probably in the Story tab since it already cycles variants.
- **Dependencies:** rewrite-by-selection (built); a voice definition per rewrite (the tone list, still ASK DAVID in `WRITER_v0.1.md`); cost judgement — whole-doc calls are the expensive kind, so this one wants an explicit "go" per run.

---

## Not decided — ASK DAVID

- The voice list for feature 5 (same open question as the rewrite tone list in v0.1).
- Whether truth nodes should feed the story pass (pills with receipts, `WRITER_v0.1.md` "Aggregate → story pass") or stay a writer-side tool only.
- Where the axiom list for feature 2 lives (a `prompts/` file? a `data/` list?).
