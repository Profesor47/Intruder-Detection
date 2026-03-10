"""
GUARDZILLA - Modern AI-Powered Security System
FastAPI Backend Server for Real-time Face Detection, Recognition, and Tracking
"""

from fastapi import FastAPI, WebSocket, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging
import os
import json
from datetime import datetime
from typing import Optional, List
import numpy as np
import cv2

# Import core modules
from core.video_capture import VideoCapture
from core.face_detection import FaceDetector
from core.face_recognition import FaceRecognizer
from core.intruder_tracking import IntruderTracker
from core.motor_control import MotorController
from database_models import init_db, get_db, KnownFace, Detection, AlertLog, SystemLog
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
video_capture: Optional[VideoCapture] = None
face_detector: Optional[FaceDetector] = None
face_recognizer: Optional[FaceRecognizer] = None
intruder_tracker: Optional[IntruderTracker] = None
motor_controller: Optional[MotorController] = None

# Application state
current_frame = None
current_detections = []
system_status = {"status": "initializing", "fps": 0, "last_detection": None}

# Mock service classes
class MockStreamService:
    """Placeholder for stream annotation service"""
    @staticmethod
    def annotate_frame(frame, detections):
        return frame

class MockDatabaseService:
    """Placeholder for database service"""
    def get_alerts(self, limit=50):
        return {
            "alerts": [
                {"id": "1", "type": "unknown_person", "timestamp": datetime.now().isoformat(), "confidence": 0.95},
                {"id": "2", "type": "motion_detected", "timestamp": datetime.now().isoformat(), "confidence": 0.87}
            ],
            "total": 2
        }
    
    def get_detections(self, limit=100, offset=0, person_id=None):
        return {
            "detections": [
                {"id": "1", "person_id": person_id or "unknown", "confidence": 0.92, "timestamp": datetime.now().isoformat()},
                {"id": "2", "person_id": person_id or "guest", "confidence": 0.88, "timestamp": datetime.now().isoformat()}
            ],
            "total": 2
        }
    
    def count_detections(self):
        return 2
    
    def save_known_face(self, name, embedding):
        return f"person_{hash(name) % 10000}"
    
    def get_known_faces(self):
        return [
            {"person_id": "1", "name": "John Doe", "confidence": 0.98},
            {"person_id": "2", "name": "Jane Smith", "confidence": 0.96}
        ]
    
    def delete_known_face(self, person_id):
        return True

class MockAlertService:
    """Placeholder for alert service"""
    def send_test_alert(self, recipient):
        logger.info(f"Test alert would be sent to {recipient}")
        return True

# Initialize mock services
stream_service = MockStreamService()
database_service = MockDatabaseService()
alert_service = MockAlertService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown lifecycle.
    Initialize AI models and hardware on startup.
    """
    global video_capture, face_detector, face_recognizer, intruder_tracker
    global motor_controller
    
    logger.info("=" * 60)
    logger.info("Starting GUARDZILLA system initialization...")
    logger.info("=" * 60)
    
    try:
        # Initialize database
        init_db()
        logger.info("✓ Database initialized")
        
        # Initialize video capture
        video_capture = VideoCapture(
            camera_index=settings.CAMERA_INDEX,
            width=settings.VIDEO_WIDTH,
            height=settings.VIDEO_HEIGHT,
            fps=settings.VIDEO_FPS
        )
        logger.info("✓ Video capture initialized")
        
        # Initialize AI models
        face_detector = FaceDetector(
            model_path=settings.YOLO_MODEL_PATH,
            confidence=settings.MODEL_CONFIDENCE_THRESHOLD
        )
        logger.info("✓ Face detector loaded")
        
        face_recognizer = FaceRecognizer(
            model_name=settings.RECOGNITION_MODEL,
            threshold=settings.RECOGNITION_THRESHOLD
        )
        logger.info("✓ Face recognizer loaded")
        
        intruder_tracker = IntruderTracker(
            frame_width=settings.VIDEO_WIDTH,
            frame_height=settings.VIDEO_HEIGHT
        )
        logger.info("✓ Intruder tracker initialized")
        
        # Initialize motor controller
        motor_controller = MotorController(
            pin_config=settings.MOTOR_PIN_CONFIG,
            enable_gpio=settings.GPIO_ENABLED
        )
        logger.info("✓ Motor controller initialized")
        
        system_status["status"] = "ready"
        logger.info("=" * 60)
        logger.info("✓ GUARDZILLA system ready!")
        logger.info("=" * 60)
        
        yield
        
    except Exception as e:
        logger.error(f"Initialization error: {str(e)}")
        system_status["status"] = "error"
        raise
    
    finally:
        # Cleanup on shutdown
        logger.info("Shutting down GUARDZILLA system...")
        if video_capture:
            video_capture.stop()
        if motor_controller:
            motor_controller.stop_all()
        logger.info("System shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="GUARDZILLA API",
    description="Modern AI-Powered Security System",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== STATUS & MONITORING ====================

@app.get("/api/status")
async def get_status():
    """Get current system status and metrics."""
    return {
        "status": system_status["status"],
        "timestamp": datetime.now().isoformat(),
        "fps": system_status.get("fps", 0),
        "last_detection": system_status.get("last_detection"),
        "uptime": "N/A"  # Will be calculated from database
    }


@app.get("/api/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy"}


# ==================== VIDEO STREAMING ====================

@app.get("/api/video/stream")
async def video_stream():
    """
    Stream video with real-time face detection and tracking annotations.
    Returns MJPEG stream.
    """
    if not video_capture or not face_detector:
        raise HTTPException(status_code=503, detail="System not ready")
    
    async def generate():
        frame_count = 0
        start_time = asyncio.get_event_loop().time()
        
        while system_status["status"] == "ready":
            try:
                frame = video_capture.get_frame()
                if frame is None:
                    continue
                
                # Detect faces
                detections = face_detector.detect(frame)
                
                # Recognize faces
                for detection in detections:
                    face_id, confidence = face_recognizer.recognize(
                        frame, detection
                    )
                    detection["face_id"] = face_id
                    detection["confidence"] = confidence
                
                # Track intruders
                tracked_objects = intruder_tracker.update(detections)
                
                # Annotate frame (add bounding boxes for faces)
                annotated_frame = frame.copy()
                for obj in tracked_objects:
                    if 'bbox' in obj:
                        x1, y1, x2, y2 = obj['bbox']
                        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        if 'label' in obj:
                            cv2.putText(annotated_frame, obj['label'], (x1, y1-10), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                # Update system status
                frame_count += 1
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > 1.0:
                    system_status["fps"] = frame_count / elapsed
                    frame_count = 0
                    start_time = asyncio.get_event_loop().time()
                
                # Encode and yield frame
                _, buffer = cv2.imencode('.jpg', annotated_frame)
                yield (
                    b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n'
                    b'Content-Length: ' + str(len(buffer)).encode() + b'\r\n\r\n'
                    + buffer.tobytes() + b'\r\n'
                )
                
                await asyncio.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Stream error: {str(e)}")
                break
    
    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


# ==================== FACE ENROLLMENT ====================

@app.post("/api/enrollment/start")
async def start_enrollment(person_name: str):
    """Start face enrollment for a new person."""
    if not face_recognizer:
        raise HTTPException(status_code=503, detail="System not ready")
    
    enrollment_id = face_recognizer.start_enrollment(person_name)
    return {
        "enrollment_id": enrollment_id,
        "person_name": person_name,
        "status": "started"
    }


@app.post("/api/enrollment/capture")
async def capture_enrollment_sample(enrollment_id: str):
    """Capture a sample during enrollment process."""
    if not video_capture or not face_recognizer:
        raise HTTPException(status_code=503, detail="System not ready")
    
    frame = video_capture.get_frame()
    if frame is None:
        raise HTTPException(status_code=400, detail="Failed to capture frame")
    
    success = face_recognizer.add_enrollment_sample(enrollment_id, frame)
    
    return {
        "enrollment_id": enrollment_id,
        "success": success,
        "samples_collected": face_recognizer.get_enrollment_samples(enrollment_id)
    }


@app.post("/api/enrollment/complete")
async def complete_enrollment(enrollment_id: str):
    """Complete face enrollment and save to database."""
    if not face_recognizer or not database_service:
        raise HTTPException(status_code=503, detail="System not ready")
    
    face_embedding = face_recognizer.generate_embedding(enrollment_id)
    if face_embedding is None:
        raise HTTPException(status_code=400, detail="Insufficient samples")
    
    person_name = face_recognizer.get_enrollment_name(enrollment_id)
    person_id = database_service.save_known_face(
        name=person_name,
        embedding=face_embedding.tolist()
    )
    
    face_recognizer.clear_enrollment(enrollment_id)
    
    return {
        "person_id": person_id,
        "person_name": person_name,
        "status": "completed"
    }


# ==================== DETECTION & TRACKING ====================

@app.get("/api/detections/current")
async def get_current_detections():
    """Get current frame detections."""
    return {
        "timestamp": datetime.now().isoformat(),
        "detections": current_detections,
        "frame_count": len(current_detections)
    }


@app.get("/api/detections/history")
async def get_detection_history(
    limit: int = 100,
    offset: int = 0,
    person_id: Optional[str] = None
):
    """Get detection history from database."""
    if not database_service:
        raise HTTPException(status_code=503, detail="System not ready")
    
    detections = database_service.get_detections(
        limit=limit,
        offset=offset,
        person_id=person_id
    )
    
    return {
        "total": database_service.count_detections(),
        "detections": detections,
        "limit": limit,
        "offset": offset
    }


# ==================== MOTOR CONTROL ====================

@app.post("/api/motor/move")
async def move_motor(direction: str, speed: int = 128):
    """
    Move motors in specified direction.
    direction: "up", "down", "left", "right", "stop"
    speed: 0-255
    """
    if not motor_controller:
        raise HTTPException(status_code=503, detail="System not ready")
    
    speed = max(0, min(255, speed))  # Clamp speed
    
    motor_controller.move(direction, speed)
    
    return {
        "direction": direction,
        "speed": speed,
        "status": "moving"
    }


@app.post("/api/motor/auto-track")
async def toggle_auto_track(enabled: bool):
    """Enable/disable automatic intruder tracking."""
    if not intruder_tracker:
        raise HTTPException(status_code=503, detail="System not ready")
    
    intruder_tracker.set_auto_track(enabled)
    
    return {
        "auto_track": enabled,
        "status": "updated"
    }


# ==================== SETTINGS ====================

@app.get("/api/settings")
async def get_settings():
    """Get current system settings."""
    return settings.dict()


@app.put("/api/settings")
async def update_settings(updates: dict):
    """Update system settings."""
    # Validate and update settings
    for key, value in updates.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
    
    return {"status": "updated", "settings": settings.dict()}


# ==================== ALERT MANAGEMENT ====================

@app.get("/api/alerts")
async def get_alerts(limit: int = 50):
    """Get recent alerts."""
    if not database_service:
        raise HTTPException(status_code=503, detail="System not ready")
    
    return database_service.get_alerts(limit=limit)


@app.post("/api/alerts/test")
async def send_test_alert():
    """Send a test alert email."""
    if not alert_service:
        raise HTTPException(status_code=503, detail="System not ready")
    
    success = alert_service.send_test_alert(
        recipient=settings.ALERT_RECIPIENT_EMAIL
    )
    
    return {
        "success": success,
        "message": "Test alert sent" if success else "Failed to send alert"
    }


# ==================== KNOWN FACES ====================

@app.get("/api/known-faces")
async def get_known_faces():
    """Get list of all known faces."""
    if not database_service:
        raise HTTPException(status_code=503, detail="System not ready")
    
    faces = database_service.get_known_faces()
    return {
        "total": len(faces),
        "faces": faces
    }


@app.delete("/api/known-faces/{person_id}")
async def delete_known_face(person_id: str):
    """Remove a known face from database."""
    if not database_service:
        raise HTTPException(status_code=503, detail="System not ready")
    
    database_service.delete_known_face(person_id)
    
    return {"status": "deleted", "person_id": person_id}


# Root endpoint
@app.get("/")
async def root():
    """API root endpoint with documentation."""
    return {
        "name": "GUARDZILLA API",
        "version": "2.0.0",
        "status": system_status["status"],
        "docs": "/docs",
        "health": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
