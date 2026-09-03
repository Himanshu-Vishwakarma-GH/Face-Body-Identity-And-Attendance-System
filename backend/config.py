import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # Application
    PROJECT_NAME: str = "AI Based Face & Body Detection Access Control System"
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_SSL: bool = False
    REDIS_FALLBACK_MEMORY: bool = True

    # Security & Cryptography
    AES_KEY: str = "dGhpcy1pcy1hLTMyLWJ5dGUtc2VjcmV0LWtleS1mb3ItYWVzIQ=="
    JWT_SECRET: str = "super-secret-jwt-signing-key-for-ibm-hackathon-2026-replace-in-prod"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440

    # Initial Admin Setup
    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_PASSWORD: str = "AdminPassword123!"
    DEFAULT_ADMIN_EMAIL: str = "admin@security.local"

    # AI Verification Thresholds
    FACE_SIMILARITY_THRESHOLD: float = 0.60
    BODY_DISTANCE_THRESHOLD: float = 0.35
    TAILGATE_DETECTION_WINDOW_SEC: int = 5
    PERSON_CONFIDENCE_THRESHOLD: float = 0.50

    # Camera & Heartbeat
    CAMERA_HEARTBEAT_INTERVAL_SEC: int = 30
    CAMERA_TIMEOUT_THRESHOLD_SEC: int = 120
    DEFAULT_CAMERA_ID: str = "CAM-01"
    DEFAULT_CAMERA_RTSP: str = "0"

    # Storage Paths
    DATA_DIR: str = str(BASE_DIR / "data")
    FACES_DIR: str = str(BASE_DIR / "data" / "faces")
    MODELS_DIR: str = str(BASE_DIR / "ml" / "models")

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_aes_key_bytes(self) -> bytes:
        import base64
        try:
            key_bytes = base64.b64decode(self.AES_KEY)
            if len(key_bytes) == 32:
                return key_bytes
        except Exception:
            pass
        # Fallback to 32 bytes derived from AES_KEY string
        import hashlib
        return hashlib.sha256(self.AES_KEY.encode()).digest()

settings = Settings()

# Ensure required storage directories exist
os.makedirs(settings.DATA_DIR, exist_ok=True)
os.makedirs(settings.FACES_DIR, exist_ok=True)
os.makedirs(settings.MODELS_DIR, exist_ok=True)
