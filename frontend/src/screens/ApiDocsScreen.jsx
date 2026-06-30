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
        Glass Box exposes a simple REST API for programmatic document pseudonymization. 
        All endpoints accept and return JSON. The server runs on <code className="font-[var(--font-mono)] bg-surface-high px-1 border border-primary">http://localhost:8000</code>.
      </p>

      {/* POST /pseudonymize */}
      <section className="border-4 border-primary bg-surface neo-shadow-lg p-6 flex flex-col gap-4">
        <div className="flex items-center gap-3 border-b-2 border-primary pb-3">
          <span className="font-[var(--font-mono)] text-xs bg-primary text-on-primary px-3 py-1 uppercase font-bold">POST</span>
          <span className="font-[var(--font-mono)] text-lg font-bold">/pseudonymize</span>
        </div>
        <p className="font-[var(--font-body)] text-base">
          Process a document and return pseudonymized output with entity details, trust score, and summary.
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
      "start": 18,
      "end": 26,
      "pseudonym_start": 18,
      "pseudonym_end": 31
    },
    {
      "original_text": "john@example.com",
      "pseudonym": "[EMAIL_1]",
      "entity_type": "EMAIL",
      "confidence": 0.95,
      "start": 43,
      "end": 59,
      "pseudonym_start": 48,
      "pseudonym_end": 57
    }
  ],
  "trust_score": 9.5,
  "category_breakdown": [
    { "category": "Names", "count": 1 },
    { "category": "Email Addresses", "count": 1 }
  ],
  "summary": "This document was scanned and 2 pieces of personal information were identified...",
  "entity_count": 2
}`}
          </pre>
        </div>

        <div>
          <h3 className="font-[var(--font-headline)] text-lg font-bold uppercase mb-2">cURL Example</h3>
          <pre className="bg-primary text-on-primary p-4 font-[var(--font-mono)] text-sm overflow-x-auto border-2 border-primary">
{`curl -X POST http://localhost:8000/pseudonymize \\
  -H "Content-Type: application/json" \\
  -d '{"text": "My name is Sarah and my SSN is 123-45-6789"}'`}
          </pre>
        </div>

        <div>
          <h3 className="font-[var(--font-headline)] text-lg font-bold uppercase mb-2">Error Responses</h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="border-2 border-primary p-3">
              <div className="font-[var(--font-mono)] text-xs font-bold">400</div>
              <div className="font-[var(--font-body)] text-sm text-secondary">Invalid input (empty text)</div>
            </div>
            <div className="border-2 border-primary p-3">
              <div className="font-[var(--font-mono)] text-xs font-bold">500</div>
              <div className="font-[var(--font-body)] text-sm text-secondary">Processing error</div>
            </div>
            <div className="border-2 border-primary p-3">
              <div className="font-[var(--font-mono)] text-xs font-bold">503</div>
              <div className="font-[var(--font-body)] text-sm text-secondary">LLM service unavailable / rate limited</div>
            </div>
          </div>
        </div>
      </section>

      {/* GET /health */}
      <section className="border-4 border-primary bg-surface neo-shadow p-6 flex flex-col gap-4">
        <div className="flex items-center gap-3 border-b-2 border-primary pb-3">
          <span className="font-[var(--font-mono)] text-xs bg-surface-high text-primary px-3 py-1 uppercase font-bold border-2 border-primary">GET</span>
          <span className="font-[var(--font-mono)] text-lg font-bold">/health</span>
        </div>
        <p className="font-[var(--font-body)] text-base">Health check endpoint. Returns server status and configured LLM provider.</p>
        <pre className="bg-primary text-on-primary p-4 font-[var(--font-mono)] text-sm overflow-x-auto border-2 border-primary">
{`{
  "status": "ok",
  "llm_provider": "gemini"
}`}
        </pre>
      </section>

      {/* GET /demo-documents */}
      <section className="border-4 border-primary bg-surface neo-shadow p-6 flex flex-col gap-4">
        <div className="flex items-center gap-3 border-b-2 border-primary pb-3">
          <span className="font-[var(--font-mono)] text-xs bg-surface-high text-primary px-3 py-1 uppercase font-bold border-2 border-primary">GET</span>
          <span className="font-[var(--font-mono)] text-lg font-bold">/demo-documents</span>
        </div>
        <p className="font-[var(--font-body)] text-base">
          List available demo documents (healthcare, finance, general business) with their full text content for quick testing.
        </p>
        <pre className="bg-primary text-on-primary p-4 font-[var(--font-mono)] text-sm overflow-x-auto border-2 border-primary">
{`{
  "documents": [
    {
      "id": "healthcare",
      "name": "Healthcare",
      "content": "Subject: Referral for Patient...",
      "length": 1946
    },
    ...
  ]
}`}
        </pre>
      </section>

      {/* Entity Types */}
      <section className="border-4 border-primary bg-surface neo-shadow p-6 flex flex-col gap-4">
        <h2 className="font-[var(--font-headline)] text-2xl font-bold uppercase border-b-2 border-primary pb-3">
          Supported Entity Types
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          {[
            'FULL_NAME', 'FIRST_NAME', 'LAST_NAME', 'EMAIL',
            'PHONE', 'ADDRESS', 'STREET', 'CITY',
            'STATE', 'ZIP_CODE', 'SSN', 'DATE_OF_BIRTH',
            'ACCOUNT_NUMBER', 'ROUTING_NUMBER', 'CREDIT_CARD_NUMBER',
            'DIAGNOSIS', 'MEDICATION', 'MEDICAL_RECORD_NUMBER',
            'INSURANCE_ID', 'NPI', 'ORGANIZATION_NAME',
            'EMPLOYEE_ID', 'IP_ADDRESS', 'URL',
          ].map((type) => (
            <div key={type} className="border-2 border-primary p-2 font-[var(--font-mono)] text-xs uppercase tracking-wider text-center">
              {type}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
