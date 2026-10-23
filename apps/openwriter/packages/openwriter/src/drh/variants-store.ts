/**
 * Sentence Variant Explorer state.
 *
 * One active session at a time. The server generates alternatives for the key
 * sentence in a paragraph; the client highlights the original sentence and
 * shows a floating card to cycle through variants and pick one.
 */
import { useSyncExternalStore } from 'react';
import type { Editor } from '@tiptap/core';
import { replaceChangedContent, findNodeById } from '../decorations/apply';
import { collectParagraphs } from './ai-edits';

export interface Variant {
  text: string;
  why: string;
}

export interface VariantSession {
  filename: string;
  paragraphId: string;
  originalSentence: string;
  variants: Variant[];
  currentIndex: number;
  loading: boolean;
  error: string;
}

interface State {
  session: VariantSession | null;
}

let state: State = { session: null };
const listeners = new Set<() => void>();
const set = (patch: Partial<State>) => { state = { ...state, ...patch }; listeners.forEach((l) => l()); };

export function useVariants(): State {
  return useSyncExternalStore((l) => { listeners.add(l); return () => listeners.delete(l); }, () => state);
}

let ctx: { editor: Editor | null; filename: string } = { editor: null, filename: '' };
export function setVariantContext(next: typeof ctx) { ctx = next; }

async function json(r: Response) {
  const type = r.headers.get('content-type') || '';
  if (r.status === 404 && !type.includes('json')) throw new Error('Enable the Deep Research Hub plugin in the Plugins tab, then restart OpenWriter.');
  const b = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(b.error || r.statusText);
  return b;
}

export function closeVariants() {
  set({ session: null });
}

export async function startVariants(paragraphId: string, text: string, contextBefore: string[], contextAfter: string[]) {
  const { filename } = ctx;
  if (!filename) { set({ session: { filename: '', paragraphId, originalSentence: '', variants: [], currentIndex: 0, loading: false, error: 'Save the document first.' } }); return; }
  set({ session: { filename, paragraphId, originalSentence: '', variants: [], currentIndex: 0, loading: true, error: '' } });
  try {
    const docId = filename.replace(/[^A-Za-z0-9_.-]/g, '_').replace(/_{2,}/g, '_').slice(0, 128);
    const b = await json(await fetch('/api/drh/variants', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ paragraphId, text, contextBefore, contextAfter, docId }),
    }));
    const variants = (Array.isArray(b.variants) ? b.variants : []).filter((v: any) => v && typeof v.text === 'string');
    if (!variants.length) throw new Error('No variants were returned.');
    set({ session: { filename, paragraphId, originalSentence: b.originalSentence || '', variants, currentIndex: 0, loading: false, error: '' } });
  } catch (e: any) {
    set({ session: { filename, paragraphId, originalSentence: '', variants: [], currentIndex: 0, loading: false, error: e?.message || 'Failed' } });
  }
}

export function nextVariant() {
  const s = state.session;
  if (!s || s.variants.length <= 1) return;
  set({ session: { ...s, currentIndex: (s.currentIndex + 1) % s.variants.length } });
}

export function prevVariant() {
  const s = state.session;
  if (!s || s.variants.length <= 1) return;
  set({ session: { ...s, currentIndex: (s.currentIndex - 1 + s.variants.length) % s.variants.length } });
}

export function pickVariant() {
  const { editor } = ctx;
  const s = state.session;
  if (!editor || !s || s.variants.length === 0) return;
  const selected = s.variants[s.currentIndex];
  if (!selected) return;

  const found = findNodeById(editor, s.paragraphId);
  if (!found) { set({ session: { ...s, error: 'Paragraph not found.' } }); return; }

  const { node, pos } = found;
  const plain = node.textContent;
  const start = plain.indexOf(s.originalSentence);
  if (start < 0) { set({ session: { ...s, error: 'Original sentence not found in paragraph.' } }); return; }

  editor.chain().command(({ tr }) => {
    const contentStart = pos + 1;
    const before = plain.slice(0, start);
    const after = plain.slice(start + s.originalSentence.length);
    const newText = before + selected.text + after;
    const newInline = [{ type: 'text', text: newText }];
    const newNode = { type: node.type.name, attrs: node.attrs, content: newInline };
    const pmNew = editor.state.schema.nodeFromJSON(newNode);
    replaceChangedContent(tr, contentStart, node, pmNew);
    tr.setMeta('addToHistory', false);
    return true;
  }).run();

  closeVariants();
}

export function getCurrentVariant(): Variant | null {
  const s = state.session;
  if (!s || s.variants.length === 0) return null;
  return s.variants[s.currentIndex] ?? null;
}

export function getCurrentParagraphInfo() {
  const { editor } = ctx;
  const s = state.session;
  if (!editor || !s) return null;
  return collectParagraphs(editor).find((p) => p.nodeId === s.paragraphId) ?? null;
}

export function getVariantSession(): VariantSession | null { return state.session; }
