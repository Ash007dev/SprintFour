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
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

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
    """Load cached responses on startup."""
    loaded = load_cached_responses()
    logger.info(f"Server started. {loaded} cached responses loaded.")

    # Verify required API keys
    provider = os.getenv("LLM_PROVIDER", "gemini")
    if provider == "gemini" and not os.getenv("GEMINI_API_KEY"):
        logger.warning("GEMINI_API_KEY not set — live pseudonymization will fail")
    if provider == "groq" and not os.getenv("GROQ_API_KEY"):
        logger.warning("GROQ_API_KEY not set — live pseudonymization will fail")


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

    # Check cache first
    cached = get_cached_response(text)
    if cached:
        logger.info("Returning cached response")
        return cached

    # Live processing
    try:
        response = await pseudonymize_document(text)
    except PseudonymizationError as e:
        error_msg = str(e)
        logger.error(f"Pseudonymization failed: {error_msg}")

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
        logger.exception(f"Unexpected error during pseudonymization: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "An unexpected error occurred. Please try again.",
            },
        )

    # Cache the successful response
    cache_response(text, response)

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
