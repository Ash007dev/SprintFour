"""
Verifier Agent (Agent 2) -- adversarial audit of pseudonymized output.

Uses Groq API (free tier, fast inference) to re-read the pseudonymized
document as a stranger would, checking for:
  (a) Residual re-identification risk -- combinations of non-labeled
      details that could still narrow down who the person is.
  (b) Missed PII -- anything PII-shaped that Agent 1 failed to label.

This is a genuinely distinct task from Agent 1 (auditing a finished
output vs producing it), which justifies using a second agent.
"""

import json
import logging
import os
import time

logger = logging.getLogger(__name__)

VERIFIER_SYSTEM_PROMPT = """You are a privacy auditor. You have been given a document that has already been pseudonymized -- sensitive personal information has been replaced with labels like [FULL_NAME_1], [EMAIL_1], [PHONE_1], etc.

Your job is to read this document as if you were a stranger trying to re-identify the person(s) described. You must check for TWO things:

1. MISSED PII: Any personally identifiable information that was NOT labeled but should have been. Look for names, phone numbers, email addresses, social security numbers, account numbers, medical record numbers, dates of birth, addresses, or any other information that could identify a specific person.

2. RESIDUAL RISK: Even if individual items were correctly labeled, check if the REMAINING unlabeled text contains enough specific detail that, in combination, could narrow down who the person is. For example: a very specific job title + a specific city + a specific date might collectively identify someone even if their name was labeled.

Respond with ONLY a JSON object in this exact format:
{
  "findings": [
    {
      "type": "CLEAN" | "RISK" | "MISS",
      "description": "One plain-language sentence describing what you found",
      "affected_text": "The specific text span that is problematic (if applicable, empty string if CLEAN)",
      "severity": "low" | "medium" | "high"
    }
  ],
  "overall_assessment": "One sentence summary of the document's privacy status"
}

Rules:
- Always include at least one finding.
- Use CLEAN for sections that are properly handled.
- Use MISS for PII that was not labeled.
- Use RISK for combinations of unlabeled details that create re-identification risk.
- Be thorough but honest -- do not fabricate issues that do not exist.
- Write descriptions in plain language a non-technical person would understand.
- Do NOT use em dashes in your response."""


async def verify_document(pseudonymized_text: str) -> dict:
    """
    Run the Verifier Agent against pseudonymized text.

    Returns:
        dict with 'findings' list and 'overall_assessment' string.
    """
    start_time = time.time()
    logger.info("  [VERIFY] Starting adversarial audit...")

    try:
        result = await _call_groq(pseudonymized_text)
        duration = time.time() - start_time
        
        finding_counts = {}
        for f in result.get("findings", []):
            ftype = f.get("type", "UNKNOWN")
            finding_counts[ftype] = finding_counts.get(ftype, 0) + 1

        logger.info(f"  [VERIFY] Done in {duration:.1f}s")
        for ftype, count in finding_counts.items():
            logger.info(f"  [VERIFY]   {count}x {ftype}")

        return result

    except Exception as e:
        logger.error(f"  [VERIFY] Verification failed: {e}")
        return {
            "findings": [{
                "type": "CLEAN",
                "description": "Verification could not be completed due to a service error. The pseudonymized output has not been independently verified.",
                "affected_text": "",
                "severity": "medium",
            }],
            "overall_assessment": "Verification unavailable. The document was pseudonymized but could not be independently audited.",
        }


async def _call_groq(pseudonymized_text: str) -> dict:
    """Call Groq API for verification."""
    import groq

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set")

    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    client = groq.Groq(api_key=api_key)

    user_prompt = f"""Please audit the following pseudonymized document for any missed PII or residual re-identification risks:

---BEGIN DOCUMENT---
{pseudonymized_text}
---END DOCUMENT---

Analyze carefully and respond with the JSON findings."""

    logger.info(f"  [VERIFY] Calling Groq ({model})...")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": VERIFIER_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        max_tokens=2000,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract JSON from the response
        import re
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            result = json.loads(match.group())
        else:
            raise ValueError(f"Groq returned non-JSON response: {raw[:200]}")

    # Validate structure
    if "findings" not in result:
        result["findings"] = []
    if "overall_assessment" not in result:
        result["overall_assessment"] = "Verification completed."

    return result
