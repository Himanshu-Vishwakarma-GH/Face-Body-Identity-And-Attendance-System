from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import time
import uuid

# --- Enumerations ---

class UserRole(str, Enum):
    ADMIN = "admin"
    SECURITY = "security"
    AUDITOR = "auditor"

class DecisionStatus(str, Enum):
    GRANTED = "GRANTED"
    DENIED = "DENIED"
    WARNING = "WARNING"

class CameraStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ERROR = "ERROR"
    UNLINKED = "UNLINKED"
    DISCOVERED = "DISCOVERED"

class TicketSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class TicketStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"

# --- Authentication Schemas ---

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    username: str
    expires_in: int

class User(BaseModel):
    username: str
    email: Optional[str] = None
    role: UserRole = UserRole.ADMIN
    is_active: bool = True
    created_at: float = Field(default_factory=time.time)

# --- Employee Schemas ---

class EmployeeBase(BaseModel):
    employee_id: str = Field(..., description="Unique employee badge/card ID, e.g. EMP001")
    name: str = Field(..., description="Full employee name")
    department: str = Field(..., description="Department, e.g. Engineering, HR, Marketing")
    access_level: int = Field(default=1, description="Security clearance level (1-5)")
    is_active: bool = Field(default=True, description="Whether employee is currently active")

class EmployeeCreate(EmployeeBase):
    face_image_base64: Optional[str] = None
    body_image_base64: Optional[str] = None

class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    access_level: Optional[int] = None
    is_active: Optional[bool] = None

class EmployeeResponse(EmployeeBase):
    has_face_profile: bool = False
    has_body_profile: bool = False
    photo_path: Optional[str] = None
    body_height: Optional[float] = None
    body_shoulder: Optional[float] = None
    body_torso: Optional[float] = None
    created_at: float
    updated_at: float

# --- Verification & Tailgating Schemas ---

class VerifyRequest(BaseModel):
    employee_id: Optional[str] = Field(None, description="Employee ID from card swipe or manual input")
    camera_id: str = Field(default="CAM-01", description="Camera stream identifier")
    frame_base64: Optional[str] = Field(None, description="Optional frame capture sent from client")

class VerifyResponse(BaseModel):
    decision: DecisionStatus
    employee_id: Optional[str] = None
    employee_name: Optional[str] = None
    department: Optional[str] = None
    face_matched: bool = False
    face_confidence: float = 0.0
    body_matched: bool = False
    body_confidence: float = 0.0
    tailgate_detected: bool = False
    message: str
    log_id: str
    timestamp: float = Field(default_factory=time.time)

class TailgateAlert(BaseModel):
    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    camera_id: str
    zone: str
    person_count: int
    card_swipes: int
    timestamp: float = Field(default_factory=time.time)
    message: str
    is_resolved: bool = False

# --- Access Log Schemas ---

class AccessLog(BaseModel):
    log_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: Optional[str] = None
    employee_name: Optional[str] = None
    department: Optional[str] = None
    camera_id: str
    zone: str
    timestamp: float = Field(default_factory=time.time)
    face_matched: bool = False
    face_confidence: float = 0.0
    body_matched: bool = False
    body_confidence: float = 0.0
    decision: DecisionStatus
    tailgate_detected: bool = False
    snapshot_path: Optional[str] = None

# --- Camera & Zone Schemas ---

class CameraBase(BaseModel):
    camera_id: str = Field(..., description="Unique camera ID, e.g. CAM-01")
    name: str = Field(..., description="Display name, e.g. Front Door")
    location: str = Field(..., description="Physical location, e.g. Main Entrance")
    floor: str = Field(default="Ground")
    zone: str = Field(default="Entry Zone A")
    ip_address: Optional[str] = "192.168.1.100"
    rtsp_url: str = Field(default="0", description="RTSP URL, video file path, or USB webcam index (0)")

class CameraCreate(CameraBase):
    pass

class CameraResponse(CameraBase):
    status: CameraStatus = CameraStatus.ACTIVE
    is_linked: bool = True
    linked_at: Optional[float] = None
    last_heartbeat: Optional[float] = None
    error_message: Optional[str] = ""
    fps: Optional[float] = 30.0

class Zone(BaseModel):
    zone_id: str = Field(default_factory=lambda: f"zone-{str(uuid.uuid4())[:8]}")
    name: str
    description: Optional[str] = ""
    camera_ids: List[str] = []

# --- Camera Health & Maintenance ---

class CameraHealthTicket(BaseModel):
    ticket_id: str = Field(default_factory=lambda: f"ticket-{str(uuid.uuid4())[:8]}")
    camera_id: str
    reported_at: float = Field(default_factory=time.time)
    status: TicketStatus = TicketStatus.OPEN
    issue: str
    severity: TicketSeverity = TicketSeverity.HIGH
    resolved_at: Optional[float] = None

# --- Dashboard & Statistics Schemas ---

class DepartmentAttendance(BaseModel):
    department: str
    present_count: int
    total_count: int
    percentage: float

class DashboardSummary(BaseModel):
    total_employees: int = 0
    present_today: int = 0
    attendance_rate: float = 0.0
    active_cameras: int = 0
    total_cameras: int = 0
    tailgate_alerts_today: int = 0
    department_stats: List[DepartmentAttendance] = []
    recent_logs: List[AccessLog] = []
