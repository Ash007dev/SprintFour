"""
Pseudonymization Agent Prompt  - System prompt and few-shot examples
for the context-aware PII pseudonymization agent.

This module constructs the system prompt sent to the LLM, including:
- Clear task definition (contextual PII detection, structured span output)
- Open/extensible entity type taxonomy
- Few-shot examples from the ai4privacy/pii-masking-43k dataset
- Explicit instructions for contextual disambiguation

The LLM returns ONLY structured span data  - the backend performs the
actual string substitution to produce pseudonymized output text.
"""

import json
from pathlib import Path

FEW_SHOT_PATH = Path(__file__).parent.parent.parent / "data" / "few_shot_examples.json"


def _load_few_shot_examples() -> list[dict]:
    """Load few-shot examples from the pre-selected dataset records."""
    if FEW_SHOT_PATH.exists():
        with open(FEW_SHOT_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


# ---------------------------------------------------------------------------
# Hardcoded fallback few-shot examples (in case the dataset file isn't ready)
# These are derived from the ai4privacy/pii-masking-43k open dataset.
# ---------------------------------------------------------------------------

FALLBACK_FEW_SHOT_EXAMPLES = [
    {
        "input_text": "Please write an email to Hazel Turcotte at Annetta69@hotmail.com discussing the latest updates in consumer protection laws.",
        "expected_output": {
            "entities": [
                {"original_text": "Hazel Turcotte", "start": 25, "end": 39, "entity_type": "FULLNAME", "confidence": 0.95, "instance_id": "FULLNAME_1"},
                {"original_text": "Annetta69@hotmail.com", "start": 43, "end": 64, "entity_type": "EMAIL", "confidence": 0.98, "instance_id": "EMAIL_1"},
            ]
        }
    },
    {
        "input_text": "Create a list of mental health support organizations in Lake Pedroberg and Bernardchester for Jessie Witting to share with their network.",
        "expected_output": {
            "entities": [
                {"original_text": "Lake Pedroberg", "start": 58, "end": 72, "entity_type": "CITY", "confidence": 0.88, "instance_id": "CITY_1"},
                {"original_text": "Bernardchester", "start": 77, "end": 91, "entity_type": "CITY", "confidence": 0.87, "instance_id": "CITY_2"},
                {"original_text": "Jessie Witting", "start": 96, "end": 110, "entity_type": "FULLNAME", "confidence": 0.94, "instance_id": "FULLNAME_1"},
            ]
        }
    },
    {
        "input_text": "13. Create a risk management framework for protecting sensitive customer data, including Tyshawn.Rath90@hotmail.com, ZxC55mrNmIe4, and 5287761891196274.",
        "expected_output": {
            "entities": [
                {"original_text": "Tyshawn.Rath90@hotmail.com", "start": 89, "end": 115, "entity_type": "EMAIL", "confidence": 0.97, "instance_id": "EMAIL_1"},
                {"original_text": "ZxC55mrNmIe4", "start": 117, "end": 129, "entity_type": "PASSWORD", "confidence": 0.82, "instance_id": "PASSWORD_1"},
                {"original_text": "5287761891196274", "start": 135, "end": 151, "entity_type": "CREDIT_CARD_NUMBER", "confidence": 0.91, "instance_id": "CREDIT_CARD_NUMBER_1"},
            ]
        }
    },
    {
        "input_text": "Prepare a grant proposal for Zola Doyle to study the effects of peer pressure on Neither risk-taking behavior.",
        "expected_output": {
            "entities": [
                {"original_text": "Zola", "start": 29, "end": 33, "entity_type": "FIRST_NAME", "confidence": 0.93, "instance_id": "FIRST_NAME_1"},
                {"original_text": "Doyle", "start": 34, "end": 39, "entity_type": "LAST_NAME", "confidence": 0.93, "instance_id": "LAST_NAME_1"},
            ]
        }
    },
    {
        "input_text": "Please create a legal analysis of the sports betting laws in Montana and send it to Nichole.Kulas96@gmail.com.",
        "expected_output": {
            "entities": [
                {"original_text": "Montana", "start": 62, "end": 69, "entity_type": "STATE", "confidence": 0.90, "instance_id": "STATE_1"},
                {"original_text": "Nichole.Kulas96@gmail.com", "start": 84, "end": 109, "entity_type": "EMAIL", "confidence": 0.97, "instance_id": "EMAIL_1"},
            ]
        }
    },
    {
        "input_text": "Please develop a survey for Heller - Dibbert to assess the impact of Industrial-Organizational Psychology interventions on employee well-being at 578 Casimer Passage.",
        "expected_output": {
            "entities": [
                {"original_text": "Heller - Dibbert", "start": 28, "end": 44, "entity_type": "ORGANIZATION_NAME", "confidence": 0.85, "instance_id": "ORGANIZATION_NAME_1"},
                {"original_text": "578", "start": 147, "end": 150, "entity_type": "BUILDING_NUMBER", "confidence": 0.80, "instance_id": "BUILDING_NUMBER_1"},
                {"original_text": "Casimer Passage", "start": 151, "end": 166, "entity_type": "STREET", "confidence": 0.88, "instance_id": "STREET_1"},
            ]
        }
    },
]


def build_system_prompt() -> str:
    """
    Construct the complete system prompt for the pseudonymization agent.

    The prompt instructs the LLM to:
    1. Analyze input text for PII using contextual understanding
    2. Return structured JSON with detected spans
    3. Use consistent instance numbering per unique entity value
    4. Distinguish PII from non-PII based on context
    """

    # Try to load dataset-derived examples first, fall back to hardcoded
    few_shot_examples = _load_few_shot_examples()
    if not few_shot_examples:
        few_shot_examples = FALLBACK_FEW_SHOT_EXAMPLES

    # Format few-shot examples for the prompt
    few_shot_text = _format_few_shot_examples(few_shot_examples)

    system_prompt = f"""You are a context-aware PII (Personally Identifiable Information) detection agent. Your task is to analyze input text and identify all PII entities, returning structured span data.

## TASK
Given input text, detect all PII entities and return a JSON object with the following structure:
{{
  "entities": [
    {{
      "original_text": "<exact text as it appears in the document>",
      "start": <character start index, 0-based>,
      "end": <character end index, exclusive>,
      "entity_type": "<category label>",
      "confidence": <float 0.0-1.0>,
      "instance_id": "<ENTITY_TYPE_N>"
    }}
  ]
}}

## ENTITY TYPE TAXONOMY (open, extensible  - use the most specific applicable type)
Common types include but are NOT limited to:
- FIRST_NAME, LAST_NAME, FULL_NAME  - personal names
- EMAIL  - email addresses
- PHONE  - phone numbers (any format)
- ADDRESS  - full street addresses
- STREET  - street names
- CITY  - city names
- STATE  - state/province names
- ZIP_CODE  - postal/zip codes
- COUNTRY  - country names
- SSN  - Social Security Numbers
- DATE_OF_BIRTH  - dates of birth
- MEDICAL_RECORD_NUMBER  - MRNs
- DIAGNOSIS  - medical diagnoses
- MEDICATION  - medication names with dosages
- INSURANCE_ID  - insurance policy numbers
- ACCOUNT_NUMBER  - bank/financial account numbers
- ROUTING_NUMBER  - bank routing numbers
- CREDIT_CARD_NUMBER  - credit card numbers
- URL  - web addresses
- IP_ADDRESS  - IPv4/IPv6 addresses
- USERNAME  - online usernames
- PASSWORD  - passwords
- ORGANIZATION_NAME  - company/organization names (only when identifying a specific, named entity  - not generic industry terms)
- NPI  - National Provider Identifier numbers
- BUILDING_NUMBER  - building/house numbers
- FINANCIAL_ID  - FINRA CRD numbers, fund identifiers, etc.

If you encounter PII that doesn't fit these categories, create a descriptive type using UPPER_SNAKE_CASE.

## CRITICAL: CONTEXTUAL DISAMBIGUATION
You MUST use context to distinguish PII from non-PII:
- "John" as a person's first name → FIRST_NAME. "John" in "John Street" → part of STREET (not a name).
- "Apple" as a company name → ORGANIZATION_NAME (when referring to the specific company). "apple" as a fruit → NOT PII.
- A phone-formatted number (e.g., "(217) 555-0193") → PHONE. A quantity like "200 shares" → NOT PII.
- "Springfield" as part of a specific address → CITY. "Springfield" in a generic reference to a location without PII context → evaluate carefully.
- "Dr. Sarah Mitchell" used as a person's name → FULL_NAME. "Dr." as a generic title → not PII on its own.
- Company names (e.g., "BlueCross BlueShield", "JPMorgan Chase") → ORGANIZATION_NAME only when they help identify a specific person's account or relationship, not when mentioned generically.

## INSTANCE NUMBERING RULES
- Each unique entity VALUE within the document gets a consistent instance number.
- If "John Doe" appears twice, both are labeled FULL_NAME_1.
- If a second, different full name appears (e.g., "Jane Smith"), it becomes FULL_NAME_2.
- Instance numbers are per entity TYPE, not global. FIRST_NAME_1 and LAST_NAME_1 are separate counters.

## CONFIDENCE SCORING GUIDELINES
- 0.95-1.0: Unambiguous PII with clear context (explicit email, SSN format, etc.)
- 0.85-0.94: High confidence, clear context but some ambiguity possible
- 0.70-0.84: Moderate confidence, context supports PII interpretation
- 0.50-0.69: Low confidence, ambiguous context, could be PII or not
- Below 0.50: Do not include  - insufficient evidence

## IMPORTANT RULES
1. Return ONLY the JSON object. No explanations, no markdown formatting, no code blocks.
2. The "start" and "end" indices MUST exactly match the character positions in the input text.
3. "end" is EXCLUSIVE  - text[start:end] should yield exactly "original_text".
4. Do NOT modify the input text. Do NOT return rewritten text. Return ONLY span metadata.
5. If the input contains NO PII, return: {{"entities": []}}
6. Process the ENTIRE document  - do not stop partway through.
7. Entities must NOT overlap. If a larger span contains a smaller one (e.g., full name contains first and last name), prefer the more granular labeling (separate FIRST_NAME and LAST_NAME) unless the text is clearly a single unit.

## FEW-SHOT EXAMPLES
{few_shot_text}
"""
    return system_prompt


def _format_few_shot_examples(examples: list[dict]) -> str:
    """Format few-shot examples for inclusion in the system prompt."""
    formatted_parts = []

    for i, ex in enumerate(examples, 1):
        input_text = ex.get("input_text", ex.get("filled_text", ""))
        
        # Handle both formats: pre-formatted with expected_output, or raw dataset format
        if "expected_output" in ex:
            output = json.dumps(ex["expected_output"], indent=2)
        elif "detected_entities" in ex:
            # Convert from dataset format to our output format
            entities = []
            type_counters = {}
            for ent in ex["detected_entities"]:
                etype = ent["entity_type"].upper()
                # Map dataset types to our taxonomy
                etype = _map_entity_type(etype)
                type_counters[etype] = type_counters.get(etype, 0) + 1
                
                start = input_text.find(ent["original_text"])
                if start == -1:
                    continue
                    
                entities.append({
                    "original_text": ent["original_text"],
                    "start": start,
                    "end": start + len(ent["original_text"]),
                    "entity_type": etype,
                    "confidence": 0.90,
                    "instance_id": f"{etype}_{type_counters[etype]}",
                })
            output = json.dumps({"entities": entities}, indent=2)
        else:
            continue

        formatted_parts.append(
            f"### Example {i}\nInput: \"{input_text}\"\nOutput:\n{output}"
        )

    return "\n\n".join(formatted_parts)


def _map_entity_type(dataset_type: str) -> str:
    """Map ai4privacy dataset entity types to our taxonomy."""
    mapping = {
        "FULLNAME": "FULL_NAME",
        "FIRSTNAME": "FIRST_NAME",
        "LASTNAME": "LAST_NAME",
        "NAME": "ORGANIZATION_NAME",
        "CREDITCARDNUMBER": "CREDIT_CARD_NUMBER",
        "BUILDINGNUMBER": "BUILDING_NUMBER",
        "IPV4": "IP_ADDRESS",
        "IPV6": "IP_ADDRESS",
        "ZIPCODE": "ZIP_CODE",
        "JOBAREA": "JOB_AREA",
        "CURRENCYCODE": "CURRENCY_CODE",
        "NUMBER": "PHONE",  # Context-dependent, but most in the dataset are phone-like
    }
    return mapping.get(dataset_type, dataset_type)


def build_user_prompt(document_text: str, presidio_detections: list = None) -> str:
    """
    Construct the user prompt containing the document to analyze.

    If Presidio base-pass results are provided, they are included as
    grounding for the LLM to confirm, adjust, or extend.
    """
    presidio_section = ""
    if presidio_detections:
        presidio_lines = []
        for d in presidio_detections:
            presidio_lines.append(
                f"  - \"{d.text}\" (type={d.presidio_type}, confidence={d.confidence}, "
                f"pos={d.start}:{d.end})"
            )
        presidio_section = f"""

BASE-PASS DETECTIONS (from a pattern-based detector, provided as grounding):
These were detected by a rule-based system. Use them as a starting point, but
apply your own contextual judgment. You may confirm, adjust the type, change
confidence, or reject any of these. You should also detect PII the base pass missed.
{chr(10).join(presidio_lines)}
"""

    return f"""Analyze the following document for PII and return the structured JSON output as specified.
{presidio_section}
DOCUMENT:
{document_text}"""

