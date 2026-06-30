"""
FastAPI Backend — Single-endpoint API for PII pseudonymization.

Endpoints:
- POST /pseudonymize: Process a document and return pseudonymized output
- GET /health: Health check
- GET /demo-documents: List available demo documents

Error handling: API failures return structured error responses, never crash.
The app never hangs silently — clear, calm error states for every failure mode.
"""

import logging
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from backend.agent.pseudonymizer import pseudonymize_document, PseudonymizationError
from backend.cache import cache_response, get_cached_response, load_cached_responses
from backend.models import (
    ErrorResponse,
    HealthResponse,
    PseudonymizeRequest,
    PseudonymizeResponse,
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
  |    ____  _                  ____                   |
  |   / ___|| | __ _ ___ ___  | __ )  _____  __       |
  |  | |  _ | |/ _` / __/ __| |  _ \ / _ \ \/ /       |
  |  | |_| || | (_| \__ \__ \ | |_) | (_) >  <        |
  |   \____||_|\__,_|___/___/ |____/ \___/_/\_\       |
  |                                                   |
  |   PII Pseudonymization API v1.0.0                 |
  |   Architectural Integrity Secured.                |
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
    title="Glass Box PII Pseudonymizer",
    description=(
        "Context-aware PII pseudonymization API. "
        "Replaces personally identifiable information with structured, "
        "human-readable labels that reveal the category without the actual data."
    ),
    version="1.0.0",
)

# CORS — allow the React frontend (dev server on port 5173 or 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
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
        print(f"  [WARN]   GEMINI_API_KEY not set -- live pseudonymization will fail!")
    if not os.getenv("GROQ_API_KEY"):
        print(f"  [INFO]   GROQ_API_KEY not set -- Groq fallback unavailable")

    print()
    print(f"  [READY]  Glass Box API is running")
    print(f"  [READY]  Docs:  http://localhost:8000/docs")
    print(f"  [READY]  Health: http://localhost:8000/health")
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
        print(f"  [AGENT]  Calling Gemini API...")
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
    print(f"  [CACHE]  Response cached")

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

    Returns a list of demo documents that can be loaded into the frontend
    for quick testing without needing to paste text manually.
    """
    if not DEMO_DIR.exists():
        return {"documents": []}

    documents = []
    for doc_file in sorted(DEMO_DIR.glob("*.txt")):
        try:
            content = doc_file.read_text(encoding="utf-8")
            # Create a human-readable name from the filename
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
