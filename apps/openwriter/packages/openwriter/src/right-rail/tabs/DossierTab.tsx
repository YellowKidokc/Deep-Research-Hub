/**
 * Dossier tab — dump everything on a topic into one place, then sort it.
 *
 *   Dump      the open document, pasted text, or links to the hub's research
 *             (Deep Research runs, Targeted Research facts, YouTube transcripts).
 *   Sort      scripts/dossier.py: each source is broken into pills tied to its
 *             own words, then sorted into the workflow's sections or cut with a
 *             reason. It sorts; it never writes the paper.
 *   Read      sections strongest-first, what was cut and why, what is unsorted.
 *             Insert drops a pill's quote and source into the document.
 *
 * The dossier lives in <hub>/data/writer/dossiers/<name>/ and can be re-run
 * any time; only new or changed sources are read again.
 * Data comes from the drh plugin (plugins/drh); see apps/openwriter/UPSTREAM.md.
 */
import { useCallback, useEffect, useState } from 'react';
import type { RightRailTabProps } from '../types';
import './StoryTab.css';

interface Summary { name: string; topic: string; workflow: string; state: string }
interface Workflow { id: string; label: string; description: string; sections: number }
interface Pill {
  id: string; kind: string; text: string; quote: string; who?: string | null; when?: string | null; source: string; title?: string;
  state: 'placed' | 'cut' | 'unsorted'; section?: string; rank?: number; reason?: string; of?: string | null; note?: string;
}
interface Ledger {
  run: string; workflow: string;
  counts: { sources: number; pills: number; placed: number; cut: number; unsorted: number; quotes_not_verbatim: number };
  sections: { id: string; label: string; notes: string[] }[];
  pills: Pill[];
  skipped: { source: string; reason: string }[];
}
interface Detail {
  meta: { name: string; topic: string; workflow: string; links: string[] };
  inbox: string[];
  status: { state: string; stage?: string; error?: string } | null;
  log: string;
  ledger: Ledger | null;
}
interface Card { kind: string; title: string; detail: string; link: string }

const KEY = 'drh.dossier';

async function call<T>(url: string, body?: unknown): Promise<T> {
  const r = await fetch(url, body === undefined ? undefined : {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  });
  const type = r.headers.get('content-type') || '';
  if (r.status === 404 && !type.includes('json')) {
    throw new Error('Enable the Deep Research Hub plugin in the Plugins tab, then restart OpenWriter.');
  }
  const data = type.includes('json') ? await r.json() : {};
  if (!r.ok) throw new Error((data as any).error || r.statusText);
  return data as T;
}

export default function DossierTab({ editors, currentFilename }: RightRailTabProps) {
  const editor = editors[0];
  const [list, setList] = useState<Summary[] | null>(null);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [name, setName] = useState<string>(() => { try { return localStorage.getItem(KEY) || ''; } catch { return ''; } });
  const [detail, setDetail] = useState<Detail | null>(null);
  const [error, setError] = useState('');
  const [making, setMaking] = useState(false);
  const [form, setForm] = useState({ name: '', topic: '', workflow: 'default' });
  const [paste, setPaste] = useState('');
  const [cards, setCards] = useState<Card[] | null>(null);
  const [open, setOpen] = useState<Record<string, boolean>>({});
  const [flash, setFlash] = useState('');

  const refreshList = useCallback(() => {
    call<{ dossiers: Summary[] }>('/api/drh/dossiers').then((r) => setList(r.dossiers)).catch((e) => setError(e.message));
  }, []);
  const refresh = useCallback(() => {
    if (!name) { setDetail(null); return; }
    call<Detail>(`/api/drh/dossiers/${encodeURIComponent(name)}`).then(setDetail).catch((e) => { setDetail(null); setError(e.message); });
  }, [name]);

  useEffect(() => {
    refreshList();
    call<{ workflows: Workflow[] }>('/api/drh/workflows').then((r) => setWorkflows(r.workflows)).catch(() => {});
  }, [refreshList]);
  useEffect(() => { setError(''); setCards(null); refresh(); try { localStorage.setItem(KEY, name); } catch { /* fine */ } }, [name, refresh]);

  // Poll while a run is going.
  const runningNow = detail?.status?.state === 'running';
  useEffect(() => {
    if (!runningNow) return;
    const t = setInterval(() => { refresh(); refreshList(); }, 2000);
    return () => clearInterval(t);
  }, [runningNow, refresh, refreshList]);

  const say = (m: string) => { setFlash(m); setTimeout(() => setFlash(''), 2500); };
  const act = async (fn: () => Promise<unknown>, done?: string) => {
    setError('');
    try { await fn(); if (done) say(done); refresh(); refreshList(); } catch (e: any) { setError(e.message); }
  };

  const make = () => act(async () => {
    await call('/api/drh/dossiers', form);
    setMaking(false);
    setName(form.name);
    setForm({ name: '', topic: '', workflow: 'default' });
  }, 'Dossier made');

  const addDoc = () => act(async () => {
    if (!editor) throw new Error('No document open');
    const text = editor.getText({ blockSeparator: '\n\n' });
    let heading = '';
    editor.state.doc.descendants((node) => {
      if (!heading && node.type.name === 'heading') heading = node.textContent.trim();
      return !heading;
    });
    await call(`/api/drh/dossiers/${encodeURIComponent(name)}/add`, { text, title: heading || currentFilename.replace(/\.md$/i, '') || 'document' });
  }, 'Document added to the dump');

  const addPaste = () => act(async () => {
    await call(`/api/drh/dossiers/${encodeURIComponent(name)}/add`, { text: paste, title: 'pasted' });
    setPaste('');
  }, 'Pasted text added');

  const findResearch = () => act(async () => {
    const r = await call<{ cards: Card[] }>(`/api/drh/research?q=${encodeURIComponent(detail?.meta.topic || name)}`);
    setCards(r.cards);
  });

  const link = (c: Card) => act(() => call(`/api/drh/dossiers/${encodeURIComponent(name)}/add`, { link: c.link }), 'Linked');
  const run = () => act(() => call(`/api/drh/dossiers/${encodeURIComponent(name)}/run`, {}), 'Sorting started');

  const insert = (p: Pill) => {
    if (!editor) return;
    editor.chain().focus().insertContent([
      { type: 'blockquote', content: [{ type: 'paragraph', content: [{ type: 'text', text: p.quote }] }] },
      { type: 'paragraph', content: [{ type: 'text', text: `— ${p.title || p.source}` + (p.who ? `, ${p.who}` : '') + (p.when ? `, ${p.when}` : '') }] },
    ]).run();
    say('Inserted');
  };

  const toggle = (k: string) => setOpen({ ...open, [k]: !open[k] });
  const pillRow = (p: Pill, extra?: string) => (
    <div key={p.id} className="story-tab__card dossier__pill" title={p.quote}>
      <div className="story-tab__card-kind">{p.kind}{p.who ? ` · ${p.who}` : ''}{p.when ? ` · ${p.when}` : ''}</div>
      <div className="story-tab__card-title">{p.text}</div>
      <div className="story-tab__card-snippet">“{p.quote}”</div>
      <div className="story-tab__note" title={p.source}>{p.title || p.source}{extra ? ` · ${extra}` : ''}</div>
      {editor && <button type="button" className="story-tab__more" onClick={() => insert(p)}>Insert</button>}
    </div>
  );

  const L = detail?.ledger;
  const cuts = L ? L.pills.filter((p) => p.state === 'cut') : [];
  const unsorted = L ? L.pills.filter((p) => p.state === 'unsorted') : [];

  return (
    <div className="story-tab">
      <section className="story-tab__group">
        <div className="story-tab__label">Dossier</div>
        {error && <div className="story-tab__note story-tab__error">{error}</div>}
        {flash && <div className="story-tab__note">{flash}</div>}
        <select className="story-tab__topic" value={name} onChange={(e) => setName(e.target.value)} aria-label="Dossier">
          <option value="">{list?.length ? 'Pick a dossier' : 'No dossiers yet'}</option>
          {list?.map((d) => <option key={d.name} value={d.name}>{d.name} — {d.state}</option>)}
        </select>
        <button type="button" className="story-tab__more" onClick={() => setMaking(!making)}>{making ? 'Cancel' : '+ New dossier'}</button>
        {making && (
          <div className="dossier__form">
            <input className="story-tab__topic" placeholder="name (letters, digits, _ . -)" value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })} aria-label="Dossier name" />
            <input className="story-tab__topic" placeholder="topic" value={form.topic}
              onChange={(e) => setForm({ ...form, topic: e.target.value })} aria-label="Dossier topic" />
            <select className="story-tab__topic" value={form.workflow} onChange={(e) => setForm({ ...form, workflow: e.target.value })} aria-label="Workflow">
              {workflows.map((w) => <option key={w.id} value={w.id}>{w.label} ({w.sections} sections)</option>)}
            </select>
            <button type="button" className="dossier__btn" onClick={make} disabled={!form.name.trim()}>Make dossier</button>
          </div>
        )}
      </section>

      {detail && (
        <>
          <section className="story-tab__group">
            <div className="story-tab__label">
              Dump <span className="story-tab__count">{detail.inbox.length} files · {detail.meta.links.length} links</span>
            </div>
            <div className="story-tab__note">Topic: {detail.meta.topic} · workflow {detail.meta.workflow}</div>
            <div className="dossier__row">
              <button type="button" className="dossier__btn" onClick={addDoc} disabled={!editor}>Add this document</button>
              <button type="button" className="dossier__btn" onClick={findResearch}>Link research…</button>
            </div>
            <textarea className="story-tab__topic dossier__paste" placeholder="Paste anything: notes, a transcript, an article…"
              value={paste} onChange={(e) => setPaste(e.target.value)} aria-label="Paste into the dump" />
            {paste.trim() && <button type="button" className="dossier__btn" onClick={addPaste}>Add pasted text</button>}
            {cards && (cards.length === 0
              ? <div className="story-tab__note">No research in the hub matches “{detail.meta.topic}”.</div>
              : cards.map((c) => (
                <div key={c.link} className="story-tab__card">
                  <div className="story-tab__card-kind">{c.kind.replace('_', ' ')} · {c.detail}</div>
                  <div className="story-tab__card-title">{c.title}</div>
                  {detail.meta.links.includes(c.link)
                    ? <div className="story-tab__note">linked</div>
                    : <button type="button" className="story-tab__more" onClick={() => link(c)}>Link to dossier</button>}
                </div>
              )))}
            <button type="button" className="story-tab__more" onClick={() => toggle('_dump')}>
              {open._dump ? 'Hide the dump' : 'Show the dump'}
            </button>
            {open._dump && (
              <ul className="story-tab__note">
                {detail.inbox.map((f) => <li key={f}>{f}</li>)}
                {detail.meta.links.map((l) => <li key={l}>↗ {l}</li>)}
              </ul>
            )}
          </section>

          <section className="story-tab__group">
            <div className="story-tab__label">
              Sort {detail.status && <span className="story-tab__count">{detail.status.state}{detail.status.stage && detail.status.state === 'running' ? ` · ${detail.status.stage}` : ''}</span>}
            </div>
            <button type="button" className="dossier__btn" onClick={run}
              disabled={runningNow || (!detail.inbox.length && !detail.meta.links.length)}>
              {runningNow ? 'Sorting…' : L ? 'Sort again (new material only is read)' : 'Sort the dump'}
            </button>
            {detail.status?.error && <div className="story-tab__note story-tab__error">{detail.status.error}</div>}
            {(runningNow || detail.status?.state === 'failed') && detail.log && <pre className="dossier__log">{detail.log}</pre>}
          </section>

          {L && (
            <section className="story-tab__group">
              <div className="story-tab__label">
                Dossier <span className="story-tab__count">{L.counts.pills} pills · {L.counts.placed} placed · {L.counts.cut} cut · {L.counts.unsorted} unsorted</span>
              </div>
              <div className="story-tab__note">
                {L.counts.sources} sources, run {L.run}{L.counts.quotes_not_verbatim ? ` · ${L.counts.quotes_not_verbatim} proposed quotes were not in their source and were dropped` : ''}
                {L.skipped.length ? ` · skipped: ${L.skipped.map((s) => `${s.source} (${s.reason})`).join(', ')}` : ''}
              </div>
              {L.sections.map((s) => {
                const here = L.pills.filter((p) => p.state === 'placed' && p.section === s.id).sort((a, b) => (a.rank ?? 999) - (b.rank ?? 999));
                return (
                  <div key={s.id} className="story-tab__extras">
                    <button type="button" className="story-tab__extras-head" onClick={() => toggle(s.id)}>
                      <span aria-hidden="true">{open[s.id] ? '▾' : '▸'}</span> {s.label}
                      <span className="story-tab__count">{here.length}</span>
                    </button>
                    {open[s.id] && (
                      <>
                        {s.notes.map((n, i) => <div key={i} className="story-tab__note">{n}</div>)}
                        {here.map((p) => pillRow(p))}
                      </>
                    )}
                  </div>
                );
              })}
              <div className="story-tab__extras">
                <button type="button" className="story-tab__extras-head" onClick={() => toggle('_cut')}>
                  <span aria-hidden="true">{open._cut ? '▾' : '▸'}</span> Cut
                  <span className="story-tab__count">{cuts.length}</span>
                </button>
                {open._cut && cuts.map((p) => pillRow(p, `${p.reason?.replace('_', ' ')}${p.of ? ` (lost to ${p.of})` : ''}${p.note ? ` — ${p.note}` : ''}`))}
              </div>
              {unsorted.length > 0 && (
                <div className="story-tab__extras">
                  <button type="button" className="story-tab__extras-head" onClick={() => toggle('_uns')}>
                    <span aria-hidden="true">{open._uns ? '▾' : '▸'}</span> Unsorted
                    <span className="story-tab__count">{unsorted.length}</span>
                  </button>
                  {open._uns && unsorted.map((p) => pillRow(p))}
                </div>
              )}
            </section>
          )}
        </>
      )}
    </div>
  );
}
