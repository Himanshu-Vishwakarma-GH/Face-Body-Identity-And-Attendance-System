import time
import logging
from typing import List, Optional, Dict, Any

from backend.models import CameraBase, CameraCreate, CameraResponse, CameraStatus
from backend.database import db

logger = logging.getLogger("ai_access.camera_manager")

def list_all_cameras(linked_only: bool = False) -> List[CameraResponse]:
    """Retrieves all registered cameras from Redis in a single batch query."""
    records = db.get_all_by_pattern("cam:*")
    cameras: List[CameraResponse] = []

    for data in records:
        if not data:
            continue
        if linked_only and not data.get("is_linked", True):
            continue

        try:
            cameras.append(CameraResponse(**data))
        except Exception as e:
            logger.error("Failed to parse camera record: %s", e)

    return sorted(cameras, key=lambda c: c.camera_id)

def get_camera_by_id(camera_id: str) -> Optional[CameraResponse]:
    """Fetches a single camera by camera_id."""
    data = db.get_json(f"cam:{camera_id}")
    if not data:
        return None
    try:
        return CameraResponse(**data)
    except Exception:
        return None

def add_camera(camera_data: CameraCreate) -> CameraResponse:
    """Registers a new camera."""
    cam_id = camera_data.camera_id.strip().upper()
    key = f"cam:{cam_id}"
    now = time.time()

    record = {
        "camera_id": cam_id,
        "name": camera_data.name.strip(),
        "location": camera_data.location.strip(),
        "floor": camera_data.floor.strip(),
        "zone": camera_data.zone.strip(),
        "ip_address": camera_data.ip_address,
        "rtsp_url": camera_data.rtsp_url,
        "status": CameraStatus.ACTIVE.value,
        "is_linked": True,
        "linked_at": now,
        "last_heartbeat": now,
        "error_message": "",
        "fps": 30.0
    }

    db.set_json(key, record)
    logger.info("Added new camera: %s (%s)", cam_id, camera_data.name)
    return CameraResponse(**record)

def update_camera_details(camera_id: str, updates: Dict[str, Any]) -> Optional[CameraResponse]:
    """Updates camera metadata."""
    key = f"cam:{camera_id}"
    data = db.get_json(key)
    if not data:
        return None

    for k, v in updates.items():
        if v is not None and k in data:
            data[k] = v

    db.set_json(key, data)
    return CameraResponse(**data)

def remove_camera(camera_id: str) -> bool:
    """Deletes a camera record from Redis."""
    key = f"cam:{camera_id}"
    return db.delete_key(key)
