import pytest
from backend.config import settings
from backend.models import (
    UserRole,
    EmployeeCreate,
    VerifyRequest,
    DecisionStatus,
    CameraResponse,
    CameraStatus
)
from backend.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    encrypt_embedding,
    decrypt_embedding
)
from backend.database import db

def test_config_paths():
    assert settings.PROJECT_NAME != ""
    assert settings.API_V1_PREFIX == "/api"
    assert len(settings.get_aes_key_bytes()) == 32

def test_password_hashing():
    pwd = "HackathonAdmin2026!"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_jwt_token():
    payload = {"sub": "admin", "role": "admin"}
    token = create_access_token(payload)
    decoded = decode_access_token(token)
    assert decoded["sub"] == "admin"
    assert decoded["role"] == "admin"
    assert "exp" in decoded

def test_aes256_embedding_encryption():
    raw_embedding = b"\xde\xad\xbe\xef" * 64  # 256 bytes
    encrypted = encrypt_embedding(raw_embedding)
    assert isinstance(encrypted, str)
    assert encrypted != raw_embedding.decode("latin1", errors="ignore")

    decrypted = decrypt_embedding(encrypted)
    assert decrypted == raw_embedding

def test_database_operations():
    db.connect()
    db.seed_initial_data()
    health = db.health_check()
    assert "redis_connected" in health
    assert "mode" in health

    test_key = "test:unit_item"
    db.set_json(test_key, {"status": "ok", "value": 42})
    res = db.get_json(test_key)
    assert res is not None
    assert res["status"] == "ok"
    assert res["value"] == 42
    db.delete_key(test_key)
    assert db.get_json(test_key) is None
