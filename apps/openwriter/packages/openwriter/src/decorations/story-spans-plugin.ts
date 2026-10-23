/**
 * ProseMirror plugin: highlights "story spans" — stretches of the doc that a
 * story JSON (see plugins/drh /api/drh/story) offers rewrite variants for.
 *
 * Spans are matched by whitespace-normalized text (both the doc text and the
 * anchor collapse whitespace runs to single spaces), so soft line breaks and
 * paragraph boundaries inside an anchor still match. Each span renders as
 * `Decoration.inline` with class `story-span story-span--<state>`:
 * idle (subtle), active (the span the Story tab is cycling), resolved (a
 * variant was chosen or the original kept).
 *
 * The React side drives it through the module-level helpers below, the same
 * way comments-plugin.ts is driven (set data + force refresh).
 */

import { Plugin, PluginKey, TextSelection } from '@tiptap/pm/state';
import { Decoration, DecorationSet } from '@tiptap/pm/view';
import type { Editor } from '@tiptap/react';

export type StorySpanStatus = 'idle' | 'active' | 'resolved';

export interface StorySpanState {
  spanId: string;
  /** The text this span is currently anchored to (the chosen variant's text
   *  after "Use this version", so the highlight follows the edit). */
  anchor: string;
  state: StorySpanStatus;
}

export const storySpanDecorationKey = new PluginKey('storySpanDecoration');

let currentSpans: StorySpanState[] = [];

/** Collapse every whitespace run to one space and trim — both sides of a
 *  match go through this, so anchors survive reflows and pasted formatting. */
export function normalizeWs(text: string): string {
  return text.replace(/\s+/g, ' ').trim();
}

interface NormChar { ch: string; pos: number | null }

/**
 * Flatten the doc to normalized text, remembering the doc position of every
 * kept character (null for synthetic separators between textblocks). This is
 * what lets a normalized match map back to a real document range.
 */
function flattenDoc(doc: any): { text: string; chars: NormChar[] } {
  const chars: NormChar[] = [];
  let firstBlock = true;
  const pushSpace = (pos: number | null) => {
    if (chars.length && chars[chars.length - 1].ch === ' ') return;
    chars.push({ ch: ' ', pos });
  };
  doc.descendants((node: any, pos: number) => {
    if (node.isTextblock) {
      if (!firstBlock) pushSpace(null);
      firstBlock = false;
      return true;
    }
    if (!node.isText || !node.text) return true;
    for (let i = 0; i < node.text.length; i++) {
      const ch = node.text[i];
      if (/\s/.test(ch)) pushSpace(pos + i);
      else chars.push({ ch, pos: pos + i });
    }
    return false;
  });
  while (chars.length && chars[0].ch === ' ') chars.shift();
  while (chars.length && chars[chars.length - 1].ch === ' ') chars.pop();
  return { text: chars.map((c) => c.ch).join(''), chars };
}

/**
 * Find an anchor in the doc by whitespace-normalized match. Returns the doc
 * range and its current text, or null when the words are no longer there.
 * Same matching as the decorations, so rail and editor always agree.
 */
export function findStorySpanRange(doc: any, anchor: string): { from: number; to: number; text: string } | null {
  const needle = normalizeWs(anchor);
  if (!needle) return null;
  const { text, chars } = flattenDoc(doc);
  const idx = text.indexOf(needle);
  if (idx === -1) return null;
  const hit = chars.slice(idx, idx + needle.length).filter((c) => c.pos !== null);
  if (!hit.length) return null;
  const from = hit[0].pos!;
  const to = hit[hit.length - 1].pos! + 1;
  return { from, to, text: doc.textBetween(from, to, ' ', ' ') };
}

function buildStorySpanDecorations(doc: any, spans: StorySpanState[] = currentSpans): DecorationSet {
  if (spans.length === 0) return DecorationSet.empty;
  const decorations: Decoration[] = [];
  const { text, chars } = flattenDoc(doc);
  const used = new Set<number>();
  for (const span of spans) {
    const needle = normalizeWs(span.anchor);
    if (!needle) continue;
    let idx = text.indexOf(needle);
    while (idx !== -1 && used.has(idx)) idx = text.indexOf(needle, idx + 1);
    if (idx === -1) continue;
    used.add(idx);
    const hit = chars.slice(idx, idx + needle.length).filter((c) => c.pos !== null);
    if (!hit.length) continue;
    const from = hit[0].pos!;
    const to = hit[hit.length - 1].pos! + 1;
    if (from >= to) continue;
    decorations.push(
      Decoration.inline(from, to, {
        nodeName: 'span',
        class: `story-span story-span--${span.state}`,
        'data-story-span': span.spanId,
      }),
    );
  }
  return DecorationSet.create(doc, decorations);
}

export function createStorySpanDecorationPlugin(): Plugin {
  return new Plugin({
    key: storySpanDecorationKey,

    state: {
      init(_, state) {
        return buildStorySpanDecorations(state.doc);
      },
      apply(tr, oldSet, _oldState, newState) {
        if (tr.docChanged || tr.getMeta('forceStorySpanUpdate')) {
          return buildStorySpanDecorations(newState.doc);
        }
        return oldSet.map(tr.mapping, tr.doc);
      },
    },

    props: {
      decorations(state) {
        return this.getState(state);
      },
    },
  });
}

export function forceStorySpanRefresh(view: any): void {
  const { state, dispatch } = view;
  dispatch(state.tr.setMeta('forceStorySpanUpdate', true));
}

/** Load (or replace) the spans of the currently imported story. */
export function setStorySpans(editor: Editor, spans: { spanId: string; anchor: string }[]): void {
  currentSpans = spans.map((s) => ({ spanId: s.spanId, anchor: s.anchor, state: 'idle' as StorySpanStatus }));
  forceStorySpanRefresh(editor.view);
}

/** Mark one span active (the one the cycler is open on) and scroll it into view. */
export function activateStorySpan(editor: Editor, spanId: string): void {
  currentSpans = currentSpans.map((s) =>
    s.spanId === spanId ? { ...s, state: 'active' as StorySpanStatus }
      : s.state === 'active' ? { ...s, state: 'idle' as StorySpanStatus }
      : s);
  const span = currentSpans.find((s) => s.spanId === spanId);
  const range = span && findStorySpanRange(editor.state.doc, span.anchor);
  if (range) {
    const tr = editor.state.tr.setSelection(TextSelection.create(editor.state.doc, range.from));
    editor.view.dispatch(tr.scrollIntoView());
  }
  forceStorySpanRefresh(editor.view);
}

/** Mark a span resolved. `newAnchor` retargets the span after "Use this
 *  version" replaced the text, so the highlight keeps following it. */
export function resolveStorySpan(editor: Editor, spanId: string, newAnchor?: string): void {
  currentSpans = currentSpans.map((s) =>
    s.spanId === spanId
      ? { ...s, state: 'resolved' as StorySpanStatus, anchor: newAnchor ?? s.anchor }
      : s);
  forceStorySpanRefresh(editor.view);
}

/** Drop all spans (story cleared, or the Story tab unmounted). */
export function clearStorySpans(editor: Editor): void {
  if (!currentSpans.length) return;
  currentSpans = [];
  forceStorySpanRefresh(editor.view);
}
