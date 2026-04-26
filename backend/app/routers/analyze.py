"""
Analysis endpoints — stateless classification + URL scraping.

For persisted evidence (saved to DB), use POST /cases/{id}/evidence instead.
These endpoints are for quick preview / classification without creating a case.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.services.classifier import classify, ClassifierUnavailableError
from app.services.pattern_detector import detect_patterns, compute_overall_severity
from app.services.evidence import hash_content, capture_timestamp, archive_url_sync
from app.services.scraper import scrape_url_sync, detect_platform
from app.services.db_helpers import add_evidence_with_classification, get_last_hash
from app.models.evidence import ClassificationResult, EvidenceItem, PatternFlag, Severity
from app.database import get_db, Case as DBCase
from app.schemas import AnalyzeTextRequest, AnalyzeUrlRequest, IngestRequest
import uuid

router = APIRouter(prefix="/analyze", tags=["analyze"])


class AnalyzeCaseRequest(BaseModel):
    evidence_items: list[EvidenceItem]


class AnalyzeCaseResponse(BaseModel):
    pattern_flags: list[PatternFlag]
    overall_severity: Severity
    evidence_count: int


@router.post("/text", response_model=ClassificationResult)
def analyze_text(req: AnalyzeTextRequest):
    """Quick classification — no persistence, no case needed.

    Dynamic-prompt context (victim_context, jurisdiction, user_lang) is
    optional; absent it the prompt falls back to the legacy default.
    """
    try:
        return classify(
            req.text,
            victim_context=req.victim_context,
            jurisdiction=req.jurisdiction,
            user_lang=req.user_lang,
        )
    except ClassifierUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/ingest")
def ingest_content(req: IngestRequest, db: Session = Depends(get_db)):
    """
    Classify text and optionally persist to a case.
    If case_id is provided, evidence is saved to the database.
    Otherwise, returns ephemeral result (backward compatible).
    """
    text = req.text
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text content is required")

    try:
        classification = classify(
            text,
            victim_context=req.victim_context,
            jurisdiction=req.jurisdiction,
            user_lang=req.user_lang,
        )
    except ClassifierUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    content_hash = hash_content(text)
    captured_at = capture_timestamp()

    # If case_id provided, persist to DB
    if req.case_id:
        case = db.query(DBCase).filter_by(id=req.case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        # Single-tier classifier — always tier 1 (LLM).
        # Field kept in schema for future multi-model support.
        tier = 1

        previous_hash = get_last_hash(db, req.case_id)
        evidence = add_evidence_with_classification(
            db=db,
            case_id=req.case_id,
            text=text,
            classification_result=classification,
            content_type="text",
            source_url=req.url or None,
            author_username=req.author_username,
            previous_hash=previous_hash,
            classifier_tier=tier,
        )

        return {
            "evidence_id": evidence.id,
            "case_id": req.case_id,
            "classification": classification,
            "content_hash": content_hash,
            "persisted": True,
            "message": "Evidence classified and saved to case."
        }

    # Ephemeral result (no case_id)
    evidence = EvidenceItem(
        id=str(uuid.uuid4()),
        url="",
        platform="unknown",
        captured_at=captured_at,
        author_username="unknown",
        content_text=text,
        content_hash=content_hash,
        classification=classification,
    )

    return {
        "evidence": evidence,
        "classification": classification,
        "persisted": False,
        "message": "Evidence classified (not saved — provide case_id to persist)."
    }


@router.post("/url")
def analyze_url(req: AnalyzeUrlRequest, db: Session = Depends(get_db)):
    """
    Scrape a social media URL, extract content, classify it.
    If case_id is provided, all evidence is persisted to the database.
    """
    url = req.url
    if not url or not url.strip():
        raise HTTPException(status_code=400, detail="URL is required")

    platform = detect_platform(url) or "web"
    scraped = scrape_url_sync(url)

    if not scraped:
        raise HTTPException(
            status_code=422,
            detail="Could not fetch content from this URL. It may be private or unavailable."
        )

    # Classify the main post
    try:
        classification = classify(
            scraped.content_text,
            victim_context=req.victim_context,
            jurisdiction=req.jurisdiction,
            user_lang=req.user_lang,
        )
    except ClassifierUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    content_hash = hash_content(scraped.content_text)
    captured_at = capture_timestamp()
    archived_url = archive_url_sync(url)

    # If case_id provided, persist everything to DB
    if req.case_id:
        case = db.query(DBCase).filter_by(id=req.case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        tier = 1  # Single-tier LLM classifier

        previous_hash = get_last_hash(db, req.case_id)
        main_evidence = add_evidence_with_classification(
            db=db, case_id=req.case_id, text=scraped.content_text,
            classification_result=classification, content_type="url",
            source_url=url, platform=platform, archived_url=archived_url,
            previous_hash=previous_hash, classifier_tier=tier,
        )

        comment_ids = []
        for comment in scraped.comments[:20]:
            if not comment.get("text"):
                continue
            c_result = classify(
                comment["text"],
                victim_context=req.victim_context,
                jurisdiction=req.jurisdiction,
                user_lang=req.user_lang,
            )
            prev = get_last_hash(db, req.case_id)
            c_evidence = add_evidence_with_classification(
                db=db, case_id=req.case_id, text=comment["text"],
                classification_result=c_result, content_type="comment",
                source_url=url, platform=platform,
                author_username=comment.get("author", "unknown"),
                previous_hash=prev, classifier_tier=tier,
            )
            comment_ids.append(c_evidence.id)

        return {
            "evidence_id": main_evidence.id,
            "comment_evidence_ids": comment_ids,
            "case_id": req.case_id,
            "classification": classification,
            "platform": platform,
            "persisted": True,
            "message": f"Content from {platform} classified and saved ({1 + len(comment_ids)} items)."
        }

    # Ephemeral result
    evidence = EvidenceItem(
        id=str(uuid.uuid4()), url=url, platform=platform,
        captured_at=captured_at, author_username=scraped.author_username,
        author_display_name=scraped.author_display_name,
        content_text=scraped.content_text, content_hash=content_hash,
        archived_url=archived_url, classification=classification,
    )

    comment_evidence = []
    for comment in scraped.comments[:20]:
        if not comment.get("text"):
            continue
        c_classification = classify(
            comment["text"],
            victim_context=req.victim_context,
            jurisdiction=req.jurisdiction,
            user_lang=req.user_lang,
        )
        comment_evidence.append(EvidenceItem(
            id=str(uuid.uuid4()), url=url, platform=platform,
            captured_at=captured_at, author_username=comment.get("author", "unknown"),
            content_text=comment["text"], content_hash=hash_content(comment["text"]),
            classification=c_classification,
        ))

    return {
        "evidence": evidence,
        "comments": comment_evidence,
        "classification": classification,
        "platform": platform,
        "persisted": False,
        "message": f"Content from {platform} classified (not saved — provide case_id to persist)."
    }


class ChatRequest(BaseModel):
    question: str
    context: str  # original text + classification summary


@router.post("/chat")
def legal_chat(req: ChatRequest):
    """Answer follow-up legal questions about a classification."""
    import os
    try:
        from openai import OpenAI
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return {"answer": "AI nicht verfügbar. Bitte OPENAI_API_KEY setzen."}

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.3,
            max_tokens=500,
            messages=[
                {"role": "system", "content": """Du bist ein juristischer Berater für Opfer digitaler Gewalt in Deutschland.
Beantworte Fragen zum konkreten Fall basierend auf dem Kontext.
Sei präzise, nenne konkrete Paragraphen und Strafen.
Erkläre verständlich, nicht juristisch.
Antworte auf Deutsch.
Ende jede Antwort mit: 'Dies ist keine Rechtsberatung. Für verbindliche Auskunft wende dich an eine Anwältin oder an HateAid (hateaid.org).'"""},
                {"role": "user", "content": f"Kontext zum Fall:\n{req.context}\n\nFrage: {req.question}"},
            ],
        )
        answer = response.choices[0].message.content
        return {"answer": answer}
    except Exception as e:
        return {"answer": f"Fehler: {str(e)}"}


@router.post("/case", response_model=AnalyzeCaseResponse)
def analyze_case(req: AnalyzeCaseRequest):
    """Analyze a batch of evidence items for patterns (stateless)."""
    pattern_flags = detect_patterns(req.evidence_items)
    overall_severity = compute_overall_severity(req.evidence_items)
    return AnalyzeCaseResponse(
        pattern_flags=pattern_flags,
        overall_severity=overall_severity,
        evidence_count=len(req.evidence_items),
    )


@router.post("/case/{case_id}/legal")
def analyze_case_legal(case_id: str, db: Session = Depends(get_db)):
    """Run case-level Legal-AI analysis and PERSIST the result.

    Reads case + all evidence + classifications, calls the Legal-AI service
    with Pydantic-enforced output, INSERTS a `case_analyses` row (audit trail),
    UPDATES `case.summary` / `summary_de` / `overall_severity`, and returns the
    structured analysis. Re-running this endpoint on the same case appends a
    new analysis row (history preserved), never duplicates evidence.

    Demonstrates: read → think (LLM) → write (insert) → update (case fields).
    """
    from app.services.legal_ai import analyze_and_persist_case

    result = analyze_and_persist_case(case_id, db)
    if result is None:
        raise HTTPException(status_code=404, detail="Case not found or analysis failed")
    return result
