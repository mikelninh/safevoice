from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.classifier import classify
from app.services.pattern_detector import detect_patterns, compute_overall_severity
from app.services.evidence import hash_content, capture_timestamp, archive_url_sync
from app.services.scraper import scrape_url_sync, detect_platform
from app.models.evidence import ClassificationResult, EvidenceItem, PatternFlag, Severity
import uuid

router = APIRouter(prefix="/analyze", tags=["analyze"])


class AnalyzeTextRequest(BaseModel):
    text: str
    author_username: str = "unknown"
    url: str = ""


class AnalyzeCaseRequest(BaseModel):
    evidence_items: list[EvidenceItem]


class AnalyzeCaseResponse(BaseModel):
    pattern_flags: list[PatternFlag]
    overall_severity: Severity
    evidence_count: int


@router.post("/text", response_model=ClassificationResult)
def analyze_text(req: AnalyzeTextRequest):
    return classify(req.text)


@router.post("/ingest")
def ingest_url(req: AnalyzeTextRequest):
    """
    MVP: accepts text directly (simulates scraping a URL).
    Production: fetch + parse the actual URL.
    """
    content_hash = hash_content(req.text)
    captured_at = capture_timestamp()
    classification = classify(req.text)

    # Try to archive the URL (non-blocking, graceful failure)
    archived_url = archive_url_sync(req.url) if req.url else None

    evidence = EvidenceItem(
        id=str(uuid.uuid4()),
        url=req.url or "https://instagram.com/mock",
        platform="instagram",
        captured_at=captured_at,
        author_username=req.author_username,
        content_text=req.text,
        content_hash=content_hash,
        archived_url=archived_url,
        classification=classification
    )

    return {
        "evidence": evidence,
        "classification": classification,
        "message": "Evidence captured and classified."
    }


class AnalyzeUrlRequest(BaseModel):
    url: str


@router.post("/url")
def analyze_url(req: AnalyzeUrlRequest):
    """
    Scrape a social media URL, extract content, classify it.
    Supports Instagram, X/Twitter, and generic web pages.
    """
    if not req.url.strip():
        raise HTTPException(status_code=400, detail="URL is required")

    platform = detect_platform(req.url) or "web"
    scraped = scrape_url_sync(req.url)

    if not scraped:
        raise HTTPException(
            status_code=422,
            detail="Could not fetch content from this URL. It may be private or unavailable."
        )

    # Classify the main post
    content_hash = hash_content(scraped.content_text)
    captured_at = capture_timestamp()
    classification = classify(scraped.content_text)
    archived_url = archive_url_sync(req.url)

    evidence = EvidenceItem(
        id=str(uuid.uuid4()),
        url=req.url,
        platform=platform,
        captured_at=captured_at,
        author_username=scraped.author_username,
        author_display_name=scraped.author_display_name,
        content_text=scraped.content_text,
        content_hash=content_hash,
        archived_url=archived_url,
        classification=classification,
    )

    # Also classify comments if present
    comment_evidence = []
    for comment in scraped.comments[:20]:  # Cap at 20 comments
        if not comment.get("text"):
            continue
        c_hash = hash_content(comment["text"])
        c_classification = classify(comment["text"])
        comment_evidence.append(EvidenceItem(
            id=str(uuid.uuid4()),
            url=req.url,
            platform=platform,
            captured_at=captured_at,
            author_username=comment.get("author", "unknown"),
            content_text=comment["text"],
            content_hash=c_hash,
            classification=c_classification,
        ))

    return {
        "evidence": evidence,
        "comments": comment_evidence,
        "classification": classification,
        "platform": platform,
        "scraped": {
            "author_username": scraped.author_username,
            "author_display_name": scraped.author_display_name,
            "posted_at": scraped.posted_at,
            "comment_count": len(scraped.comments),
            "media_count": len(scraped.media_urls),
        },
        "message": f"Content scraped from {platform} and classified."
    }


@router.post("/case", response_model=AnalyzeCaseResponse)
def analyze_case(req: AnalyzeCaseRequest):
    pattern_flags = detect_patterns(req.evidence_items)
    overall_severity = compute_overall_severity(req.evidence_items)

    return AnalyzeCaseResponse(
        pattern_flags=pattern_flags,
        overall_severity=overall_severity,
        evidence_count=len(req.evidence_items)
    )
