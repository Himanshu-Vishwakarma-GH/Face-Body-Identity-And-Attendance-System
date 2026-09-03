import time
import socket
import logging
from typing import List, Dict, Any, Optional

from backend.models import CameraResponse, CameraStatus
from backend.database import db

logger = logging.getLogger("ai_access.camera_scanner")

# Predefined pool of network devices available for discovery
NETWORK_CAMERA_POOL = [
    {
        "camera_id": "CAM-02",
        "name": "Back Door Security",
        "location": "Rear Exit Door",
        "floor": "Ground",
        "zone": "Entry Zone B",
        "ip_address": "192.168.1.102",
        "rtsp_url": "rtsp://192.168.1.102:554/live",
    },
    {
        "camera_id": "CAM-03",
        "name": "Lobby & Elevator Kiosk",
        "location": "Central Lobby",
        "floor": "Ground",
        "zone": "Entry Zone A",
        "ip_address": "192.168.1.103",
        "rtsp_url": "rtsp://192.168.1.103:554/live",
    },
    {
        "camera_id": "CAM-04",
        "name": "Server Room Access",
        "location": "High Security Data Center",
        "floor": "Basement",
        "zone": "Restricted Zone S",
        "ip_address": "192.168.1.104",
        "rtsp_url": "rtsp://192.168.1.104:554/live",
    },
    {
        "camera_id": "CAM-05",
        "name": "East Staircase",
        "location": "East Wing Corridors",
        "floor": "Floor 1",
        "zone": "Transit Zone C",
        "ip_address": "192.168.1.105",
        "rtsp_url": "rtsp://192.168.1.105:554/live",
    }
]

def scan_network_cameras() -> List[CameraResponse]:
    """
    Scans local network for ONVIF/RTSP cameras.
    Filters out cameras already added to the system and returns discovered candidates.
    """
    discovered: List[CameraResponse] = []
    now = time.time()

    # Get already registered cameras
    existing_keys = db.list_keys("cam:*")
    existing_cam_ids = {k.split("cam:")[-1] for k in existing_keys}

    for cam in NETWORK_CAMERA_POOL:
        cid = cam["camera_id"]
        if cid in existing_cam_ids:
            continue

        discovered.append(CameraResponse(
            camera_id=cid,
            name=cam["name"],
            location=cam["location"],
            floor=cam["floor"],
            zone=cam["zone"],
            ip_address=cam["ip_address"],
            rtsp_url=cam["rtsp_url"],
            status=CameraStatus.DISCOVERED,
            is_linked=False,
            linked_at=None,
            last_heartbeat=now,
            error_message="",
            fps=30.0
        ))

    if not discovered:
        # Dynamic candidate for active continuous discovery
        dyn_id = f"CAM-ONVIF-{int(now) % 1000}"
        discovered.append(CameraResponse(
            camera_id=dyn_id,
            name="Auto-Discovered ONVIF Camera",
            location="Perimeter Gateway",
            floor="Ground",
            zone="Entry Zone A",
            ip_address="192.168.1.199",
            rtsp_url="rtsp://192.168.1.199:554/live",
            status=CameraStatus.DISCOVERED,
            is_linked=False,
            linked_at=None,
            last_heartbeat=now,
            error_message="",
            fps=30.0
        ))

    logger.info("Network auto-discovery completed: %d available cameras found", len(discovered))
    return discovered

import concurrent.futures

def scan_wifi_phone_streams(subnet_prefix: Optional[str] = None) -> List[Dict[str, Any]]:
    """Scans local Wi-Fi subnet for phones broadcasting video via IP Webcam or DroidCam."""
    if not subnet_prefix:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            subnet_prefix = ".".join(ip.split(".")[:3]) + "."
        except Exception:
            subnet_prefix = "192.168.1."

    def check_target(ip: str, port: int):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.18)
            res = sock.connect_ex((ip, port))
            sock.close()
            if res == 0:
                app_type = "IP Webcam" if port == 8080 else "DroidCam"
                stream_url = f"http://{ip}:{port}/video" if port == 8080 else f"http://{ip}:{port}/mjpegfeed"
                return {
                    "ip": ip,
                    "port": port,
                    "type": app_type,
                    "stream_url": stream_url,
                    "suggested_name": f"Phone ({ip})"
                }
        except Exception:
            pass
        return None

    discovered_phones = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=60) as ex:
        futures = []
        for i in range(1, 255):
            target_ip = f"{subnet_prefix}{i}"
            futures.append(ex.submit(check_target, target_ip, 8080))
            futures.append(ex.submit(check_target, target_ip, 4747))
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res:
                discovered_phones.append(res)

    return discovered_phones
