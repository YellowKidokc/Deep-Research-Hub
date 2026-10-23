import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { useVariants, nextVariant, prevVariant, pickVariant, closeVariants } from './variants-store';
import './VariantCard.css';

interface Position { left: number; top: number }

export default function VariantCard() {
  const { session } = useVariants();
  const cardRef = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState<Position | null>(null);

  // Position the card just below the highlighted target sentence.
  useLayoutEffect(() => {
    if (!session) { setPos(null); return; }
    const card = cardRef.current;
    const target = document.querySelector('.variant-target') as HTMLElement | null;
    const editor = document.querySelector('.editor-container') as HTMLElement | null;
    const cardWidth = card?.offsetWidth ?? 420;
    const cardHeight = card?.offsetHeight ?? 180;

    let left = 0;
    let top = 0;
    if (target) {
      const rect = target.getBoundingClientRect();
      left = rect.left + rect.width / 2 - cardWidth / 2;
      top = rect.bottom + 10;
    } else if (editor) {
      const rect = editor.getBoundingClientRect();
      left = rect.left + rect.width / 2 - cardWidth / 2;
      top = rect.top + 80;
    } else {
      left = window.innerWidth / 2 - cardWidth / 2;
      top = 100;
    }

    // Keep inside viewport.
    const pad = 16;
    left = Math.max(pad, Math.min(left, window.innerWidth - cardWidth - pad));
    top = Math.max(pad, Math.min(top, window.innerHeight - cardHeight - pad));

    setPos({ left, top });
  }, [session?.paragraphId, session?.currentIndex]);

  // Scroll the target sentence into view when a session starts.
  useEffect(() => {
    if (!session) return;
    const target = document.querySelector('.variant-target') as HTMLElement | null;
    if (target) {
      target.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [session?.paragraphId]);

  // Keyboard shortcuts: ←/→ cycle, Enter picks, Escape closes.
  useEffect(() => {
    if (!session) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'ArrowLeft') { e.preventDefault(); prevVariant(); }
      if (e.key === 'ArrowRight') { e.preventDefault(); nextVariant(); }
      if (e.key === 'Escape') { e.preventDefault(); closeVariants(); }
      if (e.key === 'Enter' && !e.repeat) { e.preventDefault(); handlePick(); }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [session]);

  if (!session) return null;

  const options = session.originalSentence
    ? [{ text: session.originalSentence, why: 'Original sentence' }, ...session.variants]
    : session.variants;
  const current = options[session.currentIndex] ?? null;
  const canNav = options.length > 1;

  const handlePick = () => {
    if (session.currentIndex === 0 && session.originalSentence) {
      closeVariants();
      return;
    }
    pickVariant();
  };

  return (
    <div
      ref={cardRef}
      className="variant-card"
      style={pos ? { left: pos.left, top: pos.top } : undefined}
    >
      <div className="variant-card__header">
        <span className="variant-card__title">Better sentence</span>
        <button type="button" className="variant-card__close" onClick={closeVariants} aria-label="Close variants">×</button>
      </div>
      <div className="variant-card__body">
        {session.loading ? (
          <div className="variant-card__loading">Finding alternatives…</div>
        ) : session.error ? (
          <div className="variant-card__error">{session.error}</div>
        ) : current ? (
          <>
            <div className="variant-card__text">{current.text}</div>
            <div className="variant-card__why">{current.why}</div>
          </>
        ) : (
          <div className="variant-card__loading">No alternatives yet.</div>
        )}
      </div>
      <div className="variant-card__footer">
        <div className="variant-card__nav">
          <button
            type="button"
            className="variant-card__nav-btn"
            onClick={prevVariant}
            disabled={!canNav || session.loading || !!session.error}
            aria-label="Previous variant"
          >←</button>
          <span className="variant-card__counter">
            {options.length > 0 ? `${session.currentIndex + 1} / ${options.length}` : '-'}
          </span>
          <button
            type="button"
            className="variant-card__nav-btn"
            onClick={nextVariant}
            disabled={!canNav || session.loading || !!session.error}
            aria-label="Next variant"
          >→</button>
        </div>
        <button
          type="button"
          className="variant-card__pick"
          onClick={handlePick}
          disabled={session.loading || !!session.error || !current}
        >
          {session.currentIndex === 0 && session.originalSentence ? 'Keep original' : 'Pick this'}
        </button>
      </div>
    </div>
  );
}
