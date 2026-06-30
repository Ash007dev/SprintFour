"""
Pseudonymizer — Core orchestration for context-aware PII pseudonymization.

Handles:
1. Sending document text to the LLM agent
2. Parsing the structured span response
3. Performing string substitution to produce pseudonymized output
4. Computing the Trust Score (asymmetric weighting, 0-10 scale)
5. Generating the category breakdown and plain-language summary

This is a single-agent, single-call architecture — one LLM call per document.
No multi-agent orchestration, no chained calls.
"""

import json
import logging
import re
from collections import Counter

from backend.agent.llm_client import call_llm, LLMError
from backend.agent.prompt import build_system_prompt, build_user_prompt
from backend.models import (
    AgentResponse,
    DetectedEntity,
    EntityInfo,
    CategoryCount,
    PseudonymizeResponse,
)

logger = logging.getLogger(__name__)


class PseudonymizationError(Exception):
    """Raised when pseudonymization fails."""
    pass


async def pseudonymize_document(text: str) -> PseudonymizeResponse:
    """
    Process a document through the full pseudonymization pipeline.

    Args:
        text: Raw document text to pseudonymize.

    Returns:
        PseudonymizeResponse with pseudonymized text, entity details,
        trust score, category breakdown, and plain-language summary.

    Raises:
        PseudonymizationError: If the LLM call or response parsing fails.
    """
    # Step 1: Build prompts
    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(text)

    # Step 2: Call the LLM agent (single call)
    try:
        raw_response = await call_llm(system_prompt, user_prompt)
    except LLMError as e:
        raise PseudonymizationError(f"LLM call failed: {e}")

    # Step 3: Parse the structured response
    entities = _parse_agent_response(raw_response, text)

    # Step 4: Validate and fix entity spans
    entities = _validate_and_fix_entities(entities, text)

    # Step 5: Perform string substitution
    pseudonymized_text, entity_infos = _apply_substitutions(text, entities)

    # Step 6: Compute trust score
    trust_score = _compute_trust_score(entities)

    # Step 7: Generate category breakdown
    category_breakdown = _build_category_breakdown(entities)

    # Step 8: Generate plain-language summary
    summary = _generate_summary(entities, category_breakdown, trust_score)

    return PseudonymizeResponse(
        pseudonymized_text=pseudonymized_text,
        entities=entity_infos,
        trust_score=trust_score,
        category_breakdown=category_breakdown,
        summary=summary,
        entity_count=len(entities),
    )


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

def _parse_agent_response(raw_response: str, original_text: str) -> list[DetectedEntity]:
    """
    Parse the LLM's JSON response into validated DetectedEntity objects.

    Handles common LLM output quirks:
    - Markdown code block wrappers
    - Extra whitespace
    - Missing fields (with defaults)
    """
    # Strip markdown code block if present
    cleaned = raw_response.strip()
    if cleaned.startswith("```"):
        # Remove ```json or ``` wrapper
        lines = cleaned.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        logger.error(f"Raw response (first 500 chars): {raw_response[:500]}")
        raise PseudonymizationError(f"LLM returned invalid JSON: {e}")

    # Handle both {"entities": [...]} and direct [...] format
    if isinstance(data, list):
        entities_data = data
    elif isinstance(data, dict) and "entities" in data:
        entities_data = data["entities"]
    else:
        raise PseudonymizationError(
            f"Unexpected response structure: expected 'entities' key or array, got {type(data)}"
        )

    entities = []
    for ent_data in entities_data:
        try:
            entity = DetectedEntity(
                original_text=ent_data.get("original_text", ""),
                start=ent_data.get("start", 0),
                end=ent_data.get("end", 0),
                entity_type=ent_data.get("entity_type", "UNKNOWN"),
                confidence=min(max(float(ent_data.get("confidence", 0.5)), 0.0), 1.0),
                instance_id=ent_data.get("instance_id", "UNKNOWN_1"),
            )
            entities.append(entity)
        except (ValueError, TypeError) as e:
            logger.warning(f"Skipping malformed entity: {ent_data} — {e}")
            continue

    return entities


# ---------------------------------------------------------------------------
# Entity validation and span fixing
# ---------------------------------------------------------------------------

def _validate_and_fix_entities(
    entities: list[DetectedEntity], text: str
) -> list[DetectedEntity]:
    """
    Validate entity spans against the actual document text and fix misalignments.

    LLMs sometimes miscalculate character offsets. This function:
    1. Checks if text[start:end] matches original_text
    2. If not, searches for the original_text in the document and fixes the span
    3. Removes entities that can't be found at all
    4. Removes overlapping entities (keeps higher confidence)
    5. Sorts by start position
    """
    validated = []

    for entity in entities:
        # Check if the span matches
        actual_text = text[entity.start:entity.end]

        if actual_text == entity.original_text:
            validated.append(entity)
            continue

        # Span doesn't match — try to find the text in the document
        search_text = entity.original_text
        idx = text.find(search_text)

        if idx != -1:
            # Found it — fix the span
            entity.start = idx
            entity.end = idx + len(search_text)
            validated.append(entity)
            logger.debug(
                f"Fixed span for '{search_text}': {entity.start}:{entity.end}"
            )
        else:
            # Try case-insensitive search
            lower_text = text.lower()
            lower_search = search_text.lower()
            idx = lower_text.find(lower_search)

            if idx != -1:
                # Found with case difference — use the actual text's casing
                entity.original_text = text[idx:idx + len(search_text)]
                entity.start = idx
                entity.end = idx + len(search_text)
                validated.append(entity)
                logger.debug(
                    f"Fixed span (case-insensitive) for '{search_text}': {entity.start}:{entity.end}"
                )
            else:
                logger.warning(
                    f"Could not find entity '{search_text}' in document — removing"
                )

    # Handle multiple occurrences of the same entity text
    # Group by original_text and ensure all occurrences are captured
    entity_texts = {}
    for entity in validated:
        key = entity.original_text.lower()
        if key not in entity_texts:
            entity_texts[key] = entity
        # Keep the first occurrence's instance_id for consistency

    # Remove overlapping entities (keep higher confidence)
    validated.sort(key=lambda e: (e.start, -(e.end - e.start)))
    non_overlapping = []

    for entity in validated:
        overlaps = False
        for existing in non_overlapping:
            if entity.start < existing.end and entity.end > existing.start:
                # Overlap detected — keep the one with higher confidence
                if entity.confidence > existing.confidence:
                    non_overlapping.remove(existing)
                    non_overlapping.append(entity)
                overlaps = True
                break
        if not overlaps:
            non_overlapping.append(entity)

    # Sort by start position for sequential substitution
    non_overlapping.sort(key=lambda e: e.start)

    return non_overlapping


# ---------------------------------------------------------------------------
# String substitution
# ---------------------------------------------------------------------------

def _apply_substitutions(
    text: str, entities: list[DetectedEntity]
) -> tuple[str, list[EntityInfo]]:
    """
    Replace each detected PII span with its pseudonym label.

    Processes spans from end to start to preserve character positions.
    Tracks positions in both original and pseudonymized text for the UI.
    """
    if not entities:
        return text, []

    # Sort entities by start position (descending) for safe replacement
    sorted_entities = sorted(entities, key=lambda e: e.start, reverse=True)

    pseudonymized = text
    entity_infos = []

    # First pass: perform substitutions from end to start
    for entity in sorted_entities:
        pseudonym = f"[{entity.instance_id}]"
        pseudonymized = (
            pseudonymized[:entity.start] + pseudonym + pseudonymized[entity.end:]
        )

    # Second pass: compute positions in the pseudonymized text
    # Re-sort by start position (ascending) for position tracking
    sorted_asc = sorted(entities, key=lambda e: e.start)
    offset = 0  # Cumulative offset from substitutions

    for entity in sorted_asc:
        pseudonym = f"[{entity.instance_id}]"
        original_len = entity.end - entity.start
        pseudonym_len = len(pseudonym)
        
        pseudo_start = entity.start + offset
        pseudo_end = pseudo_start + pseudonym_len

        entity_infos.append(EntityInfo(
            original_text=entity.original_text,
            pseudonym=pseudonym,
            entity_type=entity.entity_type,
            confidence=entity.confidence,
            start=entity.start,
            end=entity.end,
            pseudonym_start=pseudo_start,
            pseudonym_end=pseudo_end,
        ))

        offset += pseudonym_len - original_len

    return pseudonymized, entity_infos


# ---------------------------------------------------------------------------
# Trust Score
# ---------------------------------------------------------------------------

def _compute_trust_score(entities: list[DetectedEntity]) -> float:
    """
    Compute the Trust Score on a 0-10 scale.

    Asymmetric weighting:
    - Baseline: average confidence * 10
    - Low-confidence entities (below 0.6) subtract more heavily
    - High-confidence entities add proportionally less
    - One uncertain label should reduce trust more than several confident ones increase it

    This mirrors how a real user evaluates tool reliability:
    one visible mistake outweighs many quiet successes.
    """
    if not entities:
        # No entities found — could mean clean document or missed PII
        # Return a moderate score rather than a perfect one
        return 7.0

    confidences = [e.confidence for e in entities]
    avg_confidence = sum(confidences) / len(confidences)

    # Start with the linear average scaled to 0-10
    base_score = avg_confidence * 10

    # Asymmetric adjustment for low-confidence entities
    low_confidence_penalty = 0.0
    high_confidence_count = 0

    for conf in confidences:
        if conf < 0.6:
            # Heavy penalty: the further below 0.6, the worse
            penalty = (0.6 - conf) * 3.0  # Max ~1.8 per entity at conf=0
            low_confidence_penalty += penalty
        elif conf >= 0.85:
            high_confidence_count += 1

    # Apply penalty
    adjusted_score = base_score - low_confidence_penalty

    # Slight boost for consistently high-confidence results, but capped
    if high_confidence_count == len(entities) and len(entities) >= 3:
        adjusted_score += 0.3  # Small consistency bonus

    # Clamp to [0, 10]
    final_score = max(0.0, min(10.0, adjusted_score))

    # Round to 1 decimal place
    return round(final_score, 1)


# ---------------------------------------------------------------------------
# Category breakdown
# ---------------------------------------------------------------------------

def _build_category_breakdown(entities: list[DetectedEntity]) -> list[CategoryCount]:
    """Build a human-readable category breakdown with counts."""

    # Map entity types to human-readable category names
    category_names = {
        "FIRST_NAME": "Names",
        "LAST_NAME": "Names",
        "FULL_NAME": "Names",
        "EMAIL": "Email Addresses",
        "PHONE": "Phone Numbers",
        "ADDRESS": "Addresses",
        "STREET": "Addresses",
        "CITY": "Addresses",
        "STATE": "Addresses",
        "ZIP_CODE": "Addresses",
        "COUNTRY": "Addresses",
        "BUILDING_NUMBER": "Addresses",
        "SSN": "Social Security Numbers",
        "DATE_OF_BIRTH": "Dates of Birth",
        "MEDICAL_RECORD_NUMBER": "Medical Record Numbers",
        "DIAGNOSIS": "Medical Diagnoses",
        "MEDICATION": "Medications",
        "INSURANCE_ID": "Insurance Information",
        "ACCOUNT_NUMBER": "Financial Account Numbers",
        "ROUTING_NUMBER": "Financial Routing Numbers",
        "CREDIT_CARD_NUMBER": "Credit Card Numbers",
        "URL": "Web URLs",
        "IP_ADDRESS": "IP Addresses",
        "USERNAME": "Usernames",
        "PASSWORD": "Passwords",
        "ORGANIZATION_NAME": "Organization Names",
        "NPI": "Provider IDs",
        "FINANCIAL_ID": "Financial IDs",
    }

    # Count by human-readable category
    counts: Counter = Counter()
    for entity in entities:
        category = category_names.get(entity.entity_type, entity.entity_type.replace("_", " ").title())
        counts[category] += 1

    # Sort by count (descending), then alphabetically
    return [
        CategoryCount(category=cat, count=count)
        for cat, count in sorted(counts.items(), key=lambda x: (-x[1], x[0]))
    ]


# ---------------------------------------------------------------------------
# Plain-language summary
# ---------------------------------------------------------------------------

def _generate_summary(
    entities: list[DetectedEntity],
    categories: list[CategoryCount],
    trust_score: float,
) -> str:
    """
    Generate a plain-language paragraph describing what was found and pseudonymized.

    Written for someone with zero technical background:
    - No jargon
    - No confidence-score numbers
    - Just a clear, calm description of what happened
    """
    if not entities:
        return (
            "No personally identifiable information was detected in this document. "
            "The text appears to be free of names, contact details, identification numbers, "
            "or other sensitive personal data."
        )

    total = len(entities)
    cat_descriptions = []

    for cat in categories:
        if cat.count == 1:
            cat_descriptions.append(f"1 {cat.category.lower().rstrip('s')}")
        else:
            cat_descriptions.append(f"{cat.count} {cat.category.lower()}")

    # Build the description
    if len(cat_descriptions) == 1:
        items_text = cat_descriptions[0]
    elif len(cat_descriptions) == 2:
        items_text = f"{cat_descriptions[0]} and {cat_descriptions[1]}"
    else:
        items_text = ", ".join(cat_descriptions[:-1]) + f", and {cat_descriptions[-1]}"

    summary = (
        f"This document was scanned and {total} {'piece' if total == 1 else 'pieces'} "
        f"of personal information {'was' if total == 1 else 'were'} identified: {items_text}. "
        f"Each item has been replaced with a descriptive label that shows what type of "
        f"information was there without revealing the actual sensitive data. "
    )

    # Add trust context
    if trust_score >= 8.5:
        summary += (
            "The system is highly confident in all of the labels applied. "
            "You can trust that the detected items have been correctly identified and categorized."
        )
    elif trust_score >= 6.5:
        summary += (
            "The system is confident in most of the labels applied, though a small number "
            "of items may have been identified with less certainty. "
            "It is recommended to review the output to confirm accuracy."
        )
    else:
        summary += (
            "Some items were identified with lower certainty, which means the system "
            "was not fully sure about every label. Please review the output carefully "
            "to confirm that all personal information was correctly identified."
        )

    return summary
