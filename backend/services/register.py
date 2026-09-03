import os
import time
import logging
import cv2
import numpy as np
from typing import Optional, Dict, Any
from pathlib import Path

from backend.config import settings
from backend.models import EmployeeCreate, EmployeeResponse
from backend.database import db
from backend.auth import encrypt_embedding
from backend.services.capture import decode_base64_image
from backend.services.face_verify import face_engine
from backend.services.body_verify import body_engine

logger = logging.getLogger("ai_access.register")

def register_employee(
    emp_data: EmployeeCreate,
    face_image_bytes: Optional[bytes] = None,
    body_image_bytes: Optional[bytes] = None
) -> EmployeeResponse:
    """Enrolls an employee, extracts biometric embeddings, encrypts at rest (AES-256), and saves to Redis."""
    emp_id = emp_data.employee_id.strip().upper()
    now = time.time()

    # 1. Resolve Face Image
    face_img: Optional[np.ndarray] = None
    if face_image_bytes:
        nparr = np.frombuffer(face_image_bytes, np.uint8)
        face_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    elif emp_data.face_image_base64:
        face_img = decode_base64_image(emp_data.face_image_base64)

    # 2. Resolve Body Image (defaults to face image if separate body image not supplied)
    body_img: Optional[np.ndarray] = None
    if body_image_bytes:
        nparr = np.frombuffer(body_image_bytes, np.uint8)
        body_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    elif emp_data.body_image_base64:
        body_img = decode_base64_image(emp_data.body_image_base64)
    else:
        body_img = face_img

    # 3. Save Face Photo to Disk
    photo_path = None
    if face_img is not None:
        photo_filename = f"{emp_id}.jpg"
        abs_photo_path = os.path.join(settings.FACES_DIR, photo_filename)
        cv2.imwrite(abs_photo_path, face_img)
        photo_path = f"/static/faces/{photo_filename}"

    # 4. Extract and Encrypt Face Embedding (512-dim)
    face_embedding_encrypted = None
    has_face_profile = False
    if face_img is not None:
        face_vec = face_engine.extract_embedding(face_img)
        if face_vec is not None:
            raw_face_bytes = face_vec.tobytes()
            face_embedding_encrypted = encrypt_embedding(raw_face_bytes)
            has_face_profile = True
            logger.info("Successfully extracted 512-dim face embedding for %s", emp_id)

    # 5. Extract and Encrypt Body Embedding (256-dim)
    body_embedding_encrypted = None
    has_body_profile = False
    body_height = None
    body_shoulder = None
    body_torso = None
    if body_img is not None:
        body_features = body_engine.extract_body_features(body_img)
        if body_features is not None:
            body_vec = body_features["embedding"]
            raw_body_bytes = body_vec.tobytes()
            body_embedding_encrypted = encrypt_embedding(raw_body_bytes)
            has_body_profile = True
            body_height = body_features["body_height"]
            body_shoulder = body_features["body_shoulder"]
            body_torso = body_features["body_torso"]
            logger.info("Successfully extracted body features for %s", emp_id)

    # 6. Save JSON Record to Redis
    employee_record = {
        "employee_id": emp_id,
        "name": emp_data.name.strip(),
        "department": emp_data.department.strip(),
        "access_level": emp_data.access_level,
        "is_active": emp_data.is_active,
        "photo_path": photo_path,
        "face_embedding_encrypted": face_embedding_encrypted,
        "body_embedding_encrypted": body_embedding_encrypted,
        "body_height": body_height,
        "body_shoulder": body_shoulder,
        "body_torso": body_torso,
        "created_at": now,
        "updated_at": now
    }

    db.set_json(f"emp:{emp_id}", employee_record)
    logger.info("Saved employee record to Redis: emp:%s", emp_id)

    return EmployeeResponse(
        employee_id=emp_id,
        name=employee_record["name"],
        department=employee_record["department"],
        access_level=employee_record["access_level"],
        is_active=employee_record["is_active"],
        has_face_profile=has_face_profile,
        has_body_profile=has_body_profile,
        photo_path=photo_path,
        body_height=body_height,
        body_shoulder=body_shoulder,
        body_torso=body_torso,
        created_at=now,
        updated_at=now
    )
