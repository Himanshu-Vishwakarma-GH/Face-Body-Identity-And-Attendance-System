# Implementation Plan — AI-Based Face & Body Detection Access Control System

## Project Overview

An AI-powered office access control system that uses face recognition and body dimension analysis to identify employees. When an employee swipes their ID card, the system verifies their identity using camera footage. If the card is forgotten, the system recognizes the employee through face and body detection.

---

## Tech Stack

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

## Core Flow

```
STEP 1: User inputs EmployeeID on Camera Screen
    |
STEP 2: Backend fetches employee profile from Redis
    |   Redis: JSON.GET emp:EMP001
    |   + VDIM vset:faces "emp:EMP001"  (get stored face vector)
    |
STEP 3: Camera captures frame (5-second window)
    |
STEP 4: Face verification (1:1)
    |   cosine_similarity(stored_face, captured_face) >= 0.6 -> MATCH
    |
STEP 5: Body verification (1:1)
    |   euclidean_distance(stored_body, captured_body) <= threshold -> MATCH
    |
STEP 6: Decision
    |   face_match AND body_match -> GRANT ACCESS
    |   face_match AND NOT body_match -> WARN
    |   NOT face_match -> DENY + TAILGATE ALERT
    |
STEP 7: Log to Redis
    |   JSON.SET log:<uuid> $ { ... }
```

---

## API Endpoints

### Camera Screen APIs

```
POST   /api/verify              # { employee_id, camera_id } -> GRANT/DENIED
GET    /api/camera/{id}/status  # Camera health status
```

### Admin Portal APIs

```
# Auth
POST   /api/auth/login          # { username, password } -> JWT token
POST   /api/auth/logout         # Invalidate token

# Dashboard
GET    /api/admin/dashboard     # Department-wise attendance summary

# Employee Management
GET    /api/admin/employees     # List all (filters: department, status)
POST   /api/admin/register      # Register new employee
PUT    /api/admin/employee/{id} # Update employee
DELETE /api/admin/employee/{id} # Deactivate employee
GET    /api/admin/employee/{id} # Get employee details

# Camera Management
GET    /api/admin/cameras              # List all cameras
POST   /api/admin/cameras              # Add camera manually
POST   /api/admin/cameras/scan         # Auto-scan network
POST   /api/admin/cameras/{id}/link    # Link camera
POST   /api/admin/cameras/{id}/unlink  # Unlink camera
POST   /api/admin/cameras/{id}/relink  # Re-link camera

# Zone Management
GET    /api/admin/zones                # List zones
POST   /api/admin/zones                # Create zone
DELETE /api/admin/zones/{id}           # Delete zone
POST   /api/admin/cameras/{id}/zones   # Assign camera to zones
DELETE /api/admin/cameras/{id}/zones/{zone_id}  # Remove from zone

# Access Logs
GET    /api/admin/logs                 # Access logs with filters

# Camera Health
GET    /api/admin/cameras/health       # All camera health
GET    /api/admin/cameras/{id}/health  # Single camera history
```

---

## File Structure

```
ai-access-system/
|
|-- backend/
|   |-- app.py                        # FastAPI entry point
|   |-- config.py                     # Settings
|   |-- database.py                   # Redis connection + indexes
|   |-- models.py                     # Pydantic models
|   |-- auth.py                       # JWT authentication
|   |
|   |-- services/
|   |   |-- register.py               # Employee enrollment
|   |   |-- fetch_profile.py          # Redis lookup
|   |   |-- face_verify.py            # 1:1 face comparison
|   |   |-- body_verify.py            # 1:1 body comparison
|   |   |-- capture.py                # Camera frame capture
|   |   |-- decision.py               # Access decision logic
|   |   |-- attendance.py             # Stats aggregation
|   |   |-- tailgate_detect.py        # Tailgating detection
|   |   |-- cross_camera.py           # Re-ID + event linking
|   |   |-- camera_manager.py         # Camera CRUD
|   |   |-- camera_scanner.py         # Network auto-discovery
|   |   |-- camera_linker.py          # Link/unlink logic
|   |   |-- camera_health.py          # Heartbeat monitor
|   |   |-- zone_manager.py           # Zone CRUD
|   |
|   +-- requirements.txt
|
|-- camera_screen/
|   |-- index.html
|   |-- style.css
|   +-- script.js
|
|-- admin_portal/
|   |-- package.json
|   |-- index.html
|   |-- vite.config.js
|   |-- tailwind.config.js
|   |
|   +-- src/
|       |-- main.jsx
|       |-- App.jsx
|       |-- api.js
|       |
|       |-- pages/
|       |   |-- Login.jsx
|       |   |-- Dashboard.jsx
|       |   |-- AddEmployee.jsx
|       |   |-- EmployeeList.jsx
|       |   |-- AccessLogs.jsx
|       |   |-- CameraManagement.jsx
|       |   |-- CameraHealth.jsx
|       |   +-- ZoneMapping.jsx
|       |
|       +-- components/
|           |-- FaceCapture.jsx
|           |-- BodyCapture.jsx
|           |-- StatsCard.jsx
|           |-- LiveFeed.jsx
|           |-- TailgateAlert.jsx
|           |-- CameraStatus.jsx
|           |-- CameraCard.jsx
|           |-- CameraScanner.jsx
|           +-- ZoneSelector.jsx
|
|-- ml/
|   |-- models/
|   |   |-- insightface/
|   |   +-- mediapipe/
|   +-- register_employee.py
|
|-- data/
|   +-- faces/
|
|-- docker/
|   |-- Dockerfile.backend
|   |-- Dockerfile.camera-screen
|   +-- Dockerfile.admin-portal
|
|-- docker-compose.yml
|
+-- tests/
    |-- test_face_verify.py
    |-- test_body_verify.py
    |-- test_decision.py
    |-- test_camera_health.py
    +-- test_tailgate.py
```

---

## Dependencies

### backend/requirements.txt

```
fastapi==0.115.0
uvicorn==0.30.0
opencv-python==4.10.0.84
mediapipe==0.10.18
insightface==0.7.3
onnxruntime==1.19.0
numpy==1.26.4
redis[hiredis]==5.1.0
pydantic==2.9.0
python-multipart==0.0.9
PyJWT==2.9.0
cryptography==43.0.0
python-dotenv==1.0.1
ultralytics==8.2.0
```

### admin_portal/package.json

```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.26.0",
    "tailwindcss": "^3.4.0",
    "axios": "^1.7.0",
    "recharts": "^2.12.0"
  }
}
```

---

## Docker Compose

```yaml
version: '3.8'
services:
  redis:
    image: redis/redis-stack-server:latest
    ports:
      - "6379:6379"
    environment:
      - REDIS_ARGS=--requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: unless-stopped

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379
      - JWT_SECRET=${JWT_SECRET}
      - AES_KEY=${AES_KEY}
    depends_on:
      - redis
    restart: unless-stopped

  camera-screen:
    build: ./camera_screen
    ports:
      - "3000:80"
    depends_on:
      - backend

  admin-portal:
    build: ./admin_portal
    ports:
      - "3001:80"
    depends_on:
      - backend

volumes:
  redis_data:
```

---

## Security Implementation

| Feature | Implementation |
|---|---|
| Encryption at rest | AES-256 for face embeddings in Redis |
| JWT authentication | Admin portal requires JWT for all API calls |
| RBAC | Admin / Security / Auditor roles |
| TLS | HTTPS for all API calls (production) |
| Audit trail | Every data access logged |
| Password hashing | bcrypt for admin passwords |

---

## Implementation Steps

| Step | Task | Est. Time |
|---|---|---|
| 1 | Backend: config.py + database.py (Redis setup + indexes) | 30 min |
| 2 | Backend: models.py (Pydantic schemas) | 15 min |
| 3 | Backend: auth.py (JWT authentication) | 20 min |
| 4 | Backend: services/register.py (Employee enrollment) | 45 min |
| 5 | Backend: services/fetch_profile.py (Redis lookup) | 15 min |
| 6 | Backend: services/face_verify.py (1:1 face comparison) | 30 min |
| 7 | Backend: services/body_verify.py (1:1 body comparison) | 25 min |
| 8 | Backend: services/capture.py (Camera frame grab) | 20 min |
| 9 | Backend: services/decision.py (Combined logic) | 15 min |
| 10 | Backend: services/tailgate_detect.py (YOLOv8) | 30 min |
| 11 | Backend: camera_manager + scanner + linker | 45 min |
| 12 | Backend: services/camera_health.py | 20 min |
| 13 | Backend: services/cross_camera.py | 30 min |
| 14 | Backend: services/attendance.py | 15 min |
| 15 | Backend: services/zone_manager.py | 15 min |
| 16 | Backend: app.py (All FastAPI routes) | 40 min |
| 17 | Camera Screen: index.html + script.js | 30 min |
| 18 | Admin Portal: React setup + all pages | 90 min |
| 19 | Docker Compose + Dockerfiles | 20 min |
| 20 | Integration testing | 30 min |
| **Total** | | **~10 hours** |
