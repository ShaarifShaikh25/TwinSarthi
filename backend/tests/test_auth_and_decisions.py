"""tests/test_auth_and_decisions.py

Test suite for POLAR-TWIN Phase 8:
- JWT Authentication (Admin, Controller, Viewer)
- Role-Based Access Control (RBAC) endpoint protection
- Simulation interface (run_simulation)
- Recommendation ingestion and decision lifecycle (Approve, Modify, Reject)
- Complete audit logging of controller actions
"""

import pytest
from datetime import datetime, timezone
from starlette.testclient import TestClient

from app.main import app
from app.core.database import Base, engine, SessionLocal
from app.models.station import Station, StationStatus
from app.models.user import User, UserRole
from app.models.recommendation import Recommendation, RecommendationStatus, RecommendationSeverity
from app.services.auth_service import seed_default_users

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Ensure database schema and test seeds exist."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Clear relevant tables
    db.query(Recommendation).delete()
    db.query(User).delete()
    db.query(Station).delete()
    db.commit()

    # Seed MAITRI station
    maitri = Station(
        id=1,
        name="Maitri Research Station",
        code="MAITRI",
        latitude=-70.7667,
        longitude=11.7333,
        status=StationStatus.ACTIVE,
    )
    db.add(maitri)
    db.commit()

    # Seed default user accounts (admin, controller, viewer)
    seed_default_users(db)
    db.close()


def _login(username: str, password: str) -> str:
    """Helper to login and extract JWT bearer access token."""
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200, f"Login failed for {username}: {resp.text}"
    return resp.json()["data"]["access_token"]


def test_jwt_authentication_and_profiles():
    """Verify login for Admin, Controller, and Viewer, and inspect GET /api/auth/me."""
    # 1. Login Admin
    admin_token = _login("admin", "Admin@123")
    resp_admin_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp_admin_me.status_code == 200
    assert resp_admin_me.json()["data"]["username"] == "admin"
    assert resp_admin_me.json()["data"]["role"] == "admin"

    # 2. Login Controller
    controller_token = _login("controller", "Controller@123")
    resp_ctrl_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {controller_token}"})
    assert resp_ctrl_me.status_code == 200
    assert resp_ctrl_me.json()["data"]["username"] == "controller"
    assert resp_ctrl_me.json()["data"]["role"] == "controller"

    # 3. Login Viewer
    viewer_token = _login("viewer", "Viewer@123")
    resp_view_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {viewer_token}"})
    assert resp_view_me.status_code == 200
    assert resp_view_me.json()["data"]["username"] == "viewer"
    assert resp_view_me.json()["data"]["role"] == "viewer"

    # 4. Invalid credentials
    resp_bad = client.post("/api/auth/login", json={"username": "admin", "password": "WrongPassword!"})
    assert resp_bad.status_code == 401

    # 5. Missing token on protected route
    resp_unauth = client.get("/api/auth/me")
    assert resp_unauth.status_code == 401


def test_simulation_run_role_protection():
    """Verify POST /api/simulation/run:
    - Controller: Allowed
    - Admin: Allowed
    - Viewer: 403 Forbidden
    - Unauthenticated: 401 Unauthorized
    """
    controller_token = _login("controller", "Controller@123")
    admin_token = _login("admin", "Admin@123")
    viewer_token = _login("viewer", "Viewer@123")

    sim_payload = {
        "station_id": "MAITRI",
        "scenario_type": "blizzard_survival",
        "duration_hours": 48,
        "parameters": {"wind_peak_ms": 45.0, "ambient_temp_c": -55.0},
    }

    # 1. Unauthenticated -> 401
    resp_unauth = client.post("/api/simulation/run", json=sim_payload)
    assert resp_unauth.status_code == 401

    # 2. Viewer -> 403 Forbidden
    resp_viewer = client.post(
        "/api/simulation/run",
        json=sim_payload,
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp_viewer.status_code == 403

    # 3. Controller -> 200 OK
    resp_ctrl = client.post(
        "/api/simulation/run",
        json=sim_payload,
        headers={"Authorization": f"Bearer {controller_token}"},
    )
    assert resp_ctrl.status_code == 200
    res_data = resp_ctrl.json()["data"]
    assert "simulation_id" in res_data
    assert res_data["station_id"] == "MAITRI"
    assert res_data["scenario_type"] == "blizzard_survival"
    assert "predicted_min_temp_c" in res_data["metrics"]

    # 4. Admin -> 200 OK
    resp_admin = client.post(
        "/api/simulation/run",
        json=sim_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp_admin.status_code == 200


def test_recommendation_ingest_and_decision_lifecycle():
    """Verify recommendation lifecycle:
    1. Ingestion (PENDING)
    2. Read access by all roles
    3. Controller approves recommendation
    4. Controller modifies recommendation
    5. Controller rejects recommendation
    6. Viewer blocked from approve/modify/reject (403)
    7. Audit trail integrity
    """
    controller_token = _login("controller", "Controller@123")
    viewer_token = _login("viewer", "Viewer@123")

    # 1. Ingest recommendation
    rec_payload = {
        "station_id": 1,
        "type": "fuel_conservation",
        "severity": "high",
        "title": "Conserve fuel during blizzard condition",
        "reason": "Severe blizzard forecast exceeds 40 m/s; fuel resupply unreachable for 14 days",
        "recommended_action": "Reduce secondary generator load to 40% and disable non-essential heating",
        "confidence": 0.89,
    }
    resp_create = client.post("/api/recommendations", json=rec_payload)
    assert resp_create.status_code == 200
    rec_id = resp_create.json()["data"]["id"]
    assert resp_create.json()["data"]["status"] == "PENDING"
    assert resp_create.json()["data"]["confidence"] == 0.89

    # 2. Viewer reads recommendations -> Allowed (read-only)
    resp_list = client.get("/api/recommendations/MAITRI", headers={"Authorization": f"Bearer {viewer_token}"})
    assert resp_list.status_code == 200
    assert any(r["id"] == rec_id for r in resp_list.json()["data"])

    # 3. Viewer attempts to approve -> 403 Forbidden
    resp_view_approve = client.post(
        f"/api/recommendations/{rec_id}/approve",
        json={"notes": "Viewer trying to approve"},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp_view_approve.status_code == 403

    # 4. Controller approves recommendation -> 200 OK
    resp_approve = client.post(
        f"/api/recommendations/{rec_id}/approve",
        json={"notes": "Approved. Load shedding scheduled for 19:00 UTC."},
        headers={"Authorization": f"Bearer {controller_token}"},
    )
    assert resp_approve.status_code == 200
    assert resp_approve.json()["data"]["status"] == "APPROVED"
    assert resp_approve.json()["data"]["decided_by"] is not None

    # 5. Ingest another recommendation for modify test
    rec2_payload = {
        "station_id": 1,
        "type": "generator_maintenance",
        "severity": "medium",
        "title": "Replace Auxiliary Air Filter",
        "reason": "Vibration levels increased by 12% over 7 days",
        "recommended_action": "Shut down Generator 1 immediately and replace air filter",
        "confidence": 0.82,
    }
    rec2_id = client.post("/api/recommendations", json=rec2_payload).json()["data"]["id"]

    # Controller modifies recommendation
    modify_payload = {
        "modified_action": "Defer shutdown until 06:00 UTC; inspect during low-demand window.",
        "notes": "Operation cannot tolerate unplanned peak outage.",
    }
    resp_mod = client.post(
        f"/api/recommendations/{rec2_id}/modify",
        json=modify_payload,
        headers={"Authorization": f"Bearer {controller_token}"},
    )
    assert resp_mod.status_code == 200
    assert resp_mod.json()["data"]["status"] == "MODIFIED"
    assert resp_mod.json()["data"]["modified_action"] == modify_payload["modified_action"]

    # 6. Ingest 3rd recommendation for reject test
    rec3_payload = {
        "station_id": 1,
        "type": "drone_recon",
        "severity": "low",
        "title": "Deploy UAV for ice crevasse mapping",
        "reason": "Routine perimeter scan",
        "recommended_action": "Launch autonomous UAV flight along Sector 4",
        "confidence": 0.75,
    }
    rec3_id = client.post("/api/recommendations", json=rec3_payload).json()["data"]["id"]

    # Controller rejects recommendation
    reject_payload = {"reason": "Current wind speeds (32 m/s) exceed safe UAV operating envelope (15 m/s)."}
    resp_rej = client.post(
        f"/api/recommendations/{rec3_id}/reject",
        json=reject_payload,
        headers={"Authorization": f"Bearer {controller_token}"},
    )
    assert resp_rej.status_code == 200
    assert resp_rej.json()["data"]["status"] == "REJECTED"
    assert resp_rej.json()["data"]["decision_notes"] == reject_payload["reason"]

    # 7. Check audit records in DB
    db = SessionLocal()
    rec1 = db.query(Recommendation).filter(Recommendation.id == rec_id).first()
    assert rec1.status == RecommendationStatus.APPROVED
    assert len(rec1.audits) >= 2  # CREATED and APPROVE
    approve_audit = next((a for a in rec1.audits if a.action == "APPROVE"), None)
    assert approve_audit is not None
    assert approve_audit.new_status == "APPROVED"
    db.close()
