"""
Cryptographic evidence chain verification.

Builds a tamper-proof hash chain linking evidence items together.
Each link's chain_hash = SHA-256(content_hash + previous_hash + sequence_number).
The first link uses "genesis" as previous_hash.
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone

from app.models.evidence import EvidenceItem


@dataclass
class ChainLink:
    evidence_id: str
    content_hash: str
    previous_hash: str
    chain_hash: str
    timestamp: datetime
    sequence_number: int


def _compute_chain_hash(content_hash: str, previous_hash: str, sequence_number: int) -> str:
    """Compute chain_hash = SHA-256(content_hash + previous_hash + sequence_number)."""
    payload = f"{content_hash}{previous_hash}{sequence_number}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_chain(evidence_items: list[EvidenceItem]) -> list[ChainLink]:
    """
    Build a hash chain from a list of evidence items.
    Each link's chain_hash depends on the previous link, creating
    a tamper-proof chain of evidence.
    """
    chain: list[ChainLink] = []
    previous_hash = "genesis"

    for i, item in enumerate(evidence_items):
        chain_hash = _compute_chain_hash(item.content_hash, previous_hash, i)
        link = ChainLink(
            evidence_id=item.id,
            content_hash=item.content_hash,
            previous_hash=previous_hash,
            chain_hash=chain_hash,
            timestamp=datetime.now(timezone.utc),
            sequence_number=i,
        )
        chain.append(link)
        previous_hash = chain_hash

    return chain


def verify_chain(chain: list[ChainLink]) -> tuple[bool, str]:
    """
    Verify the entire chain is intact.
    Returns (valid, message).
    """
    if not chain:
        return (True, "Empty chain is trivially valid.")

    # Verify genesis block
    if chain[0].previous_hash != "genesis":
        return (False, f"Genesis block has wrong previous_hash: expected 'genesis', got '{chain[0].previous_hash}'.")

    for i, link in enumerate(chain):
        # Verify sequence number
        if link.sequence_number != i:
            return (False, f"Link {i} has wrong sequence_number: expected {i}, got {link.sequence_number}.")

        # Verify chain_hash
        expected_hash = _compute_chain_hash(link.content_hash, link.previous_hash, link.sequence_number)
        if link.chain_hash != expected_hash:
            return (False, f"Link {i} (evidence {link.evidence_id}) has invalid chain_hash: expected {expected_hash}, got {link.chain_hash}.")

        # Verify previous_hash linkage (for all links after genesis)
        if i > 0 and link.previous_hash != chain[i - 1].chain_hash:
            return (False, f"Link {i} (evidence {link.evidence_id}) has broken previous_hash linkage.")

    return (True, f"Chain of {len(chain)} links verified successfully.")


def verify_single(chain: list[ChainLink], evidence_id: str) -> bool:
    """
    Verify a single item hasn't been tampered with.
    Checks that the link's chain_hash is consistent with its own data
    and that it is correctly linked to its predecessor.
    """
    for i, link in enumerate(chain):
        if link.evidence_id == evidence_id:
            # Verify chain_hash
            expected_hash = _compute_chain_hash(link.content_hash, link.previous_hash, link.sequence_number)
            if link.chain_hash != expected_hash:
                return False

            # Verify previous_hash linkage
            if i == 0:
                return link.previous_hash == "genesis"
            else:
                return link.previous_hash == chain[i - 1].chain_hash

    # Evidence ID not found in chain
    return False
