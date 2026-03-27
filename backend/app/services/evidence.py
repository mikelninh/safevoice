"""
Evidence archiving service.
- SHA-256 content hashing (tamper-proof)
- UTC timestamps (legal requirement)
- archive.org Wayback Machine submission
- Evidence integrity verification
"""

import hashlib
import logging
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

WAYBACK_SAVE_URL = "https://web.archive.org/save/"


def hash_content(text: str) -> str:
    """Generate SHA-256 hash of content. Deterministic and tamper-proof."""
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def verify_hash(text: str, expected_hash: str) -> bool:
    """Verify content integrity against stored hash."""
    return hash_content(text) == expected_hash


def capture_timestamp() -> datetime:
    """Capture current time in UTC with timezone info (legally required)."""
    return datetime.now(timezone.utc)


async def archive_url(url: str) -> str | None:
    """
    Submit URL to archive.org Wayback Machine.
    Returns the archived URL or None if it fails.
    Non-blocking — failure doesn't block the analysis flow.
    """
    if not url or url.startswith("https://instagram.com/mock"):
        return None

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                WAYBACK_SAVE_URL + url,
                follow_redirects=True,
                headers={"User-Agent": "SafeVoice/1.0 (digital justice tool)"}
            )
            if resp.status_code == 200:
                # The Wayback Machine returns the archived page
                # The archived URL is in the Content-Location header or we construct it
                archived = resp.headers.get("Content-Location")
                if archived:
                    return f"https://web.archive.org{archived}"
                # Fallback: construct from timestamp
                ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
                return f"https://web.archive.org/web/{ts}/{url}"

            logger.warning(f"archive.org returned {resp.status_code} for {url}")
            return None

    except Exception as e:
        logger.warning(f"Failed to archive URL {url}: {e}")
        return None


def archive_url_sync(url: str) -> str | None:
    """
    Synchronous version of archive_url for non-async contexts.
    """
    if not url or url.startswith("https://instagram.com/mock"):
        return None

    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(
                WAYBACK_SAVE_URL + url,
                follow_redirects=True,
                headers={"User-Agent": "SafeVoice/1.0 (digital justice tool)"}
            )
            if resp.status_code == 200:
                archived = resp.headers.get("Content-Location")
                if archived:
                    return f"https://web.archive.org{archived}"
                ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
                return f"https://web.archive.org/web/{ts}/{url}"
            return None
    except Exception as e:
        logger.warning(f"Failed to archive URL {url}: {e}")
        return None
