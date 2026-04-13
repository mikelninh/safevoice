"""
Bulk import router — NGO-grade batch classification.

For caseworkers at orgs like HateAid who need to process dozens of harassment
items at once (e.g., export from a coordinated attack on a client).

Two flows:
  1. POST /bulk/import/json     — structured list of items (for programmatic use)
  2. POST /bulk/import/csv      — CSV file upload (for human users)

Both classify in a loop, persist to the target case atomically, and preserve
the hash chain. Failures on individual items don't abort the batch.
"""

from __future__ import annotations

import csv
import io
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db, Case as DBCase, User
from app.schemas import BulkImportRequest, BulkImportResult, BulkImportItem
from app.services.authz import require_case_access
from app.services.classifier import classify, ClassifierUnavailableError
from app.services.db_helpers import add_evidence_with_classification, get_last_hash
from app.services.scraper import detect_platform
from app.routers.orgs import current_user  # reuse the auth dependency

router = APIRouter(prefix="/bulk", tags=["bulk-import"])
logger = logging.getLogger(__name__)

MAX_ITEMS_PER_BATCH = 500  # guard against runaway imports


def _import_items(
    db: Session,
    case: DBCase,
    items: list[BulkImportItem],
) -> BulkImportResult:
    """Classify + persist each item. Individual failures don't abort the batch."""
    if len(items) > MAX_ITEMS_PER_BATCH:
        raise HTTPException(
            status_code=413,
            detail=f"Batch too large ({len(items)} items). Max {MAX_ITEMS_PER_BATCH} per import.",
        )

    imported_ids: list[str] = []
    errors: list[str] = []

    for i, item in enumerate(items):
        if not item.text.strip():
            errors.append(f"Row {i}: empty text")
            continue

        try:
            classification = classify(item.text)
        except ClassifierUnavailableError as e:
            # If the classifier is fully down, we stop — no point burning tokens.
            errors.append(f"Row {i}: classifier unavailable ({e})")
            break
        except Exception as e:
            errors.append(f"Row {i}: classification error: {e}")
            continue

        previous_hash = get_last_hash(db, case.id)

        try:
            evidence = add_evidence_with_classification(
                db=db,
                case_id=case.id,
                text=item.text,
                classification_result=classification,
                content_type="text",
                source_url=item.source_url,
                author_username=item.author_username,
                platform=item.platform or (detect_platform(item.source_url) if item.source_url else None),
                previous_hash=previous_hash,
                classifier_tier=1,
            )
            imported_ids.append(evidence.id)
        except Exception as e:
            errors.append(f"Row {i}: persistence error: {e}")
            logger.exception("Bulk import row %d failed", i)

    return BulkImportResult(
        case_id=case.id,
        imported=len(imported_ids),
        failed=len(items) - len(imported_ids),
        evidence_ids=imported_ids,
        errors=errors[:50],  # cap error list to avoid runaway responses
    )


@router.post("/import/json", response_model=BulkImportResult)
def bulk_import_json(
    req: BulkImportRequest,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """Programmatic bulk import. Case must be accessible to user with write permission."""
    case = require_case_access(req.case_id, db, user, action="write")
    return _import_items(db, case, req.items)


@router.post("/import/csv", response_model=BulkImportResult)
def bulk_import_csv(
    case_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """
    CSV upload bulk import. Expected columns (any order):
      - text (required)
      - source_url (optional)
      - author_username (optional, defaults to 'unknown')
      - platform (optional)

    Accepts up to ~10 MB CSV. Rows without text are skipped.
    """
    case = require_case_access(case_id, db, user, action="write")

    # Read + parse CSV
    content = file.file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 10 MB)")

    try:
        text = content.decode("utf-8-sig")  # handle BOM
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded")

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames or "text" not in reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV must have a 'text' column")

    items: list[BulkImportItem] = []
    for row in reader:
        items.append(BulkImportItem(
            text=row.get("text", "").strip(),
            source_url=row.get("source_url") or None,
            author_username=row.get("author_username", "unknown") or "unknown",
            platform=row.get("platform") or None,
        ))

    if not items:
        raise HTTPException(status_code=400, detail="CSV contained no rows")

    return _import_items(db, case, items)
