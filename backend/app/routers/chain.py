"""
Chain verification API endpoints.
Builds and verifies tamper-proof hash chains for case evidence.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.data.mock_data import get_case_by_id
from app.services.chain import (
    ChainLink,
    build_chain,
    verify_chain as verify_chain_service,
)

router = APIRouter(prefix="/chain", tags=["chain"])

# In-memory store for built chains (keyed by case_id)
_chain_store: dict[str, list[ChainLink]] = {}


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


@router.post("/build", response_model=BuildResponse)
def build_chain_endpoint(req: BuildRequest):
    """Build a hash chain for a case's evidence items."""
    case = get_case_by_id(req.case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    chain = build_chain(case.evidence_items)
    _chain_store[req.case_id] = chain

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
def get_chain(case_id: str):
    """Get existing chain for a case, or build one if it doesn't exist."""
    if case_id in _chain_store:
        chain = _chain_store[case_id]
    else:
        case = get_case_by_id(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        chain = build_chain(case.evidence_items)
        _chain_store[case_id] = chain

    return BuildResponse(
        case_id=case_id,
        chain=_chain_links_to_schema(chain),
        length=len(chain),
    )
