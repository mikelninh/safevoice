"""
Chain verification API endpoints.
Builds and verifies tamper-proof hash chains for case evidence.
Now backed by the database (hash_chain_previous stored on each evidence item).
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.database import get_db, Case as DBCase, EvidenceItem as DBEvidence
from app.services.chain import ChainLink, build_chain, verify_chain as verify_chain_service
from app.services.db_helpers import case_to_pydantic

router = APIRouter(prefix="/chain", tags=["chain"])


class BuildRequest(BaseModel):
    case_id: str


class ChainLinkSchema(BaseModel):
    evidence_id: str
    content_hash: str
    previous_hash: str
    chain_hash: str
    timestamp: datetime
    sequence_number: int


class VerifyRequest(BaseModel):
    chain: list[ChainLinkSchema]


class BuildResponse(BaseModel):
    case_id: str
    chain: list[ChainLinkSchema]
    length: int


class VerifyResponse(BaseModel):
    valid: bool
    message: str


def _chain_links_to_schema(chain: list[ChainLink]) -> list[ChainLinkSchema]:
    return [
        ChainLinkSchema(
            evidence_id=link.evidence_id,
            content_hash=link.content_hash,
            previous_hash=link.previous_hash,
            chain_hash=link.chain_hash,
            timestamp=link.timestamp,
            sequence_number=link.sequence_number,
        )
        for link in chain
    ]


def _schema_to_chain_links(schemas: list[ChainLinkSchema]) -> list[ChainLink]:
    return [
        ChainLink(
            evidence_id=s.evidence_id,
            content_hash=s.content_hash,
            previous_hash=s.previous_hash,
            chain_hash=s.chain_hash,
            timestamp=s.timestamp,
            sequence_number=s.sequence_number,
        )
        for s in schemas
    ]


def _load_case(case_id: str, db: Session) -> DBCase:
    case = (
        db.query(DBCase)
        .options(joinedload(DBCase.evidence_items))
        .filter(DBCase.id == case_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.post("/build", response_model=BuildResponse)
def build_chain_endpoint(req: BuildRequest, db: Session = Depends(get_db)):
    """Build a hash chain for a case's evidence items."""
    db_case = _load_case(req.case_id, db)
    pydantic_case = case_to_pydantic(db_case)

    chain = build_chain(pydantic_case.evidence_items)

    # Persist chain hashes back to DB
    for link in chain:
        ev = db.query(DBEvidence).filter_by(id=link.evidence_id).first()
        if ev:
            ev.hash_chain_previous = link.previous_hash
    db.commit()

    return BuildResponse(
        case_id=req.case_id,
        chain=_chain_links_to_schema(chain),
        length=len(chain),
    )


@router.post("/verify", response_model=VerifyResponse)
def verify_chain_endpoint(req: VerifyRequest):
    """Verify that a chain is intact and untampered."""
    chain = _schema_to_chain_links(req.chain)
    valid, message = verify_chain_service(chain)
    return VerifyResponse(valid=valid, message=message)


@router.get("/{case_id}", response_model=BuildResponse)
def get_chain(case_id: str, db: Session = Depends(get_db)):
    """Get existing chain for a case, or build one if needed."""
    db_case = _load_case(case_id, db)
    pydantic_case = case_to_pydantic(db_case)
    chain = build_chain(pydantic_case.evidence_items)

    return BuildResponse(
        case_id=case_id,
        chain=_chain_links_to_schema(chain),
        length=len(chain),
    )
