export default function SummaryScreen({ result, verification, onReset, onBackToOutput }) {
  const isVerified = !!verification;
  const trustScore = isVerified ? verification.adjusted_trust_score : result.trust_score;

  const qualifier = isVerified
    ? trustScore >= 8.5
      ? 'All items were identified and independently verified with high confidence.'
      : trustScore >= 6.5
      ? 'Most items were identified with high confidence. Some findings require attention.'
      : 'The verifier flagged potential issues. Please review the audit trail.'
    : trustScore >= 8.5
      ? 'All items were identified with high confidence. Run verification for an independent audit.'
      : trustScore >= 6.5
      ? 'Most items were identified with high confidence. Verification recommended.'
      : 'Some items were identified with lower certainty. Verification strongly recommended.';

  return (
    <div className="flex flex-col items-center justify-center p-8 min-h-[80vh]">
      <div className="w-full max-w-4xl mx-auto space-y-8">
        {/* Title */}
        <header className="text-center mb-12">
          <h1 className="font-[var(--font-headline)] text-6xl md:text-7xl font-bold text-primary uppercase tracking-tighter mb-4">
            Trust Summary
          </h1>
          <p className="font-[var(--font-body)] text-lg text-on-surface-variant max-w-2xl mx-auto">
            The document has been processed{isVerified ? ' and independently verified' : ''}. Here is a breakdown of the confidence levels and identified entities.
          </p>
        </header>

        {/* Score + Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6 mb-12">
          {/* Trust Score Box */}
          <div className="md:col-span-5 flex flex-col justify-center items-center p-8 bg-surface border-4 border-primary neo-shadow-lg">
            <span className="font-[var(--font-mono)] text-xs text-secondary mb-2 uppercase tracking-widest">
              {isVerified ? 'Verified Score' : 'Unverified Score'}
            </span>
            <div className="font-[var(--font-headline)] text-primary flex items-baseline gap-2">
              <span className="text-7xl font-bold">{trustScore}</span>
              <span className="text-2xl text-on-surface-variant font-bold">/ 10</span>
            </div>
            <p className="mt-4 font-[var(--font-body)] text-sm text-center font-semibold bg-surface-high py-2 px-4 border-2 border-primary">
              {qualifier}
            </p>
            {!isVerified && (
              <p className="mt-3 font-[var(--font-mono)] text-xs text-secondary uppercase tracking-wider">
                Score is preliminary until verified
              </p>
            )}
          </div>

          {/* Stats Grid */}
          <div className="md:col-span-7 grid grid-cols-2 gap-2 p-6 bg-surface border-4 border-primary neo-shadow-lg">
            {result.category_breakdown.map((cat, i) => (
              <div
                key={i}
                className="p-4 bg-surface border-2 border-primary flex flex-col justify-between neo-shadow-sm"
              >
                <span className="font-[var(--font-headline)] text-4xl font-bold text-primary block mb-2">
                  {cat.count}
                </span>
                <span className="font-[var(--font-mono)] text-xs text-on-background uppercase border-t-2 border-primary pt-2 tracking-wider font-bold">
                  {cat.category}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Verification findings summary */}
        {isVerified && verification.findings && (
          <div className="border-4 border-primary bg-surface p-6 neo-shadow">
            <h2 className="font-[var(--font-headline)] text-xl font-bold uppercase mb-4 border-b-2 border-primary pb-2">
              Verification Findings
            </h2>
            <p className="font-[var(--font-body)] text-base mb-4">
              {verification.overall_assessment}
            </p>
            <div className="flex flex-wrap gap-3">
              {(() => {
                const counts = { CLEAN: 0, RISK: 0, MISS: 0 };
                verification.findings.forEach(f => { counts[f.type] = (counts[f.type] || 0) + 1; });
                return Object.entries(counts).filter(([, v]) => v > 0).map(([type, count]) => (
                  <span key={type} className={`font-[var(--font-mono)] text-xs px-3 py-1 border-2 border-primary uppercase font-bold ${
                    type === 'CLEAN' ? 'bg-surface' : 'bg-primary text-on-primary'
                  }`}>
                    {count}x {type}
                  </span>
                ));
              })()}
            </div>
          </div>
        )}

        {/* Summary paragraph */}
        <div className="border-t-4 border-primary pt-8 pb-6">
          <p className="font-[var(--font-body)] text-lg text-on-background max-w-3xl mx-auto border-l-4 border-primary pl-6 leading-relaxed">
            {result.summary}
          </p>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row justify-center gap-4 mt-8">
          <button
            onClick={onBackToOutput}
            className="neo-btn bg-surface border-2 border-primary text-primary font-[var(--font-headline)] text-lg px-8 py-4 uppercase tracking-tight flex items-center gap-3 cursor-pointer font-bold"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={3} viewBox="0 0 24 24">
              <path strokeLinecap="square" d="M11 17l-5-5m0 0l5-5m-5 5h12" />
            </svg>
            Back to Output
          </button>
          <button
            onClick={onReset}
            className="neo-btn bg-primary text-on-primary border-2 border-primary font-[var(--font-headline)] text-lg px-8 py-4 uppercase tracking-tight flex items-center gap-3 cursor-pointer font-bold"
          >
            Process Another Document
            <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={3} viewBox="0 0 24 24">
              <path strokeLinecap="square" d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
