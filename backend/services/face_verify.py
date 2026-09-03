import logging
import numpy as np
from typing import Optional, Tuple, Dict, Any
from backend.config import settings

logger = logging.getLogger("ai_access.face_verify")

class FaceEngine:
    """Manages InsightFace model initialization and 1:1 facial verification."""
    _instance: Optional["FaceEngine"] = None

    def __init__(self):
        self.app = None
        self._initialized = False

    @classmethod
    def get_instance(cls) -> "FaceEngine":
        if cls._instance is None:
            cls._instance = FaceEngine()
        return cls._instance

    def initialize(self):
        """Lazy loader for InsightFace FaceAnalysis model."""
        if self._initialized:
            return
        try:
            import insightface
            from insightface.app import FaceAnalysis

            logger.info("Initializing InsightFace (buffalo_sc) model...")
            self.app = FaceAnalysis(
                name="buffalo_sc",
                root=settings.MODELS_DIR,
                providers=["CPUExecutionProvider"]
            )
            self.app.prepare(ctx_id=0, det_size=(640, 640))
            self._initialized = True
            logger.info("InsightFace FaceAnalysis ready.")
        except Exception as e:
            logger.error("Failed to initialize InsightFace: %s", e)
            self._initialized = False

    def extract_embedding(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Extracts normalized 512-dimension face embedding from image."""
        if not self._initialized:
            self.initialize()

        if self.app is None or image is None:
            return None

        try:
            faces = self.app.get(image)
            if not faces:
                logger.warning("No face detected in the provided image")
                return None

            # Pick largest face by bounding box area if multiple faces detected
            largest_face = max(
                faces,
                key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1])
            )
            embedding = largest_face.embedding
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            return embedding.astype(np.float32)
        except Exception as e:
            logger.error("Face embedding extraction error: %s", e)
            return None

    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculates cosine similarity between two normalized embeddings."""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        similarity = float(np.dot(vec1, vec2) / (norm1 * norm2))
        # Clamp to range [0.0, 1.0]
        return max(0.0, min(1.0, (similarity + 1.0) / 2.0 if similarity < 0 else similarity))

    def verify_1_to_1(
        self,
        stored_embedding: np.ndarray,
        captured_image: np.ndarray,
        threshold: Optional[float] = None
    ) -> Tuple[bool, float]:
        """Performs 1:1 face verification of captured image against stored embedding."""
        th = threshold if threshold is not None else settings.FACE_SIMILARITY_THRESHOLD
        captured_embedding = self.extract_embedding(captured_image)
        if captured_embedding is None:
            return False, 0.0

        similarity = self.cosine_similarity(stored_embedding, captured_embedding)
        is_match = bool(similarity >= th)
        return is_match, round(similarity, 4)

face_engine = FaceEngine.get_instance()
