/**
 * APIs tab — preset API calls on the open doc, their last result, and a
 * composer for making your own (saved to <hub>/data/writer/actions.json).
 *
 *   Rate & pin   scored report by part (rubric, critique, issues); every issue
 *                is also a comment on the quoted words in the doc
 *   Change doc   edits land in the doc as pending rewrites (outlined, badged)
 *
 * Shares its state with the left column's "API calls" section (drh/actions-store).
 * Added in the Deep Research Hub copy; see apps/openwriter/UPSTREAM.md.
 */
import { useEffect, useState } from 'react';
import type { RightRailTabProps } from '../types';
import {
  useActions, loadActions, runAction, saveAction, deleteAction, openComposer, revealIssue, getActionEditor,
  type ApiAction,
} from '../../drh/actions-store';
import { collectParagraphs, revealNode } from '../../drh/ai-edits';
import '../../drh/Apis.css';

const short = (m: string) => m.replace(/^[^/]+\//, '');
const tone = (n: number | null) => (n == null ? '' : n >= 90 ? 'hi' : n >= 75 ? 'mid' : 'lo');

function Score({ n }: { n: number | null }) {
  if (n == null) return null;
  return <span className={`drh-apis__score drh-apis__score--${tone(n)}`}>{n}</span>;
}

export default function ApisTab({ currentFilename }: RightRailTabProps) {
  const { actions, error, running, runError, last, composing } = useActions();
  const [extra, setExtra] = useState('');
  useEffect(() => { if (actions === null) loadActions(); }, [actions]);

  const result = last && last.filename === currentFilename ? last : null;

  return (
    <div className="drh-apis">
      <section className="drh-apis__group">
        <div className="drh-apis__label">API calls <span className="drh-apis__hint">run on the open doc{' · '}select text to limit edits</span></div>
        {error && <div className="drh-apis__note drh-apis__error">{error}</div>}
        {(actions ?? []).map((a) => (
          <div key={a.id} className={`drh-apis__action${running === a.id ? ' is-running' : ''}`}>
            <button type="button" className="drh-apis__run" disabled={!!running} onClick={() => runAction(a, extra.trim())}>
              <span className={`drh-apis__dot drh-apis__dot--${a.output}`} aria-hidden="true" />
              <span className="drh-apis__action-text">
                <span className="drh-apis__action-label">{a.label}{running === a.id ? ' — running…' : ''}</span>
                <span className="drh-apis__action-desc">
                  {a.output === 'notes' ? 'Rate & pin notes' : 'Changes the doc'}{a.description ? ` · ${a.description}` : ''}{a.model ? ` · ${short(a.model)}` : ''}
                </span>
              </span>
            </button>
            {!a.builtIn && (
              <button type="button" className="drh-apis__edit" title="Edit" onClick={() => openComposer(a.id)}>✎</button>
            )}
          </div>
        ))}
        <input
          className="drh-apis__input"
          value={extra}
          onChange={(e) => setExtra(e.target.value)}
          placeholder="Extra instruction for the next run (optional)"
        />
        <button type="button" className="drh-apis__btn" onClick={() => openComposer('new')}>+ Make your own API call</button>
        {runError && <div className="drh-apis__note drh-apis__error">{runError}</div>}
      </section>

      {composing && <Composer key={composing} id={composing} actions={actions ?? []} />}

      {result && (
        <section className="drh-apis__group">
          <div className="drh-apis__label">
            Last result · {result.label} <span className="drh-apis__hint">API · {short(result.model)} · {new Date(result.at).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}</span>
          </div>
          {result.output === 'notes' && result.report ? (
            <>
              <div className="drh-apis__overall">
                <Score n={result.report.overall.score} />
                <div>
                  {result.report.overall.grade && <div className="drh-apis__grade">{result.report.overall.grade}</div>}
                  <div className="drh-apis__text">{result.report.overall.summary}</div>
                </div>
              </div>
              {result.report.rubric.length > 0 && (
                <div className="drh-apis__rubric">
                  {result.report.rubric.map((r) => (
                    <div key={r.name} className="drh-apis__bar-row" title={r.note}>
                      <span className="drh-apis__bar-name">{r.name}</span>
                      <span className="drh-apis__bar"><span className={`drh-apis__bar-fill drh-apis__score--${tone(r.score)}`} style={{ width: `${r.score ?? 0}%` }} /></span>
                      <span className="drh-apis__bar-n">{r.score ?? '–'}</span>
                    </div>
                  ))}
                </div>
              )}
              {result.reply && <div className="drh-apis__reply">{result.reply}</div>}
              <div className="drh-apis__note">
                {result.pinned ? `${result.pinned} note${result.pinned === 1 ? '' : 's'} pinned on the words in the doc — hover the dotted underlines.` : 'No notes could be pinned (quotes did not match the doc).'}
              </div>
              {result.report.sections.map((s, i) => (
                <div key={i} className="drh-apis__section">
                  <div className="drh-apis__section-head"><Score n={s.score} /><span>{s.title}</span></div>
                  {s.basis && <div className="drh-apis__basis">Basis: {s.basis}</div>}
                  {s.critique && <div className="drh-apis__text">{s.critique}</div>}
                  {s.issues.map((iss, j) => (
                    <button key={j} type="button" className="drh-apis__issue" disabled={!iss.anchor} onClick={() => revealIssue(iss)}>
                      <span className="drh-apis__issue-title">{iss.title || 'Issue'}</span>
                      {iss.quote && <span className="drh-apis__issue-quote">“{iss.quote}”</span>}
                      <span className="drh-apis__text">{iss.issue}</span>
                      {iss.next_step && <span className="drh-apis__next">Next step: {iss.next_step}</span>}
                    </button>
                  ))}
                </div>
              ))}
              {actions?.some((a) => a.id === 'fix_from_rating') && (
                <button
                  type="button"
                  className="drh-apis__btn drh-apis__btn--primary"
                  disabled={!!running}
                  onClick={() => runAction(actions.find((a) => a.id === 'fix_from_rating')!, extra.trim())}
                >Fix from this rating → doc</button>
              )}
            </>
          ) : (
            <>
              {result.reply && <div className="drh-apis__reply">{result.reply}</div>}
              <div className="drh-apis__note">
                {result.landed?.length ? `${result.landed.length} change${result.landed.length === 1 ? '' : 's'} in the doc — outlined, flip ⇠ Original to compare, ✓ or ✕.` : 'No changes.'}
              </div>
              {result.landed?.map((l, i) => (
                <button key={l.nodeId} type="button" className="drh-apis__jump" title={l.why} onClick={() => { const ed = getActionEditor(); if (ed) revealNode(ed, l.nodeId); }}>
                  {i + 1}. {l.why || l.kind}
                </button>
              ))}
            </>
          )}
        </section>
      )}
    </div>
  );
}

function Composer({ id, actions }: { id: string; actions: ApiAction[] }) {
  const existing = id !== 'new' ? actions.find((a) => a.id === id && !a.builtIn) : undefined;
  const [label, setLabel] = useState(existing?.label ?? '');
  const [description, setDescription] = useState(existing?.description ?? '');
  const [output, setOutput] = useState<'edits' | 'notes'>(existing?.output ?? 'edits');
  const [model, setModel] = useState(existing?.model ?? '');
  const [prompt, setPrompt] = useState(existing?.prompt ?? '');
  const [msg, setMsg] = useState('');

  // "Use the doc as the prompt": write the prompt in the middle, then pull it in.
  const fromDoc = () => {
    const ed = getActionEditor();
    if (!ed) return;
    const text = collectParagraphs(ed).map((p) => p.text).join('\n\n');
    if (text) setPrompt(text);
  };

  const submit = async () => {
    try {
      await saveAction({ id: existing?.id, label, description, output, model, prompt });
      openComposer(null);
    } catch (e: any) { setMsg(e.message); }
  };

  return (
    <section className="drh-apis__group drh-apis__composer">
      <div className="drh-apis__label">{existing ? `Edit “${existing.label}”` : 'Make your own API call'}</div>
      <input className="drh-apis__input" value={label} onChange={(e) => setLabel(e.target.value)} placeholder="Name (shows as the button)" />
      <input className="drh-apis__input" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="One line under the button (optional)" />
      <div className="drh-apis__seg" role="radiogroup" aria-label="What it does">
        <button type="button" role="radio" aria-checked={output === 'edits'} className={output === 'edits' ? 'is-on' : ''} onClick={() => setOutput('edits')}>Changes the doc</button>
        <button type="button" role="radio" aria-checked={output === 'notes'} className={output === 'notes' ? 'is-on' : ''} onClick={() => setOutput('notes')}>Rate &amp; pin notes</button>
      </div>
      <textarea
        className="drh-apis__input drh-apis__prompt"
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        rows={8}
        placeholder={output === 'edits'
          ? 'What should it do to the doc? e.g. "Turn every list of steps written as a paragraph into its own numbered line."'
          : 'What should it judge, and on what rubric? e.g. "Score each section on whether a skeptical physicist would keep reading."'}
      />
      <button type="button" className="drh-apis__btn" onClick={fromDoc} title="Write the prompt as a document in the middle, then pull it in here">Use the open doc as the prompt</button>
      <input className="drh-apis__input" value={model} onChange={(e) => setModel(e.target.value)} placeholder="Model (optional) — e.g. anthropic/claude-sonnet-4.5" />
      <div className="drh-apis__note">The document, your selection and the output format are added automatically.</div>
      {msg && <div className="drh-apis__note drh-apis__error">{msg}</div>}
      <div className="drh-apis__row">
        <button type="button" className="drh-apis__btn drh-apis__btn--primary" disabled={!label.trim() || !prompt.trim()} onClick={submit}>Save</button>
        <button type="button" className="drh-apis__btn" onClick={() => openComposer(null)}>Cancel</button>
        {existing && (
          <button type="button" className="drh-apis__btn drh-apis__btn--danger" onClick={async () => {
            if (!window.confirm(`Delete “${existing.label}”?`)) return;
            try { await deleteAction(existing.id); openComposer(null); } catch (e: any) { setMsg(e.message); }
          }}>Delete</button>
        )}
      </div>
    </section>
  );
}
