# Architecture — AI-Based Face & Body Detection Access Control System

## System Overview

```
+-------------------------------------------------------------------+
|                     SCREEN 1: CAMERA VIEW                         |
|                  (Entry Point / Door Display)                      |
|                                                                   |
|   +-----------------------------------------------------------+  |
|   |                  LIVE CAMERA FEED                         |  |
|   |             (employee sees themselves)                    |  |
|   +-----------------------------------------------------------+  |
|   +----------------+  +------------+  +----------------------+  |
|   | EmployeeID:    |  |  [VERIFY]  |  |  STATUS: GRANTED     |  |
|   | [EMP001     ]  |  |            |  |  Face: 92% Body: 88% |  |
|   +----------------+  +------------+  +----------------------+  |
+-------------------------------------------------------------------+

+-------------------------------------------------------------------+
|                     SCREEN 2: ADMIN PORTAL                        |
|                  (React Dashboard)                                 |
|                                                                   |
|  +-------------+ +-------------+ +-------------+ +-------------+ |
|  | Dashboard   | | Add Employee| | Cameras     | | Access Logs | |
|  +-------------+ +-------------+ +-------------+ +-------------+ |
|                                                                   |
|  +------------------------+  +-------------------------------+   |
|  | DEPARTMENT WISE        |  |  ADD NEW EMPLOYEE             |   |
|  | ATTENDANCE STATS       |  |  Name / EmpID / Dept          |   |
|  |                        |  |  [CAPTURE FACE] [CAPTURE BODY]|   |
|  | Engineering | 12/15    |  |  [SAVE]                      |   |
|  | Marketing   |  8/10    |  +-------------------------------+   |
|  | HR          |  5/5     |                                      |
|  +------------------------+  +----------------------------------+ |
+-------------------------------------------------------------------+

+-------------------------------------------------------------------+
|                       BACKEND (FastAPI)                            |
|                                                                   |
|  +----------+  +----------+  +----------+  +----------+         |
|  | Verify   |  | Register |  | Camera   |  | Health   |         |
|  | Service  |  | Service  |  | Manager  |  | Monitor  |         |
|  +----------+  +----------+  +----------+  +----------+         |
|                                                                   |
|  +----------+  +----------+  +----------+  +----------+         |
|  | Face     |  | Body     |  | Tailgate |  | Cross    |         |
|  | Verify   |  | Verify   |  | Detect   |  | Camera   |         |
|  +----------+  +----------+  +----------+  +----------+         |
+-------------------------------------------------------------------+
                           |
                 +---------v---------+
                 |   REDIS STACK     |
                 |  (Vector Search   |
                 |   + JSON Store)   |
                 +-------------------+
```

---

## Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Face Recognition | InsightFace (ONNX) | 1:1 face verification, 512-dim embeddings |
| Body Analysis | MediaPipe Pose | Body keypoint extraction, 256-dim embeddings |
| Object Detection | YOLOv8 (Ultralytics) | Person detection, tailgating |
| Backend API | FastAPI (Python) | Async REST API |
| Database | Redis Stack | Vector search + JSON storage + caching |
| Camera | OpenCV | RTSP/USB camera frame capture |
| Camera Screen | HTML + Vanilla JS | Lightweight door display |
| Admin Portal | React + Tailwind CSS | Full dashboard |
| Auth | JWT (PyJWT) | Admin portal authentication |
| Encryption | AES-256 (cryptography) | Face embedding encryption at rest |

---

## Data Flow

### Employee Registration Flow

```
Admin Portal                    Backend                      Redis
    |                              |                            |
    |-- POST /api/admin/register ->|                            |
    |   (name, emp_id, dept,       |                            |
    |    face_photo, body_photo)   |                            |
    |                              |-- Extract face embedding -->|
    |                              |   (InsightFace)            |
    |                              |-- Extract body embedding -->|
    |                              |   (MediaPipe)              |
    |                              |-- Encrypt embeddings ----->|
    |                              |   (AES-256)                |
    |                              |-- Store employee --------->|
    |                              |   JSON.SET emp:EMP001      |
    |                              |   VADD vset:faces          |
    |                              |   VADD vset:bodies         |
    |<-- 201 Created -------------|                            |
```

### Access Verification Flow

```
Camera Screen                 Backend                      Redis
    |                           |                            |
    |-- POST /api/verify ------>|                            |
    |   { employee_id,          |                            |
    |     camera_id }           |                            |
    |                           |-- Fetch profile ----------->|
    |                           |   JSON.GET emp:EMP001      |
    |                           |   VDIM vset:faces          |
    |                           |<-- (face_vec, body_vec) ---|
    |                           |                            |
    |                           |-- Capture frame ----------->|
    |                           |   (OpenCV camera)          |
    |                           |                            |
    |                           |-- 1:1 Face Compare         |
    |                           |   cosine_similarity >= 0.6 |
    |                           |                            |
    |                           |-- 1:1 Body Compare         |
    |                           |   euclidean_distance <= T   |
    |                           |                            |
    |                           |-- Log access attempt ----->|
    |                           |   JSON.SET log:<uuid>      |
    |<-- { decision, confidence }|                            |
```

### Camera Management Flow

```
Admin Portal                 Backend                      Redis
    |                           |                            |
    |-- POST /api/admin/       |                            |
    |   cameras/scan --------->|                            |
    |                          |-- Scan network (ONVIF) --->|
    |<-- [discovered cameras] -|                            |
    |                           |                            |
    |-- POST /api/admin/       |                            |
    |   cameras/CAM-05/link -->|                            |
    |                          |-- Start streaming --------->|
    |                          |-- Update status ----------->|
    |<-- 200 OK ---------------|                            |
```

---

## Database Schema (Redis)

### Vector Indexes

```bash
# Face embeddings (512 dimensions)
VADD vset:faces VALUES 512 <face_vector> "emp:EMP001"

# Body embeddings (256 dimensions)
VADD vset:bodies VALUES 256 <body_vector> "emp:EMP001"
```

### Search Index

```bash
FT.CREATE idx:employees ON JSON PREFIX 1 "emp:" SCHEMA
  $.employee_id AS employee_id TAG SORTABLE
  $.name AS name TEXT SORTABLE
  $.department AS department TAG SORTABLE
  $.access_level AS access_level NUMERIC SORTABLE
  $.is_active AS is_active NUMERIC SORTABLE
  $.created_at AS created_at NUMERIC SORTABLE
```

### Employee Document

```json
{
  "employee_id": "EMP001",
  "name": "John Doe",
  "department": "Engineering",
  "access_level": 2,
  "is_active": 1,
  "photo_path": "/data/faces/EMP001.jpg",
  "face_embedding_encrypted": "<AES-256 encrypted blob>",
  "body_height": 175.5,
  "body_shoulder": 45.2,
  "body_torso": 0.42,
  "created_at": 1724900000,
  "updated_at": 1724900000
}
```

### Access Log Document

```json
{
  "log_id": "uuid-001",
  "employee_id": "EMP001",
  "camera_id": "CAM-01",
  "zone": "Entry Zone A",
  "timestamp": 1724900100,
  "face_matched": true,
  "face_confidence": 0.92,
  "body_matched": true,
  "body_confidence": 0.88,
  "decision": "GRANTED",
  "tailgate_detected": false
}
```

### Camera Document

```json
{
  "camera_id": "CAM-01",
  "name": "Front Door",
  "location": "Main Entrance",
  "floor": "Ground",
  "zone": "Entry Zone A",
  "ip_address": "192.168.1.100",
  "rtsp_url": "rtsp://192.168.1.100:554/stream1",
  "status": "ACTIVE",
  "is_linked": 1,
  "linked_at": 1724900000,
  "last_heartbeat": 1724900100,
  "error_message": ""
}
```

---

## Security Architecture

```
+-------------------------------------------------------------------+
|                      SECURITY LAYERS                              |
+-------------------------------------------------------------------+
|                                                                   |
|  Layer 1: TRANSPORT SECURITY                                     |
|  - TLS 1.3 for all API communication                             |
|  - HTTPS for admin portal                                        |
|  - Secure WebSocket for camera streams                           |
|                                                                   |
|  Layer 2: AUTHENTICATION                                         |
|  - JWT tokens for admin portal                                   |
|  - API key for camera screen                                     |
|  - Token expiration: 24 hours                                    |
|                                                                   |
|  Layer 3: AUTHORIZATION (RBAC)                                   |
|  - Admin: Full access                                            |
|  - Security: View logs, camera status                            |
|  - Auditor: Read-only access                                     |
|                                                                   |
|  Layer 4: DATA ENCRYPTION                                        |
|  - AES-256 encryption for face embeddings at rest                |
|  - Encrypted blobs stored in Redis                               |
|  - Key rotation every 90 days                                    |
|                                                                   |
|  Layer 5: AUDIT TRAIL                                            |
|  - Every data access logged                                      |
|  - Camera footage timestamped                                    |
|  - Access attempts recorded with decision                        |
|                                                                   |
+-------------------------------------------------------------------+
```

---

## Camera Lifecycle

```
UNKNOWN (detected on network)
    |
    v
[Admin LINK]
    |
    v
LINKED (configured, not streaming)
    |
    +---> [Stream OK] -----> ACTIVE (streaming, monitoring)
    |
    +---> [Stream FAIL] ---> ERROR (auto-report created)
    |
    +---> [Admin UNLINK] --> UNLINKED (stored, can re-link)

ACTIVE
    |
    +---> [No heartbeat 2min] --> INACTIVE (auto-report created)
    |
    +---> [Admin UNLINK] ------> UNLINKED

ERROR
    |
    +---> [Admin RE-LINK] -----> LINKED
    |
    +---> [Camera repaired] ---> ACTIVE
```

---

## Tailgating Detection

```
On card swipe event:
  1. Start 5-second detection window
  2. Run YOLOv8 person detection on camera feed
  3. Count distinct persons (Re-ID to avoid double-counting)
  4. Decision logic:
     |
     +-- person_count > 1 AND card_swipes == 1
     |     --> TAILGATE ALERT
     |     --> Log event with timestamp + camera
     |     --> Alert security in real-time
     |
     +-- person_count == 0 AND card_swiped
     |     --> TIMEOUT ALERT (card used, no person detected)
     |
     +-- person_count == 1 AND card_swipes == 1
           --> NORMAL (proceed to face/body verification)
```

---

## Cross-Camera Linking

```
Each access log tagged with:
  - camera_id (which camera detected)
  - zone (entry/exit zone)
  - timestamp
  - person_reid_embedding (appearance vector for Re-ID)

Admin Portal Unified Timeline:
  09:01 - CAM-01 (Front Door) - EMP001 ENTERED
  09:05 - CAM-03 (Lobby)      - EMP001 DETECTED
  09:10 - CAM-02 (Back Door)  - EMP001 EXITED

Spatial Mapping:
  Floor plan with camera positions showing movement path
```

---

## Camera Health Monitoring

```
Background Task (runs every 30 seconds):
  For each linked camera:
    1. Ping camera / check last frame timestamp
    2. If no response for > 2 minutes:
        - status = INACTIVE
        - Create maintenance ticket in Redis
        - Push alert to admin dashboard
        - Log in camera_health_log
    3. If response OK:
        - Update last_heartbeat timestamp
        - status = ACTIVE
```

---

## Dynamic Camera Linking

```
Admin Portal: Camera Management Page

LINKED CAMERAS (Active)          AVAILABLE CAMERAS (Not Linked)
+--------------+                  +--------------+
| CAM-01       |                  | CAM-05       |
| Front Door   |                  | Staircase    |
| GREEN LIVE   |                  | GREEN FOUND  |
| [UNLINK]     |                  | [LINK]       |
+--------------+                  +--------------+

ZONE MAPPING
Entry Zone A <-> CAM-01, CAM-03
Entry Zone B <-> CAM-02
[+ Add Zone]
```

---

## Memory Cost Calculation

```
Face embedding: 512 dimensions x 4 bytes (float32) = 2,048 bytes ~ 2 KB
Body embedding: 256 dimensions x 4 bytes = 1,024 bytes ~ 1 KB
Metadata (JSON): ~500 bytes

Per employee total: ~3.5 KB

100 employees:     350 KB
1,000 employees:   3.5 MB
10,000 employees:  35 MB
100,000 employees: 350 MB (fits in RAM easily)
```

---

## Scaling Strategy

| Phase | Database | Scaling |
|---|---|---|
| Prototype | Redis Stack (self-hosted) | Single node |
| Production | Redis Cloud | Auto-scaling managed |
| Enterprise | Redis Enterprise | Multi-node cluster |

---

## Deployment Architecture

```
+-------------------------------------------------------------------+
|                    DOCKER DEPLOYMENT                              |
+-------------------------------------------------------------------+
|                                                                   |
|  +------------------+     +------------------+                   |
|  |   Redis Stack    |     |    Backend       |                   |
|  |   Port: 6379     |<----|    Port: 8000    |                   |
|  |   Volume: data   |     |    FastAPI       |                   |
|  +------------------+     +------------------+                   |
|           ^                       |                               |
|           |                       |                               |
|  +--------+--------+    +--------+--------+                     |
|  | Camera Screen   |    | Admin Portal    |                     |
|  | Port: 3000      |    | Port: 3001      |                     |
|  | HTML + JS       |    | React + Tailwind|                     |
|  +-----------------+    +-----------------+                     |
|                                                                   |
+-------------------------------------------------------------------+
```
