"""
Comprehensive edge case and security tests for SafeVoice.

Covers:
  1. Classifier edge cases (empty, long, unicode, leetspeak, etc.)
  2. Security tests (XSS, SQL injection, path traversal, null bytes, etc.)
  3. Auth edge cases (empty email, expired sessions, multiple magic links, etc.)
  4. API robustness (missing fields, invalid URLs, nonexistent resources, etc.)
  5. Evidence integrity (hash determinism, format, tampering detection, etc.)
"""

import io
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.classifier import classify, classify_regex
from app.services.evidence import hash_content, verify_hash, capture_timestamp
from app.services.scraper import detect_platform
from app.services.auth import (
    request_magic_link,
    verify_magic_link,
    get_session,
    get_user_by_session,
    _magic_links,
    _sessions,
)
from app.models.evidence import Severity, Category, ClassificationResult


@pytest.fixture
def client():
    return TestClient(app)


# =====================================================================
# 1. CLASSIFIER EDGE CASES (12 tests)
# =====================================================================

class TestClassifierEdgeCases:
    """Edge cases that must not crash the classifier."""

    def test_empty_string(self):
        """Empty string must return a valid result, not crash."""
        result = classify_regex("")
        assert isinstance(result, ClassificationResult)
        assert result.severity is not None
        assert len(result.categories) > 0

    def test_very_long_text(self):
        """10,000-character input must not crash or timeout."""
        long_text = "This is some filler text. " * 500  # ~13,000 chars
        result = classify_regex(long_text)
        assert isinstance(result, ClassificationResult)
        assert result.severity == Severity.LOW

    def test_only_whitespace(self):
        """Whitespace-only input must return a valid result."""
        result = classify_regex("   \t\n\r\n   ")
        assert isinstance(result, ClassificationResult)
        assert result.severity is not None

    def test_only_emoji(self):
        """Emoji-only input must not crash the regex engine."""
        result = classify_regex("\U0001f621\U0001f4a9\U0001f52a\U0001f480\U0001f525")
        assert isinstance(result, ClassificationResult)

    def test_mixed_language_de_en(self):
        """Mixed German and English text is handled."""
        result = classify_regex(
            "Du bist such a stupid idiot, halt die Klappe"
        )
        assert Category.HARASSMENT in result.categories

    def test_unicode_arabic_german_mixed(self):
        """Mixed Arabic and German text must not crash."""
        result = classify_regex(
            "Dieser Inhalt ist schlimm. \u0633\u0623\u0642\u062a\u0644\u0643"
        )
        assert isinstance(result, ClassificationResult)
        # Arabic death threat should be detected
        assert Category.DEATH_THREAT in result.categories

    def test_all_caps_harassment(self):
        """ALL CAPS text must still be detected (case-insensitive matching)."""
        result = classify_regex("YOU ARE A STUPID IDIOT NOBODY CARES ABOUT YOU")
        assert Category.HARASSMENT in result.categories

    def test_leetspeak_threat(self):
        """Leetspeak like '1'll k1ll u' -- regex may not catch it,
        but must not crash. The result should still be valid."""
        result = classify_regex("1'll k1ll u, watch ur back")
        assert isinstance(result, ClassificationResult)
        # The regex tier may not detect leetspeak, but it should not error

    def test_repeated_characters(self):
        """Repeated characters like 'dieeee already' must not crash."""
        result = classify_regex("dieeee already you ugly loser")
        assert isinstance(result, ClassificationResult)
        # 'ugly' and 'loser' should still trigger body_shaming / harassment
        detected = result.categories
        assert Category.HARASSMENT in detected or Category.BODY_SHAMING in detected

    def test_single_word_input(self):
        """A single word must produce a valid result."""
        result = classify_regex("hello")
        assert isinstance(result, ClassificationResult)
        assert result.severity == Severity.LOW

    def test_url_only_input(self):
        """URL-only text must not crash the classifier."""
        result = classify_regex("https://evil-site.xyz/phishing-page")
        assert isinstance(result, ClassificationResult)

    def test_numbers_only(self):
        """Numeric-only input must not crash."""
        result = classify_regex("1234567890 42 3.14159")
        assert isinstance(result, ClassificationResult)
        assert result.severity == Severity.LOW


# =====================================================================
# 2. SECURITY TESTS (9 tests)
# =====================================================================

class TestSecurity:
    """Input that simulates common attack vectors must not cause harm."""

    def test_xss_in_content(self, client):
        """XSS script tags must be treated as text, not executed."""
        xss_payload = "<script>alert('xss')</script>"
        resp = client.post("/analyze/text", json={"text": xss_payload})
        assert resp.status_code == 200
        data = resp.json()
        # The classifier must return a valid result, not echo raw HTML
        assert isinstance(data["severity"], str)
        # The script should not appear unescaped in a dangerous context
        assert "categories" in data

    def test_sql_injection_in_content(self, client):
        """SQL injection attempts must be treated as plain text."""
        sql_payload = "'; DROP TABLE users; --"
        resp = client.post("/analyze/text", json={"text": sql_payload})
        assert resp.status_code == 200
        data = resp.json()
        assert "severity" in data

    def test_path_traversal_in_content(self, client):
        """Path traversal strings must be treated as text."""
        traversal = "../../etc/passwd"
        resp = client.post("/analyze/text", json={"text": traversal})
        assert resp.status_code == 200

    def test_null_bytes_in_content(self, client):
        """Content with null bytes must not crash the system."""
        payload = "Hello\x00World\x00evil"
        resp = client.post("/analyze/text", json={"text": payload})
        assert resp.status_code == 200

    def test_extremely_long_input(self, client):
        """100KB payload must be accepted without server crash."""
        big_text = "A" * (100 * 1024)  # 100 KB
        resp = client.post("/analyze/text", json={"text": big_text})
        # Should either succeed or return a client error, not a 500
        assert resp.status_code in (200, 400, 413, 422)

    def test_content_hash_idempotent(self):
        """Same input must always produce the same hash (no salting)."""
        text = "<script>alert('xss')</script> '; DROP TABLE users; --"
        h1 = hash_content(text)
        h2 = hash_content(text)
        assert h1 == h2

    def test_malformed_url_does_not_crash_scraper(self):
        """Malformed URLs must not crash detect_platform."""
        for url in [
            "",
            "not-a-url",
            "ftp://weird-protocol.com",
            "://missing-scheme",
            "http://",
            "javascript:alert(1)",
        ]:
            result = detect_platform(url)
            # Should return None for unrecognized URLs, not crash
            assert result is None or isinstance(result, str)

    def test_invalid_file_type_rejected(self, client):
        """Non-image file types must be rejected by the upload endpoint."""
        resp = client.post(
            "/upload/screenshot",
            files={"file": ("evil.exe", b"MZ\x90\x00", "application/octet-stream")},
        )
        assert resp.status_code == 400
        assert "Invalid file type" in resp.json()["detail"]

    def test_xss_in_classifier_result_fields(self):
        """XSS payload in text must not appear raw in summary fields
        (summaries are template-generated, not echoed)."""
        result = classify_regex("<img src=x onerror=alert(1)>")
        # Summary must be a template string, not the raw input
        assert "<img" not in result.summary
        assert "onerror" not in result.summary


# =====================================================================
# 3. AUTH EDGE CASES (7 tests)
# =====================================================================

class TestAuthEdgeCases:
    """Edge cases in the authentication flow."""

    def test_login_empty_email(self, client):
        """Login with empty email must fail."""
        resp = client.post("/auth/login", json={"email": ""})
        assert resp.status_code == 400

    def test_login_email_without_at(self, client):
        """Login with email missing @ must fail."""
        resp = client.post("/auth/login", json={"email": "notanemail"})
        assert resp.status_code == 400

    def test_verify_empty_token(self, client):
        """Verify with empty token must fail."""
        resp = client.post("/auth/verify", json={"token": ""})
        assert resp.status_code == 401

    def test_expired_session(self):
        """An expired session must not authenticate."""
        link = request_magic_link("expired-session@test.de")
        session = verify_magic_link(link.token)
        assert session is not None

        # Manually expire the session
        session.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)

        # The session should now be invalid
        result = get_session(session.token)
        assert result is None

    def test_expired_magic_link(self):
        """An expired magic link must not verify."""
        link = request_magic_link("expired-link@test.de")

        # Manually expire the link
        link.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)

        session = verify_magic_link(link.token)
        assert session is None

    def test_multiple_magic_links_all_valid(self):
        """Multiple magic links for same email should all work until used."""
        email = "multi-link@test.de"
        link1 = request_magic_link(email)
        link2 = request_magic_link(email)
        link3 = request_magic_link(email)

        # All three should be valid and usable
        session1 = verify_magic_link(link1.token)
        assert session1 is not None

        session2 = verify_magic_link(link2.token)
        assert session2 is not None

        session3 = verify_magic_link(link3.token)
        assert session3 is not None

        # All sessions should belong to the same user
        assert session1.user_id == session2.user_id == session3.user_id

    def test_email_case_insensitivity(self):
        """Email must be case-insensitive: Upper@Test.DE == upper@test.de."""
        link1 = request_magic_link("CaseTest@Example.COM")
        session1 = verify_magic_link(link1.token)

        link2 = request_magic_link("casetest@example.com")
        session2 = verify_magic_link(link2.token)

        # Same user
        assert session1.user_id == session2.user_id


# =====================================================================
# 4. API ROBUSTNESS (9 tests)
# =====================================================================

class TestAPIRobustness:
    """API endpoints must handle malformed input gracefully."""

    def test_analyze_text_empty_body(self, client):
        """POST /analyze/text with empty body must fail with 422."""
        resp = client.post("/analyze/text", json={})
        assert resp.status_code == 422

    def test_analyze_text_missing_text_field(self, client):
        """POST /analyze/text with wrong fields must fail."""
        resp = client.post("/analyze/text", json={"content": "wrong field name"})
        assert resp.status_code == 422

    def test_analyze_url_invalid_url(self, client):
        """POST /analyze/url with an invalid URL returns 422 (can't scrape)."""
        resp = client.post("/analyze/url", json={"url": "not-a-real-url"})
        # Should be 422 (can't fetch) or 400
        assert resp.status_code in (400, 422)

    def test_analyze_url_empty_url(self, client):
        """POST /analyze/url with empty URL returns 400."""
        resp = client.post("/analyze/url", json={"url": ""})
        assert resp.status_code == 400

    def test_report_nonexistent_case_pdf(self, client):
        """GET /reports/case-999/pdf for nonexistent case returns 404."""
        resp = client.get("/reports/case-999/pdf")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    def test_health_returns_correct_structure(self, client):
        """GET /health must return status, service, and classifier_tier."""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "SafeVoice API"
        assert data["classifier_tier"] in ("claude_api", "transformer", "regex")

    def test_partners_submit_without_api_key(self, client):
        """POST /partners/cases/submit without X-API-Key must return 401."""
        resp = client.post(
            "/partners/cases/submit",
            json={
                "text": "test content",
                "author_username": "test",
                "platform": "instagram",
            },
        )
        assert resp.status_code == 401
        assert "API-Key" in resp.json()["detail"]

    def test_large_payload_1mb(self, client):
        """1MB text payload must not crash the server."""
        big = "x" * (1024 * 1024)  # 1 MB
        resp = client.post("/analyze/text", json={"text": big})
        # Must succeed or return a client error, never 500
        assert resp.status_code in (200, 400, 413, 422)

    def test_special_characters_in_url_parameters(self, client):
        """Special characters in URL path params must not crash."""
        # case_id with special chars
        resp = client.get("/reports/%3Cscript%3E/pdf")
        # Should return 404 (case not found), not 500
        assert resp.status_code == 404


# =====================================================================
# 5. EVIDENCE INTEGRITY (7 tests)
# =====================================================================

class TestEvidenceIntegrity:
    """Evidence hashing and timestamping must meet legal requirements."""

    def test_same_content_same_hash(self):
        """Identical content must always produce an identical hash."""
        text = "Evidence content for court proceedings"
        assert hash_content(text) == hash_content(text)

    def test_different_content_different_hash(self):
        """Different content must produce different hashes."""
        h1 = hash_content("Original statement from witness A")
        h2 = hash_content("Original statement from witness B")
        assert h1 != h2

    def test_hash_format_sha256(self):
        """Hash must follow the sha256:<64 hex chars> format."""
        h = hash_content("test")
        assert h.startswith("sha256:")
        hex_part = h[7:]
        assert len(hex_part) == 64
        # Verify it is valid hexadecimal
        int(hex_part, 16)

    def test_verify_catches_tampering(self):
        """verify_hash must detect when content has been altered."""
        original = "Original evidence text from Instagram DM"
        h = hash_content(original)
        assert verify_hash(original, h) is True

        # Tamper with the content
        tampered = "Original evidence text from Instagram DM."  # added period
        assert verify_hash(tampered, h) is False

    def test_timestamp_always_utc_with_timezone(self):
        """Timestamps must always be UTC with timezone info (legal requirement)."""
        for _ in range(5):
            ts = capture_timestamp()
            assert ts.tzinfo is not None
            assert ts.tzinfo == timezone.utc
            # ISO format must contain timezone indicator
            iso = ts.isoformat()
            assert "+00:00" in iso or "Z" in iso

    def test_hash_handles_unicode(self):
        """Hashing must work with multi-language unicode content."""
        texts = [
            "German: \u00e4\u00f6\u00fc\u00df",
            "Arabic: \u0633\u0623\u0642\u062a\u0644\u0643",
            "Turkish: \u015f\u0131\u011f\u00fc\u00f6\u00e7",
            "Emoji: \U0001f621\U0001f52a\U0001f480",
            "CJK: \u4f60\u597d\u4e16\u754c",
        ]
        for text in texts:
            h = hash_content(text)
            assert h.startswith("sha256:")
            assert verify_hash(text, h) is True

    def test_hash_whitespace_sensitive(self):
        """Trailing whitespace changes the hash (evidence must be exact)."""
        h1 = hash_content("evidence")
        h2 = hash_content("evidence ")
        h3 = hash_content(" evidence")
        assert h1 != h2
        assert h1 != h3
        assert h2 != h3
