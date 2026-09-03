import pytest
import numpy as np
from fastapi.testclient import TestClient

from backend.app import app
from backend.config import settings
from backend.database import db
from backend.auth import encrypt_embedding, decrypt_embedding
from backend.models import EmployeeCreate, VerifyRequest, DecisionStatus
from backend.services.register import register_employee
from backend.services.fetch_profile import fetch_employee_profile
from backend.services.face_verify import face_engine
from backend.services.decision import evaluate_access

client = TestClient(app)

def test_cosine_similarity_computation():
    # Same vector -> similarity 1.0
    v1 = np.random.randn(512).astype(np.float32)
    v1 = v1 / np.linalg.norm(v1)
    sim = face_engine.cosine_similarity(v1, v1)
    assert pytest.approx(sim, 0.001) == 1.0

    # Orthogonal vectors -> similarity ~0.0
    v2 = np.zeros(512, dtype=np.float32)
    v2[0] = 1.0
    v3 = np.zeros(512, dtype=np.float32)
    v3[1] = 1.0
    sim_ortho = face_engine.cosine_similarity(v2, v3)
    assert sim_ortho < 0.1

def test_employee_registration_and_decryption():
    emp_id = "TESTEMP99"
    emp_create = EmployeeCreate(
        employee_id=emp_id,
        name="Test Engineer",
        department="Engineering",
        access_level=2,
        is_active=True
    )
    res = register_employee(emp_create)
    assert res.employee_id == emp_id
    assert res.name == "Test Engineer"

    # Manually store synthetic face & body embeddings encrypted in Redis to test AES-256 roundtrip
    stored_face = np.random.randn(512).astype(np.float32)
    stored_face = stored_face / np.linalg.norm(stored_face)
    enc_face = encrypt_embedding(stored_face.tobytes())

    stored_body = np.random.randn(256).astype(np.float32)
    stored_body = stored_body / np.linalg.norm(stored_body)
    enc_body = encrypt_embedding(stored_body.tobytes())

    record = db.get_json(f"emp:{emp_id}")
    record["face_embedding_encrypted"] = enc_face
    record["body_embedding_encrypted"] = enc_body
    db.set_json(f"emp:{emp_id}", record)

    # Fetch profile and verify decrypted vectors match original
    profile = fetch_employee_profile(emp_id)
    assert profile is not None
    assert profile["employee_id"] == emp_id
    np.testing.assert_allclose(profile["face_vector"], stored_face, rtol=1e-5)
    np.testing.assert_allclose(profile["body_vector"], stored_body, rtol=1e-5)

def test_access_decision_matrix():
    emp_id = "TESTEMP88"
    db.set_json(f"emp:{emp_id}", {
        "employee_id": emp_id,
        "name": "Alice Security",
        "department": "Security",
        "access_level": 3,
        "is_active": True,
        "face_embedding_encrypted": None,
        "body_embedding_encrypted": None
    })

    # 1. Unknown employee ID
    req_unknown = VerifyRequest(employee_id="NON_EXISTENT", camera_id="CAM-01")
    res_unknown = evaluate_access(req_unknown)
    assert res_unknown.decision == DecisionStatus.DENIED

    # 2. Tailgating detected override
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    req_tailgate = VerifyRequest(employee_id=emp_id, camera_id="CAM-01")
    res_tailgate = evaluate_access(req_tailgate, tailgate_detected=True, override_frame=dummy_frame)
    assert res_tailgate.decision == DecisionStatus.DENIED
    assert res_tailgate.tailgate_detected is True
    assert "Tailgating" in res_tailgate.message

def test_api_endpoints():
    # 1. Health check
    health_resp = client.get("/api/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["status"] == "healthy"

    # 2. Login as admin
    login_resp = client.post("/api/auth/login", json={
        "username": settings.DEFAULT_ADMIN_USERNAME,
        "password": settings.DEFAULT_ADMIN_PASSWORD
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. List employees with auth header
    emp_resp = client.get("/api/admin/employees", headers=headers)
    assert emp_resp.status_code == 200
    assert isinstance(emp_resp.json(), list)

    # 4. Get Dashboard Summary
    dash_resp = client.get("/api/admin/dashboard", headers=headers)
    assert dash_resp.status_code == 200
    dash_data = dash_resp.json()
    assert "total_employees" in dash_data
    assert "active_cameras" in dash_data

    # 5. Verify endpoint without auth (public camera kiosk)
    verify_resp = client.post("/api/verify", json={
        "employee_id": "TEST_CARD_01",
        "camera_id": "CAM-01"
    })
    assert verify_resp.status_code == 200
    assert verify_resp.json()["decision"] == "DENIED"
