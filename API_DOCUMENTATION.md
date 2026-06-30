# Glass Box  - API Documentation

## Base URL

```
http://localhost:8000
```

---

## Endpoints

### POST /pseudonymize

Process a document and return pseudonymized output with entity details, trust score, and summary.

**Request:**

```json
{
  "text": "Hello, my name is John Doe and my email is john@example.com"
}
```

| Field | Type   | Required | Description                    |
|-------|--------|----------|--------------------------------|
| text  | string | Yes      | Document text (1–50,000 chars) |

**Response (200):**

```json
{
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
    }
  ],
  "trust_score": 9.5,
  "category_breakdown": [
    { "category": "Names", "count": 1 },
    { "category": "Email Addresses", "count": 1 }
  ],
  "summary": "This document was scanned and 2 pieces of personal information were identified...",
  "entity_count": 2
}
```

**cURL Example:**

```bash
curl -X POST http://localhost:8000/pseudonymize \
  -H "Content-Type: application/json" \
  -d '{"text": "My name is Sarah and my SSN is 123-45-6789"}'
```

**Error Responses:**

| Status | Error Type           | Description                    |
|--------|----------------------|--------------------------------|
| 400    | invalid_input        | Empty or invalid document text |
| 500    | processing_error     | LLM response parsing failed    |
| 503    | rate_limited         | API rate limit hit             |
| 503    | configuration_error  | Missing API key                |
| 503    | timeout              | LLM call timed out             |

---

### GET /health

Health check. Returns server status and configured LLM provider.

**Response:**

```json
{
  "status": "ok",
  "llm_provider": "gemini"
}
```

---

### GET /demo-documents

List available demo documents with their full text content.

**Response:**

```json
{
  "documents": [
    {
      "id": "healthcare",
      "name": "Healthcare",
      "content": "Subject: Referral for Patient...",
      "length": 1946
    }
  ]
}
```

---

## Supported Entity Types

| Type                   | Example                           |
|------------------------|-----------------------------------|
| FULL_NAME              | John Doe, Dr. Sarah Mitchell      |
| FIRST_NAME             | Sarah, James                      |
| LAST_NAME              | Doe, Mitchell                     |
| EMAIL                  | john@example.com                  |
| PHONE                  | (212) 555-0198                    |
| ADDRESS                | 250 Madison Avenue, NY 10016     |
| SSN                    | 123-45-6789                       |
| DATE_OF_BIRTH          | 03/15/1978                        |
| ACCOUNT_NUMBER         | 7834-2291-0056                    |
| ROUTING_NUMBER         | 021000021                         |
| CREDIT_CARD_NUMBER     | 5287761891196274                  |
| DIAGNOSIS              | coronary artery disease           |
| MEDICATION             | Lisinopril 20mg daily             |
| MEDICAL_RECORD_NUMBER  | MRN-2847301                       |
| INSURANCE_ID           | BCB-449-2210847                   |
| NPI                    | 1234567890                        |
| ORGANIZATION_NAME      | Johnson & Associates LLC          |
| EMPLOYEE_ID            | EMP-2847                          |
| IP_ADDRESS             | 146.229.205.216                   |

---

## Architecture

```
Frontend (React)  →  POST /pseudonymize  →  FastAPI Backend  →  Gemini 2.5 Flash
     ↑                                           │
     └──────────── JSON Response ────────────────┘
```

- **Single agent, single API call** per document  - no multi-agent orchestration
- **Gemini 2.5 Flash** primary, **Gemini 2.0 Flash** fallback, **Groq** last resort
- **In-memory cache** with disk persistence for demo reliability
- **Stateless**  - no database, no user sessions, no data retention

---

## Local Setup

```bash
# 1. Clone and install backend
pip install -r requirements.txt
cp .env.example .env
# Add your GEMINI_API_KEY to .env

# 2. Start backend
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# 3. Install and start frontend
cd frontend
npm install
npm run dev

# 4. Open http://localhost:5173
```
