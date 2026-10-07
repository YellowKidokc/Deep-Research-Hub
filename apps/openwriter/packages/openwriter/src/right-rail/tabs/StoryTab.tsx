/**
 * Story tab — the Deep Research Hub's column in the right rail.
 *
 *   Story checklist   baseline storytelling checks; an item turns green when
 *                     marked done. Definition: <hub>/prompts/W_story_checklist.json.
 *                     Ticks are saved per doc in <hub>/data/writer/checklists/.
 *   Paragraphs        words per paragraph against the checklist's band, with
 *                     the opening paragraph checked on its own. Computed here
 *                     from the editor; nothing is sent anywhere.
 *   Research          cards from the hub's Deep Research runs and YouTube
 *                     transcripts whose topic matches this doc.
 *
 * Data comes from the drh plugin (plugins/drh); enable it in the Plugins tab.
 * Added in the Deep Research Hub copy of OpenWriter; see apps/openwriter/UPSTREAM.md.
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import type { RightRailTabProps } from '../types';
import './StoryTab.css';

interface Item { id: string; core: boolean; label: string; question: string }
interface Tick { done: boolean; note?: string; at?: string }
interface Checklist {
  items: Item[];
  state: Record<string, Tick>;
  paragraph_band: { min_words: number; max_words: number; opening_max_words: number };
}
interface Card { kind: 'deep_research' | 'youtube'; title: string; detail: string; snippet: string; path: string; score: number }
interface Para { n: number; words: number; sentences: number; text: string }

const countWords = (t: string) => (t.match(/\S+/g) || []).length;
const countSentences = (t: string) => (t.match(/[^.!?]+[.!?]+(\s|$)/g) || []).length || (t.trim() ? 1 : 0);

function readDoc(editor: RightRailTabProps['editors'][number] | undefined): { heading: string; paras: Para[] } {
  if (!editor) return { heading: '', paras: [] };
  let heading = '';
  const paras: Para[] = [];
  editor.state.doc.descendants((node) => {
    if (node.type.name === 'heading' && !heading) heading = node.textContent.trim();
    if (node.type.name === 'paragraph') {
      const text = node.textContent.trim();
      if (text) paras.push({ n: paras.length + 1, words: countWords(text), sentences: countSentences(text), text });
      return false;
    }
    return true;
  });
  return { heading, paras };
}

function median(xs: number[]): number {
  if (!xs.length) return 0;
  const s = [...xs].sort((a, b) => a - b);
  const m = Math.floor(s.length / 2);
  return s.length % 2 ? s[m] : Math.round((s[m - 1] + s[m]) / 2);
}

/** Where this doc's ticks are filed: its docId, or its filename when it has none yet. */
function checklistKey(docId: string | null, filename: string): string {
  if (docId) return docId;
  const base = filename.replace(/\.md$/i, '').replace(/[^A-Za-z0-9_.-]+/g, '_').replace(/^[._]+/, '');
  return base ? `file-${base}`.slice(0, 120) : '';
}

export default function StoryTab({ editors, docId, currentFilename }: RightRailTabProps) {
  const editor = editors[0];
  const key = checklistKey(docId, currentFilename);
  const [checklist, setChecklist] = useState<Checklist | null>(null);
  const [error, setError] = useState('');
  const [doc, setDoc] = useState(() => readDoc(editor));
  const [topic, setTopic] = useState('');
  const [cards, setCards] = useState<Card[] | null>(null);
  const [showAll, setShowAll] = useState(false);

  // Paragraph stats follow the editor, debounced.
  useEffect(() => {
    if (!editor) return;
    setDoc(readDoc(editor));
    let t: ReturnType<typeof setTimeout> | undefined;
    const onUpdate = () => { clearTimeout(t); t = setTimeout(() => setDoc(readDoc(editor)), 300); };
    editor.on('update', onUpdate);
    return () => { clearTimeout(t); editor.off('update', onUpdate); };
  }, [editor]);

  // Checklist + this doc's ticks.
  useEffect(() => {
    let cancelled = false;
    setError('');
    fetch(`/api/drh/checklist?docId=${encodeURIComponent(key)}`)
      .then(async (r) => {
        const type = r.headers.get('content-type') || '';
        if (r.status === 404 || !type.includes('json')) {
          throw new Error('Enable the Deep Research Hub plugin in the Plugins tab, then restart OpenWriter.');
        }
        const body = await r.json();
        if (!r.ok) throw new Error(body.error || r.statusText);
        return body as Checklist;
      })
      .then((c) => { if (!cancelled) setChecklist(c); })
      .catch((e) => { if (!cancelled) { setChecklist(null); setError(e.message); } });
    return () => { cancelled = true; };
  }, [key]);

  // Default research topic: the doc's first heading, else its filename.
  const defaultTopic = doc.heading || currentFilename.replace(/\.md$/i, '');
  useEffect(() => { setTopic(defaultTopic); }, [key, defaultTopic]);

  const search = useCallback((q: string) => {
    if (!q.trim()) { setCards([]); return; }
    fetch(`/api/drh/research?q=${encodeURIComponent(q)}`)
      .then((r) => (r.ok ? r.json() : { cards: [] }))
      .then((b) => setCards(b.cards || []))
      .catch(() => setCards([]));
  }, []);
  useEffect(() => { if (checklist) search(topic); }, [checklist, topic, search]);

  const toggle = (item: Item) => {
    if (!key || !checklist) return;
    const done = !checklist.state[item.id]?.done;
    setChecklist({ ...checklist, state: { ...checklist.state, [item.id]: { ...checklist.state[item.id], done } } });
    fetch('/api/drh/checklist', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ docId: key, id: item.id, done }),
    }).then((r) => r.json()).then((b) => b.state && setChecklist((c) => (c ? { ...c, state: b.state } : c))).catch(() => {});
  };

  const stats = useMemo(() => {
    const band = checklist?.paragraph_band ?? { min_words: 40, max_words: 140, opening_max_words: 90 };
    const counts = doc.paras.map((p) => p.words);
    const verdict = (p: Para) =>
      p.n === 1 && p.words > band.opening_max_words ? 'long'
        : p.words < band.min_words ? 'short'
        : p.words > band.max_words ? 'long' : 'ok';
    const inBand = doc.paras.filter((p) => verdict(p) === 'ok').length;
    return {
      band,
      verdict,
      total: counts.reduce((a, b) => a + b, 0),
      median: median(counts),
      inBand,
      pct: doc.paras.length ? Math.round((100 * inBand) / doc.paras.length) : 0,
    };
  }, [doc, checklist]);

  if (!editor || !key) {
    return (
      <div className="story-tab__empty">
        <div className="story-tab__empty-title">No document open</div>
        <div className="story-tab__note">Open a doc to see its story checklist, paragraph stats and research.</div>
      </div>
    );
  }

  const items = checklist?.items ?? [];
  const core = items.filter((i) => i.core);
  const coreDone = core.filter((i) => checklist?.state[i.id]?.done).length;
  const shown = showAll ? items : core;

  return (
    <div className="story-tab">
      <section className="story-tab__group">
        <div className="story-tab__label">
          Story checklist <span className="story-tab__count">{coreDone}/{core.length} core</span>
        </div>
        {error && <div className="story-tab__note story-tab__error">{error}</div>}
        {shown.map((item) => {
          const done = !!checklist?.state[item.id]?.done;
          return (
            <button
              type="button"
              key={item.id}
              className={`story-tab__item${done ? ' is-done' : ''}`}
              onClick={() => toggle(item)}
              title={item.question}
            >
              <span className="story-tab__mark" aria-hidden="true">{done ? '✓' : ''}</span>
              <span className="story-tab__item-text">
                <span className="story-tab__item-label">{item.label}</span>
                <span className="story-tab__item-q">{item.question}</span>
              </span>
            </button>
          );
        })}
        {items.length > core.length && (
          <button type="button" className="story-tab__more" onClick={() => setShowAll(!showAll)}>
            {showAll ? 'Core only' : `+ ${items.length - core.length} more when they fit`}
          </button>
        )}
      </section>

      <section className="story-tab__group">
        <div className="story-tab__label">
          Paragraphs <span className="story-tab__count">{doc.paras.length}</span>
        </div>
        {doc.paras.length === 0 ? (
          <div className="story-tab__note">No paragraphs yet.</div>
        ) : (
          <>
            <div className="story-tab__note">
              {stats.total} words · median {stats.median} per paragraph · {stats.pct}% in {stats.band.min_words}–{stats.band.max_words}
            </div>
            <div className="story-tab__paras">
              {doc.paras.map((p) => {
                const v = stats.verdict(p);
                return (
                  <div key={p.n} className={`story-tab__para is-${v}`} title={p.text.slice(0, 200)}>
                    <span className="story-tab__para-n">{p.n === 1 ? 'Opening' : `¶${p.n}`}</span>
                    <span className="story-tab__para-bar" style={{ width: `${Math.min(100, (100 * p.words) / (stats.band.max_words * 1.5))}%` }} />
                    <span className="story-tab__para-w">{p.words}w · {p.sentences}s{v !== 'ok' ? ` · ${v}` : ''}</span>
                  </div>
                );
              })}
            </div>
          </>
        )}
      </section>

      <section className="story-tab__group">
        <div className="story-tab__label">
          Research <span className="story-tab__count">{cards?.length ?? 0}</span>
        </div>
        <input
          className="story-tab__topic"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="Topic to match"
          aria-label="Research topic"
        />
        {cards && cards.length === 0 && (
          <div className="story-tab__note">Nothing in the hub matches this topic yet. Run it through Deep Research or YouTube intake.</div>
        )}
        {cards?.map((c) => (
          <div key={c.path} className="story-tab__card" title={c.path}>
            <div className="story-tab__card-kind">{c.kind === 'youtube' ? 'YouTube' : 'Deep Research'} · {c.detail}</div>
            <div className="story-tab__card-title">{c.title}</div>
            {c.snippet && <div className="story-tab__card-snippet">{c.snippet}</div>}
          </div>
        ))}
      </section>
    </div>
  );
}
