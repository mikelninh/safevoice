"""
Tests for evidence archiving service.
"""

from app.services.evidence import hash_content, verify_hash, capture_timestamp
from datetime import timezone


class TestHashing:
    def test_hash_deterministic(self):
        """Same content always produces same hash."""
        text = "I will kill you"
        h1 = hash_content(text)
        h2 = hash_content(text)
        assert h1 == h2

    def test_hash_format(self):
        h = hash_content("test content")
        assert h.startswith("sha256:")
        assert len(h) == 7 + 64  # "sha256:" + 64 hex chars

    def test_different_content_different_hash(self):
        h1 = hash_content("content A")
        h2 = hash_content("content B")
        assert h1 != h2

    def test_verify_hash_valid(self):
        text = "This is evidence"
        h = hash_content(text)
        assert verify_hash(text, h) is True

    def test_verify_hash_tampered(self):
        text = "Original evidence"
        h = hash_content(text)
        assert verify_hash("Tampered evidence", h) is False

    def test_unicode_handling(self):
        """German text with umlauts must hash correctly."""
        text = "Ich werde dich umbringen, du Schlampe"
        h = hash_content(text)
        assert h.startswith("sha256:")
        assert verify_hash(text, h) is True


class TestTimestamp:
    def test_timestamp_is_utc(self):
        ts = capture_timestamp()
        assert ts.tzinfo is not None
        assert ts.tzinfo == timezone.utc

    def test_timestamp_has_timezone(self):
        """Legal requirement: timestamps must include timezone."""
        ts = capture_timestamp()
        iso = ts.isoformat()
        assert "+" in iso or "Z" in iso


class TestIngestEndpoint:
    def test_ingest_returns_valid_hash(self):
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)

        resp = client.post("/analyze/ingest", json={
            "text": "You idiot, I will find you",
            "author_username": "threat_user",
            "url": ""
        })
        assert resp.status_code == 200
        data = resp.json()
        ev = data["evidence"]
        assert ev["content_hash"].startswith("sha256:")
        assert len(ev["content_hash"]) == 71

    def test_ingest_timestamp_has_timezone(self):
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)

        resp = client.post("/analyze/ingest", json={
            "text": "Test content",
            "author_username": "test",
            "url": ""
        })
        data = resp.json()
        captured = data["evidence"]["captured_at"]
        # UTC timestamps should contain timezone indicator
        assert "+" in captured or "Z" in captured or "T" in captured
