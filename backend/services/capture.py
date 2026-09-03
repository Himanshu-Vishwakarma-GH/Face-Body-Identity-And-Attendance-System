import cv2
import numpy as np
import base64
import logging
from typing import Optional, Tuple, Dict, List, Any
from pathlib import Path

logger = logging.getLogger("ai_access.capture")

def decode_base64_image(base64_str: str) -> Optional[np.ndarray]:
    """Decodes a base64 encoded image string (with or without data URI prefix) to an OpenCV BGR image."""
    try:
        if "," in base64_str:
            base64_str = base64_str.split(",", 1)[1]
        img_bytes = base64.b64decode(base64_str)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        logger.error("Failed to decode base64 image: %s", e)
        return None

def encode_image_to_base64(image: np.ndarray, format: str = ".jpg") -> str:
    """Encodes an OpenCV BGR image to base64 jpeg data string."""
    success, buffer = cv2.imencode(format, image)
    if not success:
        raise ValueError("Failed to encode image to base64")
    return base64.b64encode(buffer).decode("utf-8")

class CameraCapture:
    """Handles camera frame acquisition via USB webcam index, RTSP stream URL, or file path."""
    def __init__(self, camera_source: str = "0"):
        self.camera_source = camera_source
        self._cap: Optional[cv2.VideoCapture] = None

    def _get_capture_device(self) -> Optional[cv2.VideoCapture]:
        try:
            # Check if integer webcam index (e.g. '0', '1')
            if self.camera_source.isdigit():
                cap = cv2.VideoCapture(int(self.camera_source))
            else:
                cap = cv2.VideoCapture(self.camera_source)
            if cap.isOpened():
                return cap
        except Exception as e:
            logger.warning("Could not open camera '%s': %s", self.camera_source, e)
        return None

    def capture_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Captures a single frame from the camera stream."""
        cap = self._get_capture_device()
        if cap is None:
            return False, None
        try:
            ret, frame = cap.read()
            cap.release()
            if ret and frame is not None:
                return True, frame
        except Exception as e:
            logger.error("Error reading frame from '%s': %s", self.camera_source, e)
            try:
                cap.release()
            except Exception:
                pass
        return False, None

# Phone Camera Buffer for local Wi-Fi transmission
PHONE_CAMERA_BUFFERS: Dict[str, Tuple[float, bytes]] = {}

def update_phone_frame(camera_id: str, frame_bytes: bytes):
    """Updates the latest frame received from a mobile phone camera on the local network."""
    PHONE_CAMERA_BUFFERS[camera_id] = (time.time(), frame_bytes)

def get_phone_frame(camera_id: str) -> Optional[bytes]:
    """Retrieves the latest frame from a mobile phone stream if received within the last 10 seconds."""
    if camera_id in PHONE_CAMERA_BUFFERS:
        ts, data = PHONE_CAMERA_BUFFERS[camera_id]
        if (time.time() - ts) < 10.0:
            return data
    return None

def detect_usb_cameras(max_devices: int = 4) -> List[Dict[str, Any]]:
    """Probes USB and integrated webcams on the host system."""
    detected = []
    for idx in range(max_devices):
        try:
            cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap = cv2.VideoCapture(idx)

            if cap.isOpened():
                ret, frame = cap.read()
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
                cap.release()

                detected.append({
                    "index": idx,
                    "name": f"USB / Integrated Camera {idx}" if idx > 0 else "Primary / Built-in Camera (Index 0)",
                    "resolution": f"{w}x{h}",
                    "available": bool(ret and frame is not None)
                })
        except Exception as e:
            logger.debug("Probe failed for camera index %d: %s", idx, e)
    return detected

def get_frame(source_param: Optional[str] = None, frame_base64: Optional[str] = None) -> Tuple[bool, Optional[np.ndarray], str]:
    """Unified helper to acquire a frame from base64 input, phone buffer, camera source, or test fallback."""
    # 1. Base64 payload supplied directly by web client
    if frame_base64:
        img = decode_base64_image(frame_base64)
        if img is not None:
            return True, img, "base64_client_frame"

    # 2. Local Phone Wi-Fi Stream
    if source_param and source_param.startswith("phone:"):
        phone_id = source_param.split("phone:", 1)[1]
        raw_bytes = get_phone_frame(phone_id)
        if raw_bytes:
            nparr = np.frombuffer(raw_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is not None:
                return True, img, f"phone_stream:{phone_id}"

    # 3. Local/RTSP camera stream
    if source_param:
        cap = CameraCapture(source_param)
        success, frame = cap.capture_frame()
        if success and frame is not None:
            return True, frame, f"camera_source:{source_param}"

    # 4. If file path
    if source_param and Path(source_param).is_file():
        img = cv2.imread(source_param)
        if img is not None:
            return True, img, f"file:{source_param}"

    return False, None, "no_frame_available"

import time

def probe_camera_source(source: str) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
    """Probes a camera source, returning (success, error_msg, preview_base64, resolution)."""
    try:
        src = int(source) if source.isdigit() else source
        cap = cv2.VideoCapture(src)

        if not cap.isOpened():
            return False, "Could not open camera stream. Check index, URL or permissions.", None, None

        ret, frame = cap.read()
        cap.release()
        if ret and frame is not None:
            h, w = frame.shape[:2]
            preview_b64 = encode_image_to_base64(frame)
            return True, None, f"data:image/jpeg;base64,{preview_b64}", f"{w}x{h}"
        return False, "Connected to camera device, but could not capture video frame.", None, None
    except Exception as e:
        logger.error("Error probing camera source '%s': %s", source, e)
        return False, str(e), None, None

def generate_camera_frames(source: str):
    """Yields multipart JPEG frames for live HTTP MJPEG streaming with graceful standby HUD fallback."""
    if source.startswith("phone:"):
        phone_id = source.split("phone:", 1)[1]
        while True:
            raw_bytes = get_phone_frame(phone_id)
            if raw_bytes:
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" + raw_bytes + b"\r\n")
                time.sleep(0.06)
            else:
                standby = np.zeros((360, 480, 3), dtype=np.uint8)
                standby[:] = (18, 14, 10)
                t_str = time.strftime("%H:%M:%S")
                cv2.putText(standby, f"PHONE CAM: {phone_id}", (30, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (220, 230, 245), 2)
                cv2.putText(standby, "AWAITING PHONE TRANSMISSION...", (30, 185), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (16, 185, 129), 1)
                cv2.putText(standby, f"TELEMETRY TIME: {t_str}", (30, 215), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (100, 120, 145), 1)
                _, buffer = cv2.imencode(".jpg", standby)
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")
                time.sleep(0.5)

    src = int(source) if source.isdigit() else source
    cap = cv2.VideoCapture(src)

    try:
        consecutive_failures = 0
        while True:
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    consecutive_failures = 0
                    success, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 65])
                    if success:
                        yield (b"--frame\r\n"
                               b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")
                        time.sleep(0.04)
                        continue

            consecutive_failures += 1
            # Standby HUD frame
            standby = np.zeros((360, 480, 3), dtype=np.uint8)
            standby[:] = (18, 14, 10)
            t_str = time.strftime("%H:%M:%S")
            cv2.putText(standby, f"CAM SOURCE: {source}", (30, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (220, 230, 245), 2)
            cv2.putText(standby, "OPTICAL SENSOR ACTIVE [STANDBY]", (30, 185), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (16, 185, 129), 1)
            cv2.putText(standby, f"TELEMETRY TIME: {t_str}", (30, 215), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (100, 120, 145), 1)
            _, buffer = cv2.imencode(".jpg", standby)
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")
            time.sleep(0.5)

            if consecutive_failures % 10 == 0:
                try:
                    cap.release()
                    cap = cv2.VideoCapture(src)
                except Exception:
                    pass
    finally:
        try:
            cap.release()
        except Exception:
            pass
