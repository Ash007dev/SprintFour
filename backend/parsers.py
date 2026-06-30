"""
File Parsers -- extract plain text from uploaded files.

Supports: PDF, JSON, TXT, MD, CSV, LOG, and other plain-text formats.
PDF text extraction uses pdfplumber (no AI involved).
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_text(file_bytes: bytes, filename: str) -> str:
    """
    Extract plain text from a file based on its extension.

    Args:
        file_bytes: Raw file content as bytes.
        filename: Original filename (used to determine format).

    Returns:
        Extracted plain text string.

    Raises:
        ValueError: If the file format is unsupported or extraction fails.
    """
    ext = Path(filename).suffix.lower()

    if ext == ".pdf":
        return _extract_pdf(file_bytes)
    elif ext == ".json":
        return _extract_json(file_bytes)
    elif ext in (".txt", ".md", ".csv", ".log", ".text", ".rst", ".tsv"):
        return _extract_plaintext(file_bytes)
    elif ext == ".docx":
        return _extract_docx(file_bytes)
    else:
        # Try as plain text for unknown extensions
        try:
            return _extract_plaintext(file_bytes)
        except Exception:
            raise ValueError(
                f"Unsupported file format: {ext}. "
                "Supported: PDF, JSON, TXT, MD, CSV, LOG, DOCX"
            )


def _extract_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF using pdfplumber."""
    try:
        import pdfplumber
        import io

        pages_text = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    pages_text.append(text)
                    logger.debug(f"  [PARSE]  PDF page {i+1}: {len(text)} chars")

        if not pages_text:
            raise ValueError("PDF contains no extractable text (may be image-only)")

        result = "\n\n".join(pages_text)
        logger.info(f"  [PARSE]  Extracted {len(result)} chars from {len(pages_text)} PDF pages")
        return result

    except ImportError:
        raise ValueError("PDF support requires pdfplumber: pip install pdfplumber")
    except Exception as e:
        if "no extractable text" in str(e).lower():
            raise
        raise ValueError(f"Failed to extract text from PDF: {e}")


def _extract_json(file_bytes: bytes) -> str:
    """Extract all string values from JSON, recursively."""
    try:
        text = file_bytes.decode("utf-8")
        data = json.loads(text)
        strings = []
        _collect_strings(data, strings)
        result = "\n".join(strings)
        logger.info(f"  [PARSE]  Extracted {len(strings)} string values from JSON")
        return result
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON file: {e}")


def _collect_strings(obj, strings: list):
    """Recursively collect all string values from a JSON structure."""
    if isinstance(obj, str):
        if obj.strip():
            strings.append(obj.strip())
    elif isinstance(obj, dict):
        for value in obj.values():
            _collect_strings(value, strings)
    elif isinstance(obj, list):
        for item in obj:
            _collect_strings(item, strings)


def _extract_plaintext(file_bytes: bytes) -> str:
    """Extract text from plain-text files."""
    # Try UTF-8 first, then fallback encodings
    for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            text = file_bytes.decode(encoding)
            logger.info(f"  [PARSE]  Read plain text ({encoding}): {len(text)} chars")
            return text
        except (UnicodeDecodeError, LookupError):
            continue

    raise ValueError("Could not decode file as text with any supported encoding")


def _extract_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX files."""
    try:
        from docx import Document
        import io

        doc = Document(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        result = "\n\n".join(paragraphs)
        logger.info(f"  [PARSE]  Extracted {len(paragraphs)} paragraphs from DOCX")
        return result
    except ImportError:
        raise ValueError("DOCX support requires python-docx: pip install python-docx")
    except Exception as e:
        raise ValueError(f"Failed to extract text from DOCX: {e}")
