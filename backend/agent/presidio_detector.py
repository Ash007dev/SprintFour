"""
Presidio Detector -- first-stage PII detection using Microsoft Presidio.

Presidio handles deterministic, pattern-based PII detection (email formats,
phone patterns, known name lists via spaCy NER) quickly and locally without
any API call. The LLM agent layer on top handles contextual judgment that
Presidio is structurally incapable of.
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Type mapping: Presidio entity types -> our taxonomy
PRESIDIO_TYPE_MAP = {
    "PERSON": "FULL_NAME",
    "EMAIL_ADDRESS": "EMAIL",
    "PHONE_NUMBER": "PHONE",
    "LOCATION": "ADDRESS",
    "CREDIT_CARD": "CREDIT_CARD_NUMBER",
    "CRYPTO": "CRYPTO_ADDRESS",
    "DATE_TIME": "DATE",
    "DOMAIN_NAME": "DOMAIN",
    "IBAN_CODE": "IBAN",
    "IP_ADDRESS": "IP_ADDRESS",
    "MEDICAL_LICENSE": "MEDICAL_LICENSE",
    "NRP": "NATIONALITY",
    "SG_NRIC_FIN": "NATIONAL_ID",
    "UK_NHS": "NATIONAL_HEALTH_ID",
    "US_BANK_NUMBER": "BANK_ACCOUNT_NUMBER",
    "US_DRIVER_LICENSE": "DRIVERS_LICENSE",
    "US_ITIN": "TAX_ID",
    "US_PASSPORT": "PASSPORT_NUMBER",
    "US_SSN": "SSN",
    "URL": "URL",
}


@dataclass
class PresidioDetection:
    """A single PII span detected by Presidio."""
    text: str
    entity_type: str  # Our mapped type
    presidio_type: str  # Original Presidio type
    confidence: float
    start: int
    end: int


def run_presidio(text: str) -> list[PresidioDetection]:
    """
    Run Presidio analyzer on text and return detected PII spans.

    Returns an empty list if Presidio is not available (graceful degradation).
    """
    try:
        from presidio_analyzer import AnalyzerEngine
    except ImportError:
        logger.warning("  [PRESIDIO] presidio-analyzer not installed, skipping base pass")
        return []

    try:
        engine = _get_engine()
        results = engine.analyze(
            text=text,
            language="en",
            score_threshold=0.4,  # Low threshold -- Agent 1 will filter
        )

        detections = []
        for result in results:
            mapped_type = PRESIDIO_TYPE_MAP.get(result.entity_type, result.entity_type)
            detected_text = text[result.start:result.end]

            detections.append(PresidioDetection(
                text=detected_text,
                entity_type=mapped_type,
                presidio_type=result.entity_type,
                confidence=round(result.score, 2),
                start=result.start,
                end=result.end,
            ))

        logger.info(f"  [PRESIDIO] Found {len(detections)} potential PII spans")
        for d in detections[:10]:
            logger.debug(f"  [PRESIDIO]   {d.entity_type}: '{d.text}' ({d.confidence})")
        if len(detections) > 10:
            logger.debug(f"  [PRESIDIO]   ... and {len(detections) - 10} more")

        return detections

    except Exception as e:
        logger.warning(f"  [PRESIDIO] Detection failed (continuing without): {e}")
        return []


# Singleton engine to avoid re-initialization
_engine_instance = None


def _get_engine():
    """Get or create the Presidio analyzer engine (singleton)."""
    global _engine_instance
    if _engine_instance is None:
        from presidio_analyzer import AnalyzerEngine
        logger.info("  [PRESIDIO] Initializing analyzer engine...")
        _engine_instance = AnalyzerEngine()
        logger.info("  [PRESIDIO] Engine ready")
    return _engine_instance
