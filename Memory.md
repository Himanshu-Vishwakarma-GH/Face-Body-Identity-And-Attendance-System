# Memory — AI-Based Face & Body Detection Access Control System

## Project Context

This file tracks all decisions, discussions, and key information about the project.

---

## Problem Statement

An AI-powered office access control system that:
1. Identifies employees upon swiping ID card for entry
2. If employee forgets card, recognizes them using face detection and body dimensions
3. Stores employee details in an elastic auto-scaling database
4. Ensures high security and confidentiality of data
5. Links data across multiple cameras
6. Auto-reports malfunctioning cameras
7. Detects tailgating

---

## Key Decisions

### Database Choice: Redis Stack
- **Decision**: Use Redis Stack for prototype, Redis Cloud for production
- **Reason**: Vector search (VADD/VSIM) + JSON storage + sub-millisecond latency + free
- **PS Compliance**: Redis Cloud provides auto-scaling for "elastic database" constraint

### Face Recognition Model: InsightFace
- **Decision**: Use InsightFace with ONNX runtime
- **Reason**: Best accuracy, 512-dim embeddings, free, works offline

### Body Analysis: MediaPipe Pose
- **Decision**: Use MediaPipe Pose for body keypoints
- **Reason**: Free, real-time, accurate keypoint extraction

### Person Detection: YOLOv8
- **Decision**: Use YOLOv8 for person detection and tailgating
- **Reason**: Fast, lightweight, MIT license

### Verification Method: 1:1 (Not 1:N)
- **Decision**: Card-first approach, then 1:1 verification
- **Flow**: EmployeeID input -> Fetch profile -> Capture -> Verify against stored profile
- **Reason**: Faster O(1) lookup, lower false positives, more secure

### Dynamic Camera Linking
- **Decision**: Admin can link/unlink cameras on the fly
- **Reason**: PS requirement for flexible camera management

---

## Screen Design

### Screen 1: Camera View (Entry Door)
- Live camera feed
- EmployeeID text input
- Verify button
- Status display (GRANTED/DENIED with confidence %)
- Tailgate alert banner

### Screen 2: Admin Portal (React Dashboard)
- Login page (JWT auth)
- Dashboard (department-wise attendance stats)
- Add Employee (name, EmpID, dept, face+body capture)
- Employee List (table with search/filter)
- Access Logs (filterable log table)
- Camera Management (link/unlink/scan)
- Camera Health (status monitor)
- Zone Mapping (zone creation, camera assignment)

---

## API Endpoints

### Camera Screen
- POST /api/verify - { employee_id, camera_id } -> GRANT/DENIED
- GET /api/camera/{id}/status - Camera health

### Admin Portal
- POST /api/auth/login - JWT token
- GET /api/admin/dashboard - Attendance summary
- POST /api/admin/register - Register employee
- GET/PUT/DELETE /api/admin/employee/{id} - Employee CRUD
- GET/POST /api/admin/cameras - Camera list/add
- POST /api/admin/cameras/scan - Auto-scan
- POST /api/admin/cameras/{id}/link|unlink|relink - Dynamic linking
- GET/POST/DELETE /api/admin/zones - Zone management
- GET /api/admin/logs - Access logs
- GET /api/admin/cameras/health - Camera health

---

## PS Constraints Compliance

| Constraint | Status | Implementation |
|---|---|---|
| Elastic auto-scaling DB | COVERED | Redis Stack -> Redis Cloud |
| Highly secure + confidential | COVERED | AES-256 + JWT + RBAC + audit |
| Cross-camera interlinking | COVERED | Re-ID + unified timeline |
| Auto-report malfunctioning cameras | COVERED | Heartbeat monitor + auto-ticket |
| Employee identification | COVERED | 1:1 face + body verification |
| Tailgating detection | COVERED | YOLOv8 person counting + alert |
| Dynamic camera linking | COVERED | Admin link/unlink on the fly |
| Least expensive | COVERED | All open-source (Redis Stack free) |

---

## File Structure

```
ai-access-system/
|-- backend/           # FastAPI backend
|-- camera_screen/     # HTML + JS door display
|-- admin_portal/      # React dashboard
|-- ml/                # ML models (InsightFace, MediaPipe)
|-- data/              # Stored face photos
|-- docker/            # Dockerfiles
|-- docker-compose.yml # Container orchestration
+-- tests/             # Unit tests
```

---

## Implementation Order

1. Backend: config.py + database.py (Redis setup)
2. Backend: models.py (Pydantic schemas)
3. Backend: auth.py (JWT)
4. Backend: services/register.py
5. Backend: services/fetch_profile.py
6. Backend: services/face_verify.py
7. Backend: services/body_verify.py
8. Backend: services/capture.py
9. Backend: services/decision.py
10. Backend: services/tailgate_detect.py
11. Backend: camera_manager + scanner + linker
12. Backend: services/camera_health.py
13. Backend: services/cross_camera.py
14. Backend: services/attendance.py
15. Backend: services/zone_manager.py
16. Backend: app.py (all routes)
17. Camera Screen: index.html + script.js
18. Admin Portal: React setup + pages
19. Docker Compose + Dockerfiles
20. Integration testing

---

## Open Items / Future Enhancements

- Elasticsearch as alternative production database
- HR system integration
- Employee self-registration portal
- Offline mode (if backend goes down)
- Data retention policy
- Camera auto-scaling (auto-provisioning)
- Load testing for concurrent cameras
- Production TLS/HTTPS setup

---

## Cost Estimate

| Item | Cost |
|---|---|
| InsightFace | Free |
| MediaPipe | Free |
| YOLOv8 | Free |
| Redis Stack | Free (self-hosted) |
| Redis Cloud | $5/mo+ (production) |
| FastAPI | Free |
| React + Tailwind | Free |
| OpenCV | Free |
| **Total** | **Near-zero software cost** |

---

## Team Notes

- Project is for IBM National Hackathon
- Two-screen requirement: Camera View + Admin Portal
- Dynamic camera linking is a key differentiator
- Focus on security and PS compliance
- Target: Working prototype in ~10 hours
