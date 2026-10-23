/**
 * Chat column — sits between the document and the right rail. Talk to the
 * model about the doc; when it changes something, the change lands in the
 * document itself as a pending rewrite (outlined, badged "API · model · Chat",
 * Original ⇄ AI, ✓/✕), never in this column. The column only keeps the talk
 * and a list of what changed, each line jumping to its paragraph.
 *
 * Scope: the whole doc, or only the paragraphs the selection touches (picked
 * automatically when there is a selection at send time).
 * Conversation kept per doc in localStorage, best effort.
 *
 * Added in the Deep Research Hub copy; see apps/openwriter/UPSTREAM.md.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import type { Editor } from '@tiptap/react';
import {
  collectParagraphs,
  selectedParagraphKeys,
  requestRevise,
  landEdits,
  revealNode,
  type LandedEdit,
} from './ai-edits';
import './ChatColumn.css';

interface Msg {
  role: 'user' | 'assistant';
  content: string;
  model?: string;
  scope?: string;
  changes?: (LandedEdit & { preview: string })[];
  error?: boolean;
}

const WIDTH_KEY = 'drh-chat-width';

function load<T>(key: string, fallback: T): T {
  try { const v = localStorage.getItem(key); return v ? JSON.parse(v) as T : fallback; } catch { return fallback; }
}
function save(key: string, value: unknown) {
  try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* storage off */ }
}

export default function ChatColumn({ editor, docKey, topic, onClose }: {
  editor: Editor | null;
  docKey: string;
  topic: string;
  onClose: () => void;
}) {
  const storeKey = `drh-chat:${docKey}`;
  const [messages, setMessages] = useState<Msg[]>(() => load(storeKey, []));
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [width, setWidth] = useState<number>(() => load(WIDTH_KEY, 360));
  const [hasSelection, setHasSelection] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Switch conversations with the doc.
  useEffect(() => { setMessages(load(storeKey, [])); }, [storeKey]);
  useEffect(() => { save(storeKey, messages.slice(-60)); }, [storeKey, messages]);
  useEffect(() => { listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' }); }, [messages, busy]);

  useEffect(() => {
    if (!editor) return;
    const onSel = () => { const { from, to } = editor.state.selection; setHasSelection(from !== to); };
    onSel();
    editor.on('selectionUpdate', onSel);
    return () => { editor.off('selectionUpdate', onSel); };
  }, [editor]);

  const startResize = useCallback((e: React.PointerEvent) => {
    e.preventDefault();
    const startX = e.clientX;
    const startW = width;
    const onMove = (ev: PointerEvent) => setWidth(Math.max(260, Math.min(720, startW + (startX - ev.clientX))));
    const onUp = () => {
      window.removeEventListener('pointermove', onMove);
      window.removeEventListener('pointerup', onUp);
      setWidth((w) => { save(WIDTH_KEY, w); return w; });
    };
    window.addEventListener('pointermove', onMove);
    window.addEventListener('pointerup', onUp);
  }, [width]);

  const send = async () => {
    const text = input.trim();
    if (!text || busy || !editor) return;
    const paras = collectParagraphs(editor);
    const editable = selectedParagraphKeys(editor, paras);
    const scope = editable.length ? `selection · ${editable.length} ¶` : 'whole doc';
    const history = messages.filter((m) => !m.error).slice(-10).map((m) => ({ role: m.role, content: m.content }));
    setMessages((ms) => [...ms, { role: 'user', content: text, scope }]);
    setInput('');
    setBusy(true);
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    try {
      const res = await requestRevise({
        mode: 'chat',
        paragraphs: paras.map((p) => ({ id: p.key, kind: p.kind, text: p.text })),
        editable,
        instruction: text,
        history,
        topic,
      }, ctrl.signal);
      const landed = landEdits(editor, paras, res.edits, 'Chat', res.model);
      const byKey = new Map(res.edits.map((e) => [e.id, e.text]));
      setMessages((ms) => [...ms, {
        role: 'assistant',
        content: res.reply || (landed.length ? 'Done.' : 'No changes.'),
        model: res.model,
        changes: landed.map((l) => ({ ...l, preview: (byKey.get(l.key) || '').replace(/[*`]/g, '').slice(0, 90) })),
      }]);
      if (landed[0]) revealNode(editor, landed[0].nodeId);
    } catch (e: any) {
      if (e?.name !== 'AbortError') setMessages((ms) => [...ms, { role: 'assistant', content: e?.message || 'Failed', error: true }]);
    } finally {
      abortRef.current = null;
      setBusy(false);
    }
  };

  return (
    <aside className="drh-chat-column" style={{ width, minWidth: width }} aria-label="Chat">
      <div className="drh-chat-resize" onPointerDown={startResize} aria-hidden="true" />
      <div className="drh-chat-head">
        <span className="drh-chat-title">Chat</span>
        <span className="drh-chat-sub">edits land in the doc</span>
        <span className="drh-chat-spacer" />
        {messages.length > 0 && (
          <button type="button" className="drh-chat-iconbtn" title="Clear this conversation" onClick={() => setMessages([])}>Clear</button>
        )}
        <button type="button" className="drh-chat-iconbtn" title="Close chat" aria-label="Close chat" onClick={onClose}>✕</button>
      </div>
      <div className="drh-chat-list" ref={listRef}>
        {messages.length === 0 && (
          <div className="drh-chat-empty">
            Ask for a change — "tighten the opening", "make ¶3 land harder", "what is this missing?".
            Select text first to work on just that part. Every change shows up outlined in the document with
            the model's name; flip <b>⇠ Original</b> to compare, then ✓ or ✕.
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`drh-chat-msg drh-chat-msg--${m.role}${m.error ? ' is-error' : ''}`}>
            {m.role === 'user' && m.scope && <div className="drh-chat-meta">{m.scope}</div>}
            <div className="drh-chat-text">{m.content}</div>
            {m.changes && m.changes.length > 0 && (
              <div className="drh-chat-changes">
                {m.changes.map((c) => (
                  <button
                    key={c.nodeId}
                    type="button"
                    className="drh-chat-change"
                    title={c.why || 'Jump to this paragraph'}
                    onClick={() => editor && revealNode(editor, c.nodeId)}
                  >
                    <span className="drh-chat-change-kind">{c.kind === 'delete' ? 'remove' : c.kind === 'split' ? 'split' : 'rewrite'}</span>
                    <span className="drh-chat-change-text">{c.preview || c.why}</span>
                  </button>
                ))}
              </div>
            )}
            {m.model && <div className="drh-chat-meta">API · {m.model.replace(/^[^/]+\//, '')}</div>}
          </div>
        ))}
        {busy && <div className="drh-chat-msg drh-chat-msg--assistant"><div className="drh-chat-text drh-chat-typing">Working on the doc…</div></div>}
      </div>
      <div className="drh-chat-compose">
        <textarea
          className="drh-chat-input"
          value={input}
          placeholder={hasSelection ? 'Change the selected part…' : 'Ask or tell it what to change…'}
          rows={3}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
          }}
        />
        <div className="drh-chat-compose-row">
          <span className="drh-chat-scope">{hasSelection ? 'Scope: selection' : 'Scope: whole doc'}</span>
          {busy
            ? <button type="button" className="drh-chat-send" onClick={() => abortRef.current?.abort()}>Stop</button>
            : <button type="button" className="drh-chat-send" disabled={!input.trim() || !editor} onClick={send}>Send</button>}
        </div>
      </div>
    </aside>
  );
}
