export default function ApiDocsScreen({ onBack }) {
  return (
    <div className="flex flex-col px-8 py-12 max-w-5xl mx-auto w-full gap-8">
      {/* Title */}
      <div className="flex items-center justify-between">
        <h1 className="font-[var(--font-headline)] text-5xl md:text-6xl font-bold text-primary uppercase tracking-tighter">
          API Reference
        </h1>
        <button
          onClick={onBack}
          className="neo-btn bg-surface border-2 border-primary px-4 py-2 font-[var(--font-mono)] text-xs uppercase tracking-wider cursor-pointer font-bold"
        >
          &larr; Back
        </button>
      </div>

      <p className="font-[var(--font-body)] text-lg text-secondary max-w-3xl">
        Conseal exposes a REST API for programmatic document pseudonymization and verification.
        All endpoints accept and return JSON. The server runs on <code className="font-[var(--font-mono)] bg-surface-high px-1 border border-primary">http://localhost:8000</code>.
      </p>

      {/* POST /pseudonymize */}
      <section className="border-4 border-primary bg-surface neo-shadow-lg p-6 flex flex-col gap-4">
        <div className="flex items-center gap-3 border-b-2 border-primary pb-3">
          <span className="font-[var(--font-mono)] text-xs bg-primary text-on-primary px-3 py-1 uppercase font-bold">POST</span>
          <span className="font-[var(--font-mono)] text-lg font-bold">/pseudonymize</span>
        </div>
        <p className="font-[var(--font-body)] text-base">
          Process a text document: run Presidio base-pass, then Gemini contextual analysis. Returns pseudonymized output with entity details, trust score, and summary.
        </p>
        <div>
          <h3 className="font-[var(--font-headline)] text-lg font-bold uppercase mb-2">Request Body</h3>
          <pre className="bg-primary text-on-primary p-4 font-[var(--font-mono)] text-sm overflow-x-auto border-2 border-primary">
{`{
  "text": "Hello, my name is John Doe and my email is john@example.com"
}`}
          </pre>
        </div>
        <div>
          <h3 className="font-[var(--font-headline)] text-lg font-bold uppercase mb-2">Response (200)</h3>
          <pre className="bg-primary text-on-primary p-4 font-[var(--font-mono)] text-sm overflow-x-auto border-2 border-primary">
{`{
  "pseudonymized_text": "Hello, my name is [FULL_NAME_1] and my email is [EMAIL_1]",
  "entities": [
    {
      "original_text": "John Doe",
      "pseudonym": "[FULL_NAME_1]",
      "entity_type": "FULL_NAME",
      "confidence": 0.95,
      "start": 18, "end": 26,
      "pseudonym_start": 18, "pseudonym_end": 31
    }
  ],
  "trust_score": 9.5,
  "category_breakdown": [{ "category": "Names", "count": 1 }],
  "summary": "This document was scanned and 1 piece of personal information was identified...",
  "entity_count": 1
}`}
          </pre>
        </div>
      </section>

      {/* POST /pseudonymize/upload */}
      <section className="border-4 border-primary bg-surface neo-shadow-lg p-6 flex flex-col gap-4">
        <div className="flex items-center gap-3 border-b-2 border-primary pb-3">
          <span className="font-[var(--font-mono)] text-xs bg-primary text-on-primary px-3 py-1 uppercase font-bold">POST</span>
          <span className="font-[var(--font-mono)] text-lg font-bold">/pseudonymize/upload</span>
        </div>
        <p className="font-[var(--font-body)] text-base">
          Upload a file (PDF, JSON, TXT, MD, CSV, DOCX, etc.) for pseudonymization. The file is parsed server-side to extract text, then processed through the same pipeline.
        </p>
        <div>
          <h3 className="font-[var(--font-headline)] text-lg font-bold uppercase mb-2">Request</h3>
          <pre className="bg-primary text-on-primary p-4 font-[var(--font-mono)] text-sm overflow-x-auto border-2 border-primary">
{`# Multipart form upload
curl -X POST http://localhost:8000/pseudonymize/upload \\
  -F "file=@document.pdf"`}
          </pre>
        </div>
        <div>
          <h3 className="font-[var(--font-headline)] text-lg font-bold uppercase mb-2">Supported Formats</h3>
          <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
            {['PDF', 'TXT', 'JSON', 'CSV', 'MD', 'DOCX', 'LOG', 'RST', 'TSV'].map((fmt) => (
              <div key={fmt} className="border-2 border-primary p-2 font-[var(--font-mono)] text-xs uppercase text-center font-bold">
                .{fmt.toLowerCase()}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* POST /verify */}
      <section className="border-4 border-primary bg-surface neo-shadow-lg p-6 flex flex-col gap-4">
        <div className="flex items-center gap-3 border-b-2 border-primary pb-3">
          <span className="font-[var(--font-mono)] text-xs bg-primary text-on-primary px-3 py-1 uppercase font-bold">POST</span>
          <span className="font-[var(--font-mono)] text-lg font-bold">/verify</span>
        </div>
        <p className="font-[var(--font-body)] text-base">
          Run adversarial verification using a second AI agent (Groq). Checks the pseudonymized output for missed PII and residual re-identification risk. Returns findings and an adjusted trust score.
        </p>
        <div>
          <h3 className="font-[var(--font-headline)] text-lg font-bold uppercase mb-2">Request Body</h3>
          <pre className="bg-primary text-on-primary p-4 font-[var(--font-mono)] text-sm overflow-x-auto border-2 border-primary">
{`{
  "pseudonymized_text": "Hello, my name is [FULL_NAME_1]...",
  "entity_count": 5,
  "baseline_trust_score": 8.5
}`}
          </pre>
        </div>
        <div>
          <h3 className="font-[var(--font-headline)] text-lg font-bold uppercase mb-2">Response (200)</h3>
          <pre className="bg-primary text-on-primary p-4 font-[var(--font-mono)] text-sm overflow-x-auto border-2 border-primary">
{`{
  "findings": [
    { "type": "CLEAN", "description": "Names properly pseudonymized", "severity": "low" },
    { "type": "RISK", "description": "Job title + city combination may narrow identification", "severity": "medium" }
  ],
  "overall_assessment": "Document is mostly safe with one residual risk noted.",
  "adjusted_trust_score": 7.5,
  "is_verified": true
}`}
          </pre>
        </div>
      </section>

      {/* GET /health */}
      <section className="border-4 border-primary bg-surface neo-shadow p-6 flex flex-col gap-4">
        <div className="flex items-center gap-3 border-b-2 border-primary pb-3">
          <span className="font-[var(--font-mono)] text-xs bg-surface-high text-primary px-3 py-1 uppercase font-bold border-2 border-primary">GET</span>
          <span className="font-[var(--font-mono)] text-lg font-bold">/health</span>
        </div>
        <p className="font-[var(--font-body)] text-base">Health check endpoint.</p>
        <pre className="bg-primary text-on-primary p-4 font-[var(--font-mono)] text-sm overflow-x-auto border-2 border-primary">
{`{ "status": "ok", "llm_provider": "gemini" }`}
        </pre>
      </section>

      {/* GET /demo-documents */}
      <section className="border-4 border-primary bg-surface neo-shadow p-6 flex flex-col gap-4">
        <div className="flex items-center gap-3 border-b-2 border-primary pb-3">
          <span className="font-[var(--font-mono)] text-xs bg-surface-high text-primary px-3 py-1 uppercase font-bold border-2 border-primary">GET</span>
          <span className="font-[var(--font-mono)] text-lg font-bold">/demo-documents</span>
        </div>
        <p className="font-[var(--font-body)] text-base">
          List available demo documents (healthcare, finance, general business) with their full text content.
        </p>
      </section>

      {/* Architecture */}
      <section className="border-4 border-primary bg-surface neo-shadow p-6 flex flex-col gap-4">
        <h2 className="font-[var(--font-headline)] text-2xl font-bold uppercase border-b-2 border-primary pb-3">
          Architecture
        </h2>
        <pre className="font-[var(--font-mono)] text-sm leading-relaxed">
{`Document
  |
  v
Presidio (local, pattern-based)  -->  Base detections
  |
  v
Agent 1: Gemini (contextual)     -->  Confirmed/extended entities
  |
  v
Text substitution                -->  Pseudonymized output
  |
  v
Agent 2: Groq (adversarial)      -->  Verification findings
  |
  v
Trust Score (adjusted)`}
        </pre>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-2">
          <div className="border-2 border-primary p-3">
            <div className="font-[var(--font-mono)] text-xs font-bold uppercase">Detection</div>
            <div className="font-[var(--font-body)] text-sm text-secondary">Presidio + spaCy NER (local)</div>
          </div>
          <div className="border-2 border-primary p-3">
            <div className="font-[var(--font-mono)] text-xs font-bold uppercase">Pseudonymization</div>
            <div className="font-[var(--font-body)] text-sm text-secondary">Gemini 2.5 Flash (API)</div>
          </div>
          <div className="border-2 border-primary p-3">
            <div className="font-[var(--font-mono)] text-xs font-bold uppercase">Verification</div>
            <div className="font-[var(--font-body)] text-sm text-secondary">Groq / Llama 3.3 70B (API)</div>
          </div>
        </div>
      </section>
    </div>
  );
}
