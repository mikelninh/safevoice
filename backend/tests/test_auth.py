"""
Tests for magic link authentication system.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.auth import (
    request_magic_link, verify_magic_link, get_user_by_session,
    soft_delete_user, emergency_delete_user, get_user, cleanup_expired,
)
from app.models.user import UserStatus
from datetime import datetime, timezone, timedelta


@pytest.fixture
def client():
    return TestClient(app)


def _login_flow(client) -> tuple[str, str]:
    """Helper: complete login flow, return (session_token, user_id)."""
    resp = client.post("/auth/login", json={"email": f"test-{id(client)}@example.com"})
    token = resp.json()["magic_link_token"]
    resp2 = client.post("/auth/verify", json={"token": token})
    data = resp2.json()
    return data["session_token"], data["user"]["id"]


class TestMagicLinkFlow:
    def test_request_magic_link(self):
        link = request_magic_link("user@test.de")
        assert link.token
        assert len(link.token) > 20
        assert link.email == "user@test.de"

    def test_verify_valid_link(self):
        link = request_magic_link("verify@test.de")
        session = verify_magic_link(link.token)
        assert session is not None
        assert session.token
        assert session.active is True

    def test_verify_creates_user(self):
        link = request_magic_link("newuser@test.de")
        session = verify_magic_link(link.token)
        user = get_user(session.user_id)
        assert user is not None
        assert user.email == "newuser@test.de"

    def test_verify_same_email_reuses_user(self):
        link1 = request_magic_link("same@test.de")
        session1 = verify_magic_link(link1.token)

        link2 = request_magic_link("same@test.de")
        session2 = verify_magic_link(link2.token)

        assert session1.user_id == session2.user_id

    def test_link_can_only_be_used_once(self):
        link = request_magic_link("once@test.de")
        session1 = verify_magic_link(link.token)
        session2 = verify_magic_link(link.token)
        assert session1 is not None
        assert session2 is None

    def test_invalid_token_returns_none(self):
        assert verify_magic_link("totally_fake_token") is None

    def test_session_authenticates_user(self):
        link = request_magic_link("session@test.de")
        session = verify_magic_link(link.token)
        user = get_user_by_session(session.token)
        assert user is not None
        assert user.email == "session@test.de"

    def test_email_is_case_insensitive(self):
        link = request_magic_link("UPPER@TEST.DE")
        session = verify_magic_link(link.token)
        user = get_user(session.user_id)
        assert user.email == "upper@test.de"


class TestAuthEndpoints:
    def test_login_endpoint(self, client):
        resp = client.post("/auth/login", json={"email": "api@test.de"})
        assert resp.status_code == 200
        data = resp.json()
        assert "magic_link_token" in data
        assert "Magic link sent" in data["message"]

    def test_login_invalid_email(self, client):
        resp = client.post("/auth/login", json={"email": "notanemail"})
        assert resp.status_code == 400

    def test_verify_endpoint(self, client):
        login_resp = client.post("/auth/login", json={"email": "verify-api@test.de"})
        token = login_resp.json()["magic_link_token"]

        resp = client.post("/auth/verify", json={"token": token})
        assert resp.status_code == 200
        data = resp.json()
        assert "session_token" in data
        assert data["user"]["email"] == "verify-api@test.de"

    def test_verify_invalid_token(self, client):
        resp = client.post("/auth/verify", json={"token": "fake"})
        assert resp.status_code == 401

    def test_get_me(self, client):
        session_token, _ = _login_flow(client)
        resp = client.get("/auth/me", headers={"Authorization": f"Bearer {session_token}"})
        assert resp.status_code == 200
        assert "email" in resp.json()

    def test_get_me_unauthenticated(self, client):
        resp = client.get("/auth/me")
        assert resp.status_code == 401

    def test_update_profile(self, client):
        session_token, _ = _login_flow(client)
        resp = client.put(
            "/auth/me",
            json={"display_name": "Test User", "lang": "en"},
            headers={"Authorization": f"Bearer {session_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["user"]["display_name"] == "Test User"

    def test_logout(self, client):
        session_token, _ = _login_flow(client)

        resp = client.post("/auth/logout", headers={"Authorization": f"Bearer {session_token}"})
        assert resp.status_code == 200

        # Session should be invalid now
        resp2 = client.get("/auth/me", headers={"Authorization": f"Bearer {session_token}"})
        assert resp2.status_code == 401


class TestDeletion:
    def test_soft_delete(self, client):
        session_token, user_id = _login_flow(client)

        resp = client.delete("/auth/me", headers={"Authorization": f"Bearer {session_token}"})
        assert resp.status_code == 200
        assert "7 days" in resp.json()["hard_delete_after"]

        # User should be gone
        assert get_user(user_id) is None

    def test_emergency_delete(self, client):
        session_token, user_id = _login_flow(client)

        resp = client.delete("/auth/me/emergency", headers={"Authorization": f"Bearer {session_token}"})
        assert resp.status_code == 200
        assert resp.json()["recovered"] is False

        # Completely gone — no soft-delete window
        assert get_user(user_id) is None

    def test_soft_delete_function(self):
        link = request_magic_link("softdel@test.de")
        session = verify_magic_link(link.token)
        user = get_user(session.user_id)
        assert user is not None

        soft_delete_user(session.user_id)
        assert get_user(session.user_id) is None  # hidden

    def test_emergency_delete_function(self):
        link = request_magic_link("harddel@test.de")
        session = verify_magic_link(link.token)

        result = emergency_delete_user(session.user_id)
        assert result is True

        # Session should be gone too
        assert get_user_by_session(session.token) is None
