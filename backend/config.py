"""
GUARDZILLA Configuration Management
Centralized settings for the security system
"""

from pydantic_settings import BaseSettings
from typing import Optional, Dict
import os


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    Use environment variables to override defaults.
    """
    
    # ==================== DATABASE ====================
    DATABASE_URL: str = "sqlite:///./guardzilla.db"
    
    # ==================== VIDEO SETTINGS ====================
    CAMERA_INDEX: int = 0  # Default camera device
    VIDEO_WIDTH: int = 1280
    VIDEO_HEIGHT: int = 720
    VIDEO_FPS: int = 30
    
    # ==================== AI MODEL PATHS ====================
    YOLO_MODEL_PATH: str = "models/yolov8n-face.pt"
    RECOGNITION_MODEL: str = "arcface"  # Options: "arcface", "facenet"
    MODEL_CONFIDENCE_THRESHOLD: float = 0.5
    RECOGNITION_THRESHOLD: float = 0.6  # Cosine similarity threshold
    
    # ==================== MOTOR PIN CONFIGURATION ====================
    GPIO_ENABLED: bool = False  # Set to True on Raspberry Pi
    
    MOTOR_PIN_CONFIG: Dict = {
        "motor_1": {"IN1": 17, "IN2": 27, "ENA": 22},
        "motor_2": {"IN3": 23, "IN4": 24, "ENB": 25},
        "motor_3": {"IN5": 5, "IN6": 6, "ENC": 12},
        "motor_4": {"IN7": 13, "IN8": 19, "END": 26},
        "buzzer": 16
    }
    
    MOTOR_PWM_FREQUENCY: int = 1000  # Hz
    MOTOR_DEFAULT_SPEED: int = 128  # 0-255
    
    # ==================== TRACKING SETTINGS ====================
    TRACKING_CONFIDENCE: float = 0.4
    MAX_TRACKING_AGE: int = 30  # frames
    MIN_HITS: int = 3  # frames before confirmed detection
    IOU_THRESHOLD: float = 0.3
    
    # ==================== ALERT SETTINGS ====================
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    ALERT_EMAIL: str = os.getenv("ALERT_EMAIL", "")
    ALERT_EMAIL_PASSWORD: str = os.getenv("ALERT_EMAIL_PASSWORD", "")
    ALERT_RECIPIENT_EMAIL: str = os.getenv("ALERT_RECIPIENT_EMAIL", "")
    
    # Alert behavior
    ENABLE_EMAIL_ALERTS: bool = True
    ALERT_COOLDOWN_SECONDS: int = 300  # Prevent alert spam
    INCLUDE_VIDEO_IN_ALERT: bool = True
    VIDEO_CLIP_DURATION: int = 5  # seconds
    
    # ==================== VIDEO CLIP STORAGE ====================
    STORAGE_TYPE: str = "local"  # Options: "local", "s3"
    LOCAL_STORAGE_PATH: str = "./storage/clips"
    AWS_S3_BUCKET: str = os.getenv("AWS_S3_BUCKET", "")
    AWS_ACCESS_KEY: str = os.getenv("AWS_ACCESS_KEY", "")
    AWS_SECRET_KEY: str = os.getenv("AWS_SECRET_KEY", "")
    
    # ==================== LOGGING ====================
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/guardzilla.log"
    
    # ==================== SERVER ====================
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4
    
    # ==================== DETECTION SETTINGS ====================
    DETECTION_MODE: str = "unknown_only"  # Options: "all", "unknown_only", "intruders"
    ENABLE_AUTO_TRACKING: bool = True
    TRACK_ON_DETECTION: bool = True
    
    # ==================== SYSTEM ====================
    DEBUG: bool = False
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def dict(self, **kwargs):
        """Return settings as dictionary, excluding sensitive data."""
        data = super().dict(**kwargs)
        # Remove sensitive fields
        sensitive_fields = [
            "ALERT_EMAIL_PASSWORD",
            "AWS_SECRET_KEY",
            "AWS_ACCESS_KEY"
        ]
        for field in sensitive_fields:
            if field in data:
                data[field] = "***hidden***"
        return data


# Create singleton instance
settings = Settings()

# Ensure required directories exist
os.makedirs(settings.LOCAL_STORAGE_PATH, exist_ok=True)
os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)
os.makedirs("models", exist_ok=True)
os.makedirs("storage/faces", exist_ok=True)
