"""
Social media scraper — fetches public post content from URLs.
Supports Instagram and X/Twitter.
Uses HTTP requests + HTML parsing (no API keys required for public content).
"""

import re
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                  "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
}


@dataclass
class ScrapedPost:
    platform: str
    url: str
    author_username: str
    author_display_name: str | None
    content_text: str
    posted_at: str | None
    comments: list[dict]  # [{author, text, posted_at}]
    media_urls: list[str]
    raw_meta: dict


def detect_platform(url: str) -> str | None:
    """Detect which platform a URL belongs to."""
    url_lower = url.lower()
    if "instagram.com" in url_lower:
        return "instagram"
    if "twitter.com" in url_lower or "x.com" in url_lower:
        return "x"
    if "tiktok.com" in url_lower:
        return "tiktok"
    if "facebook.com" in url_lower or "fb.com" in url_lower:
        return "facebook"
    return None


async def scrape_url(url: str) -> ScrapedPost | None:
    """
    Scrape a social media URL and return structured post data.
    Returns None if the URL can't be scraped.
    """
    platform = detect_platform(url)
    if platform == "instagram":
        return await _scrape_instagram(url)
    elif platform == "x":
        return await _scrape_x(url)
    else:
        return await _scrape_generic(url)


def scrape_url_sync(url: str) -> ScrapedPost | None:
    """Synchronous wrapper for scrape_url."""
    platform = detect_platform(url)
    if platform == "instagram":
        return _scrape_instagram_sync(url)
    elif platform == "x":
        return _scrape_x_sync(url)
    else:
        return _scrape_generic_sync(url)


# === INSTAGRAM ===

def _parse_instagram_html(html: str, url: str) -> ScrapedPost | None:
    """Parse Instagram page HTML to extract post data."""
    content_text = ""
    author_username = ""
    author_display_name = None
    posted_at = None
    media_urls = []
    raw_meta = {}

    # Method 1: og:description meta tag (fallback — often "N likes, M comments")
    og_desc = _extract_meta(html, "og:description")
    if og_desc:
        raw_meta["og_description"] = og_desc

    # Method 2: og:title for author info
    og_title = _extract_meta(html, "og:title")
    if og_title:
        raw_meta["og_title"] = og_title
        # Format: "Author Name on Instagram: "caption text""
        # or: "@username on Instagram: "caption""
        title_match = re.search(
            r'^(.+?)\s+on\s+Instagram:\s*["\u201c](.+?)["\u201d]',
            og_title, re.DOTALL
        )
        if title_match:
            author_display_name = title_match.group(1).strip()
            if not content_text:
                content_text = title_match.group(2).strip()

        # German format: "Author Name auf Instagram: „caption text""
        title_match_de = re.search(
            r'^(.+?)\s+auf\s+Instagram:\s*[\u201e\u201c""](.+?)[\u201c\u201d""]',
            og_title, re.DOTALL
        )
        if title_match_de:
            author_display_name = title_match_de.group(1).strip()
            if not content_text:
                content_text = title_match_de.group(2).strip()

    # Method 3: Extract username from URL
    url_match = re.search(r'instagram\.com/([^/]+)', url)
    if url_match:
        candidate = url_match.group(1)
        if candidate not in ("p", "reel", "stories", "explore"):
            author_username = candidate

    # Try to find username from meta tags
    username_meta = _extract_meta(html, "twitter:title")
    if username_meta:
        raw_meta["twitter_title"] = username_meta
        um = re.search(r'@(\w+)', username_meta)
        if um:
            author_username = um.group(1)

    # Extract post author from /p/ URL format
    if not author_username:
        author_tag = re.search(
            r'"author"\s*:\s*\{[^}]*"identifier"\s*:\s*\{[^}]*"value"\s*:\s*"([^"]+)"',
            html
        )
        if author_tag:
            author_username = author_tag.group(1)

    # Method 4: JSON-LD structured data
    json_ld_matches = re.findall(
        r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
        html, re.DOTALL
    )
    for raw_json in json_ld_matches:
        try:
            ld = json.loads(raw_json)
            raw_meta["json_ld"] = ld
            if isinstance(ld, dict):
                if "articleBody" in ld and not content_text:
                    content_text = ld["articleBody"]
                if "author" in ld:
                    author = ld["author"]
                    if isinstance(author, dict):
                        author_username = author.get("alternateName", "").lstrip("@") or author_username
                        author_display_name = author.get("name") or author_display_name
                if "datePublished" in ld:
                    posted_at = ld["datePublished"]
                # Comments
                if "comment" in ld and isinstance(ld["comment"], list):
                    raw_meta["comments"] = ld["comment"]
        except (json.JSONDecodeError, KeyError):
            continue

    # Method 5: og:image for media
    og_image = _extract_meta(html, "og:image")
    if og_image:
        media_urls.append(og_image)

    # Extract datetime from meta
    if not posted_at:
        time_match = re.search(r'<time[^>]*datetime="([^"]+)"', html)
        if time_match:
            posted_at = time_match.group(1)

    if not content_text:
        # Fallback to og:description (may contain "N likes, M comments..." prefix)
        if og_desc:
            content_text = og_desc

    if not content_text:
        # Last resort: description meta
        desc = _extract_meta(html, "description")
        if desc:
            content_text = desc

    if not content_text:
        return None

    # Parse comments from JSON-LD if available
    comments = []
    for c in raw_meta.get("comments", []):
        if isinstance(c, dict):
            comment_author = ""
            if isinstance(c.get("author"), dict):
                comment_author = c["author"].get("alternateName", "").lstrip("@")
            comments.append({
                "author": comment_author,
                "text": c.get("text", ""),
                "posted_at": c.get("datePublished"),
            })

    return ScrapedPost(
        platform="instagram",
        url=url,
        author_username=author_username or "unknown",
        author_display_name=author_display_name,
        content_text=content_text,
        posted_at=posted_at,
        comments=comments,
        media_urls=media_urls,
        raw_meta=raw_meta,
    )


async def _scrape_instagram(url: str) -> ScrapedPost | None:
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=HEADERS)
            if resp.status_code != 200:
                logger.warning(f"Instagram returned {resp.status_code} for {url}")
                return None
            return _parse_instagram_html(resp.text, url)
    except Exception as e:
        logger.warning(f"Instagram scrape failed for {url}: {e}")
        return None


def _scrape_instagram_sync(url: str) -> ScrapedPost | None:
    try:
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            resp = client.get(url, headers=HEADERS)
            if resp.status_code != 200:
                logger.warning(f"Instagram returned {resp.status_code} for {url}")
                return None
            return _parse_instagram_html(resp.text, url)
    except Exception as e:
        logger.warning(f"Instagram scrape failed for {url}: {e}")
        return None


# === X / TWITTER ===

def _parse_x_html(html: str, url: str) -> ScrapedPost | None:
    """Parse X/Twitter page HTML. Uses og: meta tags and nitter-style fallback."""
    content_text = ""
    author_username = ""
    author_display_name = None
    posted_at = None
    raw_meta = {}

    # og:description usually contains the tweet text
    og_desc = _extract_meta(html, "og:description")
    if og_desc:
        content_text = og_desc
        raw_meta["og_description"] = og_desc

    og_title = _extract_meta(html, "og:title")
    if og_title:
        raw_meta["og_title"] = og_title
        # Format: "Display Name on X: "tweet text""
        match = re.search(r'^(.+?)\s+on\s+X:\s*["\u201c](.+?)["\u201d]', og_title, re.DOTALL)
        if match:
            author_display_name = match.group(1).strip()
            if not content_text:
                content_text = match.group(2).strip()

    # Username from URL: x.com/username/status/123
    url_match = re.search(r'(?:twitter\.com|x\.com)/([^/]+)/status', url)
    if url_match:
        author_username = url_match.group(1)

    # twitter:creator meta
    creator = _extract_meta(html, "twitter:creator")
    if creator:
        author_username = creator.lstrip("@") or author_username

    if not content_text:
        return None

    return ScrapedPost(
        platform="x",
        url=url,
        author_username=author_username or "unknown",
        author_display_name=author_display_name,
        content_text=content_text,
        posted_at=posted_at,
        comments=[],
        media_urls=[],
        raw_meta=raw_meta,
    )


async def _scrape_x(url: str) -> ScrapedPost | None:
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=HEADERS)
            if resp.status_code != 200:
                logger.warning(f"X returned {resp.status_code} for {url}")
                return None
            return _parse_x_html(resp.text, url)
    except Exception as e:
        logger.warning(f"X scrape failed for {url}: {e}")
        return None


def _scrape_x_sync(url: str) -> ScrapedPost | None:
    try:
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            resp = client.get(url, headers=HEADERS)
            if resp.status_code != 200:
                return None
            return _parse_x_html(resp.text, url)
    except Exception as e:
        logger.warning(f"X scrape failed for {url}: {e}")
        return None


# === GENERIC URL ===

def _parse_generic_html(html: str, url: str) -> ScrapedPost | None:
    """Fallback: extract text content from any page via og: and meta tags."""
    content = _extract_meta(html, "og:description") or _extract_meta(html, "description") or ""
    title = _extract_meta(html, "og:title") or _extract_meta(html, "title") or ""

    if not content and not title:
        return None

    return ScrapedPost(
        platform="web",
        url=url,
        author_username="unknown",
        author_display_name=_extract_meta(html, "author"),
        content_text=f"{title}\n\n{content}".strip() if title and content else content or title,
        posted_at=None,
        comments=[],
        media_urls=[],
        raw_meta={},
    )


async def _scrape_generic(url: str) -> ScrapedPost | None:
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=HEADERS)
            if resp.status_code != 200:
                return None
            return _parse_generic_html(resp.text, url)
    except Exception as e:
        logger.warning(f"Generic scrape failed for {url}: {e}")
        return None


def _scrape_generic_sync(url: str) -> ScrapedPost | None:
    try:
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            resp = client.get(url, headers=HEADERS)
            if resp.status_code != 200:
                return None
            return _parse_generic_html(resp.text, url)
    except Exception as e:
        logger.warning(f"Generic scrape failed for {url}: {e}")
        return None


# === HELPERS ===

def _extract_meta(html: str, property_name: str) -> str | None:
    """Extract content from <meta property="..." content="..."> or <meta name="..." content="...">."""
    # property= variant (Open Graph)
    match = re.search(
        rf'<meta\s+(?:[^>]*\s)?(?:property|name)="{re.escape(property_name)}"[^>]*\scontent="([^"]*)"',
        html, re.IGNORECASE
    )
    if match:
        return _unescape_html(match.group(1))

    # content= before property= variant
    match = re.search(
        rf'<meta\s+content="([^"]*)"[^>]*\s(?:property|name)="{re.escape(property_name)}"',
        html, re.IGNORECASE
    )
    if match:
        return _unescape_html(match.group(1))

    return None


def _unescape_html(text: str) -> str:
    """Unescape common HTML entities."""
    return (
        text.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
        .replace("&#x27;", "'")
    )
