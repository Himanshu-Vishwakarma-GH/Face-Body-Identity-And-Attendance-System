import time
import logging
from typing import List, Optional, Dict, Any

from backend.models import AccessLog
from backend.database import db

logger = logging.getLogger("ai_access.cross_camera")

def get_cross_camera_timeline(
    employee_id: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Builds a unified spatial timeline of person detections and entries across multiple cameras.
    Enables security operators to trace movement paths across zones.
    """
    # Pre-cache camera metadata in memory
    cams = db.get_all_by_pattern("cam:*")
    cam_map = {c.get("camera_id"): c for c in cams if c}

    log_records = db.get_all_by_pattern("log:*")
    timeline: List[Dict[str, Any]] = []

    for entry in log_records:
        if not entry:
            continue

        emp_id = entry.get("employee_id")
        if employee_id and emp_id and emp_id.upper() != employee_id.strip().upper():
            continue

        cid = entry.get("camera_id")
        cam_info = cam_map.get(cid, {})

        timeline.append({
            "log_id": entry.get("log_id"),
            "timestamp": entry.get("timestamp"),
            "formatted_time": time.strftime("%H:%M:%S", time.localtime(entry.get("timestamp", time.time()))),
            "date": time.strftime("%Y-%m-%d", time.localtime(entry.get("timestamp", time.time()))),
            "employee_id": emp_id or "UNIDENTIFIED",
            "employee_name": entry.get("employee_name", "Unknown Person"),
            "department": entry.get("department", "N/A"),
            "camera_id": cid,
            "camera_name": cam_info.get("name", cid),
            "location": cam_info.get("location", "Unknown Location"),
            "zone": entry.get("zone", cam_info.get("zone", "General Zone")),
            "decision": entry.get("decision"),
            "face_confidence": entry.get("face_confidence", 0.0),
            "body_confidence": entry.get("body_confidence", 0.0),
            "tailgate_detected": entry.get("tailgate_detected", False)
        })

    # Sort chronologically descending
    timeline.sort(key=lambda t: t["timestamp"], reverse=True)
    return timeline[:limit]

def get_employee_movement_path(employee_id: str) -> Dict[str, Any]:
    """Extracts ordered spatial journey path of a specific employee across security checkpoints."""
    events = get_cross_camera_timeline(employee_id=employee_id, limit=20)
    # Order chronologically ascending for path view
    events.reverse()

    checkpoints = []
    for idx, ev in enumerate(events):
        checkpoints.append({
            "step": idx + 1,
            "time": ev["formatted_time"],
            "camera": ev["camera_id"],
            "camera_name": ev["camera_name"],
            "zone": ev["zone"],
            "decision": ev["decision"]
        })

    return {
        "employee_id": employee_id,
        "total_checkpoints_today": len(checkpoints),
        "path": checkpoints
    }
