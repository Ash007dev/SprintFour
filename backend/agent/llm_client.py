"""
LLM Client — Unified interface for Gemini and Groq API calls.

Provides a single function signature for both providers, switchable via
the LLM_PROVIDER environment variable. Default: Gemini (primary).
Groq is the fallback for rate-limit scenarios.

No multi-agent orchestration — this is a direct, single API call wrapper.
"""

import os
import asyncio
import logging
from typing import Optional

from google import genai
from google.genai import types
from groq import Groq

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Provider configuration
# ---------------------------------------------------------------------------

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Gemini models — 2.5-flash primary, 2.0-flash fallback
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-2.0-flash")
# Groq model — using llama-3.3-70b-versatile for quality on free tier
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Timeout for API calls (seconds)
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "60"))


class LLMError(Exception):
    """Raised when the LLM call fails after all retries."""
    pass


class RateLimitError(LLMError):
    """Raised specifically for rate-limit responses, signaling the caller
    may want to try the fallback provider."""
    pass


# ---------------------------------------------------------------------------
# Gemini client (using google.genai — the current, supported SDK)
# ---------------------------------------------------------------------------

async def _call_gemini_model(client, model: str, system_prompt: str, user_prompt: str) -> str:
    """Call a specific Gemini model. Internal helper."""
    response = await asyncio.wait_for(
        asyncio.to_thread(
            client.models.generate_content,
            model=model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.1,
                response_mime_type="application/json",
            ),
        ),
        timeout=LLM_TIMEOUT,
    )

    if not response.text:
        raise LLMError(f"Gemini ({model}) returned empty response")

    return response.text


async def _call_gemini(system_prompt: str, user_prompt: str) -> str:
    """Call Google Gemini API. Tries 2.5-flash first, falls back to 2.0-flash."""
    if not GEMINI_API_KEY:
        raise LLMError("GEMINI_API_KEY not set in environment")

    client = genai.Client(api_key=GEMINI_API_KEY)

    # Try primary model first (2.5-flash)
    try:
        logger.info(f"Trying Gemini model: {GEMINI_MODEL}")
        return await _call_gemini_model(client, GEMINI_MODEL, system_prompt, user_prompt)
    except asyncio.TimeoutError:
        raise LLMError(f"Gemini API call timed out after {LLM_TIMEOUT}s")
    except Exception as primary_err:
        error_msg = str(primary_err).lower()
        if "api key" in error_msg or "authentication" in error_msg:
            raise LLMError(f"Gemini authentication error: {primary_err}")
        if "429" in error_msg or "rate" in error_msg or "quota" in error_msg:
            raise RateLimitError(f"Gemini rate limit hit: {primary_err}")

        # Primary model failed for non-auth, non-rate-limit reason — try fallback model
        if GEMINI_FALLBACK_MODEL and GEMINI_FALLBACK_MODEL != GEMINI_MODEL:
            logger.warning(
                f"Gemini {GEMINI_MODEL} failed ({primary_err}), trying {GEMINI_FALLBACK_MODEL}"
            )
            try:
                return await _call_gemini_model(
                    client, GEMINI_FALLBACK_MODEL, system_prompt, user_prompt
                )
            except Exception as fallback_err:
                raise LLMError(
                    f"Both Gemini models failed. {GEMINI_MODEL}: {primary_err} | "
                    f"{GEMINI_FALLBACK_MODEL}: {fallback_err}"
                )

        raise LLMError(f"Gemini API error: {primary_err}")


# ---------------------------------------------------------------------------
# Groq client
# ---------------------------------------------------------------------------

async def _call_groq(system_prompt: str, user_prompt: str) -> str:
    """Call Groq API via the groq SDK."""
    if not GROQ_API_KEY:
        raise LLMError("GROQ_API_KEY not set in environment")

    client = Groq(api_key=GROQ_API_KEY)

    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(
                client.chat.completions.create,
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
                max_tokens=4096,
            ),
            timeout=LLM_TIMEOUT,
        )

        content = response.choices[0].message.content
        if not content:
            raise LLMError("Groq returned empty response")

        return content

    except asyncio.TimeoutError:
        raise LLMError(f"Groq API call timed out after {LLM_TIMEOUT}s")
    except LLMError:
        raise
    except Exception as e:
        error_msg = str(e).lower()
        if "429" in error_msg or "rate" in error_msg:
            raise RateLimitError(f"Groq rate limit hit: {e}")
        if "api key" in error_msg or "authentication" in error_msg:
            raise LLMError(f"Groq authentication error: {e}")
        raise LLMError(f"Groq API error: {e}")


# ---------------------------------------------------------------------------
# Unified entry point
# ---------------------------------------------------------------------------

async def call_llm(
    system_prompt: str,
    user_prompt: str,
    provider: Optional[str] = None,
    fallback: bool = True,
) -> str:
    """
    Call the configured LLM provider with automatic fallback.

    Args:
        system_prompt: The system/instruction prompt.
        user_prompt: The user/document prompt.
        provider: Override the default provider ("gemini" or "groq").
        fallback: If True, try the other provider on rate-limit errors.

    Returns:
        Raw string response from the LLM (expected to be valid JSON).

    Raises:
        LLMError: If all providers fail.
    """
    active_provider = provider or LLM_PROVIDER
    providers = {
        "gemini": (_call_gemini, "groq"),
        "groq": (_call_groq, "gemini"),
    }

    if active_provider not in providers:
        raise LLMError(f"Unknown LLM provider: {active_provider}")

    call_fn, fallback_name = providers[active_provider]

    try:
        logger.info(f"Calling {active_provider} LLM...")
        return await call_fn(system_prompt, user_prompt)
    except RateLimitError as e:
        if fallback and fallback_name in providers:
            logger.warning(
                f"{active_provider} rate-limited, falling back to {fallback_name}: {e}"
            )
            fallback_fn, _ = providers[fallback_name]
            try:
                return await fallback_fn(system_prompt, user_prompt)
            except LLMError as fallback_err:
                raise LLMError(
                    f"Both providers failed. {active_provider}: {e} | "
                    f"{fallback_name}: {fallback_err}"
                )
        raise
