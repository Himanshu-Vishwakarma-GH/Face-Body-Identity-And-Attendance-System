import logging
import numpy as np
from typing import Optional, Dict, Any, List, Tuple
from backend.database import db
from backend.auth import decrypt_embedding
from backend.services.face_verify import face_engine

logger = logging.getLogger("ai_access.fetch_profile")

def fetch_employee_profile(employee_id: str) -> Optional[Dict[str, Any]]:
    """Fetches employee record from Redis and decrypts vector embeddings from AES-256-GCM."""
    key = f"emp:{employee_id}"
    record = db.get_json(key)
    if not record:
        logger.info("Employee record not found for ID: %s", employee_id)
        return None

    face_vector: Optional[np.ndarray] = None
    body_vector: Optional[np.ndarray] = None

    # Decrypt face embedding from AES-256-GCM
    if record.get("face_embedding_encrypted"):
        try:
            raw_face_bytes = decrypt_embedding(record["face_embedding_encrypted"])
            face_vector = np.frombuffer(raw_face_bytes, dtype=np.float32)
        except Exception as e:
            logger.error("Failed to decrypt face embedding for %s: %s", employee_id, e)

    # Decrypt body embedding from AES-256-GCM
    if record.get("body_embedding_encrypted"):
        try:
            raw_body_bytes = decrypt_embedding(record["body_embedding_encrypted"])
            body_vector = np.frombuffer(raw_body_bytes, dtype=np.float32)
        except Exception as e:
            logger.error("Failed to decrypt body embedding for %s: %s", employee_id, e)

    return {
        "employee_id": record.get("employee_id"),
        "name": record.get("name"),
        "department": record.get("department"),
        "access_level": record.get("access_level", 1),
        "is_active": record.get("is_active", True),
        "photo_path": record.get("photo_path"),
        "face_vector": face_vector,
        "body_vector": body_vector,
        "body_height": record.get("body_height"),
        "body_shoulder": record.get("body_shoulder"),
        "body_torso": record.get("body_torso"),
        "created_at": record.get("created_at"),
        "updated_at": record.get("updated_at")
    }

def find_employee_by_face(captured_face_vector: np.ndarray, threshold: float = 0.60) -> Tuple[Optional[Dict[str, Any]], float]:
    """1:N fallback identification when an employee forgets their card badge."""
    all_emp_keys = db.list_keys("emp:*")
    best_match: Optional[Dict[str, Any]] = None
    highest_similarity = 0.0

    for key in all_emp_keys:
        emp_id = key.split("emp:")[-1]
        profile = fetch_employee_profile(emp_id)
        if not profile or not profile.get("is_active"):
            continue

        stored_vec = profile.get("face_vector")
        if stored_vec is not None and len(stored_vec) > 0:
            sim = face_engine.cosine_similarity(stored_vec, captured_face_vector)
            if sim > highest_similarity:
                highest_similarity = sim
                best_match = profile

    if highest_similarity >= threshold and best_match is not None:
        return best_match, round(highest_similarity, 4)
    return None, round(highest_similarity, 4)
