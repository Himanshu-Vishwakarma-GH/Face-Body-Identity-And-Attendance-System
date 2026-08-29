# Phases — AI-Based Face & Body Detection Access Control System

## Overview

The project is divided into 4 phases, progressing from infrastructure setup to full integration. Each phase builds on the previous one.

---

## Phase 1: Foundation (Estimated: 2 hours)

### Goal
Set up project structure, database, and core backend infrastructure.

### Tasks

| # | Task | File | Est. Time |
|---|---|---|---|
| 1.1 | Create project directory structure | All folders | 10 min |
| 1.2 | Backend: config.py - Redis URL, JWT secret, AES key, camera settings | backend/config.py | 15 min |
| 1.3 | Backend: database.py - Redis connection, index creation, health check | backend/database.py | 30 min |
| 1.4 | Backend: models.py - Pydantic request/response schemas | backend/models.py | 20 min |
| 1.5 | Backend: auth.py - JWT token creation, verification, RBAC | backend/auth.py | 25 min |
| 1.6 | Backend: requirements.txt - All Python dependencies | backend/requirements.txt | 5 min |
| 1.7 | Create .env.example with all environment variables | .env.example | 5 min |

### Deliverables
- Redis connection working
- Database indexes created
- JWT authentication working
- All Pydantic models defined

---

## Phase 2: Core AI Services (Estimated: 3 hours)

### Goal
Implement face recognition, body analysis, and the verification pipeline.

### Tasks

| # | Task | File | Est. Time |
|---|---|---|---|
| 2.1 | Backend: services/register.py - Employee enrollment (face+body extraction) | backend/services/register.py | 45 min |
| 2.2 | Backend: services/fetch_profile.py - Redis lookup by employee_id | backend/services/fetch_profile.py | 15 min |
| 2.3 | Backend: services/face_verify.py - 1:1 face comparison (cosine similarity) | backend/services/face_verify.py | 30 min |
| 2.4 | Backend: services/body_verify.py - 1:1 body comparison (euclidean distance) | backend/services/body_verify.py | 25 min |
| 2.5 | Backend: services/capture.py - Camera frame capture (OpenCV) | backend/services/capture.py | 20 min |
| 2.6 | Backend: services/decision.py - Combined access decision logic | backend/services/decision.py | 15 min |
| 2.7 | Backend: app.py - FastAPI routes for verify, register, employee CRUD | backend/app.py | 30 min |

### Deliverables
- Employee registration working (face+body extraction + Redis storage)
- 1:1 face verification working
- 1:1 body verification working
- Camera capture working
- Access decision logic working
- Basic API routes functional

---

## Phase 3: Camera & Security Features (Estimated: 2.5 hours)

### Goal
Implement camera management, tailgating detection, cross-camera linking, and health monitoring.

### Tasks

| # | Task | File | Est. Time |
|---|---|---|---|
| 3.1 | Backend: services/camera_manager.py - Camera CRUD operations | backend/services/camera_manager.py | 20 min |
| 3.2 | Backend: services/camera_scanner.py - Network auto-discovery (ONVIF) | backend/services/camera_scanner.py | 25 min |
| 3.3 | Backend: services/camera_linker.py - Link/unlink logic + stream management | backend/services/camera_linker.py | 25 min |
| 3.4 | Backend: services/camera_health.py - Heartbeat monitor + auto-reporting | backend/services/camera_health.py | 20 min |
| 3.5 | Backend: services/tailgate_detect.py - YOLOv8 person counting | backend/services/tailgate_detect.py | 30 min |
| 3.6 | Backend: services/cross_camera.py - Re-ID + event linking | backend/services/cross_camera.py | 30 min |
| 3.7 | Backend: services/attendance.py - Department-wise stats aggregation | backend/services/attendance.py | 15 min |
| 3.8 | Backend: services/zone_manager.py - Zone CRUD + camera-zone mapping | backend/services/zone_manager.py | 15 min |

### Deliverables
- Camera CRUD working
- Camera auto-scan working
- Dynamic link/unlink working
- Camera health monitoring working
- Tailgating detection working
- Cross-camera event linking working
- Attendance stats working
- Zone management working

---

## Phase 4: Frontend & Integration (Estimated: 2.5 hours)

### Goal
Build both screens (Camera View + Admin Portal) and integrate with backend.

### Tasks

| # | Task | File | Est. Time |
|---|---|---|---|
| 4.1 | Camera Screen: index.html - Camera feed + EmployeeID input | camera_screen/index.html | 15 min |
| 4.2 | Camera Screen: style.css - Minimal styling | camera_screen/style.css | 10 min |
| 4.3 | Camera Screen: script.js - API calls + display results | camera_screen/script.js | 20 min |
| 4.4 | Admin Portal: React setup (Vite + Tailwind) | admin_portal/ | 15 min |
| 4.5 | Admin Portal: Login page | admin_portal/src/pages/Login.jsx | 15 min |
| 4.6 | Admin Portal: Dashboard page | admin_portal/src/pages/Dashboard.jsx | 20 min |
| 4.7 | Admin Portal: AddEmployee page | admin_portal/src/pages/AddEmployee.jsx | 25 min |
| 4.8 | Admin Portal: EmployeeList page | admin_portal/src/pages/EmployeeList.jsx | 20 min |
| 4.9 | Admin Portal: AccessLogs page | admin_portal/src/pages/AccessLogs.jsx | 15 min |
| 4.10 | Admin Portal: CameraManagement page | admin_portal/src/pages/CameraManagement.jsx | 20 min |
| 4.11 | Admin Portal: CameraHealth page | admin_portal/src/pages/CameraHealth.jsx | 15 min |
| 4.12 | Admin Portal: ZoneMapping page | admin_portal/src/pages/ZoneMapping.jsx | 15 min |
| 4.13 | Admin Portal: API client (api.js) | admin_portal/src/api.js | 10 min |
| 4.14 | Docker: Dockerfiles + docker-compose.yml | docker/, docker-compose.yml | 20 min |
| 4.15 | Integration testing | tests/ | 20 min |

### Deliverables
- Camera Screen fully functional
- Admin Portal fully functional
- Docker deployment working
- Integration tests passing

---

## Phase Summary

| Phase | Focus | Est. Time | Dependencies |
|---|---|---|---|
| Phase 1 | Foundation | 2 hours | None |
| Phase 2 | Core AI | 3 hours | Phase 1 |
| Phase 3 | Camera + Security | 2.5 hours | Phase 2 |
| Phase 4 | Frontend + Integration | 2.5 hours | Phase 3 |
| **Total** | | **10 hours** | |

---

## Milestone Checkpoints

### After Phase 1
- [ ] Redis connection working
- [ ] Database indexes created
- [ ] JWT auth working
- [ ] API documentation accessible at /docs

### After Phase 2
- [ ] Employee registration working
- [ ] Face verification returning correct match/no-match
- [ ] Body verification returning correct match/no-match
- [ ] Camera capture capturing frames
- [ ] /api/verify endpoint returning GRANTED/DENIED

### After Phase 3
- [ ] Camera list displaying in API
- [ ] Camera link/unlink working
- [ ] Camera health status updating
- [ ] Tailgate alert triggering when >1 person detected
- [ ] Cross-camera timeline showing in API

### After Phase 4
- [ ] Camera Screen showing live feed + verification
- [ ] Admin Dashboard showing attendance stats
- [ ] Add Employee page capturing face+body
- [ ] Camera Management page linking/unlinking cameras
- [ ] Docker Compose starting all services
- [ ] Full flow working end-to-end

---

## Risk Assessment

| Risk | Impact | Mitigation |
|---|---|---|
| InsightFace model download fails | HIGH | Pre-download models, cache locally |
| Redis connection issues | HIGH | Test Redis setup first, have fallback |
| Camera RTSP stream issues | MEDIUM | Support USB webcam as fallback |
| YOLOv8 slow on CPU | MEDIUM | Use YOLOv8n (nano) for speed |
| React build issues | LOW | Use Vite, minimal config |
| Docker build issues | LOW | Test Dockerfiles early |

---

## Testing Strategy

### Unit Tests
- test_face_verify.py - Face comparison accuracy
- test_body_verify.py - Body comparison accuracy
- test_decision.py - Decision logic
- test_camera_health.py - Health monitoring
- test_tailgate.py - Tailgating detection

### Integration Tests
- Full verification flow (register -> verify -> grant/deny)
- Camera management flow (add -> link -> health check)
- Admin portal flow (login -> dashboard -> add employee)

### Manual Tests
- Camera Screen on actual device
- Admin Portal in browser
- Docker Compose deployment
- Multi-camera scenario
