"""
Tests for the screenshot upload feature: OCR service and upload endpoint.
"""

import io
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from PIL import Image

try:
    import pytesseract as _pt  # noqa: F401
    HAS_PYTESSERACT = True
except ImportError:
    HAS_PYTESSERACT = False

_skip_no_tesseract = pytest.mark.skipif(
    not HAS_PYTESSERACT, reason="pytesseract not installed"
)

from app.main import app
from app.services.ocr import (
    extract_text_from_image,
    detect_whatsapp_format,
    _clean_ocr_text,
)


client = TestClient(app)


# ── Helper: create a minimal valid PNG in memory ──────────────────────


def _make_test_image(
    fmt: str = "PNG",
    width: int = 200,
    height: int = 100,
    color: str = "white",
) -> bytes:
    """Create a minimal test image and return its bytes."""
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf.read()


# ── OCR Service Tests ─────────────────────────────────────────────────


class TestOCRService:
    """Tests for the OCR text extraction service."""

    def test_extract_text_empty_bytes(self):
        """Empty input returns empty string."""
        result = extract_text_from_image(b"")
        assert result == ""

    def test_extract_text_invalid_image(self):
        """Invalid image data returns empty string, no crash."""
        result = extract_text_from_image(b"not an image at all")
        assert result == ""

    def test_extract_text_valid_image_no_tesseract(self):
        """With Tesseract unavailable, returns empty string gracefully."""
        import app.services.ocr as ocr_module
        original = ocr_module._tesseract_available
        try:
            ocr_module._tesseract_available = False
            image_bytes = _make_test_image()
            result = extract_text_from_image(image_bytes)
            assert result == ""
        finally:
            ocr_module._tesseract_available = original

    @_skip_no_tesseract
    def test_extract_text_with_mocked_tesseract(self):
        """When tesseract is available, extracted text is returned."""
        import app.services.ocr as ocr_module
        original = ocr_module._tesseract_available
        try:
            ocr_module._tesseract_available = True
            mock_text = "Du bist so hässlich, verschwinde!\n14:32"
            with patch("pytesseract.image_to_string", return_value=mock_text):
                image_bytes = _make_test_image()
                result = extract_text_from_image(image_bytes)
                assert "hässlich" in result
                assert "14:32" in result
        finally:
            ocr_module._tesseract_available = original

    @_skip_no_tesseract
    def test_extract_text_rgba_image(self):
        """RGBA images (e.g. PNG with transparency) are handled."""
        img = Image.new("RGBA", (100, 50), (255, 255, 255, 128))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        import app.services.ocr as ocr_module
        original = ocr_module._tesseract_available
        try:
            ocr_module._tesseract_available = True
            with patch("pytesseract.image_to_string", return_value="test text"):
                result = extract_text_from_image(buf.read())
                assert result == "test text"
        finally:
            ocr_module._tesseract_available = original

    @_skip_no_tesseract
    def test_extract_text_jpeg(self):
        """JPEG images work correctly."""
        import app.services.ocr as ocr_module
        original = ocr_module._tesseract_available
        try:
            ocr_module._tesseract_available = True
            with patch("pytesseract.image_to_string", return_value="jpeg text"):
                image_bytes = _make_test_image(fmt="JPEG")
                result = extract_text_from_image(image_bytes)
                assert result == "jpeg text"
        finally:
            ocr_module._tesseract_available = original

    @_skip_no_tesseract
    def test_extract_text_falls_back_to_eng(self):
        """If deu+eng fails, falls back to eng only."""
        import app.services.ocr as ocr_module
        original = ocr_module._tesseract_available
        try:
            ocr_module._tesseract_available = True

            def side_effect(img, lang="eng"):
                if "deu" in lang:
                    raise Exception("deu not available")
                return "english only text"

            with patch("pytesseract.image_to_string", side_effect=side_effect):
                image_bytes = _make_test_image()
                result = extract_text_from_image(image_bytes)
                assert result == "english only text"
        finally:
            ocr_module._tesseract_available = original


class TestCleanOCRText:
    """Tests for OCR text cleanup."""

    def test_clean_collapses_newlines(self):
        assert _clean_ocr_text("a\n\n\n\n\nb") == "a\n\nb"

    def test_clean_strips_lines(self):
        assert _clean_ocr_text("  hello  \n  world  ") == "hello\nworld"

    def test_clean_empty(self):
        assert _clean_ocr_text("") == ""
        assert _clean_ocr_text(None) == ""

    def test_clean_drops_leading_trailing_empty_lines(self):
        assert _clean_ocr_text("\n\nhello\n\n") == "hello"


class TestDetectWhatsAppFormat:
    """Tests for WhatsApp format detection."""

    def test_detects_whatsapp_timestamps(self):
        """Multiple HH:MM timestamps indicate WhatsApp."""
        import app.services.ocr as ocr_module
        original = ocr_module._tesseract_available
        try:
            ocr_module._tesseract_available = True
            mock_text = "Hey 14:32\nDu bist eklig 14:35\nAntwort 14:36"
            with patch(
                "app.services.ocr.extract_text_from_image",
                return_value=mock_text
            ):
                result = detect_whatsapp_format(b"fake_image_data")
                assert result["is_whatsapp"] is True
                assert len(result["timestamps_found"]) >= 2
        finally:
            ocr_module._tesseract_available = original

    def test_detects_whatsapp_indicators(self):
        """WhatsApp UI text triggers detection."""
        import app.services.ocr as ocr_module
        original = ocr_module._tesseract_available
        try:
            ocr_module._tesseract_available = True
            mock_text = "WhatsApp\nzuletzt online um 14:00\nHallo!"
            with patch(
                "app.services.ocr.extract_text_from_image",
                return_value=mock_text
            ):
                result = detect_whatsapp_format(b"fake_image_data")
                assert result["is_whatsapp"] is True
                assert "whatsapp" in result["whatsapp_indicators"]
        finally:
            ocr_module._tesseract_available = original

    def test_non_whatsapp_image(self):
        """Plain text without WhatsApp markers returns False."""
        with patch(
            "app.services.ocr.extract_text_from_image",
            return_value="Just some random text"
        ):
            result = detect_whatsapp_format(b"fake_image_data")
            assert result["is_whatsapp"] is False


# ── Upload Endpoint Tests ─────────────────────────────────────────────


class TestUploadEndpoint:
    """Tests for POST /upload/screenshot."""

    def test_upload_valid_png(self):
        """Valid PNG upload returns evidence with classification."""
        image_bytes = _make_test_image()
        with patch(
            "app.routers.upload.extract_text_from_image",
            return_value=""
        ), patch(
            "app.routers.upload.detect_whatsapp_format",
            return_value={
                "is_whatsapp": False,
                "extracted_text": "",
                "timestamps_found": [],
                "has_read_receipts": False,
                "whatsapp_indicators": [],
            }
        ):
            response = client.post(
                "/upload/screenshot",
                files={"file": ("screenshot.png", image_bytes, "image/png")},
            )
            assert response.status_code == 200
            data = response.json()
            assert "evidence" in data
            assert "classification" in data
            assert data["evidence"]["content_type"] == "screenshot"

    def test_upload_with_extracted_text(self):
        """Upload with OCR text gets proper classification."""
        image_bytes = _make_test_image()
        extracted = "I will kill you, you ugly whore"
        with patch(
            "app.routers.upload.detect_whatsapp_format",
            return_value={
                "is_whatsapp": False,
                "extracted_text": extracted,
                "timestamps_found": [],
                "has_read_receipts": False,
                "whatsapp_indicators": [],
            }
        ):
            response = client.post(
                "/upload/screenshot",
                files={"file": ("screenshot.png", image_bytes, "image/png")},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["evidence"]["content_text"] == extracted
            assert data["classification"]["severity"] in [
                "high", "critical"
            ]

    def test_upload_whatsapp_screenshot(self):
        """WhatsApp screenshot sets platform to 'whatsapp'."""
        image_bytes = _make_test_image()
        with patch(
            "app.routers.upload.detect_whatsapp_format",
            return_value={
                "is_whatsapp": True,
                "extracted_text": "Du bist hässlich 14:32",
                "timestamps_found": ["14:32"],
                "has_read_receipts": True,
                "whatsapp_indicators": ["whatsapp"],
            }
        ):
            response = client.post(
                "/upload/screenshot",
                files={"file": ("wa_screenshot.png", image_bytes, "image/png")},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["evidence"]["platform"] == "whatsapp"
            assert data["ocr_metadata"]["is_whatsapp"] is True

    def test_upload_invalid_file_type(self):
        """Non-image file types are rejected."""
        response = client.post(
            "/upload/screenshot",
            files={"file": ("doc.pdf", b"fake pdf content", "application/pdf")},
        )
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

    def test_upload_empty_file(self):
        """Empty file is rejected."""
        response = client.post(
            "/upload/screenshot",
            files={"file": ("empty.png", b"", "image/png")},
        )
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_upload_oversized_file(self):
        """Files exceeding 10 MB are rejected."""
        # Create bytes just over the limit
        big_bytes = b"x" * (10 * 1024 * 1024 + 1)
        response = client.post(
            "/upload/screenshot",
            files={"file": ("huge.png", big_bytes, "image/png")},
        )
        assert response.status_code == 400
        assert "too large" in response.json()["detail"].lower()

    def test_upload_jpeg(self):
        """JPEG uploads are accepted."""
        image_bytes = _make_test_image(fmt="JPEG")
        with patch(
            "app.routers.upload.detect_whatsapp_format",
            return_value={
                "is_whatsapp": False,
                "extracted_text": "test",
                "timestamps_found": [],
                "has_read_receipts": False,
                "whatsapp_indicators": [],
            }
        ):
            response = client.post(
                "/upload/screenshot",
                files={"file": ("photo.jpg", image_bytes, "image/jpeg")},
            )
            assert response.status_code == 200

    def test_upload_response_structure(self):
        """Response contains all expected fields."""
        image_bytes = _make_test_image()
        with patch(
            "app.routers.upload.detect_whatsapp_format",
            return_value={
                "is_whatsapp": False,
                "extracted_text": "some text",
                "timestamps_found": [],
                "has_read_receipts": False,
                "whatsapp_indicators": [],
            }
        ):
            response = client.post(
                "/upload/screenshot",
                files={"file": ("test.png", image_bytes, "image/png")},
            )
            data = response.json()
            # Check top-level keys
            assert "evidence" in data
            assert "classification" in data
            assert "ocr_metadata" in data
            assert "message" in data

            # Check evidence structure
            ev = data["evidence"]
            assert "id" in ev
            assert "content_text" in ev
            assert "content_hash" in ev
            assert "classification" in ev
            assert "captured_at" in ev

            # Check OCR metadata structure
            meta = data["ocr_metadata"]
            assert "text_extracted" in meta
            assert "is_whatsapp" in meta
