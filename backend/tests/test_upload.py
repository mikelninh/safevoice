"""
Tests for the screenshot upload feature: OCR service and upload endpoint.

OCR is Vision-only (OpenAI gpt-4o-mini). Tesseract was removed because the
binary never shipped on Vercel Functions, Vision handles UI chrome better, and
the single codepath eliminated dev/prod drift.
"""

import io
from unittest.mock import patch

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.services.ocr import (
    _clean_ocr_text,
    detect_whatsapp_format,
    extract_text_from_image,
)


client = TestClient(app)


def _make_test_image(
    fmt: str = "PNG",
    width: int = 200,
    height: int = 100,
    color: str = "white",
) -> bytes:
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf.read()


# ── OCR Service Tests ─────────────────────────────────────────────────


class TestOCRService:
    def test_extract_text_empty_bytes(self):
        assert extract_text_from_image(b"") == ""

    def test_extract_text_invalid_image(self):
        assert extract_text_from_image(b"not an image at all") == ""

    def test_extract_text_vision_unavailable(self):
        """If Vision can't be initialised, returns empty string gracefully."""
        with patch("app.services.ocr._check_vision", return_value=False):
            assert extract_text_from_image(_make_test_image()) == ""

    def test_extract_text_with_mocked_vision(self):
        """Vision result is returned through _clean_ocr_text."""
        with (
            patch("app.services.ocr._check_vision", return_value=True),
            patch(
                "app.services.ocr._ocr_with_vision",
                return_value=("Du bist so hässlich, verschwinde!\n14:32", None, None),
            ),
        ):
            result = extract_text_from_image(_make_test_image())
            assert "hässlich" in result
            assert "14:32" in result

    def test_extract_text_rgba_image(self):
        """RGBA PNGs (transparency) are normalised before OCR."""
        img = Image.new("RGBA", (100, 50), (255, 255, 255, 128))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        with (
            patch("app.services.ocr._check_vision", return_value=True),
            patch(
                "app.services.ocr._ocr_with_vision",
                return_value=("test text", None, None),
            ),
        ):
            assert extract_text_from_image(buf.getvalue()) == "test text"

    def test_extract_text_jpeg(self):
        with (
            patch("app.services.ocr._check_vision", return_value=True),
            patch(
                "app.services.ocr._ocr_with_vision",
                return_value=("jpeg text", None, None),
            ),
        ):
            assert extract_text_from_image(_make_test_image(fmt="JPEG")) == "jpeg text"


class TestCleanOCRText:
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
    def test_detects_whatsapp_timestamps(self):
        mock_text = "Hey 14:32\nDu bist eklig 14:35\nAntwort 14:36"
        with patch("app.services.ocr.extract_text_from_image", return_value=mock_text):
            result = detect_whatsapp_format(b"fake_image_data")
            assert result["is_whatsapp"] is True
            assert len(result["timestamps_found"]) >= 2

    def test_detects_whatsapp_indicators(self):
        mock_text = "WhatsApp\nzuletzt online um 14:00\nHallo!"
        with patch("app.services.ocr.extract_text_from_image", return_value=mock_text):
            result = detect_whatsapp_format(b"fake_image_data")
            assert result["is_whatsapp"] is True
            assert "whatsapp" in result["whatsapp_indicators"]

    def test_non_whatsapp_image(self):
        with patch(
            "app.services.ocr.extract_text_from_image",
            return_value="Just some random text",
        ):
            result = detect_whatsapp_format(b"fake_image_data")
            assert result["is_whatsapp"] is False


# ── Upload Endpoint Tests ─────────────────────────────────────────────


class TestUploadEndpoint:
    def test_upload_valid_png(self):
        image_bytes = _make_test_image()
        with (
            patch(
                "app.routers.upload.extract_with_metadata",
                return_value={
                    "text": "",
                    "sender_handle": None,
                    "platform_hint": None,
                    "engine": "openai_vision",
                },
            ),
            patch(
                "app.routers.upload.detect_whatsapp_format",
                return_value={
                    "is_whatsapp": False,
                    "extracted_text": "",
                    "timestamps_found": [],
                    "has_read_receipts": False,
                    "whatsapp_indicators": [],
                },
            ),
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
        image_bytes = _make_test_image()
        extracted = "I will kill you, you ugly whore"
        with (
            patch(
                "app.routers.upload.extract_with_metadata",
                return_value={
                    "text": extracted,
                    "sender_handle": None,
                    "platform_hint": None,
                    "engine": "openai_vision",
                },
            ),
            patch(
                "app.routers.upload.detect_whatsapp_format",
                return_value={
                    "is_whatsapp": False,
                    "extracted_text": extracted,
                    "timestamps_found": [],
                    "has_read_receipts": False,
                    "whatsapp_indicators": [],
                },
            ),
        ):
            response = client.post(
                "/upload/screenshot",
                files={"file": ("screenshot.png", image_bytes, "image/png")},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["evidence"]["content_text"] == extracted
            assert data["classification"]["severity"] in ["high", "critical"]

    def test_upload_whatsapp_screenshot(self):
        image_bytes = _make_test_image()
        with (
            patch(
                "app.routers.upload.extract_with_metadata",
                return_value={
                    "text": "Du bist hässlich 14:32",
                    "sender_handle": None,
                    "platform_hint": None,
                    "engine": "openai_vision",
                },
            ),
            patch(
                "app.routers.upload.detect_whatsapp_format",
                return_value={
                    "is_whatsapp": True,
                    "extracted_text": "Du bist hässlich 14:32",
                    "timestamps_found": ["14:32"],
                    "has_read_receipts": True,
                    "whatsapp_indicators": ["whatsapp"],
                },
            ),
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
        response = client.post(
            "/upload/screenshot",
            files={"file": ("doc.pdf", b"fake pdf content", "application/pdf")},
        )
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

    def test_upload_empty_file(self):
        response = client.post(
            "/upload/screenshot",
            files={"file": ("empty.png", b"", "image/png")},
        )
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_upload_oversized_file(self):
        big_bytes = b"x" * (10 * 1024 * 1024 + 1)
        response = client.post(
            "/upload/screenshot",
            files={"file": ("huge.png", big_bytes, "image/png")},
        )
        assert response.status_code == 400
        assert "too large" in response.json()["detail"].lower()

    def test_upload_jpeg(self):
        image_bytes = _make_test_image(fmt="JPEG")
        with (
            patch(
                "app.routers.upload.extract_with_metadata",
                return_value={
                    "text": "test",
                    "sender_handle": None,
                    "platform_hint": None,
                    "engine": "openai_vision",
                },
            ),
            patch(
                "app.routers.upload.detect_whatsapp_format",
                return_value={
                    "is_whatsapp": False,
                    "extracted_text": "test",
                    "timestamps_found": [],
                    "has_read_receipts": False,
                    "whatsapp_indicators": [],
                },
            ),
        ):
            response = client.post(
                "/upload/screenshot",
                files={"file": ("photo.jpg", image_bytes, "image/jpeg")},
            )
            assert response.status_code == 200

    def test_upload_response_structure(self):
        image_bytes = _make_test_image()
        with (
            patch(
                "app.routers.upload.extract_with_metadata",
                return_value={
                    "text": "some text",
                    "sender_handle": None,
                    "platform_hint": None,
                    "engine": "openai_vision",
                },
            ),
            patch(
                "app.routers.upload.detect_whatsapp_format",
                return_value={
                    "is_whatsapp": False,
                    "extracted_text": "some text",
                    "timestamps_found": [],
                    "has_read_receipts": False,
                    "whatsapp_indicators": [],
                },
            ),
        ):
            response = client.post(
                "/upload/screenshot",
                files={"file": ("test.png", image_bytes, "image/png")},
            )
            data = response.json()
            assert "evidence" in data
            assert "classification" in data
            assert "ocr_metadata" in data
            assert "message" in data

            ev = data["evidence"]
            assert "id" in ev
            assert "content_text" in ev
            assert "content_hash" in ev
            assert "classification" in ev
            assert "captured_at" in ev

            meta = data["ocr_metadata"]
            assert "text_extracted" in meta
            assert "is_whatsapp" in meta
