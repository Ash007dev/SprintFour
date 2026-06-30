import { useState, useEffect } from 'react';
import { pseudonymizeDocument, getDemoDocuments } from '../api';

export default function InputScreen({ onProcessed }) {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [demoDocs, setDemoDocs] = useState([]);

  useEffect(() => {
    getDemoDocuments()
      .then(setDemoDocs)
      .catch(() => {}); // Silently fail — demo docs are optional
  }, []);

  const handleProcess = async () => {
    if (!text.trim()) return;
    setLoading(true);
    setError(null);

    try {
      const result = await pseudonymizeDocument(text.trim());
      onProcessed(result, text.trim());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => setText(event.target.result);
    reader.readAsText(file);
  };

  const loadDemo = (doc) => {
    setText(doc.content);
    setError(null);
  };

  return (
    <div className="flex flex-col items-center justify-center px-8 py-24 max-w-5xl mx-auto w-full">
      <div className="w-full max-w-4xl flex flex-col gap-12">
        {/* Hero */}
        <div className="flex flex-col gap-6">
          <h1 className="font-[var(--font-headline)] text-6xl md:text-7xl font-bold uppercase tracking-tighter text-primary">
            GLASS BOX
          </h1>
          <p className="font-[var(--font-body)] text-lg text-on-surface-variant max-w-2xl leading-relaxed">
            Paste any document. We&apos;ll show you exactly what&apos;s sensitive &mdash; in plain language, not black bars.
          </p>
        </div>

        {/* Text Area */}
        <div className="flex flex-col gap-8 w-full">
          <div className="relative w-full">
            <label
              htmlFor="document-input"
              className="absolute -top-3 left-4 bg-background px-2 font-[var(--font-mono)] text-sm font-bold uppercase tracking-wider z-10"
            >
              Document Text
            </label>
            <textarea
              id="document-input"
              className="w-full h-80 bg-surface border-4 border-primary p-6 font-[var(--font-body)] text-base focus:outline-none resize-none neo-shadow transition-shadow rounded-none"
              placeholder="Paste your document, contract, medical record, or financial statement here..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              disabled={loading}
            />
          </div>

          {/* Demo Documents */}
          {demoDocs.length > 0 && (
            <div className="flex flex-col gap-3">
              <span className="font-[var(--font-mono)] text-xs uppercase tracking-wider text-secondary">
                Try a demo document:
              </span>
              <div className="flex flex-wrap gap-3">
                {demoDocs.map((doc) => (
                  <button
                    key={doc.id}
                    onClick={() => loadDemo(doc)}
                    disabled={loading}
                    className="border-2 border-primary bg-surface px-4 py-2 font-[var(--font-mono)] text-xs uppercase tracking-wider hover:bg-primary hover:text-on-primary transition-colors cursor-pointer disabled:opacity-50"
                  >
                    {doc.name}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="border-4 border-primary bg-surface p-4 neo-shadow">
              <span className="font-[var(--font-mono)] text-sm font-bold uppercase text-primary">Error: </span>
              <span className="font-[var(--font-body)] text-sm">{error}</span>
            </div>
          )}

          {/* Actions */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-6 w-full">
            <label className="flex items-center gap-2 font-[var(--font-mono)] text-sm text-secondary hover:text-primary transition-colors cursor-pointer group">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="square" strokeLinejoin="miter" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <span className="uppercase underline underline-offset-4 decoration-2">Or upload a file</span>
              <input
                type="file"
                accept=".txt,.md,.csv,.json,.log"
                onChange={handleFileUpload}
                className="hidden"
                disabled={loading}
              />
            </label>

            <button
              onClick={handleProcess}
              disabled={!text.trim() || loading}
              className="neo-btn bg-primary text-on-primary border-2 border-primary px-8 py-4 font-[var(--font-mono)] text-xs uppercase tracking-widest w-full sm:w-auto disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer font-bold"
            >
              {loading ? 'Processing...' : 'Process Document'}
            </button>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="border-4 border-primary bg-surface p-6 neo-shadow-lg">
            <div className="flex items-center gap-4">
              <div className="w-4 h-4 bg-primary neo-loading" />
              <div className="flex flex-col gap-1">
                <span className="font-[var(--font-headline)] text-lg font-bold uppercase">Analyzing document</span>
                <span className="font-[var(--font-body)] text-sm text-secondary">
                  Scanning for personally identifiable information...
                </span>
              </div>
            </div>
            <div className="mt-4 h-1 bg-surface-high">
              <div className="h-full bg-primary neo-progress-bar" />
            </div>
          </div>
        )}

        {/* Trust badge */}
        {!loading && (
          <div className="flex items-center gap-4 p-4 border-2 border-primary bg-surface-low max-w-fit">
            <svg className="w-5 h-5 text-primary" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="square" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            <span className="font-[var(--font-mono)] text-xs uppercase tracking-wider">
              Architectural Integrity Secured. Zero retention policy.
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
