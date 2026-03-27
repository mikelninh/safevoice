"""
Tests for the social media scraper.
Tests platform detection, HTML parsing, and the /analyze/url endpoint.
"""

import pytest
from app.services.scraper import (
    detect_platform, _parse_instagram_html, _parse_x_html,
    _parse_generic_html, _extract_meta
)


class TestPlatformDetection:
    def test_instagram(self):
        assert detect_platform("https://www.instagram.com/p/abc123/") == "instagram"
        assert detect_platform("https://instagram.com/reel/xyz") == "instagram"

    def test_x_twitter(self):
        assert detect_platform("https://x.com/user/status/123") == "x"
        assert detect_platform("https://twitter.com/user/status/123") == "x"

    def test_tiktok(self):
        assert detect_platform("https://www.tiktok.com/@user/video/123") == "tiktok"

    def test_facebook(self):
        assert detect_platform("https://www.facebook.com/post/123") == "facebook"

    def test_unknown(self):
        assert detect_platform("https://example.com/page") is None

    def test_case_insensitive(self):
        assert detect_platform("https://WWW.INSTAGRAM.COM/p/abc/") == "instagram"


class TestInstagramParser:
    SAMPLE_HTML = '''
    <html>
    <head>
        <meta property="og:title" content="JaneDoe on Instagram: &quot;This is my post about justice&quot;" />
        <meta property="og:description" content="50 likes, 3 comments - JaneDoe on Instagram" />
        <meta property="og:image" content="https://scontent.cdninstagram.com/image.jpg" />
        <meta name="twitter:title" content="@janedoe123 on Instagram" />
        <script type="application/ld+json">
        {
            "author": {"name": "Jane Doe", "alternateName": "@janedoe123"},
            "articleBody": "This is my post about justice",
            "datePublished": "2024-03-15T10:30:00Z",
            "comment": [
                {"author": {"alternateName": "@hater1"}, "text": "You idiot shut up", "datePublished": "2024-03-15T11:00:00Z"},
                {"author": {"alternateName": "@troll99"}, "text": "Nobody cares about you", "datePublished": "2024-03-15T11:05:00Z"}
            ]
        }
        </script>
    </head>
    <body></body>
    </html>
    '''

    def test_extracts_post_text(self):
        result = _parse_instagram_html(self.SAMPLE_HTML, "https://instagram.com/p/abc123")
        assert result is not None
        assert "This is my post about justice" in result.content_text

    def test_extracts_author(self):
        result = _parse_instagram_html(self.SAMPLE_HTML, "https://instagram.com/p/abc123")
        assert result.author_username == "janedoe123"

    def test_extracts_display_name(self):
        result = _parse_instagram_html(self.SAMPLE_HTML, "https://instagram.com/p/abc123")
        assert result.author_display_name == "Jane Doe"

    def test_extracts_date(self):
        result = _parse_instagram_html(self.SAMPLE_HTML, "https://instagram.com/p/abc123")
        assert result.posted_at == "2024-03-15T10:30:00Z"

    def test_extracts_comments(self):
        result = _parse_instagram_html(self.SAMPLE_HTML, "https://instagram.com/p/abc123")
        assert len(result.comments) == 2
        assert result.comments[0]["author"] == "hater1"
        assert "shut up" in result.comments[0]["text"]

    def test_extracts_media(self):
        result = _parse_instagram_html(self.SAMPLE_HTML, "https://instagram.com/p/abc123")
        assert len(result.media_urls) > 0

    def test_platform_is_instagram(self):
        result = _parse_instagram_html(self.SAMPLE_HTML, "https://instagram.com/p/abc123")
        assert result.platform == "instagram"

    def test_empty_html_returns_none(self):
        result = _parse_instagram_html("<html><body></body></html>", "https://instagram.com/p/abc")
        assert result is None


class TestXParser:
    SAMPLE_HTML = '''
    <html>
    <head>
        <meta property="og:title" content="John Smith on X: &quot;Women should shut up and stop talking&quot;" />
        <meta property="og:description" content="Women should shut up and stop talking" />
        <meta name="twitter:creator" content="@jsmith_hateful" />
    </head>
    <body></body>
    </html>
    '''

    def test_extracts_post_text(self):
        result = _parse_x_html(self.SAMPLE_HTML, "https://x.com/jsmith/status/123")
        assert result is not None
        assert "Women should shut up" in result.content_text

    def test_extracts_username_from_url(self):
        result = _parse_x_html(self.SAMPLE_HTML, "https://x.com/jsmith_hateful/status/123")
        assert result.author_username == "jsmith_hateful"

    def test_extracts_display_name(self):
        result = _parse_x_html(self.SAMPLE_HTML, "https://x.com/jsmith/status/123")
        assert result.author_display_name == "John Smith"

    def test_platform_is_x(self):
        result = _parse_x_html(self.SAMPLE_HTML, "https://x.com/user/status/123")
        assert result.platform == "x"


class TestGenericParser:
    def test_extracts_from_og_tags(self):
        html = '<html><head><meta property="og:description" content="Some hateful content here" /><meta property="og:title" content="A bad page" /></head></html>'
        result = _parse_generic_html(html, "https://example.com/page")
        assert result is not None
        assert "hateful content" in result.content_text

    def test_empty_returns_none(self):
        result = _parse_generic_html("<html></html>", "https://example.com")
        assert result is None


class TestMetaExtraction:
    def test_property_format(self):
        html = '<meta property="og:title" content="Hello World" />'
        assert _extract_meta(html, "og:title") == "Hello World"

    def test_name_format(self):
        html = '<meta name="description" content="Page desc" />'
        assert _extract_meta(html, "description") == "Page desc"

    def test_reversed_attribute_order(self):
        html = '<meta content="Reversed Order" property="og:title" />'
        assert _extract_meta(html, "og:title") == "Reversed Order"

    def test_html_entities_unescaped(self):
        html = '<meta property="og:title" content="Say &quot;hello&quot; &amp; goodbye" />'
        assert _extract_meta(html, "og:title") == 'Say "hello" & goodbye'

    def test_missing_returns_none(self):
        html = '<meta property="og:image" content="img.jpg" />'
        assert _extract_meta(html, "og:title") is None


class TestAnalyzeUrlEndpoint:
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)

    def test_empty_url_returns_400(self, client):
        resp = client.post("/analyze/url", json={"url": ""})
        assert resp.status_code == 400

    def test_nonsocial_url_attempts_generic(self, client):
        # This will likely fail to scrape (no network in tests), but should return 422 not 500
        resp = client.post("/analyze/url", json={"url": "https://httpbin.org/html"})
        assert resp.status_code in (200, 422)
