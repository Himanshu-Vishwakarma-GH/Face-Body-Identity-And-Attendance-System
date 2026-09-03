import logging
import numpy as np
from typing import Optional, Tuple, Dict, Any
from backend.config import settings

logger = logging.getLogger("ai_access.body_verify")

class BodyEngine:
    """Extracts anthropometric body keypoints and ratios for secondary 1:1 physical verification."""
    _instance: Optional["BodyEngine"] = None

    def __init__(self):
        self.yolo_pose = None
        self._initialized = False

    @classmethod
    def get_instance(cls) -> "BodyEngine":
        if cls._instance is None:
            cls._instance = BodyEngine()
        return cls._instance

    def initialize(self):
        """Initializes pose estimation model."""
        if self._initialized:
            return
        try:
            from ultralytics import YOLO
            # Fast, lightweight nano pose model
            logger.info("Initializing YOLOv8n-pose model for body dimension analysis...")
            self.yolo_pose = YOLO("yolov8n-pose.pt")
            self._initialized = True
            logger.info("Pose estimation model ready.")
        except Exception as e:
            logger.error("Failed to initialize body pose engine: %s", e)
            self._initialized = False

    def extract_body_features(self, image: np.ndarray) -> Optional[Dict[str, Any]]:
        """Extracts anthropometric measurements and normalized 256-dim feature vector from person."""
        if not self._initialized:
            self.initialize()

        if self.yolo_pose is None or image is None:
            return None

        try:
            results = self.yolo_pose(image, verbose=False)
            if not results or len(results[0].boxes) == 0:
                logger.warning("No person detected for body dimension analysis")
                return None

            # Select largest person by bounding box
            boxes = results[0].boxes.xyxy.cpu().numpy()
            areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
            best_idx = int(np.argmax(areas))

            bbox = boxes[best_idx]
            bbox_w = float(bbox[2] - bbox[0])
            bbox_h = float(bbox[3] - bbox[1])
            aspect_ratio = bbox_w / max(1.0, bbox_h)

            # Keypoints: (17, 3) or (17, 2)
            keypoints_data = results[0].keypoints
            if keypoints_data is None or len(keypoints_data.xy) == 0:
                return None

            kpts = keypoints_data.xy[best_idx].cpu().numpy()  # (17, 2)

            # Standard COCO Keypoint Indices:
            # 5: left_shoulder, 6: right_shoulder, 11: left_hip, 12: right_hip
            left_shoulder = kpts[5] if len(kpts) > 5 else np.array([0, 0])
            right_shoulder = kpts[6] if len(kpts) > 6 else np.array([0, 0])
            left_hip = kpts[11] if len(kpts) > 11 else np.array([0, 0])
            right_hip = kpts[12] if len(kpts) > 12 else np.array([0, 0])

            shoulder_width = float(np.linalg.norm(left_shoulder - right_shoulder))
            hip_width = float(np.linalg.norm(left_hip - right_hip))

            mid_shoulder = (left_shoulder + right_shoulder) / 2.0
            mid_hip = (left_hip + right_hip) / 2.0
            torso_height = float(np.linalg.norm(mid_shoulder - mid_hip))

            # Scale-invariant ratios (normalized by torso height and bbox)
            ref_torso = max(10.0, torso_height)
            shoulder_ratio = shoulder_width / ref_torso
            hip_ratio = hip_width / ref_torso
            torso_to_body = ref_torso / max(20.0, bbox_h)

            # Flatten normalized keypoints relative to bounding box
            norm_kpts = (kpts - [bbox[0], bbox[1]]) / [max(1.0, bbox_w), max(1.0, bbox_h)]
            kpt_flat = norm_kpts.flatten()

            # Pad or project into fixed 256-dim embedding vector
            embedding_256 = np.zeros(256, dtype=np.float32)
            embedding_256[:min(len(kpt_flat), 256)] = kpt_flat[:min(len(kpt_flat), 256)]
            # Include scale-invariant summary scalars in vector header
            embedding_256[0] = shoulder_ratio
            embedding_256[1] = hip_ratio
            embedding_256[2] = torso_to_body
            embedding_256[3] = aspect_ratio

            norm = np.linalg.norm(embedding_256)
            if norm > 0:
                embedding_256 = embedding_256 / norm

            return {
                "embedding": embedding_256,
                "body_height": round(bbox_h, 1),
                "body_shoulder": round(shoulder_ratio, 3),
                "body_torso": round(torso_to_body, 3),
                "aspect_ratio": round(aspect_ratio, 3),
            }
        except Exception as e:
            logger.error("Body feature extraction failed: %s", e)
            return None

    def verify_1_to_1(
        self,
        stored_embedding: np.ndarray,
        captured_image: np.ndarray,
        threshold: Optional[float] = None
    ) -> Tuple[bool, float]:
        """Performs 1:1 body verification of captured image against stored body embedding."""
        th = threshold if threshold is not None else settings.BODY_DISTANCE_THRESHOLD
        features = self.extract_body_features(captured_image)
        if features is None:
            return False, 0.0

        captured_embedding = features["embedding"]
        # Cosine distance or euclidean distance
        dist = float(np.linalg.norm(stored_embedding - captured_embedding))
        # Convert distance to confidence percentage (dist near 0 = 100%, dist >= 1.0 = 0%)
        confidence = max(0.0, min(1.0, 1.0 - (dist / 1.414)))
        is_match = bool(dist <= th or confidence >= 0.70)
        return is_match, round(confidence, 4)

body_engine = BodyEngine.get_instance()
