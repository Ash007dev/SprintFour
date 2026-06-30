import { useMemo } from 'react';
import PseudoTag from '../components/PseudoTag';

export default function OutputScreen({ result, onViewSummary, onReset }) {
  // Build segments: split the pseudonymized text at pseudonym positions
  const segments = useMemo(() => {
    if (!result || !result.entities || result.entities.length === 0) {
      return [{ type: 'text', content: result?.pseudonymized_text || '' }];
    }

    const text = result.pseudonymized_text;
    const entities = [...result.entities].sort((a, b) => a.pseudonym_start - b.pseudonym_start);
    const parts = [];
    let lastIndex = 0;

    for (const entity of entities) {
      // Add text before this entity
      if (entity.pseudonym_start > lastIndex) {
        parts.push({
          type: 'text',
          content: text.slice(lastIndex, entity.pseudonym_start),
        });
      }

      // Add the entity tag
      parts.push({
        type: 'entity',
        entity,
      });

      lastIndex = entity.pseudonym_end;
    }

    // Add remaining text
    if (lastIndex < text.length) {
      parts.push({ type: 'text', content: text.slice(lastIndex) });
    }

    return parts;
  }, [result]);

  return (
    <div className="flex flex-col px-8 py-8 max-w-5xl mx-auto w-full gap-8">
      {/* Header */}
      <section className="flex flex-col gap-2">
        <h1 className="font-[var(--font-headline)] text-5xl md:text-6xl font-bold text-primary tracking-tighter">
          Here&apos;s what we found
        </h1>
        <p className="font-[var(--font-body)] text-lg text-secondary border-l-4 border-primary pl-4 max-w-3xl leading-relaxed">
          Nothing below is your original sensitive data &mdash; each label tells you what category of information was replaced.
        </p>
      </section>

      {/* Document Viewer */}
      <section className="flex-grow flex flex-col">
        <div className="bg-surface border-4 border-primary p-8 neo-shadow-lg flex flex-col gap-6">
          {/* Meta bar */}
          <div className="flex justify-between items-end border-b-2 border-primary pb-3">
            <div>
              <div className="font-[var(--font-mono)] text-xs text-secondary uppercase tracking-wider">
                Processed Document
              </div>
              <div className="font-[var(--font-headline)] text-xl font-bold">
                {result.entity_count} entities detected
              </div>
            </div>
            <div className="font-[var(--font-mono)] text-xs bg-primary text-on-primary px-3 py-1 uppercase font-bold">
              Pseudonymized
            </div>
          </div>

          {/* Document text with inline tags */}
          <div className="font-[var(--font-body)] text-lg leading-relaxed whitespace-pre-wrap">
            {segments.map((seg, i) =>
              seg.type === 'text' ? (
                <span key={i}>{seg.content}</span>
              ) : (
                <PseudoTag key={i} entity={seg.entity} />
              )
            )}
          </div>

          {/* Action button */}
          <div className="mt-6 pt-6 border-t-2 border-primary flex justify-end">
            <button
              onClick={onViewSummary}
              className="neo-btn bg-surface border-2 border-primary px-6 py-3 flex items-center gap-3 cursor-pointer group"
            >
              <span className="font-[var(--font-headline)] text-xl uppercase tracking-tight font-bold">
                View Summary
              </span>
              <svg className="w-5 h-5 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" strokeWidth={3} viewBox="0 0 24 24">
                <path strokeLinecap="square" d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
