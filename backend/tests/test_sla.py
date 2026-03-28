"""
Tests for NetzDG SLA deadline tracking system.
"""

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.models.sla import SLADashboard, SLARecord, SLAStatus
from app.services.sla_tracker import (
    check_deadlines,
    clear_records,
    create_sla_record,
    get_dashboard,
    get_all_records,
    update_sla_status,
)

client = TestClient(app)


class TestSLARecordCreation:
    def setup_method(self):
        clear_records()

    def test_create_record_returns_sla_record(self):
        """Creating an SLA record returns a valid SLARecord."""
        record = create_sla_record(
            case_id="case-001",
            evidence_id="ev-001",
            platform="instagram",
            severity="high",
        )
        assert isinstance(record, SLARecord)
        assert record.case_id == "case-001"
        assert record.evidence_id == "ev-001"
        assert record.platform == "instagram"
        assert record.status == SLAStatus.REPORTED

    def test_create_record_critical_24h_deadline(self):
        """Critical severity gets a 24-hour deadline (NetzDG clearly illegal content)."""
        record = create_sla_record(
            case_id="case-001",
            evidence_id="ev-001",
            platform="twitter",
            severity="critical",
        )
        assert record.deadline_24h is not None
        assert record.deadline_7d is None
        # Deadline should be ~24 hours from now
        expected = record.reported_at + timedelta(hours=24)
        delta = abs((record.deadline_24h - expected).total_seconds())
        assert delta < 2  # within 2 seconds tolerance

    def test_create_record_noncritical_7d_deadline(self):
        """Non-critical severity gets a 7-day deadline (NetzDG other illegal content)."""
        for severity in ["high", "medium", "low"]:
            clear_records()
            record = create_sla_record(
                case_id="case-001",
                evidence_id="ev-001",
                platform="facebook",
                severity=severity,
            )
            assert record.deadline_7d is not None
            assert record.deadline_24h is None
            expected = record.reported_at + timedelta(days=7)
            delta = abs((record.deadline_7d - expected).total_seconds())
            assert delta < 2

    def test_create_record_has_utc_timestamp(self):
        """Reported_at timestamp must be UTC with timezone info."""
        record = create_sla_record(
            case_id="case-001",
            evidence_id="ev-001",
            platform="instagram",
            severity="medium",
        )
        assert record.reported_at is not None
        assert record.reported_at.tzinfo is not None


class TestDeadlineExpiry:
    def setup_method(self):
        clear_records()

    def test_expired_24h_record_detected(self):
        """A critical record past its 24h deadline should be marked expired."""
        past = datetime.now(timezone.utc) - timedelta(hours=25)
        record = SLARecord(
            id="sla-test-expired",
            case_id="case-001",
            evidence_id="ev-001",
            platform="twitter",
            reported_at=past,
            deadline_24h=past + timedelta(hours=24),
            deadline_7d=None,
            status=SLAStatus.REPORTED,
        )
        result = check_deadlines([record])
        assert result[0].status == SLAStatus.EXPIRED

    def test_expired_7d_record_detected(self):
        """A non-critical record past its 7-day deadline should be marked expired."""
        past = datetime.now(timezone.utc) - timedelta(days=8)
        record = SLARecord(
            id="sla-test-expired-7d",
            case_id="case-002",
            evidence_id="ev-002",
            platform="facebook",
            reported_at=past,
            deadline_24h=None,
            deadline_7d=past + timedelta(days=7),
            status=SLAStatus.ACKNOWLEDGED,
        )
        result = check_deadlines([record])
        assert result[0].status == SLAStatus.EXPIRED

    def test_within_deadline_not_expired(self):
        """A record still within its deadline should NOT be marked expired."""
        now = datetime.now(timezone.utc)
        record = SLARecord(
            id="sla-test-active",
            case_id="case-003",
            evidence_id="ev-003",
            platform="youtube",
            reported_at=now,
            deadline_24h=None,
            deadline_7d=now + timedelta(days=7),
            status=SLAStatus.REPORTED,
        )
        result = check_deadlines([record])
        assert result[0].status == SLAStatus.REPORTED

    def test_removed_record_stays_removed(self):
        """A record already marked as REMOVED should not be changed to EXPIRED."""
        past = datetime.now(timezone.utc) - timedelta(days=8)
        record = SLARecord(
            id="sla-test-removed",
            case_id="case-004",
            evidence_id="ev-004",
            platform="tiktok",
            reported_at=past,
            deadline_24h=None,
            deadline_7d=past + timedelta(days=7),
            status=SLAStatus.REMOVED,
            removed_at=past + timedelta(days=3),
        )
        result = check_deadlines([record])
        assert result[0].status == SLAStatus.REMOVED


class TestStatusUpdate:
    def setup_method(self):
        clear_records()

    def test_update_status_to_removed(self):
        """Updating status to REMOVED should auto-set removed_at."""
        record = create_sla_record(
            case_id="case-001",
            evidence_id="ev-001",
            platform="instagram",
            severity="high",
        )
        updated = update_sla_status(record.id, SLAStatus.REMOVED)
        assert updated is not None
        assert updated.status == SLAStatus.REMOVED
        assert updated.removed_at is not None

    def test_update_status_with_response(self):
        """Platform response should be stored when updating status."""
        record = create_sla_record(
            case_id="case-001",
            evidence_id="ev-001",
            platform="twitter",
            severity="medium",
        )
        updated = update_sla_status(
            record.id,
            SLAStatus.ACKNOWLEDGED,
            response="We are reviewing the content.",
        )
        assert updated is not None
        assert updated.status == SLAStatus.ACKNOWLEDGED
        assert updated.platform_response == "We are reviewing the content."

    def test_update_nonexistent_record_returns_none(self):
        """Updating a nonexistent record should return None."""
        result = update_sla_status("nonexistent-id", SLAStatus.REMOVED)
        assert result is None


class TestDashboard:
    def test_empty_dashboard(self):
        """Dashboard with no records returns zeros."""
        dashboard = get_dashboard([])
        assert dashboard.total_reports == 0
        assert dashboard.removal_rate == 0.0
        assert dashboard.avg_removal_hours is None

    def test_dashboard_computation(self):
        """Dashboard should correctly compute aggregate stats."""
        now = datetime.now(timezone.utc)
        records = [
            SLARecord(
                id="sla-1",
                case_id="c-1",
                evidence_id="e-1",
                platform="instagram",
                reported_at=now - timedelta(hours=48),
                deadline_7d=now + timedelta(days=5),
                status=SLAStatus.REMOVED,
                removed_at=now - timedelta(hours=24),
            ),
            SLARecord(
                id="sla-2",
                case_id="c-1",
                evidence_id="e-2",
                platform="twitter",
                reported_at=now - timedelta(hours=6),
                deadline_24h=now + timedelta(hours=18),
                status=SLAStatus.REPORTED,
            ),
            SLARecord(
                id="sla-3",
                case_id="c-2",
                evidence_id="e-3",
                platform="facebook",
                reported_at=now - timedelta(days=10),
                deadline_7d=now - timedelta(days=3),
                status=SLAStatus.EXPIRED,
            ),
            SLARecord(
                id="sla-4",
                case_id="c-3",
                evidence_id="e-4",
                platform="tiktok",
                status=SLAStatus.PENDING,
            ),
        ]
        dashboard = get_dashboard(records)
        assert dashboard.total_reports == 4
        assert dashboard.pending == 1
        assert dashboard.expired == 1
        assert dashboard.removed == 1
        assert dashboard.within_deadline == 1
        assert dashboard.removal_rate == 25.0
        # Removal took 24 hours (48h reported, 24h ago removed)
        assert dashboard.avg_removal_hours == 24.0


class TestAPIEndpoints:
    def setup_method(self):
        clear_records()

    def test_post_sla_report(self):
        """POST /sla/report should create and return an SLA record."""
        resp = client.post("/sla/report", json={
            "case_id": "case-api-001",
            "evidence_id": "ev-api-001",
            "platform": "instagram",
            "severity": "critical",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["case_id"] == "case-api-001"
        assert data["status"] == "reported"
        assert data["deadline_24h"] is not None
        assert data["deadline_7d"] is None

    def test_get_case_sla_records(self):
        """GET /sla/{case_id} should return all SLA records for a case."""
        client.post("/sla/report", json={
            "case_id": "case-api-002",
            "evidence_id": "ev-1",
            "platform": "twitter",
            "severity": "high",
        })
        client.post("/sla/report", json={
            "case_id": "case-api-002",
            "evidence_id": "ev-2",
            "platform": "twitter",
            "severity": "medium",
        })
        resp = client.get("/sla/case-api-002")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_get_case_sla_records_not_found(self):
        """GET /sla/{case_id} with no records should return 404."""
        resp = client.get("/sla/nonexistent-case")
        assert resp.status_code == 404

    def test_put_update_status(self):
        """PUT /sla/{record_id}/status should update the record status."""
        create_resp = client.post("/sla/report", json={
            "case_id": "case-api-003",
            "evidence_id": "ev-1",
            "platform": "facebook",
            "severity": "low",
        })
        record_id = create_resp.json()["id"]

        update_resp = client.put(f"/sla/{record_id}/status", json={
            "status": "acknowledged",
            "platform_response": "Under review",
        })
        assert update_resp.status_code == 200
        data = update_resp.json()
        assert data["status"] == "acknowledged"
        assert data["platform_response"] == "Under review"

    def test_put_update_status_not_found(self):
        """PUT /sla/{record_id}/status with unknown ID should return 404."""
        resp = client.put("/sla/bad-id/status", json={"status": "removed"})
        assert resp.status_code == 404

    def test_get_dashboard(self):
        """GET /sla/dashboard should return aggregate stats."""
        client.post("/sla/report", json={
            "case_id": "case-dash",
            "evidence_id": "ev-1",
            "platform": "instagram",
            "severity": "critical",
        })
        resp = client.get("/sla/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_reports"] == 1
        assert data["removal_rate"] == 0.0
