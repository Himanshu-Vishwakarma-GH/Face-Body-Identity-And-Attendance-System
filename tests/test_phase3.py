import time
import pytest
import numpy as np
from fastapi.testclient import TestClient

from backend.app import app
from backend.config import settings
from backend.database import db
from backend.models import CameraCreate, CameraStatus, UserRole
from backend.services.camera_manager import (
    list_all_cameras, get_camera_by_id, add_camera,
    update_camera_details, remove_camera
)
from backend.services.camera_scanner import scan_network_cameras
from backend.services.camera_linker import link_camera, unlink_camera, relink_camera
from backend.services.camera_health import (
    monitor_and_report_health, record_camera_heartbeat,
    get_all_health_tickets, resolve_ticket
)
from backend.services.tailgate_detect import tailgate_detector
from backend.services.cross_camera import get_cross_camera_timeline, get_employee_movement_path
from backend.services.zone_manager import (
    list_all_zones, create_zone, delete_zone,
    assign_camera_to_zone, remove_camera_from_zone
)
from backend.services.attendance import calculate_department_attendance

client = TestClient(app)

def test_camera_crud():
    cam_data = CameraCreate(
        camera_id="CAM-TEST-99",
        name="Test Corridor",
        location="Corridor 9",
        floor="Floor 2",
        zone="Zone 9",
        ip_address="192.168.1.199",
        rtsp_url="rtsp://192.168.1.199:554/live"
    )
    created = add_camera(cam_data)
    assert created.camera_id == "CAM-TEST-99"
    assert created.status == CameraStatus.ACTIVE

    fetched = get_camera_by_id("CAM-TEST-99")
    assert fetched is not None
    assert fetched.name == "Test Corridor"

    updated = update_camera_details("CAM-TEST-99", {"name": "Test Corridor Renamed"})
    assert updated.name == "Test Corridor Renamed"

    deleted = remove_camera("CAM-TEST-99")
    assert deleted is True
    assert get_camera_by_id("CAM-TEST-99") is None

def test_dynamic_camera_linking_and_scanning():
    # 1. Network Auto-discovery
    discovered = scan_network_cameras()
    assert isinstance(discovered, list)
    assert len(discovered) > 0
    candidate_id = discovered[0].camera_id

    # 2. Dynamic Link
    linked = link_camera(candidate_id, zone_override="Dynamic Zone Test")
    assert linked is not None
    assert linked.is_linked is True
    assert linked.status == CameraStatus.ACTIVE

    # 3. Dynamic Unlink
    unlinked = unlink_camera(candidate_id)
    assert unlinked is not None
    assert unlinked.is_linked is False
    assert unlinked.status == CameraStatus.UNLINKED

    # 4. Relink
    relinked = relink_camera(candidate_id)
    assert relinked is not None
    assert relinked.is_linked is True
    assert relinked.status == CameraStatus.ACTIVE

def test_camera_auto_health_monitoring_and_ticketing():
    cam_id = "CAM-FAULTY-01"
    cam_data = CameraCreate(
        camera_id=cam_id,
        name="Side Gate Camera",
        location="Side Gate",
        floor="Ground",
        zone="Perimeter",
        ip_address="192.168.1.188",
        rtsp_url="0"
    )
    add_camera(cam_data)

    # Simulate camera heartbeat lost 5 minutes ago (300 seconds)
    stale_time = time.time() - 300
    cam_record = db.get_json(f"cam:{cam_id}")
    cam_record["last_heartbeat"] = stale_time
    cam_record["status"] = CameraStatus.ACTIVE.value
    db.set_json(f"cam:{cam_id}", cam_record)

    # Run auto-health monitor
    report = monitor_and_report_health()
    assert report["issues_flagged"] >= 1

    # Verify camera transitioned to INACTIVE
    updated_cam = get_camera_by_id(cam_id)
    assert updated_cam.status == CameraStatus.INACTIVE
    assert "Malfunction detected" in updated_cam.error_message

    # Verify maintenance ticket was automatically generated
    tickets = get_all_health_tickets(status_filter="OPEN")
    cam_tickets = [t for t in tickets if t.camera_id == cam_id]
    assert len(cam_tickets) >= 1
    ticket_id = cam_tickets[0].ticket_id

    # Resolve ticket
    resolved = resolve_ticket(ticket_id)
    assert resolved.status == "RESOLVED"
    # Camera state restored
    restored_cam = get_camera_by_id(cam_id)
    assert restored_cam.status == CameraStatus.ACTIVE

    # Clean up
    remove_camera(cam_id)

def test_tailgating_sliding_window_logic():
    cam_id = "CAM-TG-01"
    # Swipe once
    swipes = tailgate_detector.record_card_swipe(cam_id)
    assert swipes >= 1

    # Blank frame (0 persons detected) -> No tailgate
    blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    is_tg, p_count, alert = tailgate_detector.check_tailgate(cam_id, blank_frame, card_swipes=1)
    assert is_tg is False
    assert p_count == 0

def test_cross_camera_timeline_and_movement():
    now = time.time()
    emp_id = "EMP-CROSS-1"

    # Seed 2 sequential access logs across 2 cameras
    db.set_json("log:cross-log-1", {
        "log_id": "cross-log-1",
        "employee_id": emp_id,
        "employee_name": "Marcus Vance",
        "department": "Engineering",
        "camera_id": "CAM-01",
        "zone": "Front Door",
        "timestamp": now - 100,
        "decision": "GRANTED",
        "tailgate_detected": False
    })
    db.set_json("log:cross-log-2", {
        "log_id": "cross-log-2",
        "employee_id": emp_id,
        "employee_name": "Marcus Vance",
        "department": "Engineering",
        "camera_id": "CAM-03",
        "zone": "Elevator Lobby",
        "timestamp": now - 10,
        "decision": "GRANTED",
        "tailgate_detected": False
    })

    timeline = get_cross_camera_timeline(employee_id=emp_id)
    assert len(timeline) >= 2
    assert timeline[0]["camera_id"] == "CAM-03" # Most recent first

    path = get_employee_movement_path(emp_id)
    assert path["total_checkpoints_today"] >= 2
    assert path["path"][0]["camera"] == "CAM-01" # Chronological order

def test_zone_management():
    z = create_zone(name="Executive Floor", description="Restricted executive offices")
    assert z.name == "Executive Floor"

    ok = assign_camera_to_zone("CAM-01", z.zone_id)
    assert ok is True

    rem = remove_camera_from_zone("CAM-01", z.zone_id)
    assert rem is True

    deleted = delete_zone(z.zone_id)
    assert deleted is True

def test_phase3_api_endpoints():
    # Login
    login_resp = client.post("/api/auth/login", json={
        "username": settings.DEFAULT_ADMIN_USERNAME,
        "password": settings.DEFAULT_ADMIN_PASSWORD
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Camera list & scan API
    cams_resp = client.get("/api/admin/cameras", headers=headers)
    assert cams_resp.status_code == 200

    scan_resp = client.post("/api/admin/cameras/scan", headers=headers)
    assert scan_resp.status_code == 200

    # 2. Camera health API
    health_resp = client.get("/api/admin/cameras/health", headers=headers)
    assert health_resp.status_code == 200
    assert "cameras_checked" in health_resp.json()

    # 3. Cross-camera timeline API
    tl_resp = client.get("/api/admin/timeline", headers=headers)
    assert tl_resp.status_code == 200

    # 4. Zones API
    zones_resp = client.get("/api/admin/zones", headers=headers)
    assert zones_resp.status_code == 200
