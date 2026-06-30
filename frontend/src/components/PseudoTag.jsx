import { useState, useRef, useEffect } from 'react';

export default function PseudoTag({ entity }) {
  const [showPopover, setShowPopover] = useState(false);
  const tagRef = useRef(null);

  // Close popover on outside click
  useEffect(() => {
    if (!showPopover) return;
    const handleClick = (e) => {
      if (tagRef.current && !tagRef.current.contains(e.target)) {
        setShowPopover(false);
      }
    };
    document.addEventListener('click', handleClick);
    return () => document.removeEventListener('click', handleClick);
  }, [showPopover]);

  const confidenceLabel =
    entity.confidence >= 0.85 ? 'High confidence' :
    entity.confidence >= 0.6 ? 'Medium confidence' :
    'Low confidence';

  const humanType = entity.entity_type
    .replace(/_/g, ' ')
    .toLowerCase()
    .replace(/\b\w/g, c => c.toUpperCase());

  return (
    <span className="relative inline-block mx-0.5" ref={tagRef}>
      <span
        className="pseudo-tag inline-block border-2 border-primary bg-surface-high font-[var(--font-mono)] text-xs font-bold px-2 py-1 neo-shadow-sm uppercase tracking-wide"
        onClick={() => setShowPopover(!showPopover)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && setShowPopover(!showPopover)}
        title={`Click for details: ${humanType}`}
      >
        {entity.pseudonym}
      </span>

      {showPopover && (
        <span className="popover-enter absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-52 bg-surface border-4 border-primary neo-shadow p-3 z-50">
          <span className="block font-[var(--font-mono)] text-xs text-primary border-b-2 border-primary mb-2 pb-2 uppercase tracking-wider font-bold">
            {humanType}
          </span>
          <span className="block font-[var(--font-body)] text-sm text-secondary">
            {confidenceLabel} ({Math.round(entity.confidence * 100)}%)
          </span>
          <button
            onClick={() => setShowPopover(false)}
            className="absolute top-1 right-2 text-secondary hover:text-primary text-lg font-bold cursor-pointer"
            aria-label="Close"
          >
            &times;
          </button>
          {/* Caret */}
          <span className="absolute top-full left-1/2 -translate-x-1/2 w-3 h-3 bg-surface border-r-4 border-b-4 border-primary rotate-45 -mt-1.5" />
        </span>
      )}
    </span>
  );
}
