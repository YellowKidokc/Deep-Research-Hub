/**
 * Story tab — the Deep Research Hub's column in the right rail.
 *
 *   Story checklist   baseline storytelling checks; an item turns green when
 *                     marked done. Definition: <hub>/prompts/W_story_checklist.json.
 *                     Ticks are saved per doc in <hub>/data/writer/checklists/.
 *   Extras            optional techniques grouped by the video that teaches
 *                     them, with a link to the moment; go after one when it fits.
 *   Outline           pick one (or none) per doc; its sections tick the same way.
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

interface Item { id: string; group?: string; core?: boolean; label: string; question: string; source?: string; t?: number }
interface Tick { done?: boolean; note?: string; at?: string; value?: string }
interface Source { title: string; channel?: string; url: string }
interface Group { id: string; label: string }
interface Section { id: string; label: string; question: string }
interface Outline { id: string; label: string; source?: string; t?: number; sections: Section[] }
interface Checklist {
  items: Item[];
  groups?: Group[];
  sources?: Record<string, Source>;
  outlines?: Outline[];
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

const mmss = (t: number) => `${Math.floor(t / 60)}:${String(Math.floor(t % 60)).padStart(2, '0')}`;

/** Link to the moment in the source video where a technique is taught. */
function sourceLink(sources: Checklist['sources'], id?: string, t?: number): { href: string; text: string; title: string } | null {
  const src = id ? sources?.[id] : undefined;
  if (!src) return null;
  const at = typeof t === 'number' ? t : 0;
  const href = /youtube\.com|youtu\.be/.test(src.url) ? `${src.url}${src.url.includes('?') ? '&' : '?'}t=${at}s` : src.url;
  return { href, text: `around ${mmss(at)}`, title: src.title };
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
  const [openGroups, setOpenGroups] = useState<Record<string, boolean>>({});

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

  const save = (body: Record<string, unknown>, optimistic: Record<string, Tick>) => {
    if (!key || !checklist) return;
    setChecklist({ ...checklist, state: { ...checklist.state, ...optimistic } });
    fetch('/api/drh/checklist', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ docId: key, ...body }),
    }).then((r) => r.json()).then((b) => b.state && setChecklist((c) => (c ? { ...c, state: b.state } : c))).catch(() => {});
  };
  const toggle = (id: string) => {
    const done = !checklist?.state[id]?.done;
    save({ id, done }, { [id]: { ...checklist?.state[id], done } });
  };
  const pickOutline = (value: string) => save({ id: '_outline', value }, { _outline: { value } });

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
  const extras = items.filter((i) => !i.core);
  const extraGroups = (checklist?.groups ?? [])
    .map((g) => ({ ...g, items: extras.filter((i) => (i.group ?? 'yours') === g.id) }))
    .filter((g) => g.items.length);
  const ungrouped = extras.filter((i) => !extraGroups.some((g) => g.id === (i.group ?? 'yours')));
  if (ungrouped.length) extraGroups.push({ id: '_other', label: 'Other', items: ungrouped });
  const extrasDone = extras.filter((i) => checklist?.state[i.id]?.done).length;
  const outlineId = checklist?.state._outline?.value ?? '';
  const outline = checklist?.outlines?.find((o) => o.id === outlineId);

  const row = (id: string, label: string, question: string, link?: ReturnType<typeof sourceLink>) => {
    const done = !!checklist?.state[id]?.done;
    return (
      <div key={id} className={`story-tab__item${done ? ' is-done' : ''}`}>
        <button type="button" className="story-tab__item-hit" onClick={() => toggle(id)} title={question}>
          <span className="story-tab__mark" aria-hidden="true">{done ? '✓' : ''}</span>
          <span className="story-tab__item-text">
            <span className="story-tab__item-label">{label}</span>
            <span className="story-tab__item-q">{question}</span>
          </span>
        </button>
        {link && (
          <a className="story-tab__src" href={link.href} target="_blank" rel="noreferrer" title={link.title}>{link.text}</a>
        )}
      </div>
    );
  };

  return (
    <div className="story-tab">
      <section className="story-tab__group">
        <div className="story-tab__label">
          Story checklist <span className="story-tab__count">{coreDone}/{core.length} core</span>
        </div>
        {error && <div className="story-tab__note story-tab__error">{error}</div>}
        {core.map((i) => row(i.id, i.label, i.question, sourceLink(checklist?.sources, i.source, i.t)))}
      </section>

      {extraGroups.length > 0 && (
        <section className="story-tab__group">
          <div className="story-tab__label">
            Extras in the loop <span className="story-tab__count">{extrasDone} used · optional</span>
          </div>
          {extraGroups.map((g) => {
            const open = !!openGroups[g.id];
            const used = g.items.filter((i) => checklist?.state[i.id]?.done).length;
            const src = checklist?.sources?.[g.id];
            return (
              <div key={g.id} className="story-tab__extras">
                <button type="button" className="story-tab__extras-head" onClick={() => setOpenGroups({ ...openGroups, [g.id]: !open })}>
                  <span aria-hidden="true">{open ? '▾' : '▸'}</span> {g.label}
                  <span className="story-tab__count">{used ? `${used}/` : ''}{g.items.length}</span>
                </button>
                {open && (
                  <>
                    {src && (
                      <a className="story-tab__src story-tab__src--group" href={src.url} target="_blank" rel="noreferrer">
                        {src.title}{src.channel ? ` · ${src.channel}` : ''}
                      </a>
                    )}
                    {g.items.map((i) => row(i.id, i.label, i.question, sourceLink(checklist?.sources, i.source, i.t)))}
                  </>
                )}
              </div>
            );
          })}
        </section>
      )}

      {(checklist?.outlines?.length ?? 0) > 0 && (
        <section className="story-tab__group">
          <div className="story-tab__label">
            Outline {outline && <span className="story-tab__count">{outline.sections.filter((x) => checklist?.state[`${outline.id}.${x.id}`]?.done).length}/{outline.sections.length}</span>}
          </div>
          <select className="story-tab__topic" value={outlineId} onChange={(e) => pickOutline(e.target.value)} aria-label="Outline">
            <option value="">None</option>
            {checklist?.outlines?.map((o) => <option key={o.id} value={o.id}>{o.label}</option>)}
          </select>
          {outline && (() => {
            const link = sourceLink(checklist?.sources, outline.source, outline.t);
            return (
              <>
                {link && <a className="story-tab__src story-tab__src--group" href={link.href} target="_blank" rel="noreferrer">{link.title} · {link.text}</a>}
                {outline.sections.map((x) => row(`${outline.id}.${x.id}`, x.label, x.question))}
              </>
            );
          })()}
        </section>
      )}

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
