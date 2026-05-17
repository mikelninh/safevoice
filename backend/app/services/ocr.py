"""
OCR service for extracting text from screenshot images.
Supports WhatsApp, Instagram, Discord, X/Twitter, Mail, etc.

Vision-only: uses OpenAI Vision (gpt-4o-mini) for all OCR.

Why no Tesseract:
  - Vercel Functions don't ship the tesseract binary, so it never ran in prod
  - Vision handles UI chrome, emojis, multi-sender chat layouts far better
  - Vision additionally returns sender_handle + platform_hint
  - ~$0.001-0.005/image is negligible at expected volume
  - Single codepath = less drift between dev and prod
"""

import base64
import io
import logging
import os
import re
from typing import Optional

logger = logging.getLogger(__name__)

_vision_available: Optional[bool] = None


def _check_vision() -> bool:
    global _vision_available
    if _vision_available is not None:
        return _vision_available
    if not os.environ.get("OPENAI_API_KEY"):
        _vision_available = False
        logger.warning("OpenAI Vision unavailable: OPENAI_API_KEY not set")
        return False
    try:
        import openai  # noqa: F401

        _vision_available = True
    except Exception:
        _vision_available = False
        logger.warning("OpenAI Vision unavailable: openai package not installed")
    return _vision_available


def _ocr_with_vision(
    image_bytes: bytes, mime_type: str = "image/png"
) -> tuple[str, Optional[str], Optional[str]]:
    """
    Extract text + sender + platform via OpenAI Vision (gpt-4o-mini).
    Returns (text, sender_handle, platform_hint). On error: ("", None, None).
    """
    try:
        from openai import OpenAI

        client = OpenAI()
        b64 = base64.b64encode(image_bytes).decode("ascii")
        data_url = f"data:{mime_type};base64,{b64}"

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=1500,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an OCR engine for SafeVoice — a tool that documents "
                        "online harassment evidence. Look at the screenshot and return "
                        "a single JSON object with exactly these keys:\n"
                        '  "text": the harasser\'s message text — verbatim, line breaks '
                        "preserved. If the screenshot is a chat with multiple senders, "
                        "include all messages prefixed with 'SenderName: '. Do NOT "
                        "summarize or translate. If no readable text, return empty string.\n"
                        '  "sender_handle": the username or handle of the person who '
                        "wrote the harassing message — without the leading '@'. Examples: "
                        "'hateuser123' from an Instagram comment header, 'real_name42' "
                        "from an X post, the contact name from a WhatsApp chat. Return "
                        "null if no single clear sender is visible.\n"
                        '  "platform_hint": one of "instagram" | "x" | "whatsapp" | '
                        '"tiktok" | "facebook" | "telegram" | "discord" | "email" | '
                        '"screenshot" — based on visible UI chrome. Use "screenshot" '
                        "as fallback.\n"
                        "Return ONLY the JSON object, no markdown, no commentary."
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
        raw = (resp.choices[0].message.content or "").strip()
        import json

        try:
            data = json.loads(raw)
        except Exception:
            logger.warning(f"Vision returned non-JSON output: {raw[:200]}")
            return _clean_ocr_text(raw), None, None

        text = _clean_ocr_text(str(data.get("text") or ""))
        sender = data.get("sender_handle")
        if isinstance(sender, str):
            sender = sender.strip().lstrip("@") or None
        else:
            sender = None
        platform = data.get("platform_hint")
        if not isinstance(platform, str):
            platform = None
        return text, sender, platform
    except Exception as e:
        logger.error(f"OpenAI Vision OCR failed: {e}")
        return "", None, None


def _open_image(image_bytes: bytes):
    """Open + normalize an image. Returns PIL.Image or None on error."""
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes))
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        return img
    except Exception as e:
        logger.error(f"Failed to open image: {e}")
        return None


def extract_text_from_image(image_bytes: bytes, mime_type: str = "image/png") -> str:
    """
    Extract text from a screenshot via OpenAI Vision.
    Returns the extracted text, or "" on failure / missing config.
    """
    if not image_bytes:
        return ""
    if _open_image(image_bytes) is None:
        return ""
    if not _check_vision():
        return ""
    text, _sender, _platform = _ocr_with_vision(image_bytes, mime_type=mime_type)
    return text


def extract_with_metadata(image_bytes: bytes, mime_type: str = "image/png") -> dict:
    """
    Like extract_text_from_image, but also returns sender_handle and
    platform_hint. Used by the upload route so the frontend can pre-fill
    author_username and platform without the user typing them in.
    """
    out = {
        "text": "",
        "sender_handle": None,
        "platform_hint": None,
        "engine": "none",
    }
    if not image_bytes:
        return out
    if _open_image(image_bytes) is None:
        return out
    if not _check_vision():
        return out
    text, sender, platform = _ocr_with_vision(image_bytes, mime_type=mime_type)
    out["text"] = text
    out["sender_handle"] = sender
    out["platform_hint"] = platform
    out["engine"] = "openai_vision"
    return out


def _clean_ocr_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [line.strip() for line in text.splitlines()]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def detect_whatsapp_format(image_bytes: bytes, mime_type: str = "image/png") -> dict:
    """
    Detect WhatsApp-specific visual elements in a screenshot.
    Used as a hint for downstream formatting.
    """
    text = extract_text_from_image(image_bytes, mime_type=mime_type)

    timestamp_pattern = re.compile(r"\b\d{1,2}:\d{2}(?:\s*(?:AM|PM|am|pm))?\b")
    timestamps = timestamp_pattern.findall(text)
    has_read_receipts = bool(re.search(r"[✓✔]{1,2}", text))

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
