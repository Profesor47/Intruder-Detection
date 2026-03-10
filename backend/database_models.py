"""
SQLAlchemy database models for GUARDZILLA.
Stores known faces, detection history, and system logs.
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, LargeBinary, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from config import settings

# Database setup
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class KnownFace(Base):
    """Stores information about known/authorized people."""
    __tablename__ = "known_faces"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    person_id = Column(String(36), unique=True, index=True)
    
    # Face embedding (numpy array serialized as binary)
    embedding = Column(LargeBinary, nullable=True)
    embedding_version = Column(String(50), default="arcface_r100")
    
    # Metadata
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    role = Column(String(50), default="resident")  # resident, guard, staff, etc.
    
    # Face image for preview
    face_image = Column(LargeBinary, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Active/Inactive status
    is_active = Column(Boolean, default=True, index=True)
    
    # Relationships
    detections = relationship("Detection", back_populates="person", cascade="all, delete-orphan")
    enrollment_images = relationship("EnrollmentImage", back_populates="person", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<KnownFace(id={self.id}, name={self.name})>"


class EnrollmentImage(Base):
    """Stores multiple face images for a single person during enrollment."""
    __tablename__ = "enrollment_images"
    
    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("known_faces.id"), nullable=False, index=True)
    
    # Image data
    image_data = Column(LargeBinary, nullable=False)
    embedding = Column(LargeBinary, nullable=True)
    
    # Quality metrics
    quality_score = Column(Float, default=0.0)
    face_angle = Column(String(50), default="frontal")  # frontal, left, right, up, down
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationship
    person = relationship("KnownFace", back_populates="enrollment_images")
    
    def __repr__(self):
        return f"<EnrollmentImage(id={self.id}, person_id={self.person_id})>"


class Detection(Base):
    """Logs all detected faces and intruders."""
    __tablename__ = "detections"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Detection info
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    track_id = Column(Integer, index=True)  # For multi-object tracking
    
    # Face classification
    person_id = Column(Integer, ForeignKey("known_faces.id"), nullable=True, index=True)
    is_known = Column(Boolean, default=False, index=True)
    is_intruder = Column(Boolean, default=False, index=True)
    confidence = Column(Float, default=0.0)  # Detection confidence
    recognition_score = Column(Float, nullable=True)  # Face recognition similarity
    
    # Frame info
    frame_index = Column(Integer)
    face_bbox = Column(String(255))  # "x1,y1,x2,y2" format
    
    # Image data
    face_snapshot = Column(LargeBinary, nullable=True)  # Cropped face image
    embedding = Column(LargeBinary, nullable=True)
    
    # Alert info
    alert_sent = Column(Boolean, default=False, index=True)
    alert_type = Column(String(50), nullable=True)  # "intruder", "suspicious", "known"
    video_clip_path = Column(String(512), nullable=True)
    
    # Location info (if applicable)
    location = Column(String(255), nullable=True)
    motor_position = Column(String(50), nullable=True)  # "center", "left", "right", etc.
    
    # Relationship
    person = relationship("KnownFace", back_populates="detections")
    
    def __repr__(self):
        return f"<Detection(id={self.id}, timestamp={self.timestamp}, is_intruder={self.is_intruder})>"


class SystemLog(Base):
    """Logs system events, errors, and operations."""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    log_level = Column(String(20), index=True)  # INFO, WARNING, ERROR, CRITICAL
    component = Column(String(100))  # video_capture, detection, tracking, motor, etc.
    message = Column(Text)
    error_details = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<SystemLog(id={self.id}, level={self.log_level}, component={self.component})>"


class AlertLog(Base):
    """Tracks all alerts sent to users."""
    __tablename__ = "alert_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    detection_id = Column(Integer, ForeignKey("detections.id"), nullable=True, index=True)
    
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    alert_type = Column(String(50))  # "intruder", "suspicious", "system"
    alert_method = Column(String(50))  # "email", "sms", "in_app", "buzzer"
    
    recipient = Column(String(255))
    subject = Column(String(255))
    message = Column(Text)
    
    sent_successfully = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<AlertLog(id={self.id}, type={self.alert_type}, sent={self.sent_successfully})>"


class SystemConfig(Base):
    """Stores runtime system configuration."""
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True)
    value = Column(Text)
    description = Column(String(500), nullable=True)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<SystemConfig(key={self.key}, value={self.value})>"


# Create all tables
def init_db():
    """Initialize database by creating all tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for FastAPI to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
