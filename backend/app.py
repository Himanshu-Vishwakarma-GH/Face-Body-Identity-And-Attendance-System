import time
import os
import logging
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse, Response
import socket
from backend.services.capture import (
    generate_camera_frames, probe_camera_source, get_frame,
    encode_image_to_base64, detect_usb_cameras, update_phone_frame
)

from backend.config import settings, BASE_DIR
from backend.models import (
    LoginRequest, TokenResponse, User, UserRole,
    EmployeeCreate, EmployeeUpdate, EmployeeResponse,
    VerifyRequest, VerifyResponse,
    AccessLog, DashboardSummary, DepartmentAttendance,
    CameraBase, CameraCreate, CameraResponse, CameraStatus,
    Zone, CameraHealthTicket, TailgateAlert
)
from backend.database import db
from backend.auth import (
    verify_password, create_access_token,
    get_current_user, require_roles
)
from backend.services.register import register_employee
from backend.services.fetch_profile import fetch_employee_profile
from backend.services.decision import evaluate_access
from backend.services.face_verify import face_engine
from backend.services.body_verify import body_engine
from backend.services.tailgate_detect import tailgate_detector
from backend.services.camera_manager import (
    list_all_cameras, get_camera_by_id, add_camera,
    update_camera_details, remove_camera
)
from backend.services.camera_scanner import scan_network_cameras, scan_wifi_phone_streams
from backend.services.camera_linker import link_camera, unlink_camera, relink_camera
from backend.services.camera_health import (
    monitor_and_report_health, record_camera_heartbeat,
    get_all_health_tickets, resolve_ticket
)
from backend.services.cross_camera import get_cross_camera_timeline, get_employee_movement_path
from backend.services.zone_manager import (
    list_all_zones, get_zone_by_id, create_zone, delete_zone,
    assign_camera_to_zone, remove_camera_from_zone
)
from backend.services.attendance import calculate_department_attendance

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ai_access.app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing system components...")
    db.connect()
    db.seed_initial_data()
    logger.info("Application startup complete.")
    yield
    # Shutdown
    logger.info("Application shutting down...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Intelligent Office Access Control Powered by Face Recognition, Body Dimension Analysis & Cross-Camera Linking",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve stored photos statically
os.makedirs(settings.FACES_DIR, exist_ok=True)
app.mount("/static/faces", StaticFiles(directory=settings.FACES_DIR), name="faces")

# Mount Camera Screen
camera_dir = str(BASE_DIR / "camera_screen")
app.mount("/camera-ui", StaticFiles(directory=camera_dir, html=True), name="camera_ui")

@app.get("/camera", tags=["System"])
def camera_screen_redirect():
    return FileResponse(os.path.join(camera_dir, "index.html"))

@app.get("/phone-cam", tags=["System"])
def phone_camera_broadcaster():
    """Serves mobile phone camera transmitter page for same-network streaming."""
    return FileResponse(os.path.join(camera_dir, "phone_cam.html"))

@app.post("/api/camera/phone/{camera_id}/push-frame", tags=["Camera Management"])
async def push_phone_frame(camera_id: str, request: Request):
    """Receives live video frame bytes pushed from a phone on the local Wi-Fi network."""
    body_bytes = await request.body()
    if body_bytes:
        update_phone_frame(camera_id, body_bytes)
    return {"status": "ok"}

@app.get("/api/admin/cameras/detect-usb", tags=["Camera Management"])
def detect_usb_devices(current_user: User = Depends(get_current_user)):
    """Automatically scans and enumerates connected USB and integrated webcams."""
    return detect_usb_cameras()

@app.get("/api/admin/system/network-info", tags=["System"])
def get_network_info():
    """Returns local Wi-Fi IP address for 1-click mobile phone pairing on the same network."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = "127.0.0.1"

    return {
        "local_ip": ip,
        "phone_cam_url": f"http://{ip}:8000/phone-cam",
        "port": 8000,
        "subnet": ".".join(ip.split(".")[:3]) + ".0/24"
    }

# Mount Admin Portal
admin_dist_dir = str(BASE_DIR / "admin_portal" / "dist")
if os.path.isdir(admin_dist_dir):
    admin_assets_dir = os.path.join(admin_dist_dir, "assets")
    if os.path.isdir(admin_assets_dir):
        app.mount("/assets", StaticFiles(directory=admin_assets_dir), name="admin_assets")

    @app.get("/admin", tags=["System"])
    @app.get("/admin/{path:path}", tags=["System"])
    def serve_admin_portal(path: str = ""):
        return FileResponse(os.path.join(admin_dist_dir, "index.html"))

# --- System Health ---

@app.get("/", tags=["System"])
def root():
    return {
        "project": settings.PROJECT_NAME,
        "status": "online",
        "docs_url": "/docs",
        "api_prefix": settings.API_V1_PREFIX
    }

@app.get("/api/health", tags=["System"])
def health():
    return {
        "status": "healthy",
        "database": db.health_check(),
        "timestamp": time.time()
    }

# --- Authentication ---

@app.post("/api/auth/login", response_model=TokenResponse, tags=["Authentication"])
def login(creds: LoginRequest):
    admin_key = f"auth:user:{creds.username}"
    user_data = db.get_json(admin_key)

    if not user_data or not verify_password(creds.password, user_data.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    role_str = user_data.get("role", "admin")
    token = create_access_token(
        data={"sub": creds.username, "role": role_str, "email": user_data.get("email")}
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        role=UserRole(role_str),
        username=creds.username,
        expires_in=settings.JWT_EXPIRATION_MINUTES * 60
    )

@app.post("/api/auth/logout", tags=["Authentication"])
def logout():
    return {"message": "Successfully logged out"}

# --- Access Verification (Camera Screen Endpoint) ---

@app.post("/api/verify", response_model=VerifyResponse, tags=["Verification"])
def verify(request: VerifyRequest):
    """Primary verification endpoint used by the Entry Door Camera View."""
    # Check tailgating first if camera frame is provided
    tailgate_flag = False
    if request.frame_base64:
        from backend.services.capture import decode_base64_image
        frame_img = decode_base64_image(request.frame_base64)
        if frame_img is not None:
            swipes = tailgate_detector.record_card_swipe(request.camera_id)
            is_tg, p_count, alert = tailgate_detector.check_tailgate(request.camera_id, frame_img, card_swipes=1)
            tailgate_flag = is_tg

    return evaluate_access(request, tailgate_detected=tailgate_flag)

# --- Employee Management ---

@app.post("/api/admin/register", response_model=EmployeeResponse, tags=["Employee Management"])
def register_new_employee(
    emp: EmployeeCreate,
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    existing = db.get_json(f"emp:{emp.employee_id.strip().upper()}")
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Employee with ID '{emp.employee_id}' already exists"
        )
    return register_employee(emp)

@app.post("/api/admin/register-upload", response_model=EmployeeResponse, tags=["Employee Management"])
async def register_with_files(
    employee_id: str = Form(...),
    name: str = Form(...),
    department: str = Form(...),
    access_level: int = Form(1),
    face_photo: Optional[UploadFile] = File(None),
    body_photo: Optional[UploadFile] = File(None),
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    existing = db.get_json(f"emp:{employee_id.strip().upper()}")
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Employee with ID '{employee_id}' already exists"
        )

    face_bytes = await face_photo.read() if face_photo else None
    body_bytes = await body_photo.read() if body_photo else None

    emp_create = EmployeeCreate(
        employee_id=employee_id,
        name=name,
        department=department,
        access_level=access_level,
        is_active=True
    )
    return register_employee(emp_create, face_image_bytes=face_bytes, body_image_bytes=body_bytes)

@app.get("/api/admin/employees", response_model=List[EmployeeResponse], tags=["Employee Management"])
def list_employees(
    department: Optional[str] = None,
    active_only: bool = False,
    current_user: User = Depends(get_current_user)
):
    records = db.get_all_by_pattern("emp:*")
    employees: List[EmployeeResponse] = []

    for data in records:
        if not data:
            continue
        if department and data.get("department", "").lower() != department.lower():
            continue
        if active_only and not data.get("is_active", True):
            continue

        employees.append(EmployeeResponse(
            employee_id=data.get("employee_id"),
            name=data.get("name"),
            department=data.get("department"),
            access_level=data.get("access_level", 1),
            is_active=data.get("is_active", True),
            has_face_profile=bool(data.get("face_embedding_encrypted")),
            has_body_profile=bool(data.get("body_embedding_encrypted")),
            photo_path=data.get("photo_path"),
            body_height=data.get("body_height"),
            body_shoulder=data.get("body_shoulder"),
            body_torso=data.get("body_torso"),
            created_at=data.get("created_at", 0),
            updated_at=data.get("updated_at", 0)
        ))

    return sorted(employees, key=lambda e: e.employee_id)

@app.get("/api/admin/employee/{emp_id}", response_model=EmployeeResponse, tags=["Employee Management"])
def get_employee(emp_id: str, current_user: User = Depends(get_current_user)):
    data = db.get_json(f"emp:{emp_id.strip().upper()}")
    if not data:
        raise HTTPException(status_code=404, detail="Employee not found")

    return EmployeeResponse(
        employee_id=data.get("employee_id"),
        name=data.get("name"),
        department=data.get("department"),
        access_level=data.get("access_level", 1),
        is_active=data.get("is_active", True),
        has_face_profile=bool(data.get("face_embedding_encrypted")),
        has_body_profile=bool(data.get("body_embedding_encrypted")),
        photo_path=data.get("photo_path"),
        body_height=data.get("body_height"),
        body_shoulder=data.get("body_shoulder"),
        body_torso=data.get("body_torso"),
        created_at=data.get("created_at", 0),
        updated_at=data.get("updated_at", 0)
    )

@app.put("/api/admin/employee/{emp_id}", response_model=EmployeeResponse, tags=["Employee Management"])
def update_employee(
    emp_id: str,
    update_data: EmployeeUpdate,
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    key = f"emp:{emp_id.strip().upper()}"
    data = db.get_json(key)
    if not data:
        raise HTTPException(status_code=404, detail="Employee not found")

    if update_data.name is not None:
        data["name"] = update_data.name
    if update_data.department is not None:
        data["department"] = update_data.department
    if update_data.access_level is not None:
        data["access_level"] = update_data.access_level
    if update_data.is_active is not None:
        data["is_active"] = update_data.is_active

    data["updated_at"] = time.time()
    db.set_json(key, data)

    return EmployeeResponse(
        employee_id=data["employee_id"],
        name=data["name"],
        department=data["department"],
        access_level=data["access_level"],
        is_active=data["is_active"],
        has_face_profile=bool(data.get("face_embedding_encrypted")),
        has_body_profile=bool(data.get("body_embedding_encrypted")),
        photo_path=data.get("photo_path"),
        body_height=data.get("body_height"),
        body_shoulder=data.get("body_shoulder"),
        body_torso=data.get("body_torso"),
        created_at=data.get("created_at", 0),
        updated_at=data["updated_at"]
    )

@app.delete("/api/admin/employee/{emp_id}", tags=["Employee Management"])
def delete_employee(emp_id: str, current_user: User = Depends(require_roles([UserRole.ADMIN]))):
    key = f"emp:{emp_id.strip().upper()}"
    data = db.get_json(key)
    if not data:
        raise HTTPException(status_code=404, detail="Employee not found")

    data["is_active"] = False
    data["updated_at"] = time.time()
    db.set_json(key, data)
    return {"message": f"Employee {emp_id} deactivated successfully"}

# --- Camera Management & Dynamic Linking ---

@app.get("/api/admin/cameras", response_model=List[CameraResponse], tags=["Camera Management"])
def list_cameras(linked_only: bool = False, current_user: User = Depends(get_current_user)):
    return list_all_cameras(linked_only=linked_only)

@app.post("/api/admin/cameras", response_model=CameraResponse, tags=["Camera Management"])
def create_new_camera(
    camera: CameraCreate,
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    return add_camera(camera)

@app.post("/api/admin/cameras/scan", response_model=List[CameraResponse], tags=["Camera Management"])
def scan_network(current_user: User = Depends(require_roles([UserRole.ADMIN]))):
    """Auto-scans network for discoverable ONVIF/IP cameras."""
    return scan_network_cameras()

@app.get("/api/admin/cameras/scan-phones", tags=["Camera Management"])
def scan_phones(current_user: User = Depends(get_current_user)):
    """Auto-detects active phone camera streams (IP Webcam, DroidCam) on the same Wi-Fi."""
    return scan_wifi_phone_streams()

@app.post("/api/admin/cameras/{camera_id}/link", response_model=CameraResponse, tags=["Camera Management"])
def link_camera_endpoint(
    camera_id: str,
    zone: Optional[str] = None,
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    """Dynamically links an ONVIF camera on the fly without system restarts."""
    cam = link_camera(camera_id, zone_override=zone)
    if not cam:
        raise HTTPException(status_code=404, detail=f"Camera '{camera_id}' not found to link")
    return cam

@app.post("/api/admin/cameras/{camera_id}/unlink", response_model=CameraResponse, tags=["Camera Management"])
def unlink_camera_endpoint(
    camera_id: str,
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    """Dynamically unlinks an active camera."""
    cam = unlink_camera(camera_id)
    if not cam:
        raise HTTPException(status_code=404, detail=f"Camera '{camera_id}' not found")
    return cam

@app.post("/api/admin/cameras/{camera_id}/relink", response_model=CameraResponse, tags=["Camera Management"])
def relink_camera_endpoint(
    camera_id: str,
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    cam = relink_camera(camera_id)
    if not cam:
        raise HTTPException(status_code=404, detail=f"Camera '{camera_id}' not found")
    return cam

@app.delete("/api/admin/cameras/{camera_id}", tags=["Camera Management"])
def delete_camera_endpoint(
    camera_id: str,
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    success = remove_camera(camera_id)
    if not success:
        raise HTTPException(status_code=404, detail="Camera not found")
    return {"message": f"Camera {camera_id} removed"}

@app.post("/api/admin/cameras/test-source", tags=["Camera Management"])
def test_camera_source(payload: Dict[str, str], current_user: User = Depends(get_current_user)):
    """Non-technical live probe: tests USB webcam, Phone IP stream, or RTSP and returns preview."""
    source = payload.get("source", "").strip()
    if not source:
        raise HTTPException(status_code=400, detail="Camera source (index, URL, or IP) is required")
    success, err, preview_b64, res = probe_camera_source(source)
    return {
        "success": success,
        "message": err if not success else "Camera connected successfully!",
        "preview_base64": preview_b64,
        "resolution": res
    }

@app.get("/api/camera/{camera_id}/stream", tags=["Camera Management"])
def stream_camera(camera_id: str):
    """Streams live MJPEG video from any linked camera for CCTV multi-view."""
    cam = get_camera_by_id(camera_id)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    return StreamingResponse(
        generate_camera_frames(cam.rtsp_url),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/api/camera/{camera_id}/snapshot", tags=["Camera Management"])
def snapshot_camera(camera_id: str):
    """Captures and returns a single JPEG frame from the camera, with graceful standby HUD fallback."""
    cam = get_camera_by_id(camera_id)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    success, frame, _ = get_frame(source_param=cam.rtsp_url)
    import cv2
    import numpy as np
    if not success or frame is None:
        frame = np.zeros((360, 480, 3), dtype=np.uint8)
        frame[:] = (18, 14, 10)
        cv2.putText(frame, f"[ {cam.name} ]", (30, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (230, 240, 255), 2)
        cv2.putText(frame, f"ZONE: {cam.zone} | {cam.camera_id}", (30, 185), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (16, 185, 129), 1)
        cv2.putText(frame, "OPTICAL SENSOR ACTIVE", (30, 215), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 120, 145), 1)

    _, buffer = cv2.imencode(".jpg", frame)
    return Response(content=buffer.tobytes(), media_type="image/jpeg")

# --- Camera Health & Maintenance ---

@app.get("/api/admin/cameras/health", tags=["Camera Health"])
def check_camera_health(current_user: User = Depends(get_current_user)):
    """Runs health check on all cameras and auto-reports malfunctioning devices."""
    return monitor_and_report_health()

@app.post("/api/camera/{camera_id}/heartbeat", tags=["Camera Health"])
def camera_heartbeat(camera_id: str, status_str: str = "ACTIVE", error: str = ""):
    """Camera edge devices ping this endpoint periodically (every 30s) to report live status."""
    st = CameraStatus.ACTIVE if status_str == "ACTIVE" else CameraStatus.ERROR
    success = record_camera_heartbeat(camera_id, st, error)
    if not success:
        raise HTTPException(status_code=404, detail="Camera not found")
    return {"status": "ok", "camera_id": camera_id}

@app.get("/api/admin/cameras/tickets", response_model=List[CameraHealthTicket], tags=["Camera Health"])
def list_tickets(status: Optional[str] = None, current_user: User = Depends(get_current_user)):
    return get_all_health_tickets(status_filter=status)

@app.post("/api/admin/cameras/tickets/{ticket_id}/resolve", response_model=CameraHealthTicket, tags=["Camera Health"])
def resolve_camera_ticket(ticket_id: str, current_user: User = Depends(require_roles([UserRole.ADMIN]))):
    t = resolve_ticket(ticket_id)
    if not t:
        raise HTTPException(status_code=404, detail="Maintenance ticket not found")
    return t

# --- Tailgating Detection Alerts ---

@app.get("/api/admin/tailgate/alerts", response_model=List[TailgateAlert], tags=["Tailgating Detection"])
def get_tailgate_alerts(limit: int = 50, current_user: User = Depends(get_current_user)):
    records = db.get_all_by_pattern("tailgate:*")
    alerts: List[TailgateAlert] = []
    for data in records:
        if data:
            try:
                alerts.append(TailgateAlert(**data))
            except Exception:
                pass
    alerts.sort(key=lambda a: a.timestamp, reverse=True)
    return alerts[:limit]

# --- Cross-Camera Interlinking & Movement Tracking ---

@app.get("/api/admin/timeline", tags=["Cross-Camera Tracking"])
def get_timeline(
    employee_id: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Provides a unified spatial timeline of employee movement across all linked cameras."""
    return get_cross_camera_timeline(employee_id=employee_id, limit=limit)

@app.get("/api/admin/timeline/path/{employee_id}", tags=["Cross-Camera Tracking"])
def get_path(employee_id: str, current_user: User = Depends(get_current_user)):
    """Traces movement journey path for a specific employee across security checkpoints."""
    return get_employee_movement_path(employee_id)

# --- Zone Management ---

@app.get("/api/admin/zones", response_model=List[Zone], tags=["Zone Management"])
def get_zones(current_user: User = Depends(get_current_user)):
    return list_all_zones()

@app.post("/api/admin/zones", response_model=Zone, tags=["Zone Management"])
def add_zone(
    name: str = Query(...),
    description: str = Query(""),
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    return create_zone(name=name, description=description)

@app.delete("/api/admin/zones/{zone_id}", tags=["Zone Management"])
def remove_zone(zone_id: str, current_user: User = Depends(require_roles([UserRole.ADMIN]))):
    success = delete_zone(zone_id)
    if not success:
        raise HTTPException(status_code=404, detail="Zone not found")
    return {"message": "Zone deleted"}

@app.post("/api/admin/zones/{zone_id}/assign/{camera_id}", tags=["Zone Management"])
def assign_zone_camera(
    zone_id: str,
    camera_id: str,
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    ok = assign_camera_to_zone(camera_id, zone_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Zone or camera not found")
    return {"message": f"Camera {camera_id} assigned to zone {zone_id}"}

@app.delete("/api/admin/zones/{zone_id}/remove/{camera_id}", tags=["Zone Management"])
def remove_zone_camera(
    zone_id: str,
    camera_id: str,
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    ok = remove_camera_from_zone(camera_id, zone_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Zone or camera not found")
    return {"message": f"Camera {camera_id} removed from zone {zone_id}"}

# --- Access Logs & Dashboard ---

@app.get("/api/admin/logs", response_model=List[AccessLog], tags=["Access Logs"])
def get_access_logs(
    limit: int = 50,
    decision: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    log_records = db.get_all_by_pattern("log:*")
    logs: List[AccessLog] = []

    for entry in log_records:
        if not entry:
            continue
        if decision and entry.get("decision") != decision:
            continue
        try:
            logs.append(AccessLog(**entry))
        except Exception:
            pass

    logs.sort(key=lambda l: l.timestamp, reverse=True)
    return logs[:limit]

@app.get("/api/admin/dashboard", response_model=DashboardSummary, tags=["Dashboard"])
def get_dashboard_summary(current_user: User = Depends(get_current_user)):
    emp_records = db.get_all_by_pattern("emp:*")
    total_employees = len(emp_records)

    # Department aggregation
    department_stats = calculate_department_attendance()

    # Calculate overall presence
    present_total = sum(d.present_count for d in department_stats)
    rate = round((present_total / max(1, total_employees) * 100), 1)

    # Tailgate alerts today
    now = time.time()
    day_start = now - 86400
    alert_records = db.get_all_by_pattern("tailgate:*")
    tailgate_count = sum(1 for ak in alert_records if ak and ak.get("timestamp", 0) >= day_start)

    # Cameras
    cam_records = db.get_all_by_pattern("cam:*")
    total_cams = len(cam_records)
    active_cams = sum(1 for c in cam_records if c and c.get("status") == "ACTIVE")

    # Recent Logs
    log_records = db.get_all_by_pattern("log:*")
    recent_logs: List[AccessLog] = []
    for item in log_records:
        if item:
            try:
                recent_logs.append(AccessLog(**item))
            except Exception:
                pass
    recent_logs.sort(key=lambda l: l.timestamp, reverse=True)

    return DashboardSummary(
        total_employees=total_employees,
        present_today=present_total,
        attendance_rate=rate,
        active_cameras=active_cams,
        total_cameras=total_cams,
        tailgate_alerts_today=tailgate_count,
        department_stats=department_stats,
        recent_logs=recent_logs[:10]
    )

@app.get("/api/camera/{cam_id}/status", tags=["Cameras"])
def get_camera_status(cam_id: str):
    data = db.get_json(f"cam:{cam_id}")
    if not data:
        raise HTTPException(status_code=404, detail="Camera not found")
    return {
        "camera_id": data.get("camera_id"),
        "status": data.get("status"),
        "is_linked": data.get("is_linked"),
        "last_heartbeat": data.get("last_heartbeat")
    }
