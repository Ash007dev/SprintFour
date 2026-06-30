"""
In-Memory Cache  - Caches verified agent responses for demo documents.

Keyed by a hash of the input text. Pre-populated with verified responses
for the fixed demo documents so that a live judging session isn't fully
dependent on a fresh API call succeeding in real time.

The live/dynamic path still works correctly  - this is purely a fallback
for reliability during demos.

No persistent storage. No database. Cache lives only in process memory.
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Optional

from backend.models import PseudonymizeResponse

logger = logging.getLogger(__name__)

# In-memory cache: text_hash -> PseudonymizeResponse
_cache: dict[str, PseudonymizeResponse] = {}

CACHE_DIR = Path(__file__).parent.parent / "data" / "cached_responses"


def _hash_text(text: str) -> str:
    """Generate a stable hash for document text."""
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()[:16]


def get_cached_response(text: str) -> Optional[PseudonymizeResponse]:
    """
    Check if a cached response exists for the given text.

    Returns None if no cache hit  - caller should proceed with live API call.
    """
    text_hash = _hash_text(text)
    cached = _cache.get(text_hash)
    if cached:
        logger.info(f"Cache hit for text hash {text_hash}")
    return cached


def cache_response(text: str, response: PseudonymizeResponse) -> None:
    """
    Store a response in the in-memory cache.

    Also saves to disk so it can be pre-loaded on next startup.
    """
    text_hash = _hash_text(text)
    _cache[text_hash] = response
    logger.info(f"Cached response for text hash {text_hash}")

    # Persist to disk for pre-loading
    _save_to_disk(text_hash, response)


def _save_to_disk(text_hash: str, response: PseudonymizeResponse) -> None:
    """Save a cached response to disk as JSON."""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_file = CACHE_DIR / f"{text_hash}.json"
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(response.model_dump(), f, indent=2, ensure_ascii=False)
        logger.info(f"Saved cache to disk: {cache_file}")
    except Exception as e:
        logger.warning(f"Failed to save cache to disk: {e}")


def load_cached_responses() -> int:
    """
    Load any previously-saved cached responses from disk.

    Called at startup to pre-populate the cache with verified demo responses.
    Returns the number of responses loaded.
    """
    if not CACHE_DIR.exists():
        return 0

    loaded = 0
    for cache_file in CACHE_DIR.glob("*.json"):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            response = PseudonymizeResponse(**data)
            text_hash = cache_file.stem
            _cache[text_hash] = response
            loaded += 1
        except Exception as e:
            logger.warning(f"Failed to load cache file {cache_file}: {e}")

    logger.info(f"Pre-loaded {loaded} cached responses from disk")
    return loaded


def clear_cache() -> None:
    """Clear the in-memory cache (for testing)."""
    _cache.clear()
