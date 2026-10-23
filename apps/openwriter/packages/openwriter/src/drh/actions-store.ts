/**
 * API calls — preset actions on the whole doc (prompts/W_actions.json) plus
 * the writer's own (data/writer/actions.json), run from the left column's
 * "API calls" section and the right rail's APIs tab. One store so both show
 * the same list, the same running state and the same last result.
 *
 *   output 'edits'  changes land in the doc as pending rewrites (ai-edits.ts)
 *   output 'notes'  a scored report; every issue is saved as an OpenWriter
 *                   comment on the quoted words, so it sits on the text itself
 *
 * App feeds the active editor/filename/title in with setActionContext.
 * Added in the Deep Research Hub copy; see apps/openwriter/UPSTREAM.md.
 */
import { useSyncExternalStore } from 'react';
import type { Editor } from '@tiptap/core';
import { collectParagraphs, selectedParagraphKeys, landEdits, revealNode, type LandedEdit } from './ai-edits';

export interface ApiAction {
  id: string;
  label: string;
  description: string;
  output: 'edits' | 'notes';
  builtIn: boolean;
  prompt?: string;
  model?: string;
}

export interface Issue {
  title: string; quote: string; issue: string; next_step: string;
  anchor: { id: string; quote: string } | null;
}
export interface Report {
  overall: { score: number | null; summary: string; grade: string };
  rubric: { name: string; score: number | null; note: string }[];
  sections: { title: string; score: number | null; basis: string; critique: string; issues: Issue[] }[];
}

export interface ActionResult {
  actionId: string;
  label: string;
  filename: string;
  model: string;
  reply: string;
  output: 'edits' | 'notes';
  report?: Report;
  pinned?: number;
  landed?: LandedEdit[];
  at: string;
}

interface State {
  actions: ApiAction[] | null;
  error: string;
  running: string | null;
  runError: string;
  last: ActionResult | null;
  /** The APIs tab's composer: null = closed, 'new', or the id of one of yours. */
  composing: string | null;
}

let state: State = { actions: null, error: '', running: null, runError: '', last: null, composing: null };
const listeners = new Set<() => void>();
const set = (patch: Partial<State>) => { state = { ...state, ...patch }; listeners.forEach((l) => l()); };

export function useActions(): State {
  return useSyncExternalStore((l) => { listeners.add(l); return () => listeners.delete(l); }, () => state);
}

// ── context from App ────────────────────────────────────────────────────────
let ctx: { editor: Editor | null; filename: string; topic: string } = { editor: null, filename: '', topic: '' };
export function setActionContext(next: typeof ctx) {
  const docChanged = next.filename !== ctx.filename;
  ctx = next;
  if (docChanged) set({ last: loadLast(next.filename), runError: '' });
}
export function getActionEditor(): Editor | null { return ctx.editor; }

// The last result per doc survives reloads (Fix from the rating reads it).
const lastKey = (filename: string) => `drh-api-last:${filename}`;
function loadLast(filename: string): ActionResult | null {
  try { return JSON.parse(localStorage.getItem(lastKey(filename)) || 'null'); } catch { return null; }
}
function saveLast(r: ActionResult) {
  try { localStorage.setItem(lastKey(r.filename), JSON.stringify(r)); } catch { /* storage off */ }
}
function lastRating(filename: string): ActionResult | null {
  try { return JSON.parse(localStorage.getItem(`drh-api-rating:${filename}`) || 'null'); } catch { return null; }
}

/** A report as plain text: what Fix from the rating gets as its earlier result. */
export function reportToText(r: Report): string {
  const lines: string[] = [];
  if (r.overall.score != null) lines.push(`Overall: ${r.overall.score}/100 ${r.overall.grade}`.trim());
  if (r.overall.summary) lines.push(r.overall.summary);
  for (const s of r.sections) {
    lines.push('', `## ${s.title}${s.score != null ? ` — ${s.score}/100` : ''}`);
    if (s.basis) lines.push(`Basis: ${s.basis}`);
    if (s.critique) lines.push(s.critique);
    for (const i of s.issues) {
      lines.push(`- ${i.title}${i.anchor ? ` [${i.anchor.id}]` : ''}`, `  Text: "${i.quote}"`, `  Issue: ${i.issue}`, `  Next step: ${i.next_step}`);
    }
  }
  return lines.join('\n');
}

export function openComposer(id: string | null = 'new') { set({ composing: id }); }

// ── list / save / delete ────────────────────────────────────────────────────
async function json(r: Response) {
  const type = r.headers.get('content-type') || '';
  if (r.status === 404 && !type.includes('json')) throw new Error('Enable the Deep Research Hub plugin in the Plugins tab, then restart OpenWriter.');
  const b = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(b.error || r.statusText);
  return b;
}

export async function loadActions() {
  try {
    const b = await json(await fetch('/api/drh/actions'));
    set({ actions: b.actions || [], error: '' });
  } catch (e: any) {
    set({ actions: null, error: e.message });
  }
}

export async function saveAction(a: Partial<ApiAction> & { label: string; prompt: string }) {
  const b = await json(await fetch('/api/drh/actions', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(a),
  }));
  await loadActions();
  return b.action as ApiAction;
}

export async function deleteAction(id: string) {
  await json(await fetch(`/api/drh/actions?id=${encodeURIComponent(id)}`, { method: 'DELETE' }));
  await loadActions();
}

// ── run ─────────────────────────────────────────────────────────────────────
export async function runAction(action: ApiAction, extra = '') {
  const { editor, filename, topic } = ctx;
  if (!editor || state.running) return;
  const paras = collectParagraphs(editor);
  if (!paras.length) { set({ runError: 'The document is empty.' }); return; }
  let context = '';
  if (action.id === 'fix_from_rating') {
    const rating = lastRating(filename);
    if (!rating?.report) { set({ runError: 'Run Rate on this doc first — Fix works from its report.' }); return; }
    context = reportToText(rating.report);
  }
  set({ running: action.id, runError: '' });
  try {
    const b = await json(await fetch('/api/drh/action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action: action.id,
        paragraphs: paras.map((p) => ({ id: p.key, kind: p.kind, text: p.text })),
        editable: selectedParagraphKeys(editor, paras),
        extra,
        context,
        topic,
      }),
    }));
    const model = b.model || '';
    const result: ActionResult = {
      actionId: action.id, label: action.label, filename, model, reply: b.reply || '', output: b.output, at: new Date().toISOString(),
    };
    if (b.output === 'notes' && b.report) {
      result.report = b.report as Report;
      result.pinned = await pinIssues(filename, paras, result.report, action.label, model);
      try { localStorage.setItem(`drh-api-rating:${filename}`, JSON.stringify(result)); } catch { /* storage off */ }
    } else {
      result.landed = landEdits(editor, paras, b.edits || [], action.label, model);
      if (result.landed[0]) revealNode(editor, result.landed[0].nodeId);
    }
    saveLast(result);
    set({ last: result });
  } catch (e: any) {
    set({ runError: e?.message || 'Failed' });
  } finally {
    set({ running: null });
  }
}

/** Save each issue as a comment on its quoted words; returns how many landed. */
async function pinIssues(filename: string, paras: ReturnType<typeof collectParagraphs>, report: Report, label: string, model: string): Promise<number> {
  if (!filename) return 0;
  const byKey = new Map(paras.map((p) => [p.key, p.nodeId]));
  const short = model.replace(/^[^/]+\//, '');
  let n = 0;
  for (const s of report.sections) {
    for (const i of s.issues) {
      const nodeId = i.anchor ? byKey.get(i.anchor.id) : undefined;
      if (!i.anchor || !nodeId) continue;
      const note = [
        `${label} · ${s.title}${s.score != null ? ` · ${s.score}/100` : ''} · API ${short}`,
        i.title ? `${i.title}: ${i.issue}` : i.issue,
        i.next_step ? `Next step: ${i.next_step}` : '',
      ].filter(Boolean).join('\n');
      try {
        const r = await fetch('/api/comments', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ filename, text: i.anchor.quote, note, nodeId }),
        });
        if (r.ok) n++;
      } catch { /* keep going */ }
    }
  }
  return n;
}

/** Scroll to the paragraph an issue is pinned on. */
export function revealIssue(i: Issue) {
  const editor = ctx.editor;
  if (!editor || !i.anchor) return;
  const paras = collectParagraphs(editor);
  // Keys shift when the doc changes; fall back to finding the quote.
  const hit = paras.find((p) => p.text.replace(/\*\*|\*|`/g, '').includes(i.anchor!.quote)) ?? paras.find((p) => p.key === i.anchor!.id);
  if (hit) revealNode(editor, hit.nodeId);
}
