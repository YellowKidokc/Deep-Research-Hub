/**
 * Deep Research Hub plugin for OpenWriter.
 *
 * Serves the Story tab in the right rail (packages/openwriter/src/right-rail/
 * tabs/StoryTab.tsx):
 *   GET  /api/drh/status               where the hub is, whether it was found
 *   GET  /api/drh/checklist?docId=     checklist items + this doc's ticks
 *   POST /api/drh/checklist            { docId, id, done, note } -> saved
 *                                      id: item id, `<outline>.<section>`, or `_outline` with { value }
 *   GET  /api/drh/research?q=          research cards whose topic matches q
 *   GET  /api/drh/stories              story JSON files: [{ id, title, spans }]
 *   GET  /api/drh/story?id=            one validated story + warnings
 *   GET  /api/drh/story-state?docId=&storyId=   per-doc span choices
 *   POST /api/drh/story-state          { docId, storyId, spanId, choice?, kept? } -> saved
 *   POST /api/drh/rewrite              { slot, text, instruction?, contextBefore?, contextAfter? }
 *                                      -> { text }; runs prompts/W_rewrite.json via OpenRouter
 *   POST /api/drh/craft-opening        { text, topic?, docId? } -> { ok, storyId }; runs
 *                                      prompts/W_craft.json, writes data/writer/stories/crafted-<docId>.json
 *   POST /api/drh/revise               { mode: run|chat, paragraphs: [{ id: pN, kind?, text }],
 *                                      goals?, instruction?, editable?, history?, topic? }
 *                                      -> { reply, edits: [{ id, text, why }], model }; runs
 *                                      prompts/W_revise.json; the client lands edits as pending rewrites
 *   POST /api/drh/youtube-script       { text | paragraphs, topic? }
 *                                      -> { ok, title_long, title_short, youtube_script, short_script,
 *                                      sources_used, model }; runs prompts/W_youtube_script.json
 *   GET  /api/drh/nodes?q=             truth nodes (reusable passages), newest first
 *   POST /api/drh/nodes                { text, note?, tags?, source? } -> { ok, node }
 *   DELETE /api/drh/nodes?id=          404 on unknown id
 *
 * Rewrite-by-selection also adds five right-click items (contextMenuItems,
 * actions `drh:<slot>`); the client posts those to /api/drh/rewrite instead of
 * the hosted AV endpoint. Key from config openrouterKey (env OPENROUTER_API_KEY),
 * model from config model (default: the slot's model in W_rewrite.json).
 *
 * Everything lives in the hub's plain files, never in OpenWriter's state:
 *   <hub>/prompts/W_story_checklist.json     the checklist definition
 *   <hub>/data/writer/checklists/<docId>.json  ticks per document
 *   <hub>/data/writer/stories/<storyId>.json   story JSON (spans + rewrite variants)
 *   <hub>/data/writer/story-state/<docId>/<storyId>.json  chosen variants per doc
 *   <hub>/data/writer/nodes.json         truth nodes (reusable passages)
 *   <hub>/data/deep_research/<job>/<stamp>/    research runs (drh_queue.py)
 *   <hub>/data/youtube/<Channel>/<Title>.md    transcripts (ytgrab.py)
 *
 * The hub root is DRH_ROOT, or found by walking up from this file.
 */
import { appendFileSync, existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'fs';
import { dirname, join, resolve } from 'path';
import { fileURLToPath } from 'url';
import type { Request, Response, Router } from 'express';

interface RouteContext {
  app: Router;
  config: Record<string, string>;
  dataDir: string;
}

interface Card {
  kind: 'deep_research' | 'youtube';
  title: string;
  detail: string;
  snippet: string;
  path: string;
  score: number;
}

const STOP = new Set(('about after again also because been before being between both could does from have here into just more most only other over same should some such than that their them then there these they this those through very what when where which while will with would your').split(' '));

function findHubRoot(configured?: string): string | null {
  if (configured && existsSync(join(configured, 'prompts'))) return resolve(configured);
  let dir = dirname(fileURLToPath(import.meta.url));
  for (let i = 0; i < 8; i++) {
    if (existsSync(join(dir, 'prompts', 'W_story_checklist.json')) && existsSync(join(dir, 'hub'))) return dir;
    const up = dirname(dir);
    if (up === dir) break;
    dir = up;
  }
  return null;
}

function readJson(path: string): any {
  try { return JSON.parse(readFileSync(path, 'utf-8')); } catch { return null; }
}

/** docIds become file names: keep them to a safe alphabet. */
function safeId(id: unknown): string | null {
  return typeof id === 'string' && /^[A-Za-z0-9_.-]{1,128}$/.test(id) && !id.startsWith('.') ? id : null;
}

function words(text: string): string[] {
  return (text.toLowerCase().match(/[a-z][a-z'-]{3,}/g) || []).filter((w) => !STOP.has(w));
}

function overlap(query: string[], text: string): number {
  if (!query.length) return 0;
  const have = new Set(words(text));
  return query.filter((w) => have.has(w)).length / query.length;
}

function headOf(path: string, bytes = 6000): string {
  try { return readFileSync(path, 'utf-8').slice(0, bytes); } catch { return ''; }
}

function dirs(path: string): string[] {
  try { return readdirSync(path, { withFileTypes: true }).filter((e) => e.isDirectory()).map((e) => e.name); } catch { return []; }
}

function researchCards(root: string, q: string): Card[] {
  const query = Array.from(new Set(words(q)));
  const cards: Card[] = [];

  // Deep Research runs: newest finished run per job.
  const dr = join(root, 'data', 'deep_research');
  const loose: { title: string; full: string; rel: string; where: string }[] = [];
  try {
    for (const f of readdirSync(dr)) {
      if (f.endsWith('.md')) loose.push({ title: f.replace(/\.md$/, ''), full: join(dr, f), rel: join('data', 'deep_research', f), where: 'dropped' });
    }
  } catch { /* none */ }
  for (const job of dirs(dr)) {
    if (job.startsWith('_')) continue;
    let gotRun = false;
    for (const stamp of dirs(join(dr, job)).sort().reverse()) {
      const run = readJson(join(dr, job, stamp, 'run.json'));
      if (!run || run.status !== 'done') continue;
      const report = headOf(join(dr, job, stamp, 'report.md'));
      const topic = `${run.job?.query ?? ''} ${JSON.stringify(run.job?.meta ?? {})}`;
      const score = Math.max(overlap(query, topic), overlap(query, report) * 0.6);
      if (score > 0) {
        cards.push({
          kind: 'deep_research',
          title: run.job?.query || job,
          detail: `${job} · ${stamp}` + (run.receipt_summary ? ` · ${run.receipt_summary.chunks_returned} chunks from ${run.receipt_summary.files_loaded} files` : ''),
          snippet: report.replace(/^#.*$/m, '').trim().slice(0, 360),
          path: join('data', 'deep_research', job, stamp, 'report.md'),
          score,
        });
      }
      gotRun = true;
      break;
    }
    // A folder without a finished run is a dropped collection: index its markdown directly.
    if (!gotRun) {
      let files: string[] = [];
      try { files = readdirSync(join(dr, job)).filter((f) => f.endsWith('.md')); } catch { /* none */ }
      for (const f of files) {
        loose.push({ title: f.replace(/\.md$/, ''), full: join(dr, job, f), rel: join('data', 'deep_research', job, f), where: `dropped · ${job}` });
      }
    }
  }
  for (const f of loose) {
    let text = '';
    try { text = statSync(f.full).size < 2_000_000 ? readFileSync(f.full, 'utf-8') : headOf(f.full); } catch { continue; }
    const score = Math.max(overlap(query, f.title), overlap(query, text.slice(0, 8000)) * 0.6);
    if (score > 0) {
      cards.push({
        kind: 'deep_research',
        title: f.title.replace(/[-_]+/g, ' '),
        detail: f.where,
        snippet: text.replace(/^#.*$/m, '').trim().slice(0, 360),
        path: f.rel,
        score,
      });
    }
  }

  // YouTube transcripts: the baseline summary if there is one, else the header.
  const yt = join(root, 'data', 'youtube');
  for (const channel of dirs(yt)) {
    if (channel === '_archive') continue;   // zipped pre-ytgrab transcripts
    let files: string[] = [];
    try { files = readdirSync(join(yt, channel)).filter((f) => f.endsWith('.md')); } catch { /* none */ }
    for (const f of files) {
      const full = join(yt, channel, f);
      const title = f.replace(/\.md$/, '');
      const titleScore = overlap(query, `${title} ${channel}`);
      if (!titleScore && query.length && !query.some((w) => title.toLowerCase().includes(w))) continue;
      let text = '';
      try { text = statSync(full).size < 2_000_000 ? readFileSync(full, 'utf-8') : headOf(full); } catch { continue; }
      if (text.includes('**Retrieved via:** failed')) continue;
      const summary = text.split(/^## Baseline Summary\s*$/m)[1];
      const score = Math.max(titleScore, overlap(query, (summary || text).slice(0, 8000)) * 0.6);
      if (score > 0) {
        cards.push({
          kind: 'youtube',
          title,
          detail: channel + (summary ? ' · baseline summary' : ' · transcript only'),
          snippet: (summary || text.split(/^## Transcript\s*$/m)[1] || '').replace(/^\*.*\*$/m, '').trim().slice(0, 360),
          path: join('data', 'youtube', channel, f),
          score,
        });
      }
    }
  }

  return cards.sort((a, b) => b.score - a.score).slice(0, 20);
}

/** A tickable key: an item id, an outline section as `<outline>.<section>`, or `_outline` (the chosen outline). */
function validKey(def: any, key: string): boolean {
  if (!def || !key) return false;
  if (key === '_outline') return true;
  if (def.items?.some((i: any) => i.id === key)) return true;
  const dot = key.indexOf('.');
  if (dot < 1) return false;
  const outline = def.outlines?.find((o: any) => o.id === key.slice(0, dot));
  return !!outline?.sections?.some((sec: any) => sec.id === key.slice(dot + 1));
}

/**
 * Read and validate a story JSON file. Malformed spans, variants and unknown
 * checklist ids are dropped with a warning instead of failing the whole file.
 * Returns null when the file is missing or unusable.
 */
function readStory(storiesDir: string, checklistFile: string, id: string): { story: any; warnings: string[] } | null {
  const raw = readJson(join(storiesDir, `${id}.json`));
  if (!raw || typeof raw !== 'object' || !Array.isArray(raw.spans)) return null;
  const warnings: string[] = [];
  const def = readJson(checklistFile);
  const known = new Set<string>((def?.items ?? []).map((i: any) => i.id));
  const spans: any[] = [];
  for (const s of raw.spans) {
    if (!s || typeof s.id !== 'string' || typeof s.anchor !== 'string' || !s.anchor.trim() || !Array.isArray(s.variants) || s.variants.length === 0) {
      warnings.push(`span dropped: missing id, anchor or variants`);
      continue;
    }
    const variants = s.variants.filter((v: any) => v && typeof v.id === 'string' && typeof v.text === 'string');
    if (!variants.length) {
      warnings.push(`span "${s.id}" dropped: no usable variants`);
      continue;
    }
    const filterIds = (ids: unknown): string[] =>
      (Array.isArray(ids) ? ids : []).filter((x): x is string => typeof x === 'string')
        .filter((x) => {
          if (known.size && !known.has(x)) { warnings.push(`span "${s.id}": unknown checklist id "${x}" dropped`); return false; }
          return true;
        });
    spans.push({
      id: s.id,
      label: typeof s.label === 'string' ? s.label : s.id,
      anchor: s.anchor,
      checklist: { needed: filterIds(s.checklist?.needed), optional: filterIds(s.checklist?.optional) },
      variants: variants.map((v: any) => ({
        id: v.id,
        text: v.text,
        note: typeof v.note === 'string' ? v.note : '',
        source: typeof v.source === 'string' ? v.source : '',
        // Crafted stories carry per-item checklist grades; preserve them.
        ...(v.grades && typeof v.grades === 'object' && !Array.isArray(v.grades)
          ? { grades: Object.fromEntries(Object.entries(v.grades).filter(([, g]) => typeof g === 'number')) }
          : {}),
      })),
    });
  }
  return {
    story: {
      id: typeof raw.id === 'string' ? raw.id : id,
      title: typeof raw.title === 'string' ? raw.title : id,
      created: typeof raw.created === 'string' ? raw.created : '',
      spans,
    },
    warnings,
  };
}

/** The model's rewrite with any wrapping it tends to add removed. */
function cleanRewrite(raw: string): string {
  let t = raw.trim();
  const fence = t.match(/^```[^\n]*\n([\s\S]*?)\n?```$/);
  if (fence) t = fence[1].trim();
  const stripQuotes = (s: string) =>
    s.length > 1 && ((s.startsWith('"') && s.endsWith('"')) || (s.startsWith('“') && s.endsWith('”')))
      ? s.slice(1, -1).trim()
      : s;
  const stripPreamble = (s: string) =>
    s.replace(/^(here('| i)s (the |your )?(rewrite|revised (version|text|passage))|rewritten (text|passage)|rewrite)\s*[:\-–]\s*/i, '').trim();
  // Quotes may wrap the preamble ("Here is the rewrite: …"), so alternate.
  t = stripPreamble(stripQuotes(stripPreamble(stripQuotes(t))));
  return t;
}

/** Assemble system + user messages from a slot's prompt parts (W_rewrite, W_craft). */
function buildSlotMessages(promptsDir: string, slot: any, fill: (s: string) => string): { system: string; user: string } {
  const cfg = slot.prompt ?? {};
  const joiner = cfg.join ?? '\n\n';
  const stripComments = !!cfg.strip_comments;
  const systemParts: string[] = [];
  const userParts: string[] = [];
  for (const part of cfg.parts ?? []) {
    if (part?.file) {
      let text = '';
      try { text = readFileSync(join(promptsDir, part.file), 'utf-8'); } catch { continue; }
      if (stripComments) text = text.replace(/<!--.*?-->/gs, '');
      if (text.trim()) systemParts.push(text.trim());
    } else if (typeof part?.input === 'string') {
      const filled = fill(part.input).trim();
      if (filled) userParts.push(filled);
    }
  }
  return { system: systemParts.join(joiner), user: userParts.join(joiner) };
}

/** A truth node's id: slug from its note or first words, unique within the list. */
function nodeId(note: string, text: string, existing: Set<string>): string {
  const base = (note || text.split(/\s+/).slice(0, 6).join(' '))
    .toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 40) || 'node';
  let id = base;
  for (let n = 2; existing.has(id); n++) id = `${base}-${n}`;
  return id;
}

function readNodes(file: string): any[] {
  const raw = readJson(file);
  return Array.isArray(raw) ? raw : [];
}

const plugin = {
  name: '@openwriter/plugin-drh',
  version: '0.1.0',
  description: 'Deep Research Hub: story checklist, paragraph stats and research cards for the right rail.',
  category: 'productivity',
  configSchema: {
    hubRoot: { type: 'string' as const, env: 'DRH_ROOT', description: 'Deep Research Hub folder (default: found by walking up from the plugin)' },
    openrouterKey: { type: 'string' as const, env: 'OPENROUTER_API_KEY', description: 'OpenRouter API key for rewrite-by-selection (right-click menu)' },
    model: { type: 'string' as const, description: "OpenRouter model for rewrites and craft calls (default: the slot's model in prompts/W_rewrite.json / W_craft.json — openai/gpt-4o-mini)" },
  },

  registerRoutes(ctx: RouteContext) {
    const root = findHubRoot(ctx.config.hubRoot);
    const checklistFile = root ? join(root, 'prompts', 'W_story_checklist.json') : '';
    const stateDir = root ? join(root, 'data', 'writer', 'checklists') : '';

    ctx.app.get('/api/drh/status', (_req: Request, res: Response) => {
      res.json({ ok: !!root, root });
    });

    ctx.app.get('/api/drh/checklist', (req: Request, res: Response) => {
      if (!root) return res.status(503).json({ error: 'Deep Research Hub folder not found; set DRH_ROOT' });
      const def = readJson(checklistFile);
      if (!def) return res.status(500).json({ error: 'prompts/W_story_checklist.json missing or invalid' });
      const docId = safeId(req.query.docId);
      const state = docId ? readJson(join(stateDir, `${docId}.json`)) ?? {} : {};
      res.json({ ...def, state });
    });

    ctx.app.post('/api/drh/checklist', (req: Request, res: Response) => {
      if (!root) return res.status(503).json({ error: 'Deep Research Hub folder not found; set DRH_ROOT' });
      const docId = safeId(req.body?.docId);
      const itemId = typeof req.body?.id === 'string' ? req.body.id : '';
      const def = readJson(checklistFile);
      if (!docId || !validKey(def, itemId)) {
        return res.status(400).json({ error: 'bad docId or item id' });
      }
      mkdirSync(stateDir, { recursive: true });
      const file = join(stateDir, `${docId}.json`);
      const state = readJson(file) ?? {};
      if (itemId === '_outline') {
        // Which outline this doc follows ('' = none).
        const value = typeof req.body.value === 'string' ? req.body.value : '';
        if (value && !def?.outlines?.some((o: any) => o.id === value)) {
          return res.status(400).json({ error: 'unknown outline' });
        }
        state._outline = { value, at: new Date().toISOString() };
        writeFileSync(file, JSON.stringify(state, null, 2));
        return res.json({ ok: true, state });
      }
      state[itemId] = {
        done: !!req.body.done,
        note: typeof req.body.note === 'string' ? req.body.note.slice(0, 500) : state[itemId]?.note ?? '',
        at: new Date().toISOString(),
      };
      writeFileSync(file, JSON.stringify(state, null, 2));
      res.json({ ok: true, state });
    });

    ctx.app.get('/api/drh/research', (req: Request, res: Response) => {
      if (!root) return res.status(503).json({ error: 'Deep Research Hub folder not found; set DRH_ROOT' });
      const q = typeof req.query.q === 'string' ? req.query.q.slice(0, 500) : '';
      res.json({ q, cards: researchCards(root, q) });
    });

    const storiesDir = root ? join(root, 'data', 'writer', 'stories') : '';
    const storyStateDir = root ? join(root, 'data', 'writer', 'story-state') : '';

    ctx.app.get('/api/drh/stories', (_req: Request, res: Response) => {
      if (!root) return res.status(503).json({ error: 'Deep Research Hub folder not found; set DRH_ROOT' });
      let files: string[] = [];
      try { files = readdirSync(storiesDir).filter((f) => f.endsWith('.json')); } catch { /* no stories dir yet */ }
      const stories: { id: string; title: string; spans: number }[] = [];
      for (const f of files) {
        const id = safeId(f.replace(/\.json$/, ''));
        const read = id && readStory(storiesDir, checklistFile, id);
        if (id && read) stories.push({ id: read.story.id, title: read.story.title, spans: read.story.spans.length });
      }
      res.json({ stories });
    });

    ctx.app.get('/api/drh/story', (req: Request, res: Response) => {
      if (!root) return res.status(503).json({ error: 'Deep Research Hub folder not found; set DRH_ROOT' });
      const id = safeId(req.query.id);
      if (!id) return res.status(400).json({ error: 'bad story id' });
      const read = readStory(storiesDir, checklistFile, id);
      if (!read) return res.status(404).json({ error: `no story "${id}"` });
      res.json({ ...read.story, warnings: read.warnings });
    });

    ctx.app.get('/api/drh/story-state', (req: Request, res: Response) => {
      if (!root) return res.status(503).json({ error: 'Deep Research Hub folder not found; set DRH_ROOT' });
      const docId = safeId(req.query.docId);
      const storyId = safeId(req.query.storyId);
      if (!docId || !storyId) return res.status(400).json({ error: 'bad docId or storyId' });
      const saved = readJson(join(storyStateDir, docId, `${storyId}.json`));
      res.json({
        choices: saved?.choices && typeof saved.choices === 'object' ? saved.choices : {},
        kept: saved?.kept && typeof saved.kept === 'object' ? saved.kept : {},
      });
    });

    ctx.app.post('/api/drh/story-state', (req: Request, res: Response) => {
      if (!root) return res.status(503).json({ error: 'Deep Research Hub folder not found; set DRH_ROOT' });
      const docId = safeId(req.body?.docId);
      const storyId = safeId(req.body?.storyId);
      const spanId = safeId(req.body?.spanId);
      if (!docId || !storyId || !spanId) return res.status(400).json({ error: 'bad docId, storyId or spanId' });
      const read = readStory(storiesDir, checklistFile, storyId);
      if (!read) return res.status(404).json({ error: `no story "${storyId}"` });
      const span = read.story.spans.find((s: any) => s.id === spanId);
      if (!span) return res.status(400).json({ error: `no span "${spanId}" in story "${storyId}"` });
      const choice = typeof req.body?.choice === 'string' ? req.body.choice : undefined;
      if (choice !== undefined && !span.variants.some((v: any) => v.id === choice)) {
        return res.status(400).json({ error: `no variant "${choice}" in span "${spanId}"` });
      }
      const kept = Array.isArray(req.body?.kept) ? req.body.kept : undefined;
      if (kept !== undefined && kept.some((k: unknown) => typeof k !== 'string' || !span.checklist.optional.includes(k))) {
        return res.status(400).json({ error: `kept must be a subset of the span's optional checklist ids` });
      }
      const dir = join(storyStateDir, docId);
      mkdirSync(dir, { recursive: true });
      const file = join(dir, `${storyId}.json`);
      const state = readJson(file) ?? { choices: {}, kept: {} };
      if (!state.choices || typeof state.choices !== 'object') state.choices = {};
      if (!state.kept || typeof state.kept !== 'object') state.kept = {};
      if (choice !== undefined) state.choices[spanId] = choice;
      if (kept !== undefined) state.kept[spanId] = kept;
      writeFileSync(file, JSON.stringify(state, null, 2));
      res.json({ ok: true, state });
    });

    // Truth nodes: reusable passages saved from the doc or pasted from
    // chats/books, dropped into documents later from the Story tab.
    const nodesFile = root ? join(root, 'data', 'writer', 'nodes.json') : '';

    ctx.app.get('/api/drh/nodes', (req: Request, res: Response) => {
      if (!root) return res.status(503).json({ error: 'Deep Research Hub folder not found; set DRH_ROOT' });
      let nodes = readNodes(nodesFile);
      const q = typeof req.query.q === 'string' ? req.query.q.trim().toLowerCase().slice(0, 200) : '';
      if (q) {
        nodes = nodes.filter((n) =>
          `${n.text ?? ''} ${n.note ?? ''} ${(n.tags ?? []).join(' ')}`.toLowerCase().includes(q));
      }
      nodes = nodes.slice().sort((a, b) => String(b.created ?? '').localeCompare(String(a.created ?? '')));
      res.json({ nodes });
    });

    ctx.app.post('/api/drh/nodes', (req: Request, res: Response) => {
      if (!root) return res.status(503).json({ error: 'Deep Research Hub folder not found; set DRH_ROOT' });
      const text = typeof req.body?.text === 'string' ? req.body.text.trim() : '';
      if (!text) return res.status(400).json({ error: 'no text to save' });
      const wordCount = text.split(/\s+/).length;
      if (wordCount > 4000) return res.status(400).json({ error: `node too long (${wordCount} words; max 4000)` });
      const note = typeof req.body?.note === 'string' ? req.body.note.trim().slice(0, 200) : '';
      const tags = (Array.isArray(req.body?.tags) ? req.body.tags : [])
        .filter((t: unknown) => typeof t === 'string')
        .map((t: string) => t.trim().toLowerCase())
        .filter(Boolean)
        .slice(0, 12);
      const source = typeof req.body?.source === 'string' ? req.body.source.trim().slice(0, 300) : '';
      const nodes = readNodes(nodesFile);
      const node = {
        id: nodeId(note, text, new Set(nodes.map((n) => n.id))),
        text,
        note,
        tags,
        source,
        created: new Date().toISOString(),
      };
      nodes.push(node);
      mkdirSync(dirname(nodesFile), { recursive: true });
      writeFileSync(nodesFile, JSON.stringify(nodes, null, 2));
      res.json({ ok: true, node });
    });

    ctx.app.delete('/api/drh/nodes', (req: Request, res: Response) => {
      if (!root) return res.status(503).json({ error: 'Deep Research Hub folder not found; set DRH_ROOT' });
      const id = safeId(req.query.id);
      if (!id) return res.status(400).json({ error: 'bad node id' });
      const nodes = readNodes(nodesFile);
      const kept = nodes.filter((n) => n.id !== id);
      if (kept.length === nodes.length) return res.status(404).json({ error: `no node "${id}"` });
      writeFileSync(nodesFile, JSON.stringify(kept, null, 2));
      res.json({ ok: true });
    });

    // Rewrite-by-selection: run a prompts/W_rewrite.json slot over the
    // selected text via OpenRouter. Mirrors prompts/run_slot.py: the exact
    // request lands in data/api/requests/, one line in data/api/log.jsonl.
    ctx.app.post('/api/drh/rewrite', async (req: Request, res: Response) => {
      if (!root) return res.status(503).json({ error: 'Deep Research Hub folder not found; set DRH_ROOT' });
      const promptsDir = join(root, 'prompts');
      const set = readJson(join(promptsDir, 'W_rewrite.json'));
      if (!set?.slots) return res.status(500).json({ error: 'prompts/W_rewrite.json missing or invalid' });
      const slotId = typeof req.body?.slot === 'string' ? req.body.slot : '';
      const entry = Object.entries(set.slots).find(([n, s]: [string, any]) => s && (s.id === slotId || n === slotId));
      if (!entry) return res.status(400).json({ error: `unknown rewrite slot "${slotId}"` });
      const [slotNo, slot] = entry as [string, any];
      const text = typeof req.body?.text === 'string' ? req.body.text.trim() : '';
      if (!text) return res.status(400).json({ error: 'nothing selected to rewrite' });
      const wordCount = text.split(/\s+/).length;
      if (wordCount > 6000) return res.status(400).json({ error: `selection too long (${wordCount} words; max 6000)` });
      const instruction = typeof req.body?.instruction === 'string' ? req.body.instruction.trim() : '';
      if (slot.id === 'custom' && !instruction) return res.status(400).json({ error: 'custom rewrite needs an instruction' });
      const asText = (v: unknown) => (Array.isArray(v) ? v : []).filter((x) => typeof x === 'string').map((x: string) => x.trim()).filter(Boolean);
      const contextBefore = asText(req.body?.contextBefore).join('\n\n');
      const contextAfter = asText(req.body?.contextAfter).join('\n\n');

      const apiKey = ctx.config.openrouterKey || process.env.OPENROUTER_API_KEY || '';
      if (!apiKey) {
        return res.status(503).json({ error: 'Rewrite needs an OpenRouter key: set OPENROUTER_API_KEY in the environment (or the Deep Research Hub plugin’s openrouterKey setting), then restart OpenWriter.' });
      }
      const model = ctx.config.model || slot.provider?.model;
      const baseUrl = (slot.provider?.base_url || 'https://openrouter.ai/api/v1').replace(/\/$/, '');
      const fill = (s: string) => s
        .replaceAll('{text}', text)
        .replaceAll('{instruction}', instruction)
        .replaceAll('{contextBefore}', contextBefore)
        .replaceAll('{contextAfter}', contextAfter);
      const { system, user } = buildSlotMessages(promptsDir, slot, fill);
      const messages = system
        ? [{ role: 'system', content: system }, { role: 'user', content: user }]
        : [{ role: 'user', content: user }];
      const requestBody: Record<string, unknown> = {
        model,
        temperature: slot.temperature ?? 0.4,
        messages,
      };
      if (slot.max_tokens) requestBody.max_tokens = slot.max_tokens;

      const stamp = new Date();
      const pad = (n: number) => String(n).padStart(2, '0');
      const rid = `${stamp.getFullYear()}${pad(stamp.getMonth() + 1)}${pad(stamp.getDate())}-${pad(stamp.getHours())}${pad(stamp.getMinutes())}${pad(stamp.getSeconds())}_${slot.id}_selection`;
      const apiDir = join(root, 'data', 'api');
      mkdirSync(join(apiDir, 'requests'), { recursive: true });
      writeFileSync(join(apiDir, 'requests', `${rid}.json`), JSON.stringify(requestBody, null, 2));

      let data: any;
      try {
        const upstream = await fetch(`${baseUrl}/chat/completions`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${apiKey}` },
          body: JSON.stringify(requestBody),
          signal: AbortSignal.timeout(60_000),
        });
        data = await upstream.json().catch(() => null);
        if (!upstream.ok) {
          const msg = data?.error?.message || (typeof data?.error === 'string' ? data.error : '') || `HTTP ${upstream.status}`;
          return res.status(502).json({ error: `OpenRouter: ${msg}` });
        }
      } catch (err: any) {
        const msg = err?.name === 'TimeoutError' ? 'OpenRouter took too long (60s); try again' : `OpenRouter request failed: ${err?.message || err}`;
        return res.status(502).json({ error: msg });
      }

      const content = data?.choices?.[0]?.message?.content;
      if (typeof content !== 'string' || !content.trim()) {
        return res.status(502).json({ error: 'OpenRouter returned no text' });
      }
      const usage = data?.usage ?? {};
      appendFileSync(join(apiDir, 'log.jsonl'), JSON.stringify({
        id: rid,
        time: stamp.toISOString().slice(0, 19),
        slot: `W/${slotNo}`,
        slot_id: slot.id,
        model,
        file: 'openwriter-selection',
        tokens_in: usage.prompt_tokens ?? null,
        tokens_out: usage.completion_tokens ?? null,
      }) + '\n');
      res.json({ text: cleanRewrite(content), model });
    });

    // Craft-on-demand: one call turns the doc's current opening + the hub's
    // research into three graded openings, saved as a crafted story file the
    // Story tab then opens in its variant cycler.
    ctx.app.post('/api/drh/craft-opening', async (req: Request, res: Response) => {
      if (!root) return res.status(503).json({ error: 'Deep Research Hub folder not found; set DRH_ROOT' });
      const promptsDir = join(root, 'prompts');
      const set = readJson(join(promptsDir, 'W_craft.json'));
      const slot = set?.slots?.['1'];
      if (!slot) return res.status(500).json({ error: 'prompts/W_craft.json missing or slot 1 empty' });
      const text = typeof req.body?.text === 'string' ? req.body.text.trim() : '';
      if (!text) return res.status(400).json({ error: 'no opening text to work from' });
      const wordCount = text.split(/\s+/).length;
      if (wordCount > 2000) return res.status(400).json({ error: `opening too long (${wordCount} words; max 2000)` });
      const topic = typeof req.body?.topic === 'string' ? req.body.topic.trim().slice(0, 200) : '';
      const storyId = `crafted-${safeId(req.body?.docId || 'scratch') ?? 'scratch'}`;

      // Hub research for the flavors to lean on: top 3 of each kind.
      const q = topic || text.split(/\s+/).slice(0, 8).join(' ');
      const cards = researchCards(root, q);
      const cardLine = (c: Card) => `- ${c.title} (${c.detail}): ${c.snippet.slice(0, 300)}`;
      const research = cards.filter((c) => c.kind === 'deep_research').slice(0, 3).map(cardLine).join('\n') || '(none found)';
      const youtube = cards.filter((c) => c.kind === 'youtube').slice(0, 3).map(cardLine).join('\n') || '(none found)';

      // Grading always matches the live checklist: inject the core items.
      const def = readJson(checklistFile);
      const coreItems = (def?.items ?? []).filter((i: any) => i.core);
      const coreIds = new Set<string>(coreItems.map((i: any) => i.id));
      const checklist = coreItems.map((i: any) => `- ${i.id}: ${i.question}`).join('\n');

      const apiKey = ctx.config.openrouterKey || process.env.OPENROUTER_API_KEY || '';
      if (!apiKey) {
        return res.status(503).json({ error: 'Craft needs an OpenRouter key: set OPENROUTER_API_KEY in the environment (or the Deep Research Hub plugin’s openrouterKey setting), then restart OpenWriter.' });
      }
      const model = ctx.config.model || slot.provider?.model;
      const baseUrl = (slot.provider?.base_url || 'https://openrouter.ai/api/v1').replace(/\/$/, '');
      const fill = (s: string) => s
        .replaceAll('{text}', text)
        .replaceAll('{research}', research)
        .replaceAll('{youtube}', youtube)
        .replaceAll('{checklist}', checklist)
        .replaceAll('{topic}', topic);
      const { system, user } = buildSlotMessages(promptsDir, slot, fill);
      const requestBody: Record<string, unknown> = {
        model,
        temperature: slot.temperature ?? 0.7,
        messages: [{ role: 'system', content: system }, { role: 'user', content: user }],
      };

      const stamp = new Date();
      const pad = (n: number) => String(n).padStart(2, '0');
      const rid = `${stamp.getFullYear()}${pad(stamp.getMonth() + 1)}${pad(stamp.getDate())}-${pad(stamp.getHours())}${pad(stamp.getMinutes())}${pad(stamp.getSeconds())}_${slot.id}_${storyId}`;
      const apiDir = join(root, 'data', 'api');
      mkdirSync(join(apiDir, 'requests'), { recursive: true });
      writeFileSync(join(apiDir, 'requests', `${rid}.json`), JSON.stringify(requestBody, null, 2));

      let data: any;
      try {
        const upstream = await fetch(`${baseUrl}/chat/completions`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${apiKey}` },
          body: JSON.stringify(requestBody),
          signal: AbortSignal.timeout(60_000),
        });
        data = await upstream.json().catch(() => null);
        if (!upstream.ok) {
          const msg = data?.error?.message || (typeof data?.error === 'string' ? data.error : '') || `HTTP ${upstream.status}`;
          return res.status(502).json({ error: `OpenRouter: ${msg}` });
        }
      } catch (err: any) {
        const msg = err?.name === 'TimeoutError' ? 'OpenRouter took too long (60s); try again' : `OpenRouter request failed: ${err?.message || err}`;
        return res.status(502).json({ error: msg });
      }

      const content = data?.choices?.[0]?.message?.content;
      if (typeof content !== 'string' || !content.trim()) {
        return res.status(502).json({ error: 'OpenRouter returned no text' });
      }
      let parsed: any;
      try {
        const stripped = content.trim().replace(/^```(?:json)?\s*\n?/i, '').replace(/\n?```\s*$/, '');
        parsed = JSON.parse(stripped);
      } catch {
        return res.status(502).json({ error: 'The model did not return parseable JSON; try again' });
      }
      const cleanGrades = (g: any): Record<string, number> => {
        const out: Record<string, number> = {};
        if (g && typeof g === 'object') {
          for (const [k, v] of Object.entries(g)) {
            if (coreIds.has(k) && typeof v === 'number' && isFinite(v)) out[k] = Math.max(0, Math.min(10, Math.round(v)));
          }
        }
        return out;
      };
      const flavorVariants = (Array.isArray(parsed?.variants) ? parsed.variants : [])
        .filter((v: any) => v && typeof v.text === 'string' && v.text.trim() && ['research', 'story', 'youtube'].includes(v.flavor));
      if (!flavorVariants.length) {
        return res.status(502).json({ error: 'The model returned no usable openings; try again' });
      }

      const story = {
        id: storyId,
        title: `Crafted opening — ${topic || q}`,
        created: stamp.toISOString(),
        spans: [{
          id: 'crafted-opening',
          label: 'Crafted openings',
          anchor: text,
          checklist: { needed: [], optional: [] },
          variants: [
            { id: 'v0', text, note: 'Your current opening', source: 'doc', grades: cleanGrades(parsed?.current_grades) },
            ...flavorVariants.map((v: any, i: number) => ({
              id: `v${i + 1}`,
              text: v.text.trim(),
              note: `${v.flavor}${typeof v.source_note === 'string' && v.source_note.trim() ? ` — ${v.source_note.trim()}` : ''}`,
              source: 'craft',
              grades: cleanGrades(v.grades),
            })),
          ],
        }],
      };
      mkdirSync(storiesDir, { recursive: true });
      writeFileSync(join(storiesDir, `${storyId}.json`), JSON.stringify(story, null, 2));

      const usage = data?.usage ?? {};
      appendFileSync(join(apiDir, 'log.jsonl'), JSON.stringify({
        id: rid,
        time: stamp.toISOString().slice(0, 19),
        slot: 'C/1',
        slot_id: slot.id,
        model,
        file: 'openwriter-craft',
        tokens_in: usage.prompt_tokens ?? null,
        tokens_out: usage.completion_tokens ?? null,
      }) + '\n');
      res.json({ ok: true, storyId });
    });

    // Revise: the Story tab's "Run" (picked checklist items as goals) and the
    // chat column (a message + recent turns). The doc arrives as numbered
    // paragraphs; the model returns { reply, edits: [{ id, text, why }] } and
    // the client lands each edit as a pending rewrite in the doc itself.
    ctx.app.post('/api/drh/revise', async (req: Request, res: Response) => {
      if (!root) return res.status(503).json({ error: 'Deep Research Hub folder not found; set DRH_ROOT' });
      const promptsDir = join(root, 'prompts');
      const set = readJson(join(promptsDir, 'W_revise.json'));
      const mode = req.body?.mode === 'chat' ? 'chat' : 'run';
      const slot = set?.slots?.[mode === 'chat' ? '2' : '1'];
      if (!slot) return res.status(500).json({ error: 'prompts/W_revise.json missing or slot empty' });

      const paras = (Array.isArray(req.body?.paragraphs) ? req.body.paragraphs : [])
        .filter((p: any) => p && typeof p.id === 'string' && /^p\d{1,5}$/.test(p.id) && typeof p.text === 'string');
      if (!paras.length) return res.status(400).json({ error: 'the document is empty' });
      const docText = paras.map((p: any) => `[${p.id}]${typeof p.kind === 'string' && p.kind ? ` (${p.kind.slice(0, 20)})` : ''} ${p.text}`).join('\n\n');
      const wordCount = docText.split(/\s+/).length;
      if (wordCount > 30000) return res.status(400).json({ error: `document too long (${wordCount} words; max 30000)` });
      const known = new Set<string>(paras.map((p: any) => p.id));
      const editable = (Array.isArray(req.body?.editable) ? req.body.editable : []).filter((id: unknown) => typeof id === 'string' && known.has(id));
      const goals = (Array.isArray(req.body?.goals) ? req.body.goals : [])
        .filter((g: any) => g && typeof g.label === 'string')
        .slice(0, 40)
        .map((g: any) => `- ${g.label.slice(0, 120)}${typeof g.question === 'string' && g.question ? `: ${g.question.slice(0, 400)}` : ''}`)
        .join('\n');
      const instruction = typeof req.body?.instruction === 'string' ? req.body.instruction.trim().slice(0, 4000) : '';
      if (mode === 'run' && !goals && !instruction) return res.status(400).json({ error: 'pick at least one checklist item to run' });
      if (mode === 'chat' && !instruction) return res.status(400).json({ error: 'nothing to send' });
      const history = (Array.isArray(req.body?.history) ? req.body.history : [])
        .filter((m: any) => m && (m.role === 'user' || m.role === 'assistant') && typeof m.content === 'string')
        .slice(-10)
        .map((m: any) => ({ role: m.role, content: m.content.slice(0, 4000) }));
      const topic = typeof req.body?.topic === 'string' ? req.body.topic.trim().slice(0, 200) : '';

      const apiKey = ctx.config.openrouterKey || process.env.OPENROUTER_API_KEY || '';
      if (!apiKey) {
        return res.status(503).json({ error: 'Needs an OpenRouter key: set OPENROUTER_API_KEY in the environment (or the Deep Research Hub plugin’s openrouterKey setting), then restart OpenWriter.' });
      }
      const model = ctx.config.model || slot.provider?.model;
      const baseUrl = (slot.provider?.base_url || 'https://openrouter.ai/api/v1').replace(/\/$/, '');
      const fill = (s: string) => s
        .replaceAll('{document}', docText)
        .replaceAll('{goals}', goals || '(none — follow the instruction)')
        .replaceAll('{instruction}', instruction || '(none)')
        .replaceAll('{editable}', editable.length ? editable.join(', ') : 'any paragraph')
        .replaceAll('{topic}', topic || '(not given)');
      const { system, user } = buildSlotMessages(promptsDir, slot, fill);
      const requestBody: Record<string, unknown> = {
        model,
        temperature: slot.temperature ?? 0.5,
        response_format: { type: 'json_object' },
        messages: [
          { role: 'system', content: system },
          ...history,
          { role: 'user', content: user },
        ],
      };
      if (slot.max_tokens) requestBody.max_tokens = slot.max_tokens;

      const stamp = new Date();
      const pad = (n: number) => String(n).padStart(2, '0');
      const rid = `${stamp.getFullYear()}${pad(stamp.getMonth() + 1)}${pad(stamp.getDate())}-${pad(stamp.getHours())}${pad(stamp.getMinutes())}${pad(stamp.getSeconds())}_${slot.id}_doc`;
      const apiDir = join(root, 'data', 'api');
      mkdirSync(join(apiDir, 'requests'), { recursive: true });
      writeFileSync(join(apiDir, 'requests', `${rid}.json`), JSON.stringify(requestBody, null, 2));

      let data: any;
      try {
        const upstream = await fetch(`${baseUrl}/chat/completions`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${apiKey}` },
          body: JSON.stringify(requestBody),
          signal: AbortSignal.timeout(180_000),
        });
        data = await upstream.json().catch(() => null);
        if (!upstream.ok) {
          const msg = data?.error?.message || (typeof data?.error === 'string' ? data.error : '') || `HTTP ${upstream.status}`;
          return res.status(502).json({ error: `OpenRouter: ${msg}` });
        }
      } catch (err: any) {
        const msg = err?.name === 'TimeoutError' ? 'OpenRouter took too long (180s); try again' : `OpenRouter request failed: ${err?.message || err}`;
        return res.status(502).json({ error: msg });
      }

      const content = data?.choices?.[0]?.message?.content;
      if (typeof content !== 'string' || !content.trim()) {
        return res.status(502).json({ error: 'OpenRouter returned no text' });
      }
      let parsed: any;
      try {
        parsed = JSON.parse(content.trim().replace(/^```(?:json)?\s*\n?/i, '').replace(/\n?```\s*$/, ''));
      } catch {
        return res.status(502).json({ error: 'The model did not return parseable JSON; try again' });
      }
      const allowed = editable.length ? new Set<string>(editable) : known;
      const original = new Map<string, string>(paras.map((p: any) => [p.id, p.text]));
      const seen = new Set<string>();
      const edits = (Array.isArray(parsed?.edits) ? parsed.edits : [])
        .filter((e: any) => e && typeof e.id === 'string' && typeof e.text === 'string')
        .map((e: any) => ({ id: e.id.replace(/^\[|\]$/g, ''), text: e.text.trim(), why: typeof e.why === 'string' ? e.why.trim().slice(0, 400) : '' }))
        .filter((e: any) => allowed.has(e.id) && !seen.has(e.id) && seen.add(e.id) && e.text !== original.get(e.id));

      const usage = data?.usage ?? {};
      appendFileSync(join(apiDir, 'log.jsonl'), JSON.stringify({
        id: rid,
        time: stamp.toISOString().slice(0, 19),
        slot: `V/${mode === 'chat' ? 2 : 1}`,
        slot_id: slot.id,
        model,
        file: `openwriter-${mode}`,
        tokens_in: usage.prompt_tokens ?? null,
        tokens_out: usage.completion_tokens ?? null,
      }) + '\n');
      res.json({ reply: typeof parsed?.reply === 'string' ? parsed.reply.trim() : '', edits, model });
    });

    // YouTube script: turn a paper or deep-research report into a long-form
    // YouTube script and a short vertical hook script.
    ctx.app.post('/api/drh/youtube-script', async (req: Request, res: Response) => {
      if (!root) return res.status(503).json({ error: 'Deep Research Hub folder not found; set DRH_ROOT' });
      const promptsDir = join(root, 'prompts');
      const set = readJson(join(promptsDir, 'W_youtube_script.json'));
      const slot = set?.slots?.['1'];
      if (!slot) return res.status(500).json({ error: 'prompts/W_youtube_script.json missing or slot 1 empty' });

      let text = '';
      if (typeof req.body?.text === 'string') {
        text = req.body.text.trim();
      } else if (Array.isArray(req.body?.paragraphs)) {
        text = req.body.paragraphs
          .filter((p: any) => p && typeof p.text === 'string')
          .map((p: any) => p.text)
          .join('\n\n')
          .trim();
      }
      if (!text) return res.status(400).json({ error: 'no source text to work from' });
      const wordCount = text.split(/\s+/).length;
      if (wordCount > 30000) return res.status(400).json({ error: `source text too long (${wordCount} words; max 30000)` });
      const topic = typeof req.body?.topic === 'string' ? req.body.topic.trim().slice(0, 200) : '';

      const q = topic || text.split(/\s+/).slice(0, 8).join(' ');
      const cards = researchCards(root, q);
      const cardLine = (c: Card) => `- ${c.title} (${c.detail}): ${c.snippet.slice(0, 300)}`;
      const cardsText = cards.slice(0, 5).map(cardLine).join('\n') || '(none found)';

      const apiKey = ctx.config.openrouterKey || process.env.OPENROUTER_API_KEY || '';
      if (!apiKey) {
        return res.status(503).json({ error: 'Needs an OpenRouter key: set OPENROUTER_API_KEY in the environment (or the Deep Research Hub plugin’s openrouterKey setting), then restart OpenWriter.' });
      }
      const model = ctx.config.model || slot.provider?.model;
      const baseUrl = (slot.provider?.base_url || 'https://openrouter.ai/api/v1').replace(/\/$/, '');
      const fill = (s: string) => s
        .replaceAll('{text}', text)
        .replaceAll('{topic}', topic || '(not given)')
        .replaceAll('{cards}', cardsText);
      const { system, user } = buildSlotMessages(promptsDir, slot, fill);
      const requestBody: Record<string, unknown> = {
        model,
        temperature: slot.temperature ?? 0.7,
        response_format: { type: 'json_object' },
        messages: [{ role: 'system', content: system }, { role: 'user', content: user }],
      };
      if (slot.max_tokens) requestBody.max_tokens = slot.max_tokens;

      const stamp = new Date();
      const pad = (n: number) => String(n).padStart(2, '0');
      const rid = `${stamp.getFullYear()}${pad(stamp.getMonth() + 1)}${pad(stamp.getDate())}-${pad(stamp.getHours())}${pad(stamp.getMinutes())}${pad(stamp.getSeconds())}_${slot.id}_youtube`;
      const apiDir = join(root, 'data', 'api');
      mkdirSync(join(apiDir, 'requests'), { recursive: true });
      writeFileSync(join(apiDir, 'requests', `${rid}.json`), JSON.stringify(requestBody, null, 2));

      let data: any;
      try {
        const upstream = await fetch(`${baseUrl}/chat/completions`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${apiKey}` },
          body: JSON.stringify(requestBody),
          signal: AbortSignal.timeout(180_000),
        });
        data = await upstream.json().catch(() => null);
        if (!upstream.ok) {
          const msg = data?.error?.message || (typeof data?.error === 'string' ? data.error : '') || `HTTP ${upstream.status}`;
          return res.status(502).json({ error: `OpenRouter: ${msg}` });
        }
      } catch (err: any) {
        const msg = err?.name === 'TimeoutError' ? 'OpenRouter took too long (180s); try again' : `OpenRouter request failed: ${err?.message || err}`;
        return res.status(502).json({ error: msg });
      }

      const content = data?.choices?.[0]?.message?.content;
      if (typeof content !== 'string' || !content.trim()) {
        return res.status(502).json({ error: 'OpenRouter returned no text' });
      }
      let parsed: any;
      try {
        parsed = JSON.parse(content.trim().replace(/^```(?:json)?\s*\n?/i, '').replace(/\n?```\s*$/, ''));
      } catch {
        return res.status(502).json({ error: 'The model did not return parseable JSON; try again' });
      }

      const usage = data?.usage ?? {};
      appendFileSync(join(apiDir, 'log.jsonl'), JSON.stringify({
        id: rid,
        time: stamp.toISOString().slice(0, 19),
        slot: 'V/1',
        slot_id: slot.id,
        model,
        file: 'openwriter-youtube-script',
        tokens_in: usage.prompt_tokens ?? null,
        tokens_out: usage.completion_tokens ?? null,
      }) + '\n');

      const str = (v: unknown, max: number) => (typeof v === 'string' ? v.trim().slice(0, max) : '');
      const arr = (v: unknown) => Array.isArray(v) ? v.filter((x: unknown) => typeof x === 'string').map((x: string) => x.trim()) : [];
      res.json({
        ok: true,
        title_long: str(parsed?.title_long, 200),
        title_short: str(parsed?.title_short, 200),
        youtube_script: str(parsed?.youtube_script, 20000),
        short_script: str(parsed?.short_script, 5000),
        sources_used: arr(parsed?.sources_used).slice(0, 12),
        model,
      });
    });

    // API calls: preset actions run over the whole doc from the left column's
    // "API calls" section or the right rail's APIs tab. Built-ins are slots in
    // prompts/W_actions.json; the writer's own live in data/writer/actions.json.
    // Output 'edits' lands as pending rewrites (W_revise/RULES.md contract);
    // output 'notes' is a scored report whose issues become comments on the
    // quoted words (W_actions/NOTES.md contract).
    const actionsFile = root ? join(root, 'data', 'writer', 'actions.json') : '';
    const listActions = (): any[] => {
      const builtIn: any[] = [];
      const set = root ? readJson(join(root, 'prompts', 'W_actions.json')) : null;
      for (const [n, s] of Object.entries(set?.slots ?? {}) as [string, any][]) {
        if (!s?.id) continue;
        builtIn.push({ id: s.id, label: s.label || s.id, description: s.description || '', output: s.output === 'notes' ? 'notes' : 'edits', builtIn: true, slot: n, model: s.provider?.model || '' });
      }
      const custom = (readJson(actionsFile) ?? []).filter((a: any) => a && typeof a.id === 'string' && typeof a.prompt === 'string')
        .map((a: any) => ({ id: a.id, label: a.label || a.id, description: a.description || '', output: a.output === 'notes' ? 'notes' : 'edits', builtIn: false, prompt: a.prompt, model: a.model || '' }));
      return [...builtIn, ...custom];
    };

    ctx.app.get('/api/drh/actions', (_req: Request, res: Response) => {
      if (!root) return res.status(503).json({ error: 'Deep Research Hub folder not found; set DRH_ROOT' });
      res.json({ actions: listActions(), defaultModel: ctx.config.model || '' });
    });

    ctx.app.post('/api/drh/actions', (req: Request, res: Response) => {
      if (!root) return res.status(503).json({ error: 'Deep Research Hub folder not found; set DRH_ROOT' });
      const label = typeof req.body?.label === 'string' ? req.body.label.trim().slice(0, 60) : '';
      const prompt = typeof req.body?.prompt === 'string' ? req.body.prompt.trim().slice(0, 20000) : '';
      if (!label || !prompt) return res.status(400).json({ error: 'an API call needs a name and a prompt' });
      const custom: any[] = (readJson(actionsFile) ?? []).filter((a: any) => a && typeof a.id === 'string');
      const taken = new Set<string>(listActions().map((a) => a.id));
      const editing = safeId(req.body?.id);
      let id = editing && custom.some((a) => a.id === editing) ? editing : '';
      if (!id) {
        const base = `my-${label.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 40) || 'call'}`;
        id = base;
        for (let n = 2; taken.has(id); n++) id = `${base}-${n}`;
      }
      const action = {
        id,
        label,
        description: typeof req.body?.description === 'string' ? req.body.description.trim().slice(0, 200) : '',
        output: req.body?.output === 'notes' ? 'notes' : 'edits',
        prompt,
        model: typeof req.body?.model === 'string' ? req.body.model.trim().slice(0, 100) : '',
        updated: new Date().toISOString(),
      };
      const next = custom.filter((a) => a.id !== id);
      next.push(action);
      mkdirSync(dirname(actionsFile), { recursive: true });
      writeFileSync(actionsFile, JSON.stringify(next, null, 2));
      res.json({ ok: true, action: { ...action, builtIn: false } });
    });

    ctx.app.delete('/api/drh/actions', (req: Request, res: Response) => {
      if (!root) return res.status(503).json({ error: 'Deep Research Hub folder not found; set DRH_ROOT' });
      const id = safeId(req.query.id);
      const custom: any[] = readJson(actionsFile) ?? [];
      const kept = custom.filter((a) => a?.id !== id);
      if (!id || kept.length === custom.length) return res.status(404).json({ error: `no API call "${id}" of yours` });
      writeFileSync(actionsFile, JSON.stringify(kept, null, 2));
      res.json({ ok: true });
    });

    ctx.app.post('/api/drh/action', async (req: Request, res: Response) => {
      if (!root) return res.status(503).json({ error: 'Deep Research Hub folder not found; set DRH_ROOT' });
      const promptsDir = join(root, 'prompts');
      const action = listActions().find((a) => a.id === req.body?.action);
      if (!action) return res.status(400).json({ error: `unknown API call "${req.body?.action}"` });

      const paras = (Array.isArray(req.body?.paragraphs) ? req.body.paragraphs : [])
        .filter((p: any) => p && typeof p.id === 'string' && /^p\d{1,5}$/.test(p.id) && typeof p.text === 'string');
      if (!paras.length) return res.status(400).json({ error: 'the document is empty' });
      const docText = paras.map((p: any) => `[${p.id}]${typeof p.kind === 'string' && p.kind ? ` (${p.kind.slice(0, 20)})` : ''} ${p.text}`).join('\n\n');
      const wordCount = docText.split(/\s+/).length;
      if (wordCount > 30000) return res.status(400).json({ error: `document too long (${wordCount} words; max 30000)` });
      const known = new Set<string>(paras.map((p: any) => p.id));
      const editable = (Array.isArray(req.body?.editable) ? req.body.editable : []).filter((id: unknown) => typeof id === 'string' && known.has(id));
      const extra = typeof req.body?.extra === 'string' ? req.body.extra.trim().slice(0, 4000) : '';
      const context = typeof req.body?.context === 'string' ? req.body.context.trim().slice(0, 20000) : '';
      const topic = typeof req.body?.topic === 'string' ? req.body.topic.trim().slice(0, 200) : '';

      // Built-in: the slot's own parts. Custom: contract file + the writer's prompt.
      const set = readJson(join(promptsDir, 'W_actions.json'));
      const slot: any = action.builtIn ? set?.slots?.[action.slot] : {
        id: action.id,
        temperature: 0.5,
        max_tokens: 12000,
        provider: set?.slots?.['1']?.provider,
        prompt: {
          join: '\n\n---\n\n',
          strip_comments: true,
          parts: [
            { file: action.output === 'notes' ? 'W_actions/NOTES.md' : 'W_revise/RULES.md' },
            { input: `${action.prompt}\n\n{inputs}` },
          ],
        },
      };
      if (!slot) return res.status(500).json({ error: 'prompts/W_actions.json missing or slot empty' });

      const apiKey = ctx.config.openrouterKey || process.env.OPENROUTER_API_KEY || '';
      if (!apiKey) {
        return res.status(503).json({ error: 'Needs an OpenRouter key: set OPENROUTER_API_KEY in the environment (or the Deep Research Hub plugin’s openrouterKey setting), then restart OpenWriter.' });
      }
      const model = action.model || ctx.config.model || slot.provider?.model || 'openai/gpt-4o-mini';
      const baseUrl = (slot.provider?.base_url || 'https://openrouter.ai/api/v1').replace(/\/$/, '');
      const inputs = [
        `Topic: ${topic || '(not given)'}`,
        context ? `Earlier result to work from:\n<earlier>\n${context}\n</earlier>` : '',
        extra ? `Extra instruction: ${extra}` : '',
        `Editable paragraphs: ${editable.length ? editable.join(', ') : 'any paragraph'}`,
        `Document:\n<document>\n${docText}\n</document>`,
        'Return only the JSON object.',
      ].filter(Boolean).join('\n\n');
      const fill = (s: string) => s.replaceAll('{inputs}', inputs);
      const { system, user } = buildSlotMessages(promptsDir, slot, fill);
      const requestBody: Record<string, unknown> = {
        model,
        temperature: slot.temperature ?? 0.4,
        response_format: { type: 'json_object' },
        messages: [{ role: 'system', content: system }, { role: 'user', content: user }],
      };
      if (slot.max_tokens) requestBody.max_tokens = slot.max_tokens;

      const stamp = new Date();
      const pad = (n: number) => String(n).padStart(2, '0');
      const rid = `${stamp.getFullYear()}${pad(stamp.getMonth() + 1)}${pad(stamp.getDate())}-${pad(stamp.getHours())}${pad(stamp.getMinutes())}${pad(stamp.getSeconds())}_${action.id}_doc`;
      const apiDir = join(root, 'data', 'api');
      mkdirSync(join(apiDir, 'requests'), { recursive: true });
      writeFileSync(join(apiDir, 'requests', `${rid}.json`), JSON.stringify(requestBody, null, 2));

      let data: any;
      try {
        const upstream = await fetch(`${baseUrl}/chat/completions`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${apiKey}` },
          body: JSON.stringify(requestBody),
          signal: AbortSignal.timeout(180_000),
        });
        data = await upstream.json().catch(() => null);
        if (!upstream.ok) {
          const msg = data?.error?.message || (typeof data?.error === 'string' ? data.error : '') || `HTTP ${upstream.status}`;
          return res.status(502).json({ error: `OpenRouter: ${msg}` });
        }
      } catch (err: any) {
        const msg = err?.name === 'TimeoutError' ? 'OpenRouter took too long (180s); try again' : `OpenRouter request failed: ${err?.message || err}`;
        return res.status(502).json({ error: msg });
      }
      const content = data?.choices?.[0]?.message?.content;
      if (typeof content !== 'string' || !content.trim()) return res.status(502).json({ error: 'OpenRouter returned no text' });
      let parsed: any;
      try {
        parsed = JSON.parse(content.trim().replace(/^```(?:json)?\s*\n?/i, '').replace(/\n?```\s*$/, ''));
      } catch {
        return res.status(502).json({ error: 'The model did not return parseable JSON; try again' });
      }
      const usage = data?.usage ?? {};
      appendFileSync(join(apiDir, 'log.jsonl'), JSON.stringify({
        id: rid,
        time: stamp.toISOString().slice(0, 19),
        slot: action.builtIn ? `A/${action.slot}` : `A/${action.id}`,
        slot_id: action.id,
        model,
        file: 'openwriter-action',
        tokens_in: usage.prompt_tokens ?? null,
        tokens_out: usage.completion_tokens ?? null,
      }) + '\n');

      const str = (v: unknown, max: number) => (typeof v === 'string' ? v.trim().slice(0, max) : '');
      const score = (v: unknown) => (typeof v === 'number' && isFinite(v) ? Math.max(0, Math.min(100, Math.round(v))) : null);
      const reply = str(parsed?.reply, 2000);

      if (action.output === 'notes') {
        // Plain text of each paragraph (markdown marks off) to check quotes against.
        const plain = new Map<string, string>(paras.map((p: any) => [p.id, p.text.replace(/\*\*|\*|`/g, '').replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')]));
        const findQuote = (id: string, quote: string): { id: string; quote: string } | null => {
          const q = quote.replace(/\*\*|\*|`/g, '').replace(/^["“]|["”]$/g, '').trim();
          if (!q) return null;
          const at = (pid: string) => plain.get(pid)?.includes(q);
          if (known.has(id) && at(id)) return { id, quote: q };
          for (const pid of known) if (at(pid)) return { id: pid, quote: q };
          // The model paraphrased: keep the note on its paragraph, anchored to its opening words.
          if (known.has(id)) {
            const head = (plain.get(id) || '').split(/(?<=[.!?])\s/)[0].slice(0, 120);
            return head ? { id, quote: head } : null;
          }
          return null;
        };
        const sections = (Array.isArray(parsed?.sections) ? parsed.sections : []).slice(0, 20).map((s: any) => ({
          title: str(s?.title, 200),
          score: score(s?.score),
          basis: str(s?.basis, 600),
          critique: str(s?.critique, 1500),
          issues: (Array.isArray(s?.issues) ? s.issues : []).slice(0, 12).map((i: any) => {
            const anchor = findQuote(str(i?.id, 10).replace(/^\[|\]$/g, ''), str(i?.quote, 600));
            return { title: str(i?.title, 160), quote: str(i?.quote, 600), issue: str(i?.issue, 1200), next_step: str(i?.next_step, 800), anchor };
          }),
        }));
        return res.json({
          output: 'notes',
          model,
          reply,
          report: {
            overall: { score: score(parsed?.overall?.score), summary: str(parsed?.overall?.summary, 1500), grade: str(parsed?.overall?.grade, 60) },
            rubric: (Array.isArray(parsed?.rubric) ? parsed.rubric : []).slice(0, 12).map((r: any) => ({ name: str(r?.name, 80), score: score(r?.score), note: str(r?.note, 400) })),
            sections,
          },
        });
      }

      const allowed = editable.length ? new Set<string>(editable) : known;
      const original = new Map<string, string>(paras.map((p: any) => [p.id, p.text]));
      const seen = new Set<string>();
      const edits = (Array.isArray(parsed?.edits) ? parsed.edits : [])
        .filter((e: any) => e && typeof e.id === 'string' && typeof e.text === 'string')
        .map((e: any) => ({ id: e.id.replace(/^\[|\]$/g, ''), text: e.text.trim(), why: str(e.why, 400) }))
        .filter((e: any) => allowed.has(e.id) && !seen.has(e.id) && seen.add(e.id) && e.text !== original.get(e.id));
      res.json({ output: 'edits', model, reply, edits });
    });
  },

  contextMenuItems() {
    return [
      { label: 'Rewrite: shorter', action: 'drh:shorter', condition: 'has-selection' as const },
      { label: 'Rewrite: plainer', action: 'drh:plainer', condition: 'has-selection' as const },
      { label: 'Rewrite: as the Skeptic', action: 'drh:as_the_skeptic', condition: 'has-selection' as const },
      { label: 'Rewrite: the unforgotten sentence', action: 'drh:unforgotten_sentence', condition: 'has-selection' as const },
      { label: 'Rewrite: custom…', action: 'drh:custom', condition: 'has-selection' as const, promptForInput: true },
      { label: 'Save as truth node', action: 'drh:save-node', condition: 'has-selection' as const },
    ];
  },
};

export default plugin;
