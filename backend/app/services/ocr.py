"""
OCR service for extracting text from screenshot images.
Supports WhatsApp, Instagram, and other messaging app screenshots.

Two-tier extraction:
  1. Tesseract OCR (fast, free, local) — used when available.
  2. OpenAI Vision (gpt-4o) fallback — used when Tesseract is missing,
     e.g. on Vercel Functions where system packages aren't installed.

Both are optional. When neither is available the function returns "" and
the caller decides how to handle a screenshot with no extracted text
(SafeVoice still saves the image bytes to the DB as evidence).
"""

import base64
import io
import logging
import os
import re
from typing import Optional

logger = logging.getLogger(__name__)

# Track whether pytesseract + Tesseract engine are usable
_tesseract_available: Optional[bool] = None
# Track whether OpenAI client + key are configured
_openai_vision_available: Optional[bool] = None


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


def _check_openai_vision() -> bool:
    """Check whether OpenAI Vision is available (key + SDK + model)."""
    global _openai_vision_available
    if _openai_vision_available is not None:
        return _openai_vision_available
    if not os.environ.get("OPENAI_API_KEY"):
        _openai_vision_available = False
        return False
    try:
        import openai  # noqa: F401

        _openai_vision_available = True
        logger.info("OpenAI Vision OCR fallback is available")
    except Exception:
        _openai_vision_available = False
        logger.warning("OpenAI Vision unavailable: openai package not installed")
    return _openai_vision_available


def _ocr_with_openai_vision(image_bytes: bytes, mime_type: str = "image/png") -> str:
    """
    Extract text via OpenAI Vision (gpt-4o-mini). Used when Tesseract is
    unavailable, e.g. on Vercel Functions. Costs ~$0.001-0.005 per image
    depending on size. Returns empty string on any error.
    """
    try:
        from openai import OpenAI

        client = OpenAI()
        b64 = base64.b64encode(image_bytes).decode("ascii")
        data_url = f"data:{mime_type};base64,{b64}"

        # gpt-4o-mini supports vision and is the cheapest vision-capable model.
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=1500,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an OCR engine. Transcribe ALL visible text in the "
                        "screenshot exactly as written, preserving line breaks. Do not "
                        "summarize, do not translate, do not add commentary. If the "
                        "image contains a chat conversation, prefix each message with "
                        "the visible sender name + colon (e.g. 'Anna: ...'). If timestamps "
                        "are visible, include them. If there is no readable text, return "
                        "the literal token NO_TEXT."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                },
            ],
        )
        text = (resp.choices[0].message.content or "").strip()
        if text == "NO_TEXT":
            return ""
        return _clean_ocr_text(text)
    except Exception as e:
        logger.error(f"OpenAI Vision OCR failed: {e}")
        return ""


def extract_text_from_image(image_bytes: bytes, mime_type: str = "image/png") -> str:
    """
    Extract text from a screenshot image using OCR.

    Tries Tesseract first (fast, local, free). Falls back to OpenAI Vision
    (gpt-4o-mini) when Tesseract is unavailable — which is the case on
    Vercel Functions because system packages aren't installed there.

    Returns the extracted text, or "" if both engines are unavailable
    or fail. The caller still saves the screenshot bytes as evidence
    regardless of OCR success.
    """
    if not image_bytes:
        return ""

    # Image must be openable for either engine.
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes))
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
    except Exception as e:
        logger.error(f"Failed to open image: {e}")
        return ""

    # --- Tier 1: Tesseract (preferred when present) ---
    if _check_tesseract():
        try:
            import pytesseract

            text = pytesseract.image_to_string(img, lang="deu+eng")
            cleaned = _clean_ocr_text(text)
            if cleaned:
                return cleaned
        except Exception as e:
            logger.warning(f"Tesseract deu+eng failed ({e}), trying eng only")
            try:
                import pytesseract

                text = pytesseract.image_to_string(img, lang="eng")
                cleaned = _clean_ocr_text(text)
                if cleaned:
                    return cleaned
            except Exception as e2:
                logger.error(f"Tesseract eng-only also failed: {e2}")

    # --- Tier 2: OpenAI Vision (Vercel/serverless fallback) ---
    if _check_openai_vision():
        return _ocr_with_openai_vision(image_bytes, mime_type=mime_type)

    logger.warning("OCR unavailable: neither Tesseract nor OpenAI Vision configured")
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


def detect_whatsapp_format(image_bytes: bytes, mime_type: str = "image/png") -> dict:
    """
    Detect WhatsApp-specific visual elements in a screenshot.

    Looks for:
    - WhatsApp-style timestamps (HH:MM format)
    - Message bubble text patterns
    - Typical WhatsApp UI indicators in OCR text

    Returns a dict with detection metadata.
    """
    text = extract_text_from_image(image_bytes, mime_type=mime_type)

    # Look for WhatsApp timestamp patterns like "14:32", "9:05 PM"
    timestamp_pattern = re.compile(r"\b\d{1,2}:\d{2}(?:\s*(?:AM|PM|am|pm))?\b")
    timestamps = timestamp_pattern.findall(text)

    # Look for WhatsApp-style read receipts / status indicators
    has_read_receipts = bool(re.search(r"[✓✔]{1,2}", text))

    # Look for typical WhatsApp UI text
    whatsapp_indicators = [
        "whatsapp",
        "online",
        "zuletzt online",
        "last seen",
        "typing...",
        "schreibt...",
        "today",
        "heute",
        "yesterday",
        "gestern",
    ]
    indicator_matches = [
        ind for ind in whatsapp_indicators if ind.lower() in text.lower()
    ]

    is_likely_whatsapp = (
        len(timestamps) >= 2 or has_read_receipts or len(indicator_matches) >= 1
    )

    return {
        "is_whatsapp": is_likely_whatsapp,
        "extracted_text": text,
        "timestamps_found": timestamps,
        "has_read_receipts": has_read_receipts,
        "whatsapp_indicators": indicator_matches,
    }
