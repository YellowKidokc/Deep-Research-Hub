/**
 * ProseMirror plugin: outlines every pending rewrite / insert in the doc and
 * pins a small badge above it — "API · <model> · <who asked>" — with
 * Original ⇄ AI, accept (✓) and reject (✕). The label comes from the drh
 * ai-edits store (Story tab Run, chat column, right-click rewrites); a pending
 * change with no label (an MCP agent write) shows as "AI edit".
 *
 * Original ⇄ AI swaps the paragraph's text in place using the same preview
 * state the Review tab uses, so the paragraph turns red-struck while showing
 * the original and the doc is not synced to disk until it flips back.
 *
 * Added in the Deep Research Hub copy; see apps/openwriter/UPSTREAM.md.
 */
import { Plugin, PluginKey } from '@tiptap/pm/state';
import { Decoration, DecorationSet } from '@tiptap/pm/view';
import type { Editor } from '@tiptap/core';
import {
  getAiEditLabel,
  isShowingOriginal,
  toggleOriginal,
  acceptAiEdit,
  rejectAiEdit,
} from '../drh/ai-edits';

export const aiEditBadgeKey = new PluginKey('aiEditBadges');

function button(text: string, title: string, cls: string, onClick: () => void): HTMLButtonElement {
  const b = document.createElement('button');
  b.type = 'button';
  b.className = `ai-edit-badge__btn ${cls}`;
  b.textContent = text;
  b.title = title;
  // mousedown would move the selection into the paragraph first.
  b.addEventListener('mousedown', (e) => { e.preventDefault(); e.stopPropagation(); });
  b.addEventListener('click', (e) => { e.preventDefault(); e.stopPropagation(); onClick(); });
  return b;
}

function shortModel(model: string): string {
  return model.replace(/^[^/]+\//, '');
}

export function createAiEditBadgePlugin(editor: Editor) {
  return new Plugin({
    key: aiEditBadgeKey,
    props: {
      decorations(state) {
        const decos: Decoration[] = [];
        const seenGroups = new Set<string>();
        state.doc.descendants((node: any, pos: number) => {
          const status = node.attrs?.pendingStatus;
          if (status !== 'rewrite' && status !== 'insert' && status !== 'delete') return true;
          const nodeId: string | undefined = node.attrs?.id;
          if (!nodeId) return true;
          const label = getAiEditLabel(nodeId);
          // Only outline leaf text blocks; wrappers (lists) would double up.
          if (!node.isTextblock && !node.isAtom) return true;

          decos.push(Decoration.node(pos, pos + node.nodeSize, {
            class: `ai-edit-outline ai-edit-outline--${status}${label ? '' : ' ai-edit-outline--unlabelled'}`,
          }));

          const groupId: string | undefined = node.attrs?.pendingGroupId;
          if (groupId) {
            if (seenGroups.has(groupId)) return false;
            seenGroups.add(groupId);
          }
          if (!node.isTextblock) return false;

          const showingOriginal = isShowingOriginal(nodeId);
          const canFlip = status === 'rewrite' && !groupId && !!node.attrs?.pendingOriginalContent;
          const text = label
            ? `API · ${shortModel(label.model) || 'model'} · ${label.source}`
            : 'AI edit';
          const key = `ai-badge-${nodeId}-${status}-${showingOriginal ? 'o' : 'm'}-${text}`;
          decos.push(Decoration.widget(pos + 1, () => {
            const wrap = document.createElement('span');
            wrap.className = `ai-edit-badge ai-edit-badge--${status}${showingOriginal ? ' is-original' : ''}`;
            wrap.contentEditable = 'false';
            const tag = document.createElement('span');
            tag.className = 'ai-edit-badge__label';
            tag.textContent = showingOriginal ? 'Original' : status === 'delete' ? `${text} · remove?` : status === 'insert' ? `${text} · added` : text;
            if (label?.why) tag.title = label.why;
            wrap.appendChild(tag);
            if (canFlip) {
              wrap.appendChild(button(
                showingOriginal ? 'Show AI ⇢' : '⇠ Original',
                showingOriginal ? 'Show the AI version again' : 'Show the original paragraph',
                'ai-edit-badge__flip',
                () => toggleOriginal(editor, nodeId),
              ));
            }
            wrap.appendChild(button('✓', 'Keep the AI version', 'ai-edit-badge__accept', () => acceptAiEdit(editor, nodeId)));
            wrap.appendChild(button('✕', 'Reject — back to the original', 'ai-edit-badge__reject', () => rejectAiEdit(editor, nodeId)));
            return wrap;
          }, { side: -1, key, ignoreSelection: true, stopEvent: () => true }));
          return false;
        });
        return DecorationSet.create(state.doc, decos);
      },
    },
  });
}
