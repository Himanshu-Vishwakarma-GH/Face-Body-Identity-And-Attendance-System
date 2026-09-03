import time
import logging
from typing import Optional

from backend.models import CameraResponse, CameraStatus
from backend.database import db
from backend.services.camera_scanner import NETWORK_CAMERA_POOL

logger = logging.getLogger("ai_access.camera_linker")

def link_camera(camera_id: str, zone_override: Optional[str] = None) -> Optional[CameraResponse]:
    """Dynamically links an IP/ONVIF camera into the active security perimeter without restarting."""
    cid = camera_id.strip().upper()
    key = f"cam:{cid}"
    data = db.get_json(key)
    now = time.time()

    if not data:
        # Check discovered pool to auto-register and link
        discovered_info = next((c for c in NETWORK_CAMERA_POOL if c["camera_id"] == cid), None)
        if not discovered_info:
            discovered_info = {
                "name": f"Security Camera {cid}",
                "location": "Perimeter Entrance",
                "floor": "Ground",
                "zone": zone_override or "General Zone",
                "ip_address": "192.168.1.200",
                "rtsp_url": "0",
            }

        data = {
            "camera_id": cid,
            "name": discovered_info["name"],
            "location": discovered_info["location"],
            "floor": discovered_info["floor"],
            "zone": zone_override or discovered_info["zone"],
            "ip_address": discovered_info["ip_address"],
            "rtsp_url": discovered_info["rtsp_url"],
            "status": CameraStatus.ACTIVE.value,
            "is_linked": True,
            "linked_at": now,
            "last_heartbeat": now,
            "error_message": "",
            "fps": 30.0
        }
        db.set_json(key, data)
        logger.info("Auto-registered and linked discovered camera: %s", cid)
        return CameraResponse(**data)

    data["is_linked"] = True
    data["status"] = CameraStatus.ACTIVE.value
    data["linked_at"] = now
    data["last_heartbeat"] = now
    data["error_message"] = ""
    if zone_override:
        data["zone"] = zone_override

    db.set_json(key, data)
    logger.info("Camera %s linked and active.", cid)
    return CameraResponse(**data)

def unlink_camera(camera_id: str) -> Optional[CameraResponse]:
    """Dynamically unlinks an active camera (keeps record, pauses stream monitoring)."""
    cid = camera_id.strip().upper()
    key = f"cam:{cid}"
    data = db.get_json(key)
    if not data:
        return None

    data["is_linked"] = False
    data["status"] = CameraStatus.UNLINKED.value
    db.set_json(key, data)
    logger.info("Camera %s unlinked.", cid)
    return CameraResponse(**data)

def relink_camera(camera_id: str) -> Optional[CameraResponse]:
    """Re-links and clears error state for a previously errored or unlinked camera."""
    return link_camera(camera_id)
