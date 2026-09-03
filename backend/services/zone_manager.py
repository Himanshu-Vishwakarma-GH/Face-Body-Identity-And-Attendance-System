import uuid
import logging
from typing import List, Optional, Dict, Any

from backend.models import Zone
from backend.database import db

logger = logging.getLogger("ai_access.zone_manager")

def list_all_zones() -> List[Zone]:
    """Retrieves all registered security zones."""
    keys = db.list_keys("zone:*")
    zones: List[Zone] = []

    for k in keys:
        data = db.get_json(k)
        if data:
            try:
                zones.append(Zone(**data))
            except Exception:
                pass

    return sorted(zones, key=lambda z: z.name)

def get_zone_by_id(zone_id: str) -> Optional[Zone]:
    data = db.get_json(f"zone:{zone_id}")
    return Zone(**data) if data else None

def create_zone(name: str, description: str = "", camera_ids: Optional[List[str]] = None) -> Zone:
    """Creates a new security zone."""
    zid = f"zone-{str(uuid.uuid4())[:8]}"
    zone = Zone(
        zone_id=zid,
        name=name.strip(),
        description=description.strip(),
        camera_ids=camera_ids or []
    )
    db.set_json(f"zone:{zid}", zone.model_dump())
    logger.info("Created new zone: %s (%s)", zid, name)
    return zone

def delete_zone(zone_id: str) -> bool:
    """Deletes a zone record."""
    return db.delete_key(f"zone:{zone_id}")

def assign_camera_to_zone(camera_id: str, zone_id: str) -> bool:
    """Assigns camera to a zone and updates both camera and zone records."""
    z_key = f"zone:{zone_id}"
    zone_data = db.get_json(z_key)
    if not zone_data:
        return False

    c_key = f"cam:{camera_id}"
    cam_data = db.get_json(c_key)
    if not cam_data:
        return False

    if camera_id not in zone_data.get("camera_ids", []):
        zone_data["camera_ids"].append(camera_id)
        db.set_json(z_key, zone_data)

    cam_data["zone"] = zone_data["name"]
    db.set_json(c_key, cam_data)
    logger.info("Assigned camera %s to zone %s", camera_id, zone_data["name"])
    return True

def remove_camera_from_zone(camera_id: str, zone_id: str) -> bool:
    """Removes camera from a zone."""
    z_key = f"zone:{zone_id}"
    zone_data = db.get_json(z_key)
    if not zone_data:
        return False

    if camera_id in zone_data.get("camera_ids", []):
        zone_data["camera_ids"].remove(camera_id)
        db.set_json(z_key, zone_data)
        logger.info("Removed camera %s from zone %s", camera_id, zone_data["name"])
        return True
    return False
