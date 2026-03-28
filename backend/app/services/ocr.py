"""
OCR service for extracting text from screenshot images.
Supports WhatsApp, Instagram, and other messaging app screenshots.

Uses pytesseract (Tesseract OCR) if available, with a graceful fallback
that returns an empty string when Tesseract is not installed.
"""

import io
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# Track whether pytesseract + Tesseract engine are usable
_tesseract_available: Optional[bool] = None


def _check_tesseract() -> bool:
    """Check if pytesseract and the Tesseract binary are available."""
    global _tesseract_available
    if _tesseract_available is not None:
        return _tesseract_available
    try:
        import pytesseract
        # This will raise if the tesseract binary isn't found
        pytesseract.get_tesseract_version()
        _tesseract_available = True
        logger.info("Tesseract OCR is available")
    except Exception:
        _tesseract_available = False
        logger.warning(
            "Tesseract OCR is not available. "
            "Screenshot text extraction will return empty results. "
            "Install Tesseract: https://github.com/tesseract-ocr/tesseract"
        )
    return _tesseract_available


def extract_text_from_image(image_bytes: bytes) -> str:
    """
    Extract text from a screenshot image using OCR.

    Supports PNG, JPEG, and WebP formats.
    Uses German + English language packs for best results with
    WhatsApp screenshots from German-speaking users.

    Args:
        image_bytes: Raw bytes of the image file.

    Returns:
        Extracted text as a string. Returns empty string if OCR
        is unavailable or extraction fails.
    """
    if not image_bytes:
        return ""

    try:
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes))

        # Convert to RGB if necessary (e.g. RGBA PNGs, palette images)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
    except Exception as e:
        logger.error(f"Failed to open image: {e}")
        return ""

    if not _check_tesseract():
        logger.warning("OCR skipped: Tesseract not available")
        return ""

    try:
        import pytesseract

        # Use German + English for best coverage of WhatsApp messages
        # in the German-speaking context SafeVoice targets
        text = pytesseract.image_to_string(img, lang="deu+eng")
        return _clean_ocr_text(text)
    except Exception as e:
        # If the deu language pack is missing, fall back to eng only
        logger.warning(f"OCR with deu+eng failed ({e}), trying eng only")
        try:
            import pytesseract
            text = pytesseract.image_to_string(img, lang="eng")
            return _clean_ocr_text(text)
        except Exception as e2:
            logger.error(f"OCR extraction failed: {e2}")
            return ""


def _clean_ocr_text(text: str) -> str:
    """Clean up raw OCR output: collapse whitespace, strip artifacts."""
    if not text:
        return ""
    # Replace multiple newlines with single newline
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove leading/trailing whitespace per line
    lines = [line.strip() for line in text.splitlines()]
    # Drop empty lines at start/end
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def detect_whatsapp_format(image_bytes: bytes) -> dict:
    """
    Detect WhatsApp-specific visual elements in a screenshot.

    Looks for:
    - WhatsApp-style timestamps (HH:MM format)
    - Message bubble text patterns
    - Typical WhatsApp UI indicators in OCR text

    Returns a dict with detection metadata.
    """
    text = extract_text_from_image(image_bytes)

    # Look for WhatsApp timestamp patterns like "14:32", "9:05 PM"
    timestamp_pattern = re.compile(
        r"\b\d{1,2}:\d{2}(?:\s*(?:AM|PM|am|pm))?\b"
    )
    timestamps = timestamp_pattern.findall(text)

    # Look for WhatsApp-style read receipts / status indicators
    has_read_receipts = bool(re.search(r"[✓✔]{1,2}", text))

    # Look for typical WhatsApp UI text
    whatsapp_indicators = [
        "whatsapp", "online", "zuletzt online", "last seen",
        "typing...", "schreibt...", "today", "heute",
        "yesterday", "gestern",
    ]
    indicator_matches = [
        ind for ind in whatsapp_indicators
        if ind.lower() in text.lower()
    ]

    is_likely_whatsapp = (
        len(timestamps) >= 2
        or has_read_receipts
        or len(indicator_matches) >= 1
    )

    return {
        "is_whatsapp": is_likely_whatsapp,
        "extracted_text": text,
        "timestamps_found": timestamps,
        "has_read_receipts": has_read_receipts,
        "whatsapp_indicators": indicator_matches,
    }
