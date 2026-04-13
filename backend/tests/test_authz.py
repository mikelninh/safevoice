"""
Tests for authorization logic.

Covers:
  - role_meets helper
  - require_case_access happy + denial paths
  - Multi-tenant isolation (user A can't see user B's case)
  - Org membership role enforcement
"""

import pytest
from fastapi import HTTPException

from app.database import SessionLocal, User, Org, OrgMember, Case, gen_uuid
from app.services.authz import (
    role_meets, require_case_access, require_org_access,
    list_accessible_cases,
)


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    # Cleanup test data
    session.rollback()
    session.close()


@pytest.fixture
def org_setup(db):
    """Create two orgs with distinct users/cases for isolation tests."""
    # Org A
    alice = User(id=gen_uuid(), email=f"alice-{gen_uuid()[:6]}@test")
    bob = User(id=gen_uuid(), email=f"bob-{gen_uuid()[:6]}@test")
    org_a = Org(id=gen_uuid(), slug=f"org-a-{gen_uuid()[:6]}", display_name="Org A")
    db.add_all([alice, bob, org_a])
    db.flush()
    db.add_all([
        OrgMember(user_id=alice.id, org_id=org_a.id, role="owner"),
        OrgMember(user_id=bob.id, org_id=org_a.id, role="caseworker"),
    ])

    # Org B
    carol = User(id=gen_uuid(), email=f"carol-{gen_uuid()[:6]}@test")
    org_b = Org(id=gen_uuid(), slug=f"org-b-{gen_uuid()[:6]}", display_name="Org B")
    db.add_all([carol, org_b])
    db.flush()
    db.add(OrgMember(user_id=carol.id, org_id=org_b.id, role="owner"))

    # Cases
    case_alice_private = Case(
        id=gen_uuid(), title="Alice private", user_id=alice.id,
        org_id=org_a.id, visibility="private",
    )
    case_org_a_shared = Case(
        id=gen_uuid(), title="Org A shared", user_id=alice.id,
        org_id=org_a.id, visibility="org",
    )
    case_org_b = Case(
        id=gen_uuid(), title="Org B case", user_id=carol.id,
        org_id=org_b.id, visibility="org",
    )
    db.add_all([case_alice_private, case_org_a_shared, case_org_b])
    db.commit()

    yield {
        "alice": alice, "bob": bob, "carol": carol,
        "org_a": org_a, "org_b": org_b,
        "case_alice_private": case_alice_private,
        "case_org_a_shared": case_org_a_shared,
        "case_org_b": case_org_b,
    }

    # Cleanup
    for case in [case_alice_private, case_org_a_shared, case_org_b]:
        db.delete(case)
    db.query(OrgMember).filter(OrgMember.org_id.in_([org_a.id, org_b.id])).delete()
    db.query(Org).filter(Org.id.in_([org_a.id, org_b.id])).delete()
    db.query(User).filter(User.id.in_([alice.id, bob.id, carol.id])).delete()
    db.commit()


class TestRoleMeets:
    def test_owner_meets_everything(self):
        assert role_meets("owner", "owner") is True
        assert role_meets("owner", "admin") is True
        assert role_meets("owner", "caseworker") is True
        assert role_meets("owner", "viewer") is True

    def test_viewer_meets_only_viewer(self):
        assert role_meets("viewer", "viewer") is True
        assert role_meets("viewer", "caseworker") is False
        assert role_meets("viewer", "admin") is False
        assert role_meets("viewer", "owner") is False

    def test_caseworker_between(self):
        assert role_meets("caseworker", "viewer") is True
        assert role_meets("caseworker", "caseworker") is True
        assert role_meets("caseworker", "admin") is False

    def test_unknown_role_fails(self):
        assert role_meets("god", "viewer") is False
        assert role_meets("", "viewer") is False


class TestCaseAccess:
    def test_creator_can_read_own_case(self, db, org_setup):
        s = org_setup
        case = require_case_access(
            s["case_alice_private"].id, db, s["alice"], action="read",
        )
        assert case.id == s["case_alice_private"].id

    def test_creator_can_delete_own_case(self, db, org_setup):
        s = org_setup
        # No exception
        require_case_access(
            s["case_alice_private"].id, db, s["alice"], action="delete",
        )

    def test_other_org_user_cannot_access(self, db, org_setup):
        """Carol (Org B) cannot see Org A's case."""
        s = org_setup
        with pytest.raises(HTTPException) as exc:
            require_case_access(s["case_org_a_shared"].id, db, s["carol"], action="read")
        assert exc.value.status_code == 403

    def test_non_creator_cannot_see_private_case(self, db, org_setup):
        """Bob (member of Org A) cannot see Alice's private case in the same org."""
        s = org_setup
        with pytest.raises(HTTPException) as exc:
            require_case_access(s["case_alice_private"].id, db, s["bob"], action="read")
        assert exc.value.status_code == 403
        assert "Private" in exc.value.detail or "private" in exc.value.detail

    def test_caseworker_can_read_org_case(self, db, org_setup):
        """Bob (caseworker in Org A) can read the org-visible case."""
        s = org_setup
        case = require_case_access(
            s["case_org_a_shared"].id, db, s["bob"], action="read",
        )
        assert case.id == s["case_org_a_shared"].id

    def test_caseworker_cannot_delete(self, db, org_setup):
        """Bob (caseworker) can't delete — requires admin+."""
        s = org_setup
        with pytest.raises(HTTPException) as exc:
            require_case_access(s["case_org_a_shared"].id, db, s["bob"], action="delete")
        assert exc.value.status_code == 403

    def test_missing_case_404(self, db, org_setup):
        s = org_setup
        with pytest.raises(HTTPException) as exc:
            require_case_access("nonexistent-id", db, s["alice"])
        assert exc.value.status_code == 404


class TestOrgAccess:
    def test_member_can_read_org(self, db, org_setup):
        s = org_setup
        org, mem = require_org_access(s["org_a"].id, db, s["alice"], action="read")
        assert org.id == s["org_a"].id
        assert mem.role == "owner"

    def test_non_member_cannot_read_org(self, db, org_setup):
        s = org_setup
        with pytest.raises(HTTPException) as exc:
            require_org_access(s["org_b"].id, db, s["alice"], action="read")
        assert exc.value.status_code == 403

    def test_slug_lookup_works(self, db, org_setup):
        s = org_setup
        org, _ = require_org_access(s["org_a"].slug, db, s["alice"], action="read")
        assert org.id == s["org_a"].id

    def test_caseworker_cannot_manage(self, db, org_setup):
        s = org_setup
        with pytest.raises(HTTPException) as exc:
            require_org_access(s["org_a"].id, db, s["bob"], action="manage_org")
        assert exc.value.status_code == 403


class TestListAccessibleCases:
    def test_alice_sees_her_cases_and_shared(self, db, org_setup):
        s = org_setup
        cases = list_accessible_cases(db, s["alice"])
        ids = [c.id for c in cases]
        assert s["case_alice_private"].id in ids  # her own
        assert s["case_org_a_shared"].id in ids   # she created it
        assert s["case_org_b"].id not in ids      # different org

    def test_bob_sees_org_cases_only(self, db, org_setup):
        s = org_setup
        cases = list_accessible_cases(db, s["bob"])
        ids = [c.id for c in cases]
        assert s["case_alice_private"].id not in ids  # private, not his
        assert s["case_org_a_shared"].id in ids       # org-visible
        assert s["case_org_b"].id not in ids          # different org
