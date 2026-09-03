import time
import logging
import numpy as np
from typing import Optional, Tuple, List, Dict, Any

from backend.config import settings
from backend.models import TailgateAlert
from backend.database import db

logger = logging.getLogger("ai_access.tailgate")

class TailgateDetector:
    """Detects multiple persons in frame during access swipe window using YOLOv8."""
    _instance: Optional["TailgateDetector"] = None

    def __init__(self):
        self.yolo_model = None
        self._initialized = False
        # Window tracker: camera_id -> list of swipe timestamps
        self._swipe_windows: Dict[str, List[float]] = {}

    @classmethod
    def get_instance(cls) -> "TailgateDetector":
        if cls._instance is None:
            cls._instance = TailgateDetector()
        return cls._instance

    def initialize(self):
        if self._initialized:
            return
        try:
            from ultralytics import YOLO
            logger.info("Initializing YOLOv8n detector for person & tailgating detection...")
            self.yolo_model = YOLO("yolov8n.pt")
            self._initialized = True
            logger.info("YOLOv8n object detector ready.")
        except Exception as e:
            logger.error("Failed to initialize YOLO detector: %s", e)
            self._initialized = False

    def record_card_swipe(self, camera_id: str) -> int:
        """Records a card swipe event and returns active swipe count in current 5-second window."""
        now = time.time()
        window_sec = settings.TAILGATE_DETECTION_WINDOW_SEC

        if camera_id not in self._swipe_windows:
            self._swipe_windows[camera_id] = []

        # Prune expired timestamps
        self._swipe_windows[camera_id] = [
            ts for ts in self._swipe_windows[camera_id] if (now - ts) <= window_sec
        ]
        self._swipe_windows[camera_id].append(now)
        return len(self._swipe_windows[camera_id])

    def count_persons_in_frame(
        self,
        frame: np.ndarray,
        conf_threshold: Optional[float] = None
    ) -> Tuple[int, List[List[float]]]:
        """Runs YOLOv8 object detection filtered to COCO class 0 (Person)."""
        if not self._initialized:
            self.initialize()

        if self.yolo_model is None or frame is None:
            return 0, []

        th = conf_threshold if conf_threshold is not None else settings.PERSON_CONFIDENCE_THRESHOLD

        try:
            # Predict only class 0 (person)
            results = self.yolo_model(frame, classes=[0], conf=th, verbose=False)
            if not results or len(results[0].boxes) == 0:
                return 0, []

            boxes = results[0].boxes.xyxy.cpu().numpy().tolist()
            return len(boxes), boxes
        except Exception as e:
            logger.error("Person detection failed: %s", e)
            return 0, []

    def check_tailgate(
        self,
        camera_id: str,
        frame: Optional[np.ndarray],
        card_swipes: int = 1
    ) -> Tuple[bool, int, Optional[TailgateAlert]]:
        """
        Decision logic for tailgating:
        - person_count > 1 AND card_swipes == 1 -> TAILGATE ALERT!
        - person_count == 0 AND card_swipes > 0 -> TIMEOUT / GHOST SWIPE ALERT
        - person_count <= card_swipes -> NORMAL
        """
        if frame is None:
            return False, 0, None

        cam_record = db.get_json(f"cam:{camera_id}") or {}
        zone = cam_record.get("zone", "Entry Zone")

        person_count, bboxes = self.count_persons_in_frame(frame)
        now = time.time()

        if person_count > card_swipes and card_swipes > 0:
            alert = TailgateAlert(
                camera_id=camera_id,
                zone=zone,
                person_count=person_count,
                card_swipes=card_swipes,
                timestamp=now,
                message=f"SECURITY ALERT: Tailgating detected! {person_count} persons detected for {card_swipes} card swipe(s) in {zone} ({camera_id})"
            )
            # Persist alert in Redis
            db.set_json(f"tailgate:{alert.alert_id}", alert.model_dump())
            logger.warning("Tailgate event triggered at %s: %d persons detected", camera_id, person_count)
            return True, person_count, alert

        return False, person_count, None

tailgate_detector = TailgateDetector.get_instance()
