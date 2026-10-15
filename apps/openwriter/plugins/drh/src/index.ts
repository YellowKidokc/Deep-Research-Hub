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
 *   GET  /api/drh/workflows            saved dossier workflows (prompts/D_dossier/workflows)
 *   GET  /api/drh/dossiers             every dossier with its topic and last run state
 *   POST /api/drh/dossiers             { name, topic, workflow } -> a new dossier
 *   GET  /api/drh/dossiers/:name       its settings, dump, run status and latest ledger
 *   POST /api/drh/dossiers/:name/add   { text, title } into the dump, or { link } to a hub path
 *   POST /api/drh/dossiers/:name/run   starts scripts/dossier.py run <name>
 *
 * The same dossier functions are MCP tools for an agent connected to
 * OpenWriter: drh_dossier_list, drh_dossier_create, drh_dossier_add,
 * drh_dossier_run, drh_dossier_read, drh_research_search.
 *
 * Everything lives in the hub's plain files, never in OpenWriter's state:
 *   <hub>/prompts/W_story_checklist.json     the checklist definition
 *   <hub>/data/writer/checklists/<docId>.json  ticks per document
 *   <hub>/data/deep_research/<job>/<stamp>/    research runs (drh_queue.py)
 *   <hub>/data/youtube/<Channel>/<Title>.md    transcripts (ytgrab.py)
 *   <hub>/data/targeted/<topic>/<stamp>/       Targeted Research facts (drh_targeted.py)
 *   <hub>/data/writer/dossiers/<name>/         dossiers (scripts/dossier.py)
 *
 * The hub root is DRH_ROOT, or found by walking up from this file.
 */
import { spawn } from 'child_process';
import { existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'fs';
import { dirname, join, resolve } from 'path';
import { fileURLToPath } from 'url';
import type { Request, Response, Router } from 'express';

interface RouteContext {
  app: Router;
  config: Record<string, string>;
  dataDir: string;
}

interface Card {
  kind: 'deep_research' | 'youtube' | 'targeted';
  title: string;
  detail: string;
  snippet: string;
  path: string;
  /** What a dossier links to for this card: a run folder, or the transcript file. */
  link: string;
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
  for (const job of dirs(dr)) {
    if (job.startsWith('_')) continue;
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
          link: ['data', 'deep_research', job, stamp].join('/'),
          score,
        });
      }
      break;
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
          link: ['data', 'youtube', channel, f].join('/'),
          score,
        });
      }
    }
  }

  // Targeted Research: newest run per topic.
  const tr = join(root, 'data', 'targeted');
  for (const topicDir of dirs(tr)) {
    for (const stamp of dirs(join(tr, topicDir)).sort().reverse()) {
      const run = readJson(join(tr, topicDir, stamp, 'run.json'));
      if (!run || run.status !== 'done') continue;
      const score = overlap(query, String(run.topic ?? topicDir));
      if (score > 0) {
        const s = run.summary || {};
        cards.push({
          kind: 'targeted',
          title: run.topic || topicDir,
          detail: `${stamp} · ${run.findings ?? 0} findings · ` + Object.entries(s).map(([k, v]) => `${k} ${v}`).join(', '),
          snippet: headOf(join(tr, topicDir, stamp, 'facts.md'), 1200).replace(/^#.*$/gm, '').trim().slice(0, 360),
          path: join('data', 'targeted', topicDir, stamp, 'facts.md'),
          link: ['data', 'targeted', topicDir, stamp].join('/'),
          score,
        });
      }
      break;
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


// ------------------------------------------------------------------ dossiers
// One implementation for the Dossier tab (routes) and the agent (MCP tools).
const DOSSIER_NAME = /^[A-Za-z0-9_.-]{1,80}$/;

class DossierError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

function dossierName(v: unknown): string {
  if (typeof v === 'string' && DOSSIER_NAME.test(v) && !v.startsWith('.')) return v;
  throw new DossierError(400, 'dossier name: letters, digits, _ . - only (up to 80)');
}

function stamp(): string {
  const d = new Date();
  const p = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}-${p(d.getHours())}${p(d.getMinutes())}${p(d.getSeconds())}`;
}

const running = new Map<string, number>();

function dossierDir(root: string, name: string): string {
  return join(root, 'data', 'writer', 'dossiers', name);
}

function dossierMeta(root: string, name: string): any {
  const meta = readJson(join(dossierDir(root, name), 'dossier.json'));
  if (!meta) throw new DossierError(404, `no dossier ${name}`);
  return meta;
}

function listWorkflows(root: string) {
  const dir = join(root, 'prompts', 'D_dossier', 'workflows');
  let files: string[] = [];
  try { files = readdirSync(dir).filter((f) => f.endsWith('.json')); } catch { /* none */ }
  return files.map((f) => readJson(join(dir, f))).filter(Boolean)
    .map((w: any) => ({ id: w.id, label: w.label, description: w.description, sections: (w.sections || []).length }));
}

function listDossiers(root: string) {
  const base = join(root, 'data', 'writer', 'dossiers');
  return dirs(base).map((name) => {
    const meta = readJson(join(base, name, 'dossier.json'));
    if (!meta) return null;
    const st = readJson(join(base, name, 'status.json'));
    return { name, topic: meta.topic, workflow: meta.workflow, state: running.has(name) ? 'running' : st?.state ?? 'not run' };
  }).filter(Boolean);
}

function createDossier(root: string, body: any) {
  const name = dossierName(body?.name);
  const workflow = dossierName(body?.workflow || 'default');
  if (!existsSync(join(root, 'prompts', 'D_dossier', 'workflows', `${workflow}.json`))) throw new DossierError(400, `no workflow ${workflow}`);
  const dir = dossierDir(root, name);
  if (existsSync(join(dir, 'dossier.json'))) throw new DossierError(409, `${name} already exists`);
  mkdirSync(join(dir, 'inbox'), { recursive: true });
  const topic = typeof body?.topic === 'string' && body.topic.trim() ? body.topic.trim().slice(0, 300) : name;
  writeFileSync(join(dir, 'dossier.json'), JSON.stringify({ name, topic, workflow, created: new Date().toISOString(), links: [] }, null, 2));
  return { ok: true, name, topic, workflow };
}

/** Add to the dump: { text, title } becomes an inbox file; { link } records a path under data/. */
function addToDossier(root: string, rawName: unknown, body: any) {
  const name = dossierName(rawName);
  const dir = dossierDir(root, name);
  const meta = dossierMeta(root, name);
  if (body?.link !== undefined) {
    const link = body.link;
    if (typeof link !== 'string' || !link.startsWith('data/') || link.split('/').some((p: string) => p === '..' || p === '')
        || !existsSync(join(root, ...link.split('/')))) {
      throw new DossierError(400, 'link must be an existing path under data/, e.g. data/deep_research/<job>/<stamp>');
    }
    if (!meta.links.includes(link)) meta.links.push(link);
    writeFileSync(join(dir, 'dossier.json'), JSON.stringify(meta, null, 2));
    return { ok: true, added: `link ${link}` };
  }
  const text = typeof body?.text === 'string' ? body.text : '';
  if (!text.trim()) throw new DossierError(400, 'nothing to add: give text or link');
  if (text.length > 5_000_000) throw new DossierError(413, 'over 5 MB in one go; split it');
  const title = typeof body?.title === 'string' ? body.title.trim().slice(0, 200) : '';
  const slug = (title || 'pasted').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 40) || 'pasted';
  mkdirSync(join(dir, 'inbox'), { recursive: true });
  let file = `${stamp()}-${slug}.md`;
  for (let k = 2; existsSync(join(dir, 'inbox', file)); k++) file = `${stamp()}-${slug}-${k}.md`;
  writeFileSync(join(dir, 'inbox', file), (title ? `# ${title}\n\n` : '') + text.trim() + '\n');
  return { ok: true, added: file };
}

function startDossierRun(root: string, rawName: unknown) {
  const name = dossierName(rawName);
  dossierMeta(root, name);
  if (running.has(name)) throw new DossierError(409, `${name} is already sorting`);
  const python = process.env.DRH_PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
  const log = join(dossierDir(root, name), 'run.log');
  writeFileSync(log, '');
  const child = spawn(python, [join(root, 'scripts', 'dossier.py'), 'run', name], { cwd: root, windowsHide: true });
  running.set(name, Date.now());
  const append = (b: Buffer) => { try { writeFileSync(log, b, { flag: 'a' }); } catch { /* log only */ } };
  child.stdout.on('data', append);
  child.stderr.on('data', append);
  child.on('error', (e) => { append(Buffer.from(`could not start ${python}: ${e.message}\n`)); running.delete(name); });
  child.on('close', () => running.delete(name));
  return { ok: true, started: name };
}

function readDossier(root: string, rawName: unknown) {
  const name = dossierName(rawName);
  const dir = dossierDir(root, name);
  const meta = dossierMeta(root, name);
  let inbox: string[] = [];
  try { inbox = readdirSync(join(dir, 'inbox')).sort(); } catch { /* empty */ }
  let log = '';
  try { log = readFileSync(join(dir, 'run.log'), 'utf-8').slice(-4000); } catch { /* not run */ }
  const status = readJson(join(dir, 'status.json'));
  return { meta, inbox, status: running.has(name) ? { ...(status || {}), state: 'running' } : status,
    log, ledger: readJson(join(dir, 'ledger.json')) };
}

/** The dossier as an agent reads it: sections strongest-first, then what was cut and why. */
function dossierForAgent(root: string, rawName: unknown, opts: { section?: unknown; cut?: unknown; limit?: unknown }) {
  const d = readDossier(root, rawName);
  const L = d.ledger;
  const base = { name: d.meta.name, topic: d.meta.topic, workflow: d.meta.workflow, state: d.status?.state ?? 'not run',
    dump: { files: d.inbox.length, links: d.meta.links } };
  if (!L) return { ...base, note: 'not sorted yet: call drh_dossier_run' };
  const limit = Math.min(Math.max(Number(opts.limit) || 25, 1), 200);
  const pill = (p: any) => ({ id: p.id, kind: p.kind, text: p.text, quote: p.quote, who: p.who, when: p.when,
    source: p.title || p.source, ...(p.state === 'cut' ? { reason: p.reason, lost_to: p.of, note: p.note } : {}) });
  const sections = L.sections
    .filter((s: any) => !opts.section || s.id === opts.section)
    .map((s: any) => {
      const here = L.pills.filter((p: any) => p.state === 'placed' && p.section === s.id).sort((a: any, b: any) => (a.rank ?? 999) - (b.rank ?? 999));
      return { id: s.id, label: s.label, notes: s.notes, count: here.length, pills: here.slice(0, limit).map(pill) };
    });
  const cut = L.pills.filter((p: any) => p.state === 'cut');
  return { ...base, run: L.run, counts: L.counts, sections,
    cut: opts.cut ? cut.slice(0, limit).map(pill) : { count: cut.length, note: 'pass cut: true to list them' },
    unsorted: L.pills.filter((p: any) => p.state === 'unsorted').slice(0, limit).map(pill) };
}

function send(res: Response, fn: () => unknown) {
  try { res.json(fn()); }
  catch (e: any) { res.status(e instanceof DossierError ? e.status : 500).json({ error: e.message }); }
}

function noRoot(): never {
  throw new DossierError(503, 'Deep Research Hub folder not found; set DRH_ROOT');
}

const plugin = {
  name: '@openwriter/plugin-drh',
  version: '0.1.0',
  description: 'Deep Research Hub: story checklist, paragraph stats, research cards and dossiers, in the right rail and as agent tools.',
  category: 'productivity',
  configSchema: {
    hubRoot: { type: 'string' as const, env: 'DRH_ROOT', description: 'Deep Research Hub folder (default: found by walking up from the plugin)' },
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


    // Dossiers (the Dossier tab).
    const r = () => root || noRoot();
    ctx.app.get('/api/drh/workflows', (_req: Request, res: Response) => send(res, () => ({ workflows: listWorkflows(r()) })));
    ctx.app.get('/api/drh/dossiers', (_req: Request, res: Response) => send(res, () => ({ dossiers: listDossiers(r()) })));
    ctx.app.post('/api/drh/dossiers', (req: Request, res: Response) => send(res, () => createDossier(r(), req.body)));
    ctx.app.get('/api/drh/dossiers/:name', (req: Request, res: Response) => send(res, () => readDossier(r(), req.params.name)));
    ctx.app.post('/api/drh/dossiers/:name/add', (req: Request, res: Response) => send(res, () => addToDossier(r(), req.params.name, req.body)));
    ctx.app.post('/api/drh/dossiers/:name/run', (req: Request, res: Response) => send(res, () => startDossierRun(r(), req.params.name)));

    ctx.app.get('/api/drh/research', (req: Request, res: Response) => {
      if (!root) return res.status(503).json({ error: 'Deep Research Hub folder not found; set DRH_ROOT' });
      const q = typeof req.query.q === 'string' ? req.query.q.slice(0, 500) : '';
      res.json({ q, cards: researchCards(root, q) });
    });
  },

  /** The same dossier functions for an agent connected to OpenWriter's MCP server. */
  mcpTools(config: Record<string, string>) {
    const r = () => findHubRoot(config.hubRoot) || noRoot();
    const wrap = (fn: (a: any) => unknown) => async (a: Record<string, unknown>) => {
      try { return fn(a); } catch (e: any) { return { error: e.message }; }
    };
    const NAME = { type: 'string', description: 'dossier name (letters, digits, _ . -)' };
    return [
      { name: 'drh_dossier_list', description: 'List the Deep Research Hub dossiers (topic, workflow, last sort state) and the saved workflows.',
        inputSchema: { type: 'object', properties: {} },
        handler: wrap(() => ({ dossiers: listDossiers(r()), workflows: listWorkflows(r()) })) },
      { name: 'drh_dossier_create', description: 'Make a new dossier: a folder that collects everything on one topic, to be sorted (not written up) into the sections of a saved workflow.',
        inputSchema: { type: 'object', properties: { name: NAME, topic: { type: 'string', description: 'what the dossier is about' },
          workflow: { type: 'string', description: 'saved workflow id; default "default"' } }, required: ['name'] },
        handler: wrap((a) => createDossier(r(), a)) },
      { name: 'drh_dossier_add', description: 'Add material to a dossier\'s dump. Either text (notes, a transcript, an article, research you gathered; any size up to 5 MB per call, call again for more) or link: a hub path under data/ (a Deep Research run folder, a Targeted Research run folder, a YouTube transcript file; find them with drh_research_search). Keep the material as found: the sort quotes it word for word.',
        inputSchema: { type: 'object', properties: { name: NAME, text: { type: 'string' }, title: { type: 'string', description: 'what this piece is (shown as its source)' },
          link: { type: 'string', description: 'e.g. data/deep_research/<job>/<stamp>' } }, required: ['name'] },
        handler: wrap((a) => addToDossier(r(), a.name, a)) },
      { name: 'drh_dossier_run', description: 'Sort the dossier\'s dump: every source is broken into pills tied to its own words, then each pill is placed in a section or cut with a reason. Only new or changed sources are read again. Runs in the background; poll drh_dossier_read until state is done.',
        inputSchema: { type: 'object', properties: { name: NAME }, required: ['name'] },
        handler: wrap((a) => startDossierRun(r(), a.name)) },
      { name: 'drh_dossier_read', description: 'Read a sorted dossier: counts, each section\'s pills strongest first (text, verbatim quote, who, when, source) and notes on what the section is missing; what was cut and why with cut: true; what is unsorted.',
        inputSchema: { type: 'object', properties: { name: NAME, section: { type: 'string', description: 'only this section id' },
          cut: { type: 'boolean', description: 'list the cut pills with their reasons' }, limit: { type: 'number', description: 'pills per section (default 25, max 200)' } }, required: ['name'] },
        handler: wrap((a) => dossierForAgent(r(), a.name, a)) },
      { name: 'drh_research_search', description: 'Find research already in the Deep Research Hub on a topic: Deep Research runs, Targeted Research facts, YouTube transcripts. Each result has a link to pass to drh_dossier_add.',
        inputSchema: { type: 'object', properties: { q: { type: 'string' } }, required: ['q'] },
        handler: wrap((a) => ({ cards: researchCards(r(), String(a.q || '').slice(0, 500)).map(({ kind, title, detail, link }) => ({ kind, title, detail, link })) })) },
    ];
  },
};

export default plugin;
