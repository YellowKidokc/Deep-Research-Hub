/**
 * AI edits for the Deep Research Hub copy of OpenWriter: the Story tab's Run
 * and the chat column both send the doc to POST /api/drh/revise and land the
 * reply's edits here, in the document itself, as pending rewrites (blue, with
 * the original kept for review).
 *
 * Every landed edit is labelled (who asked, which model, why) in a small store
 * keyed by node id; the ai-edit-badges decoration plugin reads it to outline
 * the paragraph and show its "API · model" badge with Original ⇄ AI, accept
 * and reject. The store is per browser (localStorage), best effort.
 *
 * Added in the Deep Research Hub copy; see apps/openwriter/UPSTREAM.md.
 */
import type { Editor, JSONContent } from '@tiptap/core';
import { applyInsert, applyRewrite, applyDelete, findNodeById } from '../decorations/apply';
import { acceptChange, rejectChange } from '../decorations/resolve';
import { setPreviewState, isPreviewActive, getPreviewNodeId, getSavedModifiedContent } from '../decorations/plugin';

// ============================================================================
// LABEL STORE
// ============================================================================

export interface AiEditLabel { source: string; model: string; why: string; at: string }

const STORE_KEY = 'drh-ai-edits';
const labels = new Map<string, AiEditLabel>();
try {
  const raw = JSON.parse(localStorage.getItem(STORE_KEY) || '{}');
  for (const [id, v] of Object.entries(raw)) labels.set(id, v as AiEditLabel);
} catch { /* storage off */ }

function persist() {
  try {
    // Keep the newest 500; old labels for long-resolved paragraphs are dead weight.
    const entries = [...labels.entries()].sort((a, b) => b[1].at.localeCompare(a[1].at)).slice(0, 500);
    localStorage.setItem(STORE_KEY, JSON.stringify(Object.fromEntries(entries)));
  } catch { /* storage off */ }
}

export function getAiEditLabel(nodeId: string): AiEditLabel | undefined { return labels.get(nodeId); }

export function recordAiEdit(nodeId: string, label: Omit<AiEditLabel, 'at'>) {
  labels.set(nodeId, { ...label, at: new Date().toISOString() });
  persist();
}

// ============================================================================
// DOC → PARAGRAPHS (what the model sees)
// ============================================================================

export interface DocParagraph { key: string; nodeId: string; kind: string; text: string }

/** Inline content as light markdown, so bold/italic/links survive a rewrite. */
function inlineToMarkdown(node: any): string {
  let out = '';
  node.forEach((child: any) => {
    if (child.isText) {
      let t = child.text as string;
      const marks = child.marks.map((m: any) => m.type.name);
      if (marks.includes('code')) t = '`' + t + '`';
      if (marks.includes('italic')) t = `*${t}*`;
      if (marks.includes('bold')) t = `**${t}**`;
      const link = child.marks.find((m: any) => m.type.name === 'link');
      if (link?.attrs?.href) t = `[${t}](${link.attrs.href})`;
      out += t;
    } else if (child.type.name === 'hardBreak') {
      out += '\n';
    }
  });
  return out;
}

/** Light markdown back to inline JSON content: **bold**, *italic*, `code`, [text](url), line breaks. */
export function markdownToInline(text: string): JSONContent[] {
  const out: JSONContent[] = [];
  const re = /\*\*([^*]+)\*\*|\*([^*\n]+)\*|`([^`]+)`|\[([^\]]+)\]\(([^)\s]+)\)|\n/g;
  let last = 0;
  let m: RegExpExecArray | null;
  const push = (t: string, marks?: any[]) => { if (t) out.push(marks?.length ? { type: 'text', text: t, marks } : { type: 'text', text: t }); };
  while ((m = re.exec(text))) {
    push(text.slice(last, m.index));
    if (m[1] !== undefined) {
      // Bold may wrap italic or a link; one level of nesting is enough here.
      for (const n of markdownToInline(m[1])) out.push({ ...n, marks: [...(n.marks ?? []), { type: 'bold' }] });
    } else if (m[2] !== undefined) push(m[2], [{ type: 'italic' }]);
    else if (m[3] !== undefined) push(m[3], [{ type: 'code' }]);
    else if (m[4] !== undefined) {
      for (const n of markdownToInline(m[4])) out.push({ ...n, marks: [...(n.marks ?? []), { type: 'link', attrs: { href: m[5] } }] });
    } else out.push({ type: 'hardBreak' });
    last = re.lastIndex;
  }
  push(text.slice(last));
  return out;
}

/**
 * Text blocks (paragraphs, headings) with ids, in doc order, keyed p1…pN.
 * Pending deletes are left out — they are on their way out.
 */
export function collectParagraphs(editor: Editor): DocParagraph[] {
  const paras: DocParagraph[] = [];
  editor.state.doc.descendants((node: any, _pos: number, parent: any) => {
    if (!node.isTextblock) return true;
    if (node.type.name === 'codeBlock') return false;
    const id = node.attrs?.id;
    const text = inlineToMarkdown(node).trim();
    if (!id || !text || node.attrs?.pendingStatus === 'delete') return false;
    const kind = node.type.name === 'heading' ? `heading ${node.attrs.level ?? ''}`.trim()
      : parent?.type?.name === 'listItem' || parent?.type?.name === 'taskItem' ? 'list item'
      : parent?.type?.name === 'blockquote' ? 'quote' : '';
    paras.push({ key: `p${paras.length + 1}`, nodeId: id, kind, text });
    return false;
  });
  return paras;
}

/** Keys of the paragraphs the current selection touches (empty when nothing is selected). */
export function selectedParagraphKeys(editor: Editor, paras: DocParagraph[]): string[] {
  const { from, to } = editor.state.selection;
  if (from === to) return [];
  const ids = new Set<string>();
  editor.state.doc.nodesBetween(from, to, (node: any) => {
    if (node.isTextblock && node.attrs?.id) ids.add(node.attrs.id);
    return !node.isTextblock;
  });
  return paras.filter((p) => ids.has(p.nodeId)).map((p) => p.key);
}

// ============================================================================
// CALL + LAND
// ============================================================================

export interface ReviseEdit { id: string; text: string; why: string }
export interface ReviseResult { reply: string; edits: ReviseEdit[]; model: string }

export async function requestRevise(body: Record<string, unknown>, signal?: AbortSignal): Promise<ReviseResult> {
  const r = await fetch('/api/drh/revise', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  });
  const type = r.headers.get('content-type') || '';
  if (r.status === 404 || !type.includes('json')) {
    throw new Error('Enable the Deep Research Hub plugin in the Plugins tab, then restart OpenWriter.');
  }
  const b = await r.json();
  if (!r.ok) throw new Error(b.error || r.statusText);
  return { reply: b.reply || '', edits: Array.isArray(b.edits) ? b.edits : [], model: b.model || '' };
}

export interface LandedEdit { nodeId: string; key: string; why: string; kind: 'rewrite' | 'delete' | 'split' }

/**
 * Land edits as pending changes. Each keeps its block type (and heading
 * level); a blank line in the text splits it, the extra blocks arriving as
 * pending inserts after it. An empty text proposes a delete.
 */
export function landEdits(editor: Editor, paras: DocParagraph[], edits: ReviseEdit[], source: string, model: string): LandedEdit[] {
  stopAiPreview(editor);
  const byKey = new Map(paras.map((p) => [p.key, p]));
  const landed: LandedEdit[] = [];
  for (const e of edits) {
    const para = byKey.get(e.id);
    if (!para) continue;
    const found = findNodeById(editor, para.nodeId);
    if (!found) continue;
    const { node } = found;
    const label = { source, model, why: e.why };
    if (!e.text.trim()) {
      recordAiEdit(para.nodeId, label);
      if (applyDelete(editor, para.nodeId).success) {
        landed.push({ nodeId: para.nodeId, key: e.id, why: e.why, kind: 'delete' });
      }
      continue;
    }
    const attrs = node.type.name === 'heading' ? { level: node.attrs.level } : {};
    const blocks = e.text.split(/\n\s*\n/).map((t) => t.trim()).filter(Boolean);
    const first: JSONContent = { type: node.type.name, attrs, content: markdownToInline(blocks[0]) };
    // Label first: the badge plugin reads it while the rewrite's transaction renders.
    recordAiEdit(para.nodeId, label);
    if (!applyRewrite(editor, para.nodeId, first).success) continue;
    if (blocks.length > 1) {
      const extra: JSONContent[] = blocks.slice(1).map((t) => ({ type: 'paragraph', content: markdownToInline(t) }));
      const ins = applyInsert(editor, { afterNodeId: para.nodeId }, extra);
      // Label the inserted blocks too: they sit right after the rewritten one.
      if (ins.success) {
        const after = findNodeById(editor, para.nodeId);
        if (after) {
          let pos = after.pos + after.node.nodeSize;
          for (let i = 0; i < extra.length; i++) {
            const n = editor.state.doc.nodeAt(pos);
            if (!n) break;
            if (n.attrs?.id) recordAiEdit(n.attrs.id, label);
            pos += n.nodeSize;
          }
        }
      }
    }
    landed.push({ nodeId: para.nodeId, key: e.id, why: e.why, kind: blocks.length > 1 ? 'split' : 'rewrite' });
  }
  if (landed.length) {
    refreshBadges(editor);
    window.dispatchEvent(new CustomEvent('ow-pending-write-applied'));
  }
  return landed;
}

/** Re-render decorations without touching the doc (labels/preview state changed). */
export function refreshBadges(editor: Editor) {
  if (editor.isDestroyed) return;
  editor.view.dispatch(editor.state.tr.setMeta('aiEditRefresh', true).setMeta('addToHistory', false));
}

/** Scroll a paragraph into view and flash it. */
export function revealNode(editor: Editor, nodeId: string) {
  const found = findNodeById(editor, nodeId);
  if (!found) return;
  const dom = editor.view.nodeDOM(found.pos) as HTMLElement | null;
  if (!dom?.scrollIntoView) return;
  dom.scrollIntoView({ behavior: 'smooth', block: 'center' });
  dom.classList.add('ai-edit-flash');
  setTimeout(() => dom.classList.remove('ai-edit-flash'), 1200);
}

// ============================================================================
// ORIGINAL ⇄ AI, ACCEPT, REJECT (the badge's buttons)
// ============================================================================

/** Swap a node's content in place, keeping its pending attrs (mirrors the Review tab). */
function replaceNodeContent(editor: Editor, nodeId: string, newContent: any): boolean {
  const found = findNodeById(editor, nodeId);
  if (!found) return false;
  const { pos, node } = found;
  const replacement = {
    type: newContent.type || node.type.name,
    attrs: {
      ...(newContent.attrs || {}),
      id: node.attrs.id,
      pendingStatus: node.attrs.pendingStatus,
      pendingOriginalContent: node.attrs.pendingOriginalContent,
      pendingSelectionFrom: node.attrs.pendingSelectionFrom,
      pendingSelectionTo: node.attrs.pendingSelectionTo,
      pendingOriginalFrom: node.attrs.pendingOriginalFrom,
      pendingOriginalTo: node.attrs.pendingOriginalTo,
    },
    content: newContent.content,
  };
  try {
    editor.chain()
      .command(({ tr }) => { tr.setMeta('addToHistory', false); return true; })
      .deleteRange({ from: pos, to: pos + node.nodeSize })
      .insertContentAt(pos, replacement)
      .run();
    return true;
  } catch { return false; }
}

export function isShowingOriginal(nodeId: string): boolean {
  return isPreviewActive() && getPreviewNodeId() === nodeId;
}

/** End any single-node preview: put the AI version back. */
export function stopAiPreview(editor: Editor) {
  const nodeId = getPreviewNodeId();
  if (!isPreviewActive() || !nodeId) return;
  const modified = getSavedModifiedContent();
  if (modified && !Array.isArray(modified)) replaceNodeContent(editor, nodeId, modified);
  setPreviewState(false);
  refreshBadges(editor);
}

/** Flip one rewritten paragraph between its original and the AI version. */
export function toggleOriginal(editor: Editor, nodeId: string) {
  if (isShowingOriginal(nodeId)) { stopAiPreview(editor); return; }
  stopAiPreview(editor);
  const found = findNodeById(editor, nodeId);
  const original = found?.node.attrs?.pendingOriginalContent;
  if (!found || found.node.attrs?.pendingStatus !== 'rewrite' || !original || Array.isArray(original)) return;
  setPreviewState(true, nodeId, found.node.toJSON());
  if (!replaceNodeContent(editor, nodeId, original)) setPreviewState(false);
}

export function acceptAiEdit(editor: Editor, nodeId: string) {
  stopAiPreview(editor);
  acceptChange(editor, nodeId);
}

export function rejectAiEdit(editor: Editor, nodeId: string) {
  stopAiPreview(editor);
  rejectChange(editor, nodeId);
}
