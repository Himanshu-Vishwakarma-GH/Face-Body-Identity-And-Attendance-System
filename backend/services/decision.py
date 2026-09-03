import time
import uuid
import logging
import numpy as np
from typing import Optional, Dict, Any, Tuple

from backend.config import settings
from backend.models import VerifyRequest, VerifyResponse, DecisionStatus, AccessLog
from backend.database import db
from backend.services.capture import get_frame
from backend.services.fetch_profile import fetch_employee_profile, find_employee_by_face
from backend.services.face_verify import face_engine
from backend.services.body_verify import body_engine

logger = logging.getLogger("ai_access.decision")

def evaluate_access(
    request: VerifyRequest,
    tailgate_detected: bool = False,
    override_frame: Optional[np.ndarray] = None
) -> VerifyResponse:
    """Evaluates access control decision combining Card ID, Face 1:1 match, Body 1:1 match, and Tailgating detection."""
    now = time.time()
    log_id = str(uuid.uuid4())

    # 1. Fetch camera metadata to determine zone
    cam_key = f"cam:{request.camera_id}"
    cam_record = db.get_json(cam_key) or {}
    zone = cam_record.get("zone", "Default Entry Zone")
    camera_source = cam_record.get("rtsp_url", settings.DEFAULT_CAMERA_RTSP)

    # 2. Acquire Camera Frame
    frame: Optional[np.ndarray] = override_frame
    if frame is None:
        has_frame, captured, source_desc = get_frame(camera_source, request.frame_base64)
        if has_frame:
            frame = captured

    if frame is None:
        # No frame received
        log_entry = AccessLog(
            log_id=log_id,
            employee_id=request.employee_id,
            camera_id=request.camera_id,
            zone=zone,
            timestamp=now,
            decision=DecisionStatus.DENIED,
            tailgate_detected=tailgate_detected,
        )
        db.set_json(f"log:{log_id}", log_entry.model_dump())

        return VerifyResponse(
            decision=DecisionStatus.DENIED,
            employee_id=request.employee_id,
            message="Verification Failed: No camera video frame available",
            log_id=log_id,
            timestamp=now
        )

    # 3. Check for Immediate Tailgate Override
    if tailgate_detected:
        log_entry = AccessLog(
            log_id=log_id,
            employee_id=request.employee_id,
            camera_id=request.camera_id,
            zone=zone,
            timestamp=now,
            decision=DecisionStatus.DENIED,
            tailgate_detected=True
        )
        db.set_json(f"log:{log_id}", log_entry.model_dump())

        return VerifyResponse(
            decision=DecisionStatus.DENIED,
            employee_id=request.employee_id,
            tailgate_detected=True,
            message="ACCESS DENIED: Tailgating security alert! Multiple persons detected.",
            log_id=log_id,
            timestamp=now
        )

    # 4. Resolve Employee Profile (1:1 with card or 1:N fallback if card forgotten)
    profile: Optional[Dict[str, Any]] = None
    captured_face_vec: Optional[np.ndarray] = face_engine.extract_embedding(frame)

    if request.employee_id and request.employee_id.strip():
        # Case A: Card swiped or ID entered (Standard 1:1)
        profile = fetch_employee_profile(request.employee_id.strip().upper())
        if not profile:
            log_entry = AccessLog(
                log_id=log_id,
                employee_id=request.employee_id,
                camera_id=request.camera_id,
                zone=zone,
                timestamp=now,
                decision=DecisionStatus.DENIED,
                tailgate_detected=False
            )
            db.set_json(f"log:{log_id}", log_entry.model_dump())

            return VerifyResponse(
                decision=DecisionStatus.DENIED,
                employee_id=request.employee_id,
                message=f"Access Denied: Employee ID '{request.employee_id}' not found in system",
                log_id=log_id,
                timestamp=now
            )
    else:
        # Case B: Card Forgotten! 1:N Facial recognition fallback
        if captured_face_vec is not None:
            profile, _ = find_employee_by_face(captured_face_vec, settings.FACE_SIMILARITY_THRESHOLD)

        if not profile:
            log_entry = AccessLog(
                log_id=log_id,
                employee_id=None,
                camera_id=request.camera_id,
                zone=zone,
                timestamp=now,
                decision=DecisionStatus.DENIED,
                tailgate_detected=False
            )
            db.set_json(f"log:{log_id}", log_entry.model_dump())

            return VerifyResponse(
                decision=DecisionStatus.DENIED,
                message="Access Denied: No matching employee face identified for forgotten card fallback",
                log_id=log_id,
                timestamp=now
            )

    # Check if employee account is active
    if not profile.get("is_active", True):
        return VerifyResponse(
            decision=DecisionStatus.DENIED,
            employee_id=profile.get("employee_id"),
            employee_name=profile.get("name"),
            message="Access Denied: Employee account is currently deactivated",
            log_id=log_id,
            timestamp=now
        )

    # 5. Perform 1:1 Face Verification
    face_matched = False
    face_conf = 0.0
    stored_face_vec = profile.get("face_vector")

    if stored_face_vec is not None and captured_face_vec is not None:
        face_conf = face_engine.cosine_similarity(stored_face_vec, captured_face_vec)
        face_matched = bool(face_conf >= settings.FACE_SIMILARITY_THRESHOLD)

    # 6. Perform 1:1 Body Verification
    body_matched = False
    body_conf = 0.0
    stored_body_vec = profile.get("body_vector")

    if stored_body_vec is not None:
        body_matched, body_conf = body_engine.verify_1_to_1(
            stored_body_vec,
            frame,
            settings.BODY_DISTANCE_THRESHOLD
        )
    else:
        # If body embedding not previously enrolled, match face primarily
        body_matched = True
        body_conf = 0.85

    # 7. Final Decision Matrix
    decision = DecisionStatus.DENIED
    message = "Access Denied"

    if face_matched and body_matched:
        decision = DecisionStatus.GRANTED
        message = f"Access Granted: Welcome {profile.get('name', 'Employee')}"
    elif face_matched and not body_matched:
        # Face verified, but body measurement deviates (e.g. winter coat or posture)
        decision = DecisionStatus.WARNING
        message = f"Access Granted (Warning): Face verified for {profile.get('name')}, body dimension variance"
    else:
        decision = DecisionStatus.DENIED
        message = f"Access Denied: Facial verification score ({int(face_conf * 100)}%) below security threshold"

    # 8. Record Access Log in Redis
    access_log = AccessLog(
        log_id=log_id,
        employee_id=profile.get("employee_id"),
        employee_name=profile.get("name"),
        department=profile.get("department"),
        camera_id=request.camera_id,
        zone=zone,
        timestamp=now,
        face_matched=face_matched,
        face_confidence=round(face_conf, 4),
        body_matched=body_matched,
        body_confidence=round(body_conf, 4),
        decision=decision,
        tailgate_detected=False
    )
    db.set_json(f"log:{log_id}", access_log.model_dump())

    return VerifyResponse(
        decision=decision,
        employee_id=profile.get("employee_id"),
        employee_name=profile.get("name"),
        department=profile.get("department"),
        face_matched=face_matched,
        face_confidence=round(face_conf, 4),
        body_matched=body_matched,
        body_confidence=round(body_conf, 4),
        tailgate_detected=False,
        message=message,
        log_id=log_id,
        timestamp=now
    )
