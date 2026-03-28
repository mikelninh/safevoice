"""
Screenshot upload router for WhatsApp and messaging app evidence.

Accepts image uploads, runs OCR to extract text, classifies the content,
and returns an EvidenceItem with classification results.
"""

import uuid
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.services.ocr import extract_text_from_image, detect_whatsapp_format
from app.services.classifier import classify
from app.services.evidence import hash_content, capture_timestamp
from app.models.evidence import EvidenceItem

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])

# 10 MB max file size
MAX_FILE_SIZE = 10 * 1024 * 1024

ALLOWED_CONTENT_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
}


@router.post("/screenshot")
async def upload_screenshot(file: UploadFile = File(...)):
    """
    Upload a screenshot (WhatsApp, Instagram DM, etc.) for OCR + classification.

    Accepts PNG, JPEG, or WebP images up to 10 MB.
    Extracts text via OCR, detects WhatsApp format, classifies content,
    and returns an EvidenceItem with full classification.
    """
    # Validate content type
    content_type = file.content_type or ""
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {content_type}. "
                   f"Accepted types: PNG, JPEG, WebP."
        )

    # Read and validate size
    image_bytes = await file.read()
    if len(image_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({len(image_bytes)} bytes). "
                   f"Maximum size is {MAX_FILE_SIZE // (1024 * 1024)} MB."
        )

    if len(image_bytes) == 0:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    # Detect WhatsApp format and extract text
    whatsapp_meta = detect_whatsapp_format(image_bytes)
    extracted_text = whatsapp_meta["extracted_text"]

    if not extracted_text.strip():
        # Even without OCR text, we can still create evidence
        # with the screenshot itself as proof
        logger.info("No text extracted from screenshot (OCR unavailable or image has no text)")
        extracted_text = "[Screenshot uploaded - no text extracted via OCR]"

    # Classify the extracted text
    classification = classify(extracted_text)

    # Build evidence item
    content_hash = hash_content(extracted_text)
    captured_at = capture_timestamp()

    evidence = EvidenceItem(
        id=str(uuid.uuid4()),
        url="",
        platform="whatsapp" if whatsapp_meta["is_whatsapp"] else "screenshot",
        captured_at=captured_at,
        author_username="unknown",
        content_text=extracted_text,
        content_type="screenshot",
        content_hash=content_hash,
        classification=classification,
    )

    return {
        "evidence": evidence,
        "classification": classification,
        "ocr_metadata": {
            "text_extracted": bool(extracted_text and not extracted_text.startswith("[")),
            "is_whatsapp": whatsapp_meta["is_whatsapp"],
            "timestamps_found": whatsapp_meta["timestamps_found"],
            "has_read_receipts": whatsapp_meta["has_read_receipts"],
            "whatsapp_indicators": whatsapp_meta["whatsapp_indicators"],
        },
        "message": "Screenshot uploaded and classified.",
    }
