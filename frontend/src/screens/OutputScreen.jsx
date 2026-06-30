import { useMemo, useState } from 'react';
import PseudoTag from '../components/PseudoTag';
import AuditTrail from '../components/AuditTrail';
import { verifyDocument } from '../api';

export default function OutputScreen({ result, verification, onVerified, onViewSummary, onReset }) {
  const [verifying, setVerifying] = useState(false);
  const [verifyError, setVerifyError] = useState(null);

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
      if (entity.pseudonym_start > lastIndex) {
        parts.push({ type: 'text', content: text.slice(lastIndex, entity.pseudonym_start) });
      }
      parts.push({ type: 'entity', entity });
      lastIndex = entity.pseudonym_end;
    }

    if (lastIndex < text.length) {
      parts.push({ type: 'text', content: text.slice(lastIndex) });
    }

    return parts;
  }, [result]);

  // Build audit trail entries from detection results + verification
  const auditEntries = useMemo(() => {
    const entries = [];
    const now = new Date();

    // Add detection entries (from Agent 1)
    if (result?.entities) {
      result.entities.forEach((entity) => {
        entries.push({
          type: 'DETECT',
          description: `Detected '${entity.original_text}' as ${entity.entity_type.replace(/_/g, ' ').toLowerCase()} - labeled ${entity.pseudonym}`,
          affected_text: entity.original_text,
          timestamp: now.toLocaleTimeString(),
        });
      });

      // Add baseline trust score entry
      entries.push({
        type: 'SCORE',
        description: `Baseline trust score: ${result.trust_score}/10 (unverified)`,
        affected_text: '',
        timestamp: now.toLocaleTimeString(),
      });
    }

    // Add verification entries (from Agent 2)
    if (verification?.findings) {
      verification.findings.forEach((finding) => {
        entries.push({
          type: finding.type,
          description: finding.description,
          affected_text: finding.affected_text || '',
          severity: finding.severity,
          timestamp: now.toLocaleTimeString(),
        });
      });

      // Add adjusted score entry
      entries.push({
        type: 'SCORE',
        description: `Verified trust score: ${verification.adjusted_trust_score}/10`,
        affected_text: '',
        timestamp: now.toLocaleTimeString(),
      });
    }

    // Newest first
    return entries.reverse();
  }, [result, verification]);

  const handleVerify = async () => {
    setVerifying(true);
    setVerifyError(null);

    try {
      const verifyResult = await verifyDocument(
        result.pseudonymized_text,
        result.entity_count,
        result.trust_score
      );
      onVerified(verifyResult);
    } catch (err) {
      setVerifyError(err.message);
    } finally {
      setVerifying(false);
    }
  };

  const currentScore = verification ? verification.adjusted_trust_score : result.trust_score;
  const isVerified = !!verification;

  return (
    <div className="flex flex-col px-8 py-8 max-w-6xl mx-auto w-full gap-8">
      {/* Header */}
      <section className="flex flex-col gap-2">
        <h1 className="font-[var(--font-headline)] text-5xl md:text-6xl font-bold text-primary tracking-tighter">
          Here is what we found
        </h1>
        <p className="font-[var(--font-body)] text-lg text-secondary border-l-4 border-primary pl-4 max-w-3xl leading-relaxed">
          Nothing below is your original sensitive data - each label tells you what category of information was replaced.
        </p>
      </section>

      {/* Main content: document + sidebar */}
      <div className="flex flex-col lg:flex-row gap-8">
        {/* Document Viewer */}
        <section className="flex-grow flex flex-col lg:w-2/3">
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
              <div className="flex items-center gap-3">
                {/* Trust score badge */}
                <div className={`font-[var(--font-mono)] text-xs px-3 py-1 uppercase font-bold border-2 border-primary ${isVerified ? 'bg-primary text-on-primary' : 'bg-surface-high text-primary'}`}>
                  {currentScore}/10 {isVerified ? 'Verified' : 'Unverified'}
                </div>
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

            {/* Actions */}
            <div className="mt-6 pt-6 border-t-2 border-primary flex flex-wrap justify-between items-center gap-4">
              {!isVerified ? (
                <button
                  onClick={handleVerify}
                  disabled={verifying}
                  className="neo-btn bg-surface border-2 border-primary px-6 py-3 flex items-center gap-3 cursor-pointer group disabled:opacity-50"
                >
                  {verifying ? (
                    <>
                      <div className="w-4 h-4 bg-primary neo-loading" />
                      <span className="font-[var(--font-headline)] text-lg uppercase tracking-tight font-bold">
                        Verifying...
                      </span>
                    </>
                  ) : (
                    <>
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                        <path strokeLinecap="square" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                      </svg>
                      <span className="font-[var(--font-headline)] text-lg uppercase tracking-tight font-bold">
                        Verify
                      </span>
                    </>
                  )}
                </button>
              ) : (
                <div className="font-[var(--font-mono)] text-xs uppercase tracking-wider text-secondary flex items-center gap-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                    <path strokeLinecap="square" d="M5 13l4 4L19 7" />
                  </svg>
                  Verification complete
                </div>
              )}

              <button
                onClick={onViewSummary}
                className="neo-btn bg-primary text-on-primary border-2 border-primary px-6 py-3 flex items-center gap-3 cursor-pointer group"
              >
                <span className="font-[var(--font-headline)] text-lg uppercase tracking-tight font-bold">
                  View Summary
                </span>
                <svg className="w-5 h-5 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" strokeWidth={3} viewBox="0 0 24 24">
                  <path strokeLinecap="square" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </button>
            </div>

            {/* Verify error */}
            {verifyError && (
              <div className="border-4 border-primary bg-surface p-4 neo-shadow mt-2">
                <span className="font-[var(--font-mono)] text-sm font-bold uppercase text-primary">Verify Error: </span>
                <span className="font-[var(--font-body)] text-sm">{verifyError}</span>
              </div>
            )}
          </div>
        </section>

        {/* Sidebar: Audit Trail */}
        <aside className="lg:w-1/3">
          <AuditTrail entries={auditEntries} />
        </aside>
      </div>
    </div>
  );
}
