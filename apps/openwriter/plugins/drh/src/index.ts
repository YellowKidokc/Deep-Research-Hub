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
 *
 * Everything lives in the hub's plain files, never in OpenWriter's state:
 *   <hub>/prompts/W_story_checklist.json     the checklist definition
 *   <hub>/data/writer/checklists/<docId>.json  ticks per document
 *   <hub>/data/deep_research/<job>/<stamp>/    research runs (drh_queue.py)
 *   <hub>/data/youtube/<Channel>/<Title>.md    transcripts (ytgrab.py)
 *
 * The hub root is DRH_ROOT, or found by walking up from this file.
 */
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

const plugin = {
  name: '@openwriter/plugin-drh',
  version: '0.1.0',
  description: 'Deep Research Hub: story checklist, paragraph stats and research cards for the right rail.',
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

    ctx.app.get('/api/drh/research', (req: Request, res: Response) => {
      if (!root) return res.status(503).json({ error: 'Deep Research Hub folder not found; set DRH_ROOT' });
      const q = typeof req.query.q === 'string' ? req.query.q.slice(0, 500) : '';
      res.json({ q, cards: researchCards(root, q) });
    });
  },
};

export default plugin;
