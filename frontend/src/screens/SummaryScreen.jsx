export default function SummaryScreen({ result, verification, onReset, onBackToOutput }) {
  const isVerified = !!verification;
  const trustScore = isVerified ? verification.adjusted_trust_score : result.trust_score;

  const qualifier = isVerified
    ? trustScore >= 8.5
      ? 'All items were identified and independently verified with high confidence.'
      : trustScore >= 6.5
      ? 'Most items were identified with high confidence. Some findings require attention.'
      : 'The verifier flagged potential issues. Please review the findings below.'
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
            {isVerified
              ? 'Your document has been processed and independently audited by a second AI agent. Here is the complete breakdown.'
              : 'Your document has been processed. Here is a breakdown of what was found. Run verification for an independent audit.'}
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
                className="p-4 bg-surface border-2 border-primary flex flex-col justify-between neo-shadow-sm hover:bg-surface-high transition-colors"
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

        {/* Detailed Verification Findings */}
        {isVerified && verification.findings && verification.findings.length > 0 && (
          <div className="border-4 border-primary bg-surface neo-shadow-lg">
            {/* Header */}
            <div className="bg-primary text-on-primary px-6 py-3 flex items-center justify-between">
              <h2 className="font-[var(--font-headline)] text-xl font-bold uppercase tracking-tight">
                Verification Findings
              </h2>
              <span className="font-[var(--font-mono)] text-xs uppercase">
                {verification.findings.length} finding{verification.findings.length !== 1 ? 's' : ''}
              </span>
            </div>

            {/* Overall assessment */}
            <div className="px-6 py-4 border-b-2 border-primary bg-surface-high">
              <p className="font-[var(--font-body)] text-base font-medium">
                {verification.overall_assessment}
              </p>
            </div>

            {/* Individual findings */}
            <div className="divide-y-2 divide-primary">
              {verification.findings.map((finding, i) => (
                <div
                  key={i}
                  className={`px-6 py-4 flex gap-4 items-start hover:bg-surface-high transition-colors ${
                    finding.type === 'MISS' || finding.type === 'RISK' ? 'border-l-4 border-l-primary' : ''
                  }`}
                >
                  {/* Type badge */}
                  <div className="shrink-0 mt-0.5">
                    <span className={`font-[var(--font-mono)] text-xs px-3 py-1 uppercase font-bold tracking-wider border-2 border-primary ${
                      finding.type === 'CLEAN'
                        ? 'bg-surface text-primary'
                        : 'bg-primary text-on-primary'
                    }`}>
                      {finding.type}
                    </span>
                  </div>

                  {/* Description */}
                  <div className="flex-grow">
                    <p className="font-[var(--font-body)] text-sm leading-relaxed">
                      {finding.description}
                    </p>
                    {finding.affected_text && (
                      <p className="font-[var(--font-mono)] text-xs text-secondary mt-2 bg-surface-high px-2 py-1 border border-primary inline-block">
                        &quot;{finding.affected_text}&quot;
                      </p>
                    )}
                  </div>

                  {/* Severity */}
                  {finding.severity && finding.type !== 'CLEAN' && (
                    <span className={`shrink-0 font-[var(--font-mono)] text-xs px-2 py-0.5 uppercase font-bold border border-primary ${
                      finding.severity === 'high' ? 'bg-primary text-on-primary' : 'bg-surface'
                    }`}>
                      {finding.severity}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* What was found and why */}
        <div className="border-4 border-primary bg-surface neo-shadow p-6">
          <h2 className="font-[var(--font-headline)] text-xl font-bold uppercase mb-4 border-b-2 border-primary pb-3">
            What we did and why
          </h2>
          <p className="font-[var(--font-body)] text-base text-on-background leading-relaxed mb-4">
            {result.summary}
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-4">
            <div className="border-2 border-primary p-3 bg-surface-high">
              <div className="font-[var(--font-mono)] text-xs font-bold uppercase mb-1">Step 1: Detect</div>
              <div className="font-[var(--font-body)] text-sm text-secondary">
                Presidio scanned for patterns (emails, phone numbers, SSNs). Gemini then analyzed context to confirm or reject each detection.
              </div>
            </div>
            <div className="border-2 border-primary p-3 bg-surface-high">
              <div className="font-[var(--font-mono)] text-xs font-bold uppercase mb-1">Step 2: Label</div>
              <div className="font-[var(--font-body)] text-sm text-secondary">
                Each confirmed PII item was replaced with a descriptive label like [FULL_NAME_1] so you can see exactly what was replaced and why.
              </div>
            </div>
            <div className="border-2 border-primary p-3 bg-surface-high">
              <div className="font-[var(--font-mono)] text-xs font-bold uppercase mb-1">Step 3: Verify</div>
              <div className="font-[var(--font-body)] text-sm text-secondary">
                {isVerified
                  ? 'A second AI agent re-read the output looking for anything that was missed or could still identify someone.'
                  : 'Run verification to have a second AI agent independently audit the pseudonymized output.'}
              </div>
            </div>
          </div>
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
