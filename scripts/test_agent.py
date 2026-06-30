"""
Agent Test Script — Tests the pseudonymization agent against all demo documents.

Run standalone: python scripts/test_agent.py
Tests the full pipeline: prompt construction -> LLM call -> response parsing ->
span substitution -> trust score -> summary generation.
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.agent.pseudonymizer import pseudonymize_document, PseudonymizationError

DEMO_DIR = Path(__file__).parent.parent / "data" / "demo_documents"


def load_demo_documents() -> dict[str, str]:
    """Load all demo documents."""
    docs = {}
    for doc_file in sorted(DEMO_DIR.glob("*.txt")):
        docs[doc_file.stem] = doc_file.read_text(encoding="utf-8")
    return docs


async def test_document(name: str, text: str) -> bool:
    """Test pseudonymization on a single document."""
    print(f"\n{'='*80}")
    print(f"TESTING: {name}")
    print(f"{'='*80}")
    print(f"Input length: {len(text)} characters")
    print(f"First 200 chars: {text[:200]}...")

    try:
        response = await pseudonymize_document(text)
    except PseudonymizationError as e:
        print(f"\nERROR: {e}")
        return False
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Display results
    print(f"\n--- PSEUDONYMIZED OUTPUT ---")
    print(response.pseudonymized_text[:500])
    if len(response.pseudonymized_text) > 500:
        print(f"... ({len(response.pseudonymized_text)} total chars)")

    print(f"\n--- DETECTED ENTITIES ({response.entity_count}) ---")
    for entity in response.entities:
        print(
            f"  [{entity.pseudonym}] '{entity.original_text}' "
            f"(type={entity.entity_type}, confidence={entity.confidence:.2f}, "
            f"pos={entity.start}:{entity.end})"
        )

    print(f"\n--- TRUST SCORE ---")
    print(f"  {response.trust_score} / 10")

    print(f"\n--- CATEGORY BREAKDOWN ---")
    for cat in response.category_breakdown:
        print(f"  {cat.category}: {cat.count}")

    print(f"\n--- SUMMARY ---")
    print(f"  {response.summary}")

    # Basic validation checks
    print(f"\n--- VALIDATION ---")
    issues = []

    # Check that pseudonym labels appear in the output
    for entity in response.entities:
        if entity.pseudonym not in response.pseudonymized_text:
            issues.append(f"Pseudonym {entity.pseudonym} not found in output")

    # Check that original PII is NOT in the pseudonymized output
    for entity in response.entities:
        if entity.original_text in response.pseudonymized_text:
            issues.append(
                f"Original PII '{entity.original_text}' still present in output!"
            )

    # Check trust score is valid
    if not 0 <= response.trust_score <= 10:
        issues.append(f"Invalid trust score: {response.trust_score}")

    if issues:
        print(f"  ISSUES FOUND:")
        for issue in issues:
            print(f"    - {issue}")
        return False
    else:
        print(f"  All checks passed!")
        return True


async def main():
    """Test all demo documents."""
    docs = load_demo_documents()

    if not docs:
        print("No demo documents found! Check data/demo_documents/ directory.")
        sys.exit(1)

    print(f"Found {len(docs)} demo documents: {list(docs.keys())}")

    results = {}
    for name, text in docs.items():
        success = await test_document(name, text)
        results[name] = success

    # Summary
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")
    for name, success in results.items():
        status = "PASS" if success else "FAIL"
        print(f"  {name}: {status}")

    total = len(results)
    passed = sum(1 for s in results.values() if s)
    print(f"\n{passed}/{total} tests passed")

    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
