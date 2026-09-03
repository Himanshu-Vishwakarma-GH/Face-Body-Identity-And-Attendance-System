import pytest
from fastapi.testclient import TestClient
from backend.app import app
from backend.config import settings

client = TestClient(app)

def test_camera_screen_endpoint():
    res = client.get("/camera")
    assert res.status_code == 200
    assert "ACCESS CONTROL SYSTEM" in res.text or "Checkpoint" in res.text

def test_admin_portal_endpoint():
    res = client.get("/admin")
    assert res.status_code == 200
    assert "AI Access" in res.text or "root" in res.text

import time
from backend.database import db

def test_end_to_end_verification_flow():
    # 1. Login
    login_res = client.post("/api/auth/login", json={
        "username": settings.DEFAULT_ADMIN_USERNAME,
        "password": settings.DEFAULT_ADMIN_PASSWORD
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Register new employee with unique ID for idempotency
    emp_id = f"EMP-E2E-{int(time.time())}"
    emp_res = client.post("/api/admin/register", json={
        "employee_id": emp_id,
        "name": "Jordan Cole",
        "department": "Engineering",
        "access_level": 2,
        "is_active": True
    }, headers=headers)
    assert emp_res.status_code == 200
    assert emp_res.json()["employee_id"] == emp_id

    # 3. Verify access via card swipe endpoint
    verify_res = client.post("/api/verify", json={
        "employee_id": emp_id,
        "camera_id": "CAM-01"
    })
    assert verify_res.status_code == 200
    assert verify_res.json()["decision"] == "DENIED"
    msg = verify_res.json()["message"].lower()
    assert "access denied" in msg or "verification failed" in msg

    # 4. Check that access log was created and shows on Dashboard
    dash_res = client.get("/api/admin/dashboard", headers=headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert dash_data["total_employees"] >= 1

    # Cleanup
    db.delete_key(f"emp:{emp_id}")
