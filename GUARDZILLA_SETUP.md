# GUARDZILLA - AI-Powered Security System Setup Guide

## System Overview

GUARDZILLA is a state-of-the-art Raspberry Pi-based security system that combines:
- Real-time face detection (YOLOv8)
- Face recognition and identification (InsightFace ArcFace)
- Multi-object tracking (ByteTrack)
- Automatic motor control for intruder tracking
- Professional React dashboard for monitoring
- Email alerts with video snapshots

## Architecture

### Backend (FastAPI)
Located in `/backend/`:
- `app.py` - Main FastAPI server
- `config.py` - Configuration management
- `core/` - Core AI/ML modules
  - `video_capture.py` - Real-time video input
  - `face_detection.py` - YOLOv8 face detection
  - `face_recognition.py` - Face embeddings and identification
  - `intruder_tracking.py` - Multi-object tracking
  - `motor_control.py` - L298N motor driver control
- `services/` - Business logic services
  - `database_service.py` - SQLite data persistence
  - `alert_service.py` - Email notifications
  - `stream_service.py` - Video frame annotation and streaming

### Frontend (React/Next.js)
Located in `/components/dashboard/`:
- `video-feed.tsx` - Live camera stream display
- `system-status.tsx` - System metrics and status
- `detection-history.tsx` - Detection log with filtering
- `alert-timeline.tsx` - Recent alerts and events
- `motor-control.tsx` - Manual and automatic motor control
- `face-enrollment.tsx` - Add/remove authorized faces

## Installation

### Prerequisites
- Raspberry Pi 4 (8GB recommended) or compatible Linux
- Python 3.9+
- USB camera or Raspberry Pi Camera Module
- L298N motor driver with 4 DC motors
- Buzzer module (optional)

### Backend Setup

1. **Install Python dependencies:**
```bash
cd backend
pip install -r requirements.txt
```

2. **Configure environment variables** (`.env` file):
```bash
# Email alerts (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
ALERT_EMAIL=your-email@gmail.com
ALERT_EMAIL_PASSWORD=your-app-password
ALERT_RECIPIENT_EMAIL=recipient@example.com

# Camera
CAMERA_INDEX=0
VIDEO_WIDTH=1280
VIDEO_HEIGHT=720
VIDEO_FPS=30

# Database
DATABASE_URL=sqlite:///./guardzilla.db

# GPIO (set to true on Raspberry Pi)
GPIO_ENABLED=false
```

3. **Download AI models:**
```bash
# YOLOv8 Face Detection (auto-downloads on first run)
# InsightFace ArcFace (auto-downloads on first run)
```

4. **Initialize database:**
```bash
python -c "from services.database_service import DatabaseService; db = DatabaseService(); db.init_db()"
```

5. **Run the backend:**
```bash
python app.py
# Server runs on http://localhost:8000
# API docs available at http://localhost:8000/docs
```

### Frontend Setup

1. **Install dependencies:**
```bash
npm install
# or
pnpm install
```

2. **Configure API endpoint** in components (default: `http://localhost:8000`):
```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
```

3. **Run development server:**
```bash
npm run dev
# Access dashboard at http://localhost:3000
```

## API Endpoints

### Status & Monitoring
- `GET /api/status` - System status and metrics
- `GET /api/health` - Health check

### Video & Streaming
- `GET /api/video/stream` - MJPEG video stream
- `GET /api/detections/current` - Current frame detections

### Face Enrollment
- `POST /api/enrollment/start` - Begin enrollment for new person
- `POST /api/enrollment/capture` - Capture enrollment sample
- `POST /api/enrollment/complete` - Finalize enrollment

### Detection & History
- `GET /api/detections/history` - Detection log
- `GET /api/alerts` - Recent alerts

### Motor Control
- `POST /api/motor/move` - Manual motor movement
- `POST /api/motor/auto-track` - Enable/disable auto tracking

### Face Management
- `GET /api/known-faces` - List authorized people
- `DELETE /api/known-faces/{person_id}` - Remove authorized person

## Hardware Setup

### GPIO Pin Configuration (Default)
```python
MOTOR_PIN_CONFIG = {
    "motor_1": {"IN1": 17, "IN2": 27, "ENA": 22},  # Pan left/right
    "motor_2": {"IN3": 23, "IN4": 24, "ENB": 25},  # Pan right/left
    "motor_3": {"IN5": 5, "IN6": 6, "ENC": 12},    # Tilt up/down
    "motor_4": {"IN7": 13, "IN8": 19, "END": 26},  # Tilt down/up
    "buzzer": 16  # Alert buzzer
}
```

### Wiring
- L298N Module IN pins → GPIO pins (set as output)
- L298N Module ENA/ENB pins → PWM-capable GPIO
- Motor outputs → DC motor connections
- Buzzer → GPIO pin with resistor protection

## Performance Tuning

### For Raspberry Pi 4
1. **Disable GUI** to free resources:
   ```bash
   sudo systemctl set-default multi-user.target
   ```

2. **Increase GPU memory**:
   ```bash
   sudo raspi-config
   # GPU Memory: 256MB (or higher)
   ```

3. **Optimize video resolution**:
   - Default 1280x720 @ 30 FPS
   - Reduce to 640x480 for better performance on limited CPU

### Expected Performance
- Face Detection: 15-25 FPS
- Face Recognition: <100ms per face
- Motor Response: <200ms
- Email Alert: <5 seconds

## Troubleshooting

### Camera Not Detected
```bash
# Check connected cameras
ls /dev/video*

# Test with OpenCV
python -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"
```

### Motor Not Moving
1. Check GPIO configuration matches your wiring
2. Verify L298N power supply (5V min, 12V recommended)
3. Test pins individually: `gpio readall`
4. Ensure `GPIO_ENABLED=true` in `.env`

### Email Alerts Not Sending
1. Use app-specific passwords for Gmail
2. Check SMTP credentials in `.env`
3. Test email in logs: Check `/logs/guardzilla.log`
4. For Gmail: Enable "Less secure app access"

### High CPU/Memory Usage
1. Reduce video resolution
2. Lower FPS (20 instead of 30)
3. Disable auto-tracking for lower load
4. Close dashboard when not needed

## Deployment

### Run as Service
Create `/etc/systemd/system/guardzilla.service`:
```ini
[Unit]
Description=GUARDZILLA Security System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/guardzilla/backend
ExecStart=/usr/bin/python3 /home/pi/guardzilla/backend/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable guardzilla
sudo systemctl start guardzilla
sudo systemctl status guardzilla
```

### Access from Network
- Local: `http://raspberrypi.local:3000`
- Configured DDNS: Add to reverse proxy (nginx)
- Cloud: Deploy frontend to Vercel, backend to Fly.io/Railway

## API Examples

### Enroll a Face
```bash
# Start enrollment
curl -X POST http://localhost:8000/api/enrollment/start \
  -H "Content-Type: application/json" \
  -d '{"person_name": "John Doe"}'

# Capture 5 samples
for i in {1..5}; do
  curl -X POST http://localhost:8000/api/enrollment/capture
  sleep 2
done

# Complete enrollment
curl -X POST http://localhost:8000/api/enrollment/complete
```

### Get Detection History
```bash
curl http://localhost:8000/api/detections/history?limit=10
```

### Manual Motor Control
```bash
# Move up
curl -X POST http://localhost:8000/api/motor/move \
  -H "Content-Type: application/json" \
  -d '{"direction": "up", "speed": 150}'

# Stop
curl -X POST http://localhost:8000/api/motor/move \
  -H "Content-Type: application/json" \
  -d '{"direction": "stop"}'
```

## Security Notes

1. **Change default credentials** before deployment
2. **Use HTTPS** in production (nginx + Let's Encrypt)
3. **Authenticate API** with API keys or JWT
4. **Set strong email passwords** for alerts
5. **Restrict network access** to authorized users
6. **Enable RLS** in database for multi-user scenarios

## License

GUARDZILLA - AI-Powered Security System
For educational and authorized security purposes only.

## Support

For issues, check:
1. Log files: `/logs/guardzilla.log`
2. API docs: http://localhost:8000/docs
3. GitHub issues (if applicable)

---

**Last Updated:** March 2026
**Version:** 2.0.0
