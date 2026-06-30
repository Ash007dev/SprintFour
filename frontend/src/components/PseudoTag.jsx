import { useState, useRef, useEffect } from 'react';
import { getReasonForType, humanizeEntityType } from '../utils/explainability';

export default function PseudoTag({ entity }) {
  const [expanded, setExpanded] = useState(false);
  const tagRef = useRef(null);

  // Close on outside click
  useEffect(() => {
    if (!expanded) return;
    const handleClick = (e) => {
      if (tagRef.current && !tagRef.current.contains(e.target)) {
        setExpanded(false);
      }
    };
    document.addEventListener('click', handleClick);
    return () => document.removeEventListener('click', handleClick);
  }, [expanded]);

  const confidencePercent = Math.round(entity.confidence * 100);
  const confidenceLabel =
    entity.confidence >= 0.85 ? 'High' :
    entity.confidence >= 0.6 ? 'Medium' :
    'Low';

  const humanType = humanizeEntityType(entity.entity_type);

  const reason = getReasonForType(entity.entity_type);

  return (
    <span className="relative inline-block mx-0.5" ref={tagRef}>
      {/* The tag itself */}
      <span
        className="pseudo-tag inline-block border-2 border-primary bg-surface-high font-[var(--font-mono)] text-xs font-bold px-2 py-1 neo-shadow-sm uppercase tracking-wide select-none"
        onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && setExpanded(!expanded)}
        title={`Click for details: ${humanType}`}
      >
        {entity.pseudonym}
      </span>

      {/* Expanded detail card */}
      {expanded && (
        <span className="popover-enter absolute bottom-full left-1/2 -translate-x-1/2 mb-3 w-72 bg-surface border-4 border-primary neo-shadow-lg p-0 z-50 flex flex-col">
          {/* Header */}
          <span className="flex items-center justify-between px-4 py-2 bg-primary text-on-primary">
            <span className="font-[var(--font-mono)] text-xs uppercase tracking-wider font-bold">
              {humanType}
            </span>
            <button
              onClick={(e) => { e.stopPropagation(); setExpanded(false); }}
              className="text-on-primary hover:opacity-70 text-lg font-bold cursor-pointer leading-none"
              aria-label="Close"
            >
              &times;
            </button>
          </span>

          {/* Body */}
          <span className="flex flex-col gap-3 px-4 py-3">
            {/* Confidence */}
            <span className="flex items-center justify-between">
              <span className="font-[var(--font-mono)] text-xs text-secondary uppercase">Confidence</span>
              <span className="flex items-center gap-2">
                <span className="font-[var(--font-mono)] text-sm font-bold">{confidencePercent}%</span>
                <span className={`font-[var(--font-mono)] text-xs px-2 py-0.5 border border-primary uppercase font-bold ${
                  confidenceLabel === 'High' ? 'bg-surface-high' : 'bg-surface'
                }`}>
                  {confidenceLabel}
                </span>
              </span>
            </span>

            {/* Confidence bar */}
            <span className="block w-full h-1.5 bg-surface-high border border-primary">
              <span
                className="block h-full bg-primary transition-all"
                style={{ width: `${confidencePercent}%` }}
              />
            </span>

            {/* WHY it was flagged */}
            <span className="block border-t-2 border-primary pt-3">
              <span className="block font-[var(--font-mono)] text-xs text-primary uppercase tracking-wider font-bold mb-1">
                Why flagged
              </span>
              <span className="block font-[var(--font-body)] text-sm text-on-background leading-relaxed">
                {reason}
              </span>
            </span>
          </span>

          {/* Caret */}
          <span className="absolute top-full left-1/2 -translate-x-1/2 w-3 h-3 bg-surface border-r-4 border-b-4 border-primary rotate-45 -mt-1.5" />
        </span>
      )}
    </span>
  );
}
