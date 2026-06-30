export default function AuditTrail({ entries }) {
  if (!entries || entries.length === 0) return null;

  const getIcon = (type) => {
    switch (type) {
      case 'CLEAN':
        return (
          <span className="w-6 h-6 flex items-center justify-center bg-surface border-2 border-primary text-xs font-bold font-[var(--font-mono)]">
            +
          </span>
        );
      case 'RISK':
        return (
          <span className="w-6 h-6 flex items-center justify-center bg-primary text-on-primary text-xs font-bold font-[var(--font-mono)]">
            !
          </span>
        );
      case 'MISS':
        return (
          <span className="w-6 h-6 flex items-center justify-center bg-primary text-on-primary text-xs font-bold font-[var(--font-mono)]">
            X
          </span>
        );
      case 'DETECT':
        return (
          <span className="w-6 h-6 flex items-center justify-center bg-surface-high border-2 border-primary text-xs font-bold font-[var(--font-mono)]">
            D
          </span>
        );
      case 'SCORE':
        return (
          <span className="w-6 h-6 flex items-center justify-center bg-surface border-2 border-primary text-xs font-bold font-[var(--font-mono)]">
            S
          </span>
        );
      default:
        return (
          <span className="w-6 h-6 flex items-center justify-center bg-surface border-2 border-primary text-xs font-bold font-[var(--font-mono)]">
            ?
          </span>
        );
    }
  };

  const getSeverityStyle = (entry) => {
    if (entry.type === 'MISS' || (entry.type === 'RISK' && entry.severity === 'high')) {
      return 'border-l-4 border-l-primary bg-surface';
    }
    if (entry.type === 'RISK') {
      return 'border-l-4 border-l-primary';
    }
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

      <div className="border-4 border-primary bg-surface max-h-80 overflow-y-auto">
        {entries.map((entry, i) => (
          <div
            key={i}
            className={`flex items-start gap-3 p-3 border-b-2 border-primary last:border-b-0 ${getSeverityStyle(entry)}`}
          >
            {getIcon(entry.type)}
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
