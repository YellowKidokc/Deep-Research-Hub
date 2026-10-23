/**
 * ProseMirror plugin: highlights the target sentence while a variant session
 * is active. The highlight is an inline decoration over the exact characters
 * of the original sentence inside its paragraph.
 */
import { Plugin, PluginKey } from '@tiptap/pm/state';
import { Decoration, DecorationSet } from '@tiptap/pm/view';
import type { Editor } from '@tiptap/core';
import { getCurrentParagraphInfo, getVariantSession } from '../drh/variants-store';

export const variantDecorationKey = new PluginKey('variantDecorations');

/**
 * Map a text character offset within a node's inline content to a ProseMirror
 * document position. Mirrors pendingDecoration.ts.
 */
function mapTextOffsetToPos(node: any, nodeStartPos: number, textOffset: number): number | null {
  let charCount = 0;
  let pos = nodeStartPos + 1;
  for (let i = 0; i < node.childCount; i++) {
    const child = node.child(i);
    if (child.isText) {
      if (charCount + child.text.length >= textOffset) return pos + (textOffset - charCount);
      charCount += child.text.length;
      pos += child.nodeSize;
    } else {
      const leafLen = child.type.name === 'hardBreak' ? 1
        : (child.type.spec.leafText ? child.type.spec.leafText(child).length : 0);
      if (leafLen > 0 && charCount + leafLen >= textOffset) return pos;
      charCount += leafLen;
      pos += child.nodeSize;
    }
  }
  if (textOffset === charCount) return pos;
  return null;
}

function buildDecorations(doc: any): DecorationSet {
  const info = getCurrentParagraphInfo();
  if (!info) return DecorationSet.create(doc, []);

  const session = getVariantSession();
  if (!session) return DecorationSet.create(doc, []);
  const targetSentence = session.originalSentence;
  if (!targetSentence) return DecorationSet.create(doc, []);

  const decorations: Decoration[] = [];
  doc.descendants((node: any, pos: number) => {
    if (!node.attrs?.id || node.attrs.id !== info.nodeId) return true;
    if (!node.isTextblock) return false;
    const nodeText = node.textContent;
    const start = nodeText.indexOf(targetSentence);
    if (start < 0) return false;
    const from = mapTextOffsetToPos(node, pos, start);
    const to = mapTextOffsetToPos(node, pos, start + targetSentence.length);
    if (from !== null && to !== null && from < to) {
      decorations.push(Decoration.inline(from, to, { class: 'variant-target' }));
    }
    return false;
  });
  return DecorationSet.create(doc, decorations);
}

export function createVariantDecorationPlugin(_editor: Editor) {
  return new Plugin({
    key: variantDecorationKey,
    state: {
      init(_, state) { return buildDecorations(state.doc); },
      apply(tr, oldSet, _oldState, newState) {
        if (tr.docChanged || tr.getMeta('forceVariantRefresh')) return buildDecorations(newState.doc);
        return oldSet.map(tr.mapping, newState.doc);
      },
    },
    props: {
      decorations(state) { return this.getState(state); },
    },
  });
}

export function forceVariantRefresh(view: any): void {
  const { state, dispatch } = view;
  dispatch(state.tr.setMeta('forceVariantRefresh', true));
}
