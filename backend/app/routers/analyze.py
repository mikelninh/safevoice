from fastapi import APIRouter
from pydantic import BaseModel
from app.services.classifier import classify
from app.services.pattern_detector import detect_patterns, compute_overall_severity
from app.services.evidence import hash_content, capture_timestamp, archive_url_sync
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


@router.post("/case", response_model=AnalyzeCaseResponse)
def analyze_case(req: AnalyzeCaseRequest):
    pattern_flags = detect_patterns(req.evidence_items)
    overall_severity = compute_overall_severity(req.evidence_items)

    return AnalyzeCaseResponse(
        pattern_flags=pattern_flags,
        overall_severity=overall_severity,
        evidence_count=len(req.evidence_items)
    )
