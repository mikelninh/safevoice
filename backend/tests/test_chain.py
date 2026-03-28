"""
Tests for the cryptographic evidence chain verification system.
"""

import copy

from app.data.mock_data import get_case_by_id
from app.models.evidence import EvidenceItem
from app.services.chain import ChainLink, build_chain, verify_chain, verify_single


class TestBuildChain:
    def test_build_chain_with_multiple_items(self):
        """Chain should have the same number of links as evidence items."""
        case = get_case_by_id("case-001")
        assert case is not None
        chain = build_chain(case.evidence_items)
        assert len(chain) == len(case.evidence_items)
        assert len(chain) == 3

    def test_chain_links_have_correct_evidence_ids(self):
        """Each link should reference the correct evidence item."""
        case = get_case_by_id("case-001")
        chain = build_chain(case.evidence_items)
        for i, link in enumerate(chain):
            assert link.evidence_id == case.evidence_items[i].id

    def test_chain_links_have_sequential_numbers(self):
        """Sequence numbers should be 0, 1, 2, ..."""
        case = get_case_by_id("case-001")
        chain = build_chain(case.evidence_items)
        for i, link in enumerate(chain):
            assert link.sequence_number == i

    def test_chain_hashes_are_unique(self):
        """Each link should have a unique chain_hash."""
        case = get_case_by_id("case-001")
        chain = build_chain(case.evidence_items)
        hashes = [link.chain_hash for link in chain]
        assert len(set(hashes)) == len(hashes)

    def test_chain_links_are_connected(self):
        """Each link's previous_hash should match the prior link's chain_hash."""
        case = get_case_by_id("case-001")
        chain = build_chain(case.evidence_items)
        for i in range(1, len(chain)):
            assert chain[i].previous_hash == chain[i - 1].chain_hash


class TestGenesisBlock:
    def test_genesis_has_correct_previous_hash(self):
        """The first link must use 'genesis' as previous_hash."""
        case = get_case_by_id("case-001")
        chain = build_chain(case.evidence_items)
        assert chain[0].previous_hash == "genesis"

    def test_genesis_has_sequence_zero(self):
        """The first link must have sequence_number 0."""
        case = get_case_by_id("case-001")
        chain = build_chain(case.evidence_items)
        assert chain[0].sequence_number == 0


class TestVerifyChain:
    def test_valid_chain_passes_verification(self):
        """A freshly built chain should verify successfully."""
        case = get_case_by_id("case-001")
        chain = build_chain(case.evidence_items)
        valid, message = verify_chain(chain)
        assert valid is True
        assert "verified successfully" in message

    def test_valid_chain_case_002(self):
        """Verification works with different cases."""
        case = get_case_by_id("case-002")
        chain = build_chain(case.evidence_items)
        valid, message = verify_chain(chain)
        assert valid is True

    def test_empty_chain_is_valid(self):
        """An empty chain is trivially valid."""
        valid, message = verify_chain([])
        assert valid is True

    def test_tampered_content_hash_fails(self):
        """Changing a content_hash should break verification."""
        case = get_case_by_id("case-001")
        chain = build_chain(case.evidence_items)
        # Tamper with the second link's content_hash
        chain[1].content_hash = "sha256:tampered_hash_value"
        valid, message = verify_chain(chain)
        assert valid is False
        assert "invalid chain_hash" in message

    def test_tampered_chain_hash_fails(self):
        """Changing a chain_hash should break verification."""
        case = get_case_by_id("case-001")
        chain = build_chain(case.evidence_items)
        chain[0].chain_hash = "tampered_chain_hash"
        valid, message = verify_chain(chain)
        assert valid is False

    def test_tampered_previous_hash_fails(self):
        """Changing a previous_hash should break verification."""
        case = get_case_by_id("case-001")
        chain = build_chain(case.evidence_items)
        chain[1].previous_hash = "tampered_previous_hash"
        valid, message = verify_chain(chain)
        assert valid is False

    def test_tampered_genesis_previous_hash_fails(self):
        """Changing the genesis previous_hash from 'genesis' should fail."""
        case = get_case_by_id("case-001")
        chain = build_chain(case.evidence_items)
        chain[0].previous_hash = "not_genesis"
        valid, message = verify_chain(chain)
        assert valid is False

    def test_wrong_sequence_number_fails(self):
        """Wrong sequence numbers should fail verification."""
        case = get_case_by_id("case-001")
        chain = build_chain(case.evidence_items)
        chain[1].sequence_number = 99
        valid, message = verify_chain(chain)
        assert valid is False


class TestVerifySingle:
    def test_single_valid_item(self):
        """A single item in an untampered chain should verify."""
        case = get_case_by_id("case-001")
        chain = build_chain(case.evidence_items)
        assert verify_single(chain, "ev-001-a") is True
        assert verify_single(chain, "ev-001-b") is True
        assert verify_single(chain, "ev-001-c") is True

    def test_single_tampered_item_fails(self):
        """Tampering with an item's content_hash should fail single verification."""
        case = get_case_by_id("case-001")
        chain = build_chain(case.evidence_items)
        chain[1].content_hash = "sha256:tampered"
        assert verify_single(chain, "ev-001-b") is False

    def test_nonexistent_evidence_id_fails(self):
        """An evidence ID not in the chain should return False."""
        case = get_case_by_id("case-001")
        chain = build_chain(case.evidence_items)
        assert verify_single(chain, "ev-nonexistent") is False

    def test_genesis_item_verifies(self):
        """The genesis item should verify correctly."""
        case = get_case_by_id("case-001")
        chain = build_chain(case.evidence_items)
        assert verify_single(chain, "ev-001-a") is True


class TestChainAPI:
    def _client(self):
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)

    def test_build_chain_endpoint(self):
        """POST /chain/build should return a chain for a valid case."""
        client = self._client()
        resp = client.post("/chain/build", json={"case_id": "case-001"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["case_id"] == "case-001"
        assert data["length"] == 3
        assert len(data["chain"]) == 3
        # Verify genesis
        assert data["chain"][0]["previous_hash"] == "genesis"

    def test_build_chain_not_found(self):
        """POST /chain/build with unknown case_id should 404."""
        client = self._client()
        resp = client.post("/chain/build", json={"case_id": "nonexistent"})
        assert resp.status_code == 404

    def test_verify_chain_endpoint_valid(self):
        """POST /chain/verify with a valid chain should return valid=True."""
        client = self._client()
        # First build
        build_resp = client.post("/chain/build", json={"case_id": "case-001"})
        chain_data = build_resp.json()["chain"]
        # Then verify
        resp = client.post("/chain/verify", json={"chain": chain_data})
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True

    def test_verify_chain_endpoint_tampered(self):
        """POST /chain/verify with a tampered chain should return valid=False."""
        client = self._client()
        build_resp = client.post("/chain/build", json={"case_id": "case-001"})
        chain_data = build_resp.json()["chain"]
        # Tamper
        chain_data[1]["content_hash"] = "sha256:tampered"
        resp = client.post("/chain/verify", json={"chain": chain_data})
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is False

    def test_get_chain_endpoint(self):
        """GET /chain/{case_id} should return a chain."""
        client = self._client()
        resp = client.get("/chain/case-002")
        assert resp.status_code == 200
        data = resp.json()
        assert data["case_id"] == "case-002"
        assert data["length"] == 2

    def test_get_chain_not_found(self):
        """GET /chain/{case_id} with unknown case_id should 404."""
        client = self._client()
        resp = client.get("/chain/nonexistent")
        assert resp.status_code == 404

    def test_get_chain_returns_cached(self):
        """GET /chain/{case_id} after build should return the same chain."""
        client = self._client()
        # Build first
        build_resp = client.post("/chain/build", json={"case_id": "case-004"})
        build_chain = build_resp.json()["chain"]
        # Get should return the cached version
        get_resp = client.get("/chain/case-004")
        get_chain = get_resp.json()["chain"]
        assert build_chain == get_chain
