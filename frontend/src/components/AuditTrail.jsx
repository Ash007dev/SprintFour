export default function AuditTrail({ entries }) {
  if (!entries || entries.length === 0) return null;

  const getLabel = (type) => {
    switch (type) {
      case 'CLEAN':
        return (
          <span className="font-[var(--font-mono)] text-xs px-2 py-0.5 bg-surface border-2 border-primary uppercase font-bold tracking-wider">
            Clean
          </span>
        );
      case 'RISK':
        return (
          <span className="font-[var(--font-mono)] text-xs px-2 py-0.5 bg-primary text-on-primary uppercase font-bold tracking-wider">
            Risk
          </span>
        );
      case 'MISS':
        return (
          <span className="font-[var(--font-mono)] text-xs px-2 py-0.5 bg-primary text-on-primary uppercase font-bold tracking-wider">
            Miss
          </span>
        );
      case 'DETECT':
        return (
          <span className="font-[var(--font-mono)] text-xs px-2 py-0.5 bg-surface-high border-2 border-primary uppercase font-bold tracking-wider">
            Found
          </span>
        );
      case 'SCORE':
        return (
          <span className="font-[var(--font-mono)] text-xs px-2 py-0.5 bg-surface border-2 border-primary uppercase font-bold tracking-wider">
            Score
          </span>
        );
      default:
        return (
          <span className="font-[var(--font-mono)] text-xs px-2 py-0.5 bg-surface border-2 border-primary uppercase font-bold tracking-wider">
            Info
          </span>
        );
    }
  };

  const getBorderStyle = (entry) => {
    if (entry.type === 'MISS') return 'border-l-4 border-l-primary';
    if (entry.type === 'RISK') return 'border-l-4 border-l-primary';
    return '';
  };

  return (
    <div className="flex flex-col gap-0">
      <div className="font-[var(--font-headline)] text-lg font-bold uppercase tracking-tight mb-3 flex items-center gap-2">
        <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
          <path strokeLinecap="square" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
        Audit Trail
      </div>

      <div className="border-4 border-primary bg-surface max-h-96 overflow-y-auto">
        {entries.map((entry, i) => (
          <div
            key={i}
            className={`flex items-start gap-3 p-3 border-b-2 border-primary last:border-b-0 transition-colors hover:bg-surface-high ${getBorderStyle(entry)}`}
          >
            <div className="shrink-0 mt-0.5">
              {getLabel(entry.type)}
            </div>
            <div className="flex-grow min-w-0">
              <p className="font-[var(--font-body)] text-sm leading-snug">
                {entry.description}
              </p>
              {entry.affected_text && (
                <p className="font-[var(--font-mono)] text-xs text-secondary mt-1 truncate">
                  &quot;{entry.affected_text}&quot;
                </p>
              )}
            </div>
            <span className="font-[var(--font-mono)] text-xs text-secondary whitespace-nowrap shrink-0">
              {entry.timestamp}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
