/**
 * Left column, bottom half: "API calls" — one click runs a preset on the
 * open doc; results open in the right rail's APIs tab. "+ New" opens the
 * composer there. Added in the Deep Research Hub copy; see UPSTREAM.md.
 */
import { useEffect } from 'react';
import { useRightRail } from '../right-rail/RightRailContext';
import { useActions, loadActions, runAction, openComposer } from './actions-store';
import './Apis.css';

export default function SidebarApis() {
  const { actions, error, running } = useActions();
  const { openTab } = useRightRail();
  useEffect(() => { if (actions === null && !error) loadActions(); }, [actions, error]);

  return (
    <section className="drh-sidebar-apis" aria-label="API calls">
      <div className="drh-sidebar-apis__head">
        <span>API calls</span>
        <button type="button" className="drh-sidebar-apis__new" title="Make your own API call" onClick={() => { openComposer('new'); openTab('apis'); }}>+ New</button>
      </div>
      <button
        type="button"
        className="drh-sidebar-apis__variants"
        title="Explore sentence variants for the current paragraph"
        onClick={() => window.dispatchEvent(new CustomEvent('ow-explore-variants'))}
      >
        Variants
      </button>
      {error && <div className="drh-apis__note drh-apis__error">{error}</div>}
      <div className="drh-sidebar-apis__list">
        {(actions ?? []).map((a) => (
          <button
            key={a.id}
            type="button"
            className={`drh-sidebar-apis__item${running === a.id ? ' is-running' : ''}`}
            disabled={!!running}
            title={a.description || a.label}
            onClick={() => { openTab('apis'); runAction(a); }}
          >
            <span className={`drh-apis__dot drh-apis__dot--${a.output}`} aria-hidden="true" />
            <span className="drh-sidebar-apis__label">{a.label}</span>
            {running === a.id ? <span className="drh-sidebar-apis__busy">running…</span> : !a.builtIn && <span className="drh-sidebar-apis__mine">yours</span>}
          </button>
        ))}
      </div>
    </section>
  );
}
