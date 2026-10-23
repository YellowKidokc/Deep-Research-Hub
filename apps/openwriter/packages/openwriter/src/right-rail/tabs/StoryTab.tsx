/**
 * Story tab — the Deep Research Hub's column in the right rail.
 *
 *   Story import      load a story JSON from <hub>/data/writer/stories/ — or
 *                     craft one on demand from the hub's research, graded
 *                     against the checklist — highlight its spans in the doc,
 *                     cycle rewrite variants with a word diff, and apply or
 *                     keep per span. Choices saved per doc in
 *                     <hub>/data/writer/story-state/.
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
 *   Run on the doc    pick any checklist items, extras or outline sections (◎),
 *                     press Run: the model makes the best version of the doc
 *                     against them, and every change lands in the document as
 *                     a pending rewrite (outlined, "API · model" badge,
 *                     Original ⇄ AI, ✓/✕) — not in this column.
 *
 * Data comes from the drh plugin (plugins/drh); enable it in the Plugins tab.
 * Added in the Deep Research Hub copy of OpenWriter; see apps/openwriter/UPSTREAM.md.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { RightRailTabProps } from '../types';
import {
  activateStorySpan,
  clearStorySpans,
  findStorySpanRange,
  resolveStorySpan,
  setStorySpans,
} from '../../decorations/story-spans-plugin';
import { wordDiff } from './wordDiff';
import {
  collectParagraphs,
  selectedParagraphKeys,
  requestRevise,
  landEdits,
  revealNode,
  type LandedEdit,
} from '../../drh/ai-edits';
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
interface StoryVariant { id: string; text: string; note: string; source: string; grades?: Record<string, number> }
interface StorySpan { id: string; label: string; anchor: string; checklist: { needed: string[]; optional: string[] }; variants: StoryVariant[] }
interface Story { id: string; title: string; created: string; spans: StorySpan[]; warnings?: string[] }
interface StoryListEntry { id: string; title: string; spans: number }
interface StoryState { choices: Record<string, string>; kept: Record<string, string[]> }
interface TruthNode { id: string; text: string; note: string; tags: string[]; source: string; created: string }
interface Loop { id: string; label: string; scaffold: string }

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

  // Story import: a story JSON's spans, its per-doc choices, and the cycler.
  const [stories, setStories] = useState<StoryListEntry[] | null>(null);
  const [storyId, setStoryId] = useState('');
  const [story, setStory] = useState<Story | null>(null);
  const [storyWarnings, setStoryWarnings] = useState<string[]>([]);
  const [storyState, setStoryState] = useState<StoryState>({ choices: {}, kept: {} });
  const [activeSpanId, setActiveSpanId] = useState<string | null>(null);
  const [variantIdx, setVariantIdx] = useState(0);
  const [storyMsg, setStoryMsg] = useState('');
  const [crafting, setCrafting] = useState(false);
  // Set by "Craft opening" so the freshly crafted story's span opens as soon
  // as the story-load effect lands it.
  const autoOpenRef = useRef(false);

  // Run on the doc: picked goals (persisted per doc in this browser).
  const targetsKey = `drh-run-targets:${key}`;
  const [targets, setTargetsState] = useState<string[]>([]);
  useEffect(() => {
    try { setTargetsState(JSON.parse(localStorage.getItem(targetsKey) || '[]')); } catch { setTargetsState([]); }
  }, [targetsKey]);
  const setTargets = (next: string[]) => {
    setTargetsState(next);
    try { localStorage.setItem(targetsKey, JSON.stringify(next)); } catch { /* storage off */ }
  };
  const toggleTarget = (id: string) => setTargets(targets.includes(id) ? targets.filter((t) => t !== id) : [...targets, id]);
  const [runInstruction, setRunInstruction] = useState('');
  const [running, setRunning] = useState(false);
  const [runResult, setRunResult] = useState<{ reply: string; model: string; landed: LandedEdit[] } | null>(null);
  const [runError, setRunError] = useState('');
  const [hasSelection, setHasSelection] = useState(false);
  useEffect(() => {
    if (!editor) return;
    const onSel = () => { const { from, to } = editor.state.selection; setHasSelection(from !== to); };
    onSel();
    editor.on('selectionUpdate', onSel);
    return () => { editor.off('selectionUpdate', onSel); };
  }, [editor]);

  // Truth nodes: the hub's snippet library (data/writer/nodes.json).
  const [nodes, setNodes] = useState<TruthNode[] | null>(null);
  const [nodesQ, setNodesQ] = useState('');
  const [nodesError, setNodesError] = useState('');
  const [openNodes, setOpenNodes] = useState<Record<string, boolean>>({});
  const [showNodeForm, setShowNodeForm] = useState(false);
  const [newNodeText, setNewNodeText] = useState('');
  const [newNodeNote, setNewNodeNote] = useState('');
  const [newNodeTags, setNewNodeTags] = useState('');

  // Kait loops: reusable paragraph scaffolds from data/writer/loops.json.
  const [loops, setLoops] = useState<Loop[]>([]);
  const [loopsError, setLoopsError] = useState('');
  const [openLoops, setOpenLoops] = useState<Record<string, boolean>>({});

  // Locked story: the crafted opening this doc has committed to.
  const lockKey = `drh-locked-story:${key}`;
  const [lockedStoryId, setLockedStoryId] = useState<string | null>(null);
  useEffect(() => {
    try { setLockedStoryId(localStorage.getItem(lockKey)); } catch { setLockedStoryId(null); }
  }, [lockKey]);
  const toggleLock = () => {
    const next = lockedStoryId === storyId ? null : storyId;
    setLockedStoryId(next);
    try { next ? localStorage.setItem(lockKey, next) : localStorage.removeItem(lockKey); } catch { /* storage off */ }
  };

  const loadNodes = useCallback((q: string) => {
    fetch(`/api/drh/nodes?q=${encodeURIComponent(q)}`)
      .then(async (r) => {
        const type = r.headers.get('content-type') || '';
        if (r.status === 404 || !type.includes('json')) {
          throw new Error('Enable the Deep Research Hub plugin in the Plugins tab, then restart OpenWriter.');
        }
        const body = await r.json();
        if (!r.ok) throw new Error(body.error || r.statusText);
        return body;
      })
      .then((b) => { setNodes(b.nodes || []); setNodesError(''); })
      .catch((e) => { setNodes(null); setNodesError(e.message); });
  }, []);
  useEffect(() => { loadNodes(nodesQ); }, [nodesQ, loadNodes]);

  // Load Kait loops once.
  useEffect(() => {
    let cancelled = false;
    fetch('/api/drh/loops')
      .then(async (r) => {
        if (!r.ok) throw new Error('loops unavailable');
        return r.json();
      })
      .then((b) => { if (!cancelled) { setLoops(b.loops || []); setLoopsError(''); } })
      .catch((e) => { if (!cancelled) { setLoops([]); setLoopsError(e.message); } });
    return () => { cancelled = true; };
  }, []);

  // The story picker list (plugin routes; quiet when the plugin is off — the
  // checklist effect already shows that error).
  useEffect(() => {
    let cancelled = false;
    fetch('/api/drh/stories')
      .then((r) => (r.ok ? r.json() : { stories: [] }))
      .then((b) => { if (!cancelled) setStories(b.stories || []); })
      .catch(() => { if (!cancelled) setStories([]); });
    return () => { cancelled = true; };
  }, []);

  // Effective anchor: once a variant was chosen, the doc holds its text.
  const anchorFor = useCallback((span: StorySpan, choices: Record<string, string>) => {
    const choice = choices[span.id];
    const variant = choice ? span.variants.find((v) => v.id === choice) : undefined;
    return variant?.text ?? span.anchor;
  }, []);

  // Load the picked story + this doc's choices, and light up its spans.
  useEffect(() => {
    if (!editor) return;
    if (!storyId || !key) {
      setStory(null);
      setStoryWarnings([]);
      setStoryState({ choices: {}, kept: {} });
      setActiveSpanId(null);
      clearStorySpans(editor);
      return;
    }
    let cancelled = false;
    Promise.all([
      fetch(`/api/drh/story?id=${encodeURIComponent(storyId)}`).then((r) => (r.ok ? r.json() : Promise.reject(new Error('story')))),
      fetch(`/api/drh/story-state?docId=${encodeURIComponent(key)}&storyId=${encodeURIComponent(storyId)}`).then((r) => (r.ok ? r.json() : { choices: {}, kept: {} })),
    ])
      .then(([s, state]: [Story, StoryState]) => {
        if (cancelled) return;
        const loaded: StoryState = {
          choices: state.choices && typeof state.choices === 'object' ? state.choices : {},
          kept: state.kept && typeof state.kept === 'object' ? state.kept : {},
        };
        setStory(s);
        setStoryWarnings(s.warnings ?? []);
        setStoryState(loaded);
        setActiveSpanId(null);
        setVariantIdx(0);
        setStoryMsg('');
        setStorySpans(editor, s.spans.map((span) => ({ spanId: span.id, anchor: anchorFor(span, loaded.choices) })));
        for (const span of s.spans) {
          if (loaded.choices[span.id]) resolveStorySpan(editor, span.id, anchorFor(span, loaded.choices));
        }
        // A crafted story opens its span straight into the cycler.
        if (autoOpenRef.current && s.spans.length) {
          autoOpenRef.current = false;
          setActiveSpanId(s.spans[0].id);
          activateStorySpan(editor, s.spans[0].id);
        }
      })
      .catch(() => { if (!cancelled) { setStory(null); setStoryMsg('Could not load that story.'); } });
    return () => { cancelled = true; };
  }, [editor, storyId, key, anchorFor]);

  // Clear the editor highlights when the tab unmounts.
  useEffect(() => {
    if (!editor) return;
    return () => clearStorySpans(editor);
  }, [editor]);

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

  // Story import handlers.
  const itemById = useMemo(() => {
    const map: Record<string, Item> = {};
    for (const i of checklist?.items ?? []) map[i.id] = i;
    return map;
  }, [checklist]);

  // A picked goal's label + question: a checklist item or an outline section.
  const goalFor = (id: string): { label: string; question: string } | null => {
    const item = itemById[id];
    if (item) return { label: item.label, question: item.question };
    const dot = id.indexOf('.');
    const o = dot > 0 ? checklist?.outlines?.find((x) => x.id === id.slice(0, dot)) : undefined;
    const sec = o?.sections.find((x) => x.id === id.slice(dot + 1));
    return o && sec ? { label: `${o.label} — ${sec.label}`, question: sec.question } : null;
  };

  const runGoals = async () => {
    if (!editor || running) return;
    const goals = targets.map(goalFor).filter((g): g is { label: string; question: string } => !!g);
    if (!goals.length && !runInstruction.trim()) return;
    const paras = collectParagraphs(editor);
    if (!paras.length) { setRunError('The document is empty.'); return; }
    setRunning(true);
    setRunError('');
    setRunResult(null);
    try {
      const res = await requestRevise({
        mode: 'run',
        paragraphs: paras.map((p) => ({ id: p.key, kind: p.kind, text: p.text })),
        editable: selectedParagraphKeys(editor, paras),
        goals,
        instruction: runInstruction.trim(),
        topic: topic.trim() || defaultTopic,
      });
      const landed = landEdits(editor, paras, res.edits, 'Story run', res.model);
      setRunResult({ reply: res.reply, model: res.model, landed });
      if (landed[0]) revealNode(editor, landed[0].nodeId);
    } catch (e: any) {
      setRunError(e?.message || 'Run failed');
    } finally {
      setRunning(false);
    }
  };
  const shortModel = (m: string) => m.replace(/^[^/]+\//, '');

  const postStoryState = (spanId: string, body: { choice?: string; kept?: string[] }, optimistic: Partial<StoryState>) => {
    if (!key || !storyId) return;
    setStoryState((s) => ({
      choices: optimistic.choices ?? s.choices,
      kept: optimistic.kept ?? s.kept,
    }));
    fetch('/api/drh/story-state', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ docId: key, storyId, spanId, ...body }),
    })
      .then((r) => r.json())
      .then((b) => {
        if (b.state) setStoryState({ choices: b.state.choices ?? {}, kept: b.state.kept ?? {} });
        else if (b.error) setStoryMsg(b.error);
      })
      .catch(() => {});
  };

  const keptFor = (span: StorySpan): string[] => storyState.kept[span.id] ?? span.checklist.optional;

  const toggleKept = (span: StorySpan, itemId: string) => {
    const kept = keptFor(span);
    const next = kept.includes(itemId) ? kept.filter((k) => k !== itemId) : [...kept, itemId];
    postStoryState(span.id, { kept: next }, { kept: { ...storyState.kept, [span.id]: next } });
  };

  const openSpan = (span: StorySpan) => {
    if (!editor) return;
    setActiveSpanId(span.id);
    setVariantIdx(Math.max(0, span.variants.findIndex((v) => v.id === storyState.choices[span.id])));
    activateStorySpan(editor, span.id);
  };

  // "Use this version": swap the span's current text for the variant's.
  const useVariant = (span: StorySpan, variant: StoryVariant) => {
    if (!editor) return;
    const range = findStorySpanRange(editor.state.doc, anchorFor(span, storyState.choices));
    if (!range) {
      setStoryMsg('That span is not in the doc right now — edit it back or re-import.');
      return;
    }
    editor.view.dispatch(editor.state.tr.insertText(variant.text, range.from, range.to));
    postStoryState(span.id, { choice: variant.id }, { choices: { ...storyState.choices, [span.id]: variant.id } });
    resolveStorySpan(editor, span.id, variant.text);
    setStoryMsg('');
  };

  // "Keep original": record v0 and resolve the span without touching the doc.
  const keepOriginal = (span: StorySpan) => {
    if (!editor) return;
    postStoryState(span.id, { choice: 'v0' }, { choices: { ...storyState.choices, [span.id]: 'v0' } });
    resolveStorySpan(editor, span.id);
    setStoryMsg('');
  };

  // "Craft opening": the selection if there is one, else the first paragraph.
  // The route grades the current text and returns seven new openings as a
  // crafted story; select it and open the cycler when it lands.
  const craftedStoryId = `crafted-${key || 'scratch'}`;
  const craftOpening = () => {
    if (!editor || crafting) return;
    const { from, to } = editor.state.selection;
    const selected = from !== to ? editor.state.doc.textBetween(from, to, '\n').trim() : '';
    const text = selected || doc.paras[0]?.text || '';
    if (!text) return;
    if (lockedStoryId === craftedStoryId && !window.confirm('This doc has a locked crafted opening. Re-run will overwrite it. Continue?')) return;
    setCrafting(true);
    setStoryMsg('');
    fetch('/api/drh/craft-opening', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, topic: topic.trim() || undefined, docId: key || undefined }),
    })
      .then(async (r) => {
        const b = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(b.error || r.statusText);
        return b;
      })
      .then((b) => {
        autoOpenRef.current = true;
        fetch('/api/drh/stories')
          .then((r) => (r.ok ? r.json() : { stories: [] }))
          .then((d) => setStories(d.stories || []))
          .catch(() => {})
          .finally(() => setStoryId(b.storyId));
      })
      .catch((e) => setStoryMsg(e.message))
      .finally(() => setCrafting(false));
  };

  // Kait loops: insert the scaffold at the cursor.
  const insertLoop = (loop: Loop) => {
    if (!editor) return;
    editor.chain().focus().insertContent({ type: 'paragraph', content: [{ type: 'text', text: loop.scaffold }] }).run();
  };

  // Truth nodes: insert at the cursor as plain paragraphs (blank-line split).
  const insertNode = (node: TruthNode) => {
    if (!editor) return;
    const paragraphs = node.text.split(/\n\s*\n/).map((p) => p.trim()).filter(Boolean);
    if (!paragraphs.length) return;
    editor.chain().focus().insertContent(
      paragraphs.map((p) => ({ type: 'paragraph', content: [{ type: 'text', text: p }] })),
    ).run();
  };

  const deleteNode = (node: TruthNode) => {
    if (!window.confirm(`Delete "${node.note || node.text.slice(0, 60)}"?`)) return;
    fetch(`/api/drh/nodes?id=${encodeURIComponent(node.id)}`, { method: 'DELETE' })
      .then(async (r) => {
        const b = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(b.error || r.statusText);
        loadNodes(nodesQ);
      })
      .catch((e) => setNodesError(e.message));
  };

  const saveNode = () => {
    const text = newNodeText.trim();
    if (!text) return;
    fetch('/api/drh/nodes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text,
        note: newNodeNote.trim() || undefined,
        tags: newNodeTags.split(',').map((t) => t.trim()).filter(Boolean),
      }),
    })
      .then(async (r) => {
        const b = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(b.error || r.statusText);
        setNewNodeText('');
        setNewNodeNote('');
        setNewNodeTags('');
        setShowNodeForm(false);
        loadNodes(nodesQ);
      })
      .catch((e) => setNodesError(e.message));
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

  if (!editor) {
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

  // The span the cycler is open on, and its current text in the doc (the doc
  // may have drifted from the anchor; read the live range when it matches).
  const activeSpan = story?.spans.find((s) => s.id === activeSpanId) ?? null;
  const variantCount = activeSpan?.variants.length ?? 0;
  const activeVariant = activeSpan && variantCount ? activeSpan.variants[Math.min(variantIdx, variantCount - 1)] : null;
  const spanCurrentText = activeSpan
    ? findStorySpanRange(editor.state.doc, anchorFor(activeSpan, storyState.choices))?.text ?? anchorFor(activeSpan, storyState.choices)
    : '';

  const row = (id: string, label: string, question: string, link?: ReturnType<typeof sourceLink>) => {
    const done = !!checklist?.state[id]?.done;
    const picked = targets.includes(id);
    return (
      <div key={id} className={`story-tab__item${done ? ' is-done' : ''}${picked ? ' is-picked' : ''}`}>
        <button
          type="button"
          className={`story-tab__target${picked ? ' is-on' : ''}`}
          onClick={() => toggleTarget(id)}
          title={picked ? 'Picked for Run — click to drop' : 'Pick for Run on the doc'}
          aria-pressed={picked}
        >{picked ? '◉' : '◎'}</button>
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
      <section className="story-tab__group story-tab__run">
        <div className="story-tab__label">
          Run on the doc <span className="story-tab__count">{targets.length} picked</span>
        </div>
        {targets.length === 0 ? (
          <div className="story-tab__note">Tap ◎ on any checklist item, extra or outline section below to pick it, then Run. Changes land in the document, outlined, to keep or reject.</div>
        ) : (
          <div className="story-tab__chips">
            {targets.map((id) => (
              <button key={id} type="button" className="story-tab__chip story-tab__chip--needed" title="Drop" onClick={() => toggleTarget(id)}>
                {goalFor(id)?.label ?? id} ✕
              </button>
            ))}
          </div>
        )}
        <textarea
          className="story-tab__node-textarea story-tab__run-instruction"
          value={runInstruction}
          onChange={(e) => setRunInstruction(e.target.value)}
          placeholder="Extra instruction (optional) — e.g. keep it under 1,500 words"
          rows={2}
        />
        <div className="story-tab__cycler-actions">
          <button
            type="button"
            className="story-tab__btn story-tab__btn--primary"
            disabled={running || (!targets.length && !runInstruction.trim())}
            onClick={runGoals}
          >{running ? 'Running…' : `Run ${targets.length || ''} → ${hasSelection ? 'selection' : 'doc'}`}</button>
          <button type="button" className="story-tab__btn" onClick={() => setTargets(Array.from(new Set([...targets, ...core.map((i) => i.id)])))}>Pick all core</button>
          {targets.length > 0 && <button type="button" className="story-tab__btn" onClick={() => setTargets([])}>Clear</button>}
          <button type="button" className="story-tab__btn" onClick={() => window.dispatchEvent(new CustomEvent('drh-open-chat'))}>Chat</button>
        </div>
        {runError && <div className="story-tab__note story-tab__error">{runError}</div>}
        {runResult && (
          <div className="story-tab__run-result">
            <div className="story-tab__note">
              {runResult.landed.length
                ? `${runResult.landed.length} change${runResult.landed.length === 1 ? '' : 's'} in the doc · API · ${shortModel(runResult.model)}`
                : `No changes · ${shortModel(runResult.model)}`}
            </div>
            {runResult.reply && <div className="story-tab__run-reply">{runResult.reply}</div>}
            {runResult.landed.map((l, i) => (
              <button key={l.nodeId} type="button" className="story-tab__run-jump" title={l.why} onClick={() => revealNode(editor, l.nodeId)}>
                {i + 1}. {l.why || (l.kind === 'delete' ? 'remove paragraph' : 'rewrite')}
              </button>
            ))}
          </div>
        )}
      </section>

      <section className="story-tab__group">
        <div className="story-tab__label">
          Story import {story && <span className="story-tab__count">{story.spans.length} spans</span>}
        </div>
        {!key ? (
          <div className="story-tab__note">Save or name this doc first — story choices are filed under the doc.</div>
        ) : (
          <>
            <select className="story-tab__topic" value={storyId} onChange={(e) => setStoryId(e.target.value)} aria-label="Story">
              <option value="">No story</option>
              {(stories ?? []).map((s) => (
                <option key={s.id} value={s.id}>{s.title} · {s.spans} spans</option>
              ))}
            </select>
            <button
              type="button"
              className="story-tab__btn story-tab__btn--primary story-tab__craft"
              disabled={crafting || (doc.paras.length === 0 && !hasSelection)}
              title={doc.paras.length === 0 && !hasSelection
                ? 'Write or select an opening paragraph first'
                : 'Craft seven Kait-style openings from the hub’s research, graded against the story checklist'}
              onClick={craftOpening}
            >{crafting ? 'Crafting…' : 'Craft opening'}</button>
            {doc.paras.length === 0 && !hasSelection && (
              <div className="story-tab__note">Write or select an opening paragraph first — craft needs text to work from.</div>
            )}
            {stories !== null && stories.length === 0 && (
              <div className="story-tab__note">No stories in the hub yet. Add a story JSON to data/writer/stories/.</div>
            )}
            {storyMsg && <div className="story-tab__note story-tab__error">{storyMsg}</div>}
            {storyWarnings.map((w) => (
              <div key={w} className="story-tab__note">{w}</div>
            ))}
            {story?.spans.map((span) => {
              const choice = storyState.choices[span.id];
              const chosen = span.variants.find((v) => v.id === choice);
              return (
                <div
                  key={span.id}
                  className={`story-tab__span${activeSpanId === span.id ? ' is-active' : ''}${choice ? ' is-resolved' : ''}`}
                >
                  <button type="button" className="story-tab__item-hit" onClick={() => openSpan(span)}>
                    <span className="story-tab__item-text">
                      <span className="story-tab__item-label">{span.label}</span>
                      {choice && chosen && (
                        <span className="story-tab__span-note">✓ {chosen.note || chosen.id}</span>
                      )}
                    </span>
                  </button>
                  {(span.checklist.needed.length > 0 || span.checklist.optional.length > 0) && (
                    <div className="story-tab__chips">
                      {span.checklist.needed.map((id) => (
                        <span key={id} className="story-tab__chip story-tab__chip--needed" title={itemById[id]?.question ?? id}>
                          {itemById[id]?.label ?? id}
                        </span>
                      ))}
                      {span.checklist.optional.map((id) => {
                        const kept = keptFor(span).includes(id);
                        return (
                          <button
                            key={id}
                            type="button"
                            className={`story-tab__chip story-tab__chip--optional${kept ? '' : ' is-dropped'}`}
                            title={itemById[id]?.question ?? id}
                            onClick={() => toggleKept(span, id)}
                          >
                            {itemById[id]?.label ?? id}
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
            {story && activeSpan && activeVariant && (
              <div className="story-tab__cycler">
                <div className="story-tab__cycler-head">
                  <button
                    type="button"
                    className="story-tab__cycler-nav"
                    aria-label="Previous variant"
                    onClick={() => setVariantIdx((i) => (i - 1 + variantCount) % variantCount)}
                  >◀</button>
                  <span className="story-tab__cycler-count">{Math.min(variantIdx, variantCount - 1) + 1} / {variantCount}</span>
                  <button
                    type="button"
                    className={`story-tab__cycler-nav${lockedStoryId === storyId ? ' is-locked' : ''}`}
                    aria-label={lockedStoryId === storyId ? 'Unlock this opening' : 'Lock this opening'}
                    title={lockedStoryId === storyId ? 'Locked — Craft opening will warn before overwriting' : 'Lock this crafted opening'}
                    onClick={toggleLock}
                  >{lockedStoryId === storyId ? '★' : '☆'}</button>
                  <button
                    type="button"
                    className="story-tab__cycler-nav"
                    aria-label="Next variant"
                    onClick={() => setVariantIdx((i) => (i + 1) % variantCount)}
                  >▶</button>
                </div>
                {(activeVariant.note || activeVariant.source) && (
                  <div className="story-tab__cycler-meta">
                    {activeVariant.note}{activeVariant.source ? ` · ${activeVariant.source}` : ''}
                  </div>
                )}
                {activeVariant.grades && Object.keys(activeVariant.grades).length > 0 && (
                  <div className="story-tab__grades" title="Story-checklist grades for this version">
                    {Object.entries(activeVariant.grades)
                      .filter(([id]) => itemById[id])
                      .map(([id, g]) => (
                        <span key={id} className="story-tab__grade" title={itemById[id].question}>
                          {itemById[id].label} {g}/10
                        </span>
                      ))}
                  </div>
                )}
                <div className="story-tab__diff">
                  {wordDiff(spanCurrentText, activeVariant.text).map((p, i) => (
                    <span key={i} className={p.type === 'same' ? undefined : `story-tab__diff-${p.type}`}>
                      {p.text}{' '}
                    </span>
                  ))}
                </div>
                <div className="story-tab__cycler-actions">
                  <button
                    type="button"
                    className="story-tab__btn story-tab__btn--primary"
                    disabled={activeVariant.id === 'v0'}
                    onClick={() => useVariant(activeSpan, activeVariant)}
                  >Use this version</button>
                  <button
                    type="button"
                    className="story-tab__btn"
                    onClick={() => keepOriginal(activeSpan)}
                  >Keep original</button>
                </div>
              </div>
            )}
          </>
        )}
      </section>

      <section className="story-tab__group">
        <div className="story-tab__label">
          Kait loops <span className="story-tab__count">{loops.length}</span>
        </div>
        {loopsError && <div className="story-tab__note story-tab__error">{loopsError}</div>}
        {loops.length === 0 && !loopsError && (
          <div className="story-tab__note">No loops in data/writer/loops.json yet.</div>
        )}
        {loops.map((loop) => {
          const open = !!openLoops[loop.id];
          return (
            <div key={loop.id} className="story-tab__node">
              <button
                type="button"
                className="story-tab__extras-head"
                onClick={() => setOpenLoops({ ...openLoops, [loop.id]: !open })}
              >
                <span aria-hidden="true">{open ? '▾' : '▸'}</span>{' '}
                <span className="story-tab__node-title">{loop.label}</span>
              </button>
              {open && (
                <div className="story-tab__node-body">
                  <div className="story-tab__node-text">{loop.scaffold}</div>
                  <div className="story-tab__cycler-actions">
                    <button type="button" className="story-tab__btn story-tab__btn--primary" onClick={() => insertLoop(loop)}>Insert at cursor</button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </section>

      <section className="story-tab__group">
        <div className="story-tab__label">
          Truth nodes <span className="story-tab__count">{nodes?.length ?? 0}</span>
        </div>
        <input
          className="story-tab__topic"
          value={nodesQ}
          onChange={(e) => setNodesQ(e.target.value)}
          placeholder="Search nodes"
          aria-label="Search truth nodes"
        />
        {nodesError && <div className="story-tab__note story-tab__error">{nodesError}</div>}
        {nodes && !nodesError && nodes.length === 0 && (
          <div className="story-tab__note">
            {nodesQ ? 'No nodes match.' : 'No truth nodes yet — select text and right-click → Save as truth node, or paste one below.'}
          </div>
        )}
        {nodes?.map((n) => {
          const open = !!openNodes[n.id];
          return (
            <div key={n.id} className="story-tab__node">
              <button
                type="button"
                className="story-tab__extras-head"
                onClick={() => setOpenNodes({ ...openNodes, [n.id]: !open })}
              >
                <span aria-hidden="true">{open ? '▾' : '▸'}</span>{' '}
                <span className="story-tab__node-title">{n.note || n.text.split('\n')[0].slice(0, 80)}</span>
              </button>
              {n.tags.length > 0 && (
                <div className="story-tab__chips story-tab__chips--node">
                  {n.tags.map((t) => <span key={t} className="story-tab__chip">{t}</span>)}
                </div>
              )}
              {open && (
                <div className="story-tab__node-body">
                  <div className="story-tab__node-text">{n.text}</div>
                  {n.source && <div className="story-tab__note">{n.source}</div>}
                  <div className="story-tab__cycler-actions">
                    <button type="button" className="story-tab__btn story-tab__btn--primary" onClick={() => insertNode(n)}>Insert</button>
                    <button type="button" className="story-tab__btn" onClick={() => deleteNode(n)}>Delete</button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
        <button type="button" className="story-tab__extras-head" onClick={() => setShowNodeForm(!showNodeForm)}>
          <span aria-hidden="true">{showNodeForm ? '▾' : '▸'}</span> Paste a new truth node
        </button>
        {showNodeForm && (
          <div className="story-tab__node-form">
            <textarea
              className="story-tab__node-textarea"
              value={newNodeText}
              onChange={(e) => setNewNodeText(e.target.value)}
              placeholder="The passage worth keeping…"
              rows={5}
            />
            <input
              className="story-tab__topic"
              value={newNodeNote}
              onChange={(e) => setNewNodeNote(e.target.value)}
              placeholder="Note (what it is, optional)"
              aria-label="Node note"
            />
            <input
              className="story-tab__topic"
              value={newNodeTags}
              onChange={(e) => setNewNodeTags(e.target.value)}
              placeholder="Tags, comma separated"
              aria-label="Node tags"
            />
            <div className="story-tab__cycler-actions">
              <button
                type="button"
                className="story-tab__btn story-tab__btn--primary"
                disabled={!newNodeText.trim()}
                onClick={saveNode}
              >Save node</button>
            </div>
          </div>
        )}
      </section>

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
