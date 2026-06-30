"""
Conseal API - PII pseudonymization backend.

Endpoints:
- POST /pseudonymize: Process text and return pseudonymized output
- POST /pseudonymize/upload: Process an uploaded file (PDF, JSON, TXT, etc.)
- POST /verify: Run adversarial verification on pseudonymized output
- GET /health: Health check
- GET /demo-documents: List available demo documents

Error handling: API failures return structured error responses, never crash.
"""

import logging
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from backend.agent.pseudonymizer import pseudonymize_document, PseudonymizationError
from backend.agent.verifier import verify_document
from backend.cache import cache_response, get_cached_response, load_cached_responses
from backend.parsers import extract_text
from backend.models import (
    ErrorResponse,
    HealthResponse,
    PseudonymizeRequest,
    PseudonymizeResponse,
    VerifierFinding,
    VerifyRequest,
    VerifyResponse,
)

# Load environment variables
load_dotenv()

# Configure logging with rich formatting
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Suppress noisy third-party loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("google_genai").setLevel(logging.WARNING)


# ---------------------------------------------------------------------------
# Rich terminal logging helpers
# ---------------------------------------------------------------------------

def _log_banner():
    """Print startup banner."""
    banner = r"""
  +---------------------------------------------------+
  |                                                   |
  |    ____                            _              |
  |   / ___|___  _ __  ___  ___  __ _| |             |
  |  | |   / _ \| '_ \/ __|/ _ \/ _` | |             |
  |  | |__| (_) | | | \__ \  __/ (_| | |             |
  |   \____\___/|_| |_|___/\___|\__,_|_|             |
  |                                                   |
  |   PII Pseudonymization API v1.0.0                 |
  |   A Pseudonymization Approach to Trust            |
  |                                                   |
  +---------------------------------------------------+
"""
    print(banner)


def _log_config():
    """Log configuration details."""
    provider = os.getenv("LLM_PROVIDER", "gemini")
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    fallback_model = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-2.0-flash")
    has_gemini = bool(os.getenv("GEMINI_API_KEY"))
    has_groq = bool(os.getenv("GROQ_API_KEY"))
    timeout = os.getenv("LLM_TIMEOUT", "120")

    print(f"  [CONFIG] LLM Provider:     {provider}")
    print(f"  [CONFIG] Primary Model:    {model}")
    print(f"  [CONFIG] Fallback Model:   {fallback_model}")
    print(f"  [CONFIG] Gemini API Key:   {'***' + os.getenv('GEMINI_API_KEY', '')[-4:] if has_gemini else 'NOT SET'}")
    print(f"  [CONFIG] Groq API Key:     {'***' + os.getenv('GROQ_API_KEY', '')[-4:] if has_groq else 'NOT SET'}")
    print(f"  [CONFIG] Timeout:          {timeout}s")
    print()


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Conseal PII Pseudonymizer",
    description=(
        "Context-aware PII pseudonymization API. "
        "Replaces personally identifiable information with structured, "
        "human-readable labels that reveal the category without the actual data."
    ),
    version="1.0.0",
)

def _get_allowed_origins() -> list[str]:
    """Return local and configured frontend origins for browser access."""
    configured = os.getenv("FRONTEND_ORIGINS") or os.getenv("FRONTEND_ORIGIN", "")
    origins = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    origins.extend(origin.strip() for origin in configured.split(",") if origin.strip())
    return origins


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_allowed_origins(),
    allow_origin_regex=os.getenv("FRONTEND_ORIGIN_REGEX", r"https://.*\.vercel\.app"),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Demo documents directory
DEMO_DIR = Path(__file__).parent.parent / "data" / "demo_documents"


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup():
    """Load cached responses and display startup info."""
    _log_banner()
    _log_config()

    loaded = load_cached_responses()
    print(f"  [CACHE]  Loaded {loaded} cached responses from disk")

    # Count demo documents
    demo_count = len(list(DEMO_DIR.glob("*.txt"))) if DEMO_DIR.exists() else 0
    print(f"  [DEMO]   {demo_count} demo documents available")

    # Verify API keys
    provider = os.getenv("LLM_PROVIDER", "gemini")
    if provider == "gemini" and not os.getenv("GEMINI_API_KEY"):
        print("  [WARN]   GEMINI_API_KEY not set - live pseudonymization will fail!")
    if not os.getenv("GROQ_API_KEY"):
        print("  [INFO]   GROQ_API_KEY not set - Groq verifier unavailable")

    print()
    print("  [READY]  Conseal API is running")
    print("  [READY]  Docs:   http://localhost:8000/docs")
    print("  [READY]  Health: http://localhost:8000/health")
    print()
    print("  " + "=" * 50)
    print()


# ---------------------------------------------------------------------------
# Request logging middleware
# ---------------------------------------------------------------------------

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log every request with timing."""
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    # Skip logging for health checks to avoid noise
    if request.url.path == "/health":
        return response

    status = response.status_code
    method = request.method
    path = request.url.path
    duration_ms = int(duration * 1000)

    marker = "OK" if status < 400 else "ERR"
    print(f"  [{marker}]    {method} {path} -> {status} ({duration_ms}ms)")

    return response


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.post(
    "/pseudonymize",
    response_model=PseudonymizeResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input"},
        500: {"model": ErrorResponse, "description": "Processing error"},
        503: {"model": ErrorResponse, "description": "LLM service unavailable"},
    },
)
async def pseudonymize(request: PseudonymizeRequest):
    """
    Pseudonymize a document: detect PII and replace with contextual labels.

    Returns the pseudonymized text, per-entity details, trust score,
    category breakdown, and a plain-language summary.
    """
    text = request.text.strip()

    if not text:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_input", "message": "Document text cannot be empty"},
        )

    return await _process_text(text)


@app.post(
    "/pseudonymize/upload",
    response_model=PseudonymizeResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input or unsupported format"},
        500: {"model": ErrorResponse, "description": "Processing error"},
        503: {"model": ErrorResponse, "description": "LLM service unavailable"},
    },
)
async def pseudonymize_upload(file: UploadFile = File(...)):
    """
    Upload a file (PDF, JSON, TXT, MD, CSV, DOCX, etc.) for pseudonymization.

    The file is parsed to extract plain text, then processed through the
    same pseudonymization pipeline as the text endpoint.
    """
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_input", "message": "No file provided"},
        )

    # Read file content
    try:
        file_bytes = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "read_error", "message": f"Could not read file: {e}"},
        )

    # Extract text
    try:
        print(f"  [PARSE]  Extracting text from: {file.filename}")
        text = extract_text(file_bytes, file.filename)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "parse_error", "message": str(e)},
        )

    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail={"error": "empty_document", "message": "No text could be extracted from the file"},
        )

    print(f"  [PARSE]  Extracted {len(text)} chars from {file.filename}")

    return await _process_text(text.strip())


@app.post(
    "/verify",
    response_model=VerifyResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input"},
        503: {"model": ErrorResponse, "description": "Verification service unavailable"},
    },
)
async def verify(request: VerifyRequest):
    """
    Run adversarial verification on pseudonymized output.

    Uses the Verifier Agent (Groq) to check for missed PII and
    residual re-identification risk. Returns findings and an
    adjusted trust score.
    """
    text = request.pseudonymized_text.strip()
    if not text:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_input", "message": "Pseudonymized text cannot be empty"},
        )

    print(f"  [VERIFY] Starting verification ({len(text)} chars)...")

    try:
        result = await verify_document(text)
    except Exception as e:
        print(f"  [ERROR]  Verification failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "verification_error",
                "message": "Verification service is temporarily unavailable. Please try again.",
            },
        )

    # Compute adjusted trust score
    findings = [
        VerifierFinding(
            type=f.get("type", "CLEAN"),
            description=f.get("description", ""),
            affected_text=f.get("affected_text", ""),
            severity=f.get("severity", "low"),
        )
        for f in result.get("findings", [])
    ]

    adjusted_score = _adjust_trust_score(
        baseline=request.baseline_trust_score,
        findings=findings,
    )

    # Log results
    for f in findings:
        icon = {"CLEAN": "+", "RISK": "!", "MISS": "X"}.get(f.type, "?")
        print(f"  [VERIFY] [{icon}] {f.type}: {f.description}")
    print(f"  [VERIFY] Score: {request.baseline_trust_score} -> {adjusted_score}")

    return VerifyResponse(
        findings=findings,
        overall_assessment=result.get("overall_assessment", "Verification completed."),
        adjusted_trust_score=adjusted_score,
        is_verified=True,
    )


def _adjust_trust_score(baseline: float, findings: list[VerifierFinding]) -> float:
    """
    Adjust trust score based on verification findings.

    Asymmetric weighting: one miss reduces trust far more than
    several confirmations increase it.
    """
    adjustment = 0.0
    for f in findings:
        if f.type == "CLEAN":
            adjustment += 0.1
        elif f.type == "RISK":
            if f.severity == "high":
                adjustment -= 2.0
            elif f.severity == "medium":
                adjustment -= 1.5
            else:
                adjustment -= 0.5
        elif f.type == "MISS":
            if f.severity == "high":
                adjustment -= 2.5
            elif f.severity == "medium":
                adjustment -= 1.5
            else:
                adjustment -= 1.0

    adjusted = baseline + adjustment
    return round(max(0.0, min(10.0, adjusted)), 1)


async def _process_text(text: str) -> PseudonymizeResponse:
    """Shared processing logic for both text and file upload endpoints."""
    doc_length = len(text)
    print(f"  [AGENT]  Processing document ({doc_length} chars)...")

    # Check cache first
    cached = get_cached_response(text)
    if cached:
        print(f"  [CACHE]  Cache hit! Returning cached response")
        print(f"  [CACHE]  {cached.entity_count} entities, trust: {cached.trust_score}/10")
        return cached

    # Live processing
    start_time = time.time()
    try:
        print("  [AGENT]  Running Presidio base-pass...")
        print("  [AGENT]  Calling Gemini API...")
        response = await pseudonymize_document(text)
        duration = time.time() - start_time

        # Rich output
        print(f"  [AGENT]  Done in {duration:.1f}s")
        print(f"  [AGENT]  Entities detected: {response.entity_count}")
        print(f"  [AGENT]  Trust score: {response.trust_score}/10")
        for cat in response.category_breakdown:
            print(f"  [AGENT]    - {cat.count}x {cat.category}")

    except PseudonymizationError as e:
        error_msg = str(e)
        duration = time.time() - start_time
        print(f"  [ERROR]  Pseudonymization failed after {duration:.1f}s: {error_msg}")

        if "rate limit" in error_msg.lower() or "quota" in error_msg.lower():
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "rate_limited",
                    "message": (
                        "The AI service is temporarily rate-limited. "
                        "Please wait a moment and try again."
                    ),
                },
            )

        if "api key" in error_msg.lower() or "authentication" in error_msg.lower():
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "configuration_error",
                    "message": (
                        "The AI service is not properly configured. "
                        "Please check the API key settings."
                    ),
                },
            )

        if "timeout" in error_msg.lower():
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "timeout",
                    "message": (
                        "The AI service took too long to respond. "
                        "Please try again with a shorter document."
                    ),
                },
            )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "processing_error",
                "message": (
                    "An error occurred while processing your document. "
                    "Please try again."
                ),
                "detail": error_msg,
            },
        )
    except Exception as e:
        print(f"  [ERROR]  Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "An unexpected error occurred. Please try again.",
            },
        )

    # Cache the successful response
    cache_response(text, response)
    print("  [CACHE]  Response cached")

    return response


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        llm_provider=os.getenv("LLM_PROVIDER", "gemini"),
    )


@app.get("/demo-documents")
async def list_demo_documents():
    """
    List available demo documents with their content.
    """
    if not DEMO_DIR.exists():
        return {"documents": []}

    documents = []
    for doc_file in sorted(DEMO_DIR.glob("*.txt")):
        try:
            content = doc_file.read_text(encoding="utf-8")
            name = doc_file.stem.replace("_", " ").title()
            documents.append({
                "id": doc_file.stem,
                "name": name,
                "content": content,
                "length": len(content),
            })
        except Exception as e:
            logger.warning(f"Failed to read demo document {doc_file}: {e}")

    return {"documents": documents}


# ---------------------------------------------------------------------------
# Run with uvicorn
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
