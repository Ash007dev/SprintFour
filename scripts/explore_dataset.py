"""
Dataset Exploration Script
Loads the ai4privacy/pii-masking-43k dataset from Hugging Face,
inspects its structure, and selects diverse few-shot examples
for the pseudonymization agent's system prompt.

Uses on_bad_lines='skip' to handle the known CSV parsing issue at line 42759.
"""

import json
import ast
from pathlib import Path
from datasets import load_dataset

OUTPUT_DIR = Path(__file__).parent.parent / "data"
FEW_SHOT_PATH = OUTPUT_DIR / "few_shot_examples.json"


def load_ds():
    """Load the dataset, skipping the malformed CSV row."""
    print("Loading ai4privacy/pii-masking-43k dataset...")
    ds = load_dataset(
        "ai4privacy/pii-masking-43k",
        split="train",
        on_bad_lines="skip",  # Skip the malformed row at line 42759
    )
    print(f"Dataset size: {len(ds)} records")
    print(f"Column names: {ds.column_names}")
    return ds


def parse_record(record):
    """Parse a single dataset record into a structured format usable as a few-shot example."""
    template = record.get("Template", "")
    filled = record.get("Filled Template", "")
    tokens_str = record.get("Tokens", "[]")
    tokenised_str = record.get("Tokenised Filled Template", "[]")

    # Parse string representations of lists
    try:
        bio_tags = ast.literal_eval(tokens_str)
        word_tokens = ast.literal_eval(tokenised_str)
    except (ValueError, SyntaxError):
        return None

    if not bio_tags or not word_tokens or len(bio_tags) != len(word_tokens):
        return None

    # Extract entities from BIO tags
    entities = []
    current_entity = None
    current_tokens = []

    for token, tag in zip(word_tokens, bio_tags):
        if tag.startswith("B-"):
            # Save previous entity
            if current_entity:
                entities.append({
                    "type": current_entity,
                    "value": _reconstruct_text(current_tokens),
                })
            current_entity = tag[2:]
            current_tokens = [token]
        elif tag.startswith("I-") and current_entity:
            current_tokens.append(token)
        else:
            if current_entity:
                entities.append({
                    "type": current_entity,
                    "value": _reconstruct_text(current_tokens),
                })
                current_entity = None
                current_tokens = []

    # Don't forget the last entity
    if current_entity:
        entities.append({
            "type": current_entity,
            "value": _reconstruct_text(current_tokens),
        })

    return {
        "template": template,
        "filled_text": filled,
        "entities": entities,
        "entity_types": list(set(e["type"] for e in entities)),
    }


def _reconstruct_text(tokens):
    """Reconstruct readable text from WordPiece tokens."""
    text = ""
    for token in tokens:
        if token.startswith("##"):
            text += token[2:]
        elif text and not text.endswith(("-", "/", "(")):
            text += " " + token
        else:
            text += token
    return text


def select_few_shot_examples(ds, target_count=8):
    """
    Select diverse few-shot examples covering a wide range of entity types.
    Prioritizes records with multiple entity types and moderate length.
    """
    candidates = []
    covered_types = set()

    # Target entity types we want to cover
    priority_types = {
        "FULLNAME", "FIRSTNAME", "LASTNAME", "EMAIL", "CITY", "STATE",
        "URL", "USERNAME", "ZIPCODE", "STREET", "BUILDINGNUMBER",
        "PASSWORD", "CREDITCARDNUMBER", "IPV4", "NUMBER", "NAME",
        "JOBAREA", "GENDER",
    }

    for i in range(min(5000, len(ds))):
        record = ds[i]
        parsed = parse_record(record)
        if not parsed or not parsed["entities"]:
            continue

        filled = parsed["filled_text"]
        # Filter: moderate length, has meaningful entities
        if len(filled) < 40 or len(filled) > 400:
            continue

        # Score: more uncovered entity types = higher priority
        new_types = set(parsed["entity_types"]) - covered_types
        type_diversity = len(set(parsed["entity_types"]))

        candidates.append({
            "parsed": parsed,
            "new_types": new_types,
            "diversity": type_diversity,
            "index": i,
        })

    # Sort by number of new entity types covered, then by diversity
    candidates.sort(key=lambda c: (len(c["new_types"]), c["diversity"]), reverse=True)

    selected = []
    for candidate in candidates:
        if len(selected) >= target_count:
            break
        # Prefer records that cover new entity types
        selected.append(candidate["parsed"])
        covered_types.update(candidate["parsed"]["entity_types"])

    return selected


def save_few_shot_examples(examples):
    """Save selected examples to JSON."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Format for prompt embedding
    formatted = []
    for ex in examples:
        formatted.append({
            "input_text": ex["filled_text"],
            "template": ex["template"],
            "detected_entities": [
                {"original_text": e["value"], "entity_type": e["type"]}
                for e in ex["entities"]
            ],
        })

    with open(FEW_SHOT_PATH, "w", encoding="utf-8") as f:
        json.dump(formatted, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(formatted)} few-shot examples to {FEW_SHOT_PATH}")
    print(f"Entity types covered: {sorted(set(t for ex in examples for t in ex['entity_types']))}")

    for i, ex in enumerate(examples):
        print(f"\n--- Example {i + 1} ---")
        print(f"  Text: {ex['filled_text'][:120]}...")
        print(f"  Types: {ex['entity_types']}")
        print(f"  Entities: {[(e['type'], e['value'][:30]) for e in ex['entities']]}")


def collect_all_entity_types(ds, sample_size=2000):
    """Catalog all entity types present in a sample."""
    types = set()
    for i in range(min(sample_size, len(ds))):
        parsed = parse_record(ds[i])
        if parsed:
            types.update(parsed["entity_types"])

    print(f"\nAll entity types found in {min(sample_size, len(ds))} records:")
    for t in sorted(types):
        print(f"  - {t}")
    return types


if __name__ == "__main__":
    ds = load_ds()

    # Inspect first few records
    print("\n" + "=" * 80)
    print("SAMPLE RECORDS")
    print("=" * 80)
    for i in range(3):
        print(f"\n--- Record {i} ---")
        for key in ds.column_names:
            val = str(ds[i][key])[:200]
            print(f"  {key}: {val}")

    # Collect entity types
    all_types = collect_all_entity_types(ds)

    # Select and save few-shot examples
    examples = select_few_shot_examples(ds)
    save_few_shot_examples(examples)

    print("\n✓ Dataset exploration complete.")
