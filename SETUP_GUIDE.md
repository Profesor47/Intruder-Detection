# GUARDZILLA - Complete Setup Guide

This guide walks you through setting up the GUARDZILLA AI Security System from scratch.

## Prerequisites

- Raspberry Pi 4B (2GB+ RAM) or Linux desktop/server
- Python 3.9+
- Node.js 16+
- Camera (USB or CSI ribbon)
- L298N motor driver + 4 DC motors (optional)

## Step 1: System Preparation

### Update System
```bash
sudo apt update
sudo apt upgrade -y
```

### Install System Dependencies
```bash
sudo apt install -y python3-pip python3-venv nodejs npm
sudo apt install -y libatlas-base-dev libjasper-dev libtiff5 libjasper-dev
sudo apt install -y libharfbuzz0b libwebp6 libtiff5 libjasper-dev
sudo apt install -y libhdf5-dev libharfbuzz0b libwebp6 libtiff5
```

### Enable Camera (Raspberry Pi only)
```bash
sudo raspi-config
# Navigate to: Interfacing Options → Camera → Enable
```

## Step 2: Backend Setup

### 1. Navigate to Backend Directory
```bash
cd backend
```

### 2. Create Python Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs:
- FastAPI & Uvicorn for API server
- OpenCV for video processing
- YOLOv8 for face detection
- PyTorch for deep learning
- SQLAlchemy for database ORM
- And more...

### 4. Configure Settings
Edit `config.py` and update:

```python
# Camera Configuration
CAMERA_DEVICE = 0           # Camera index (0 = default)
FRAME_WIDTH = 1280          # Resolution width
FRAME_HEIGHT = 720          # Resolution height
FPS = 30                    # Frames per second

# Detection Models
YOLO_MODEL = "yolov8n-face"    # Face detection model
DETECTION_CONFIDENCE = 0.5      # Confidence threshold (0-1)
RECOGNITION_THRESHOLD = 0.6    # Face recognition threshold

# GPIO (Raspberry Pi only)
GPIO_ENABLED = True         # Enable GPIO control
MOTOR_ENABLED = True        # Enable motor control
BUZZER_ENABLED = True       # Enable buzzer

# Camera Pins
MOTOR_IN1 = 17
MOTOR_IN2 = 27
MOTOR_IN3 = 22
MOTOR_IN4 = 23
MOTOR_IN5 = 24
MOTOR_IN6 = 25
MOTOR_IN7 = 26
MOTOR_IN8 = 5
BUZZER_PIN = 18

# Database
DATABASE_URL = "sqlite:///guardzilla.db"
```

### 5. Test Backend
```bash
python app.py
```

You should see:
```
============================================================
Starting GUARDZILLA system initialization...
============================================================
✓ Database initialized
✓ Video capture initialized
✓ Face detector loaded
✓ Face recognizer loaded
✓ Intruder tracker initialized
✓ Motor controller initialized
============================================================
✓ GUARDZILLA system ready!
============================================================
```

Navigate to http://localhost:8000/docs to view API documentation.

## Step 3: Frontend Setup

### 1. Navigate to Project Root
```bash
cd ..
```

### 2. Install Node Dependencies
```bash
npm install
```

### 3. Start Development Server
```bash
npm run dev
```

The dashboard will be available at http://localhost:3000.

### 4. Access Dashboard
Open your browser and navigate to:
```
http://localhost:3000
```

You should see the GUARDZILLA dashboard with:
- Live video feed from camera
- System status monitoring
- Tabs for enrollment, history, motor control, and alerts

## Step 4: Hardware Setup (Optional)

### Motor Wiring

Connect L298N motor driver to Raspberry Pi GPIO:

```
L298N IN1 ← GPIO17 (Motor 1)
L298N IN2 ← GPIO27 (Motor 1)
L298N IN3 ← GPIO22 (Motor 2)
L298N IN4 ← GPIO23 (Motor 2)
L298N IN5 ← GPIO24 (Motor 3)
L298N IN6 ← GPIO25 (Motor 3)
L298N IN7 ← GPIO26 (Motor 4)
L298N IN8 ← GPIO5  (Motor 4)

Motor Configuration:
- Motor 1 & 2: Horizontal pan (left/right)
- Motor 3 & 4: Vertical tilt (up/down)

Power Supply:
- L298N: 12V DC
- Motors: 12V DC
- Raspberry Pi: 5V 3A+
```

### Buzzer (Optional)
```
Buzzer + ← GPIO18 (PWM capable)
Buzzer - ← GND
```

## Step 5: First Run

### 1. Start Backend
```bash
cd backend
source venv/bin/activate
python app.py
```

Keep this terminal running.

### 2. Start Frontend (New Terminal)
```bash
npm run dev
```

### 3. Enroll Your Face
1. Open http://localhost:3000
2. Click **Enrollment** tab
3. Enter your name
4. Click **Start Enrollment**
5. Position your face in front of camera
6. Click **Capture Frame** 5+ times
7. Click **Complete Enrollment**

### 4. Test Motor Control (Optional)
1. Click **Motor Control** tab
2. Use D-pad to move camera
3. Enable **Auto-Track Mode**
4. Step away from camera - motors should follow you!

## Step 6: Production Deployment

### Option 1: Systemd Service (Linux)

Create `/etc/systemd/system/guardzilla.service`:

```ini
[Unit]
Description=GUARDZILLA Security System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/guardzilla
ExecStart=/home/pi/guardzilla/backend/venv/bin/python /home/pi/guardzilla/backend/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable guardzilla
sudo systemctl start guardzilla
sudo systemctl status guardzilla
```

### Option 2: Docker Deployment

Create `Dockerfile`:
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY backend/ .
CMD ["python", "app.py"]
```

Build and run:
```bash
docker build -t guardzilla .
docker run -p 8000:8000 --device /dev/video0 guardzilla
```

### Option 3: Cloud Deployment

**Frontend (Vercel):**
1. Push code to GitHub
2. Import project in Vercel
3. Deploy automatically

**Backend (Railway/Fly.io):**
```bash
# Railway
railway up

# Or Fly.io
flyctl deploy
```

## Troubleshooting

### Issue: Camera Not Detected
```bash
# Check devices
ls -la /dev/video*

# Test camera
python3 -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'FAIL')"
```

**Solution:**
- Check camera is connected
- Try different camera index (0, 1, 2...)
- For USB camera, may need different driver

### Issue: Models Not Loading
```bash
# Clear YOLOv8 cache
rm -rf ~/.cache/yolov8

# Reinstall ultralytics
pip install --upgrade ultralytics
```

### Issue: Motor Not Moving
```bash
# Check GPIO access
python3 -c "from gpiozero import Motor; Motor(17, 27).forward()"

# If permission denied:
sudo usermod -a -G gpio $USER
```

### Issue: Low FPS Performance
**Solutions:**
1. Lower resolution: `FRAME_WIDTH = 640, FRAME_HEIGHT = 480`
2. Reduce FPS: `FPS = 15`
3. Use smaller model: `YOLO_MODEL = "yolov8n-face"`
4. Reduce threads: `WORKERS = 1`

### Issue: Out of Memory
```bash
# Check memory
free -h

# Kill unnecessary services
sudo systemctl stop cups
sudo systemctl stop avahi-daemon

# Reduce detection batch size
BATCH_SIZE = 1  # in config.py
```

## Performance Tuning

### For Raspberry Pi 4B:

1. **Overclock GPU** (optional, may increase temps):
   ```bash
   sudo nano /boot/config.txt
   # Add: gpu_mem=256
   ```

2. **Disable Unnecessary Services**:
   ```bash
   sudo systemctl disable avahi-daemon
   sudo systemctl disable cups
   ```

3. **Use Lighter Models**:
   ```python
   YOLO_MODEL = "yolov8n-face"  # nano is fastest
   FRAME_WIDTH = 640
   FRAME_HEIGHT = 480
   FPS = 15
   ```

4. **Enable Hardware Acceleration**:
   ```bash
   pip install onnxruntime-rpi  # For RPi optimization
   ```

## Testing

### Test Video Stream
```bash
curl http://localhost:8000/api/video/snapshot -o frame.jpg
```

### Test Face Enrollment
```bash
# Start enrollment
curl -X POST "http://localhost:8000/api/enrollment/start?person_name=TestUser"

# Capture frame
curl -X POST "http://localhost:8000/api/enrollment/capture?enrollment_id=YOUR_ID"

# Complete enrollment
curl -X POST "http://localhost:8000/api/enrollment/complete?enrollment_id=YOUR_ID"
```

### Test Motor Control
```bash
# Move left
curl -X POST "http://localhost:8000/api/motor/move?direction=left&speed=200"

# Move right
curl -X POST "http://localhost:8000/api/motor/move?direction=right&speed=200"

# Stop
curl -X POST "http://localhost:8000/api/motor/move?direction=stop"
```

## Security Best Practices

1. **Change Default Credentials**
   - Update any hardcoded API keys
   - Use environment variables

2. **Enable HTTPS**
   ```bash
   # Using nginx as reverse proxy
   sudo apt install nginx
   sudo certbot certonly --nginx -d yourdomain.com
   ```

3. **Secure Database**
   - Use strong database passwords
   - Enable SQL injection prevention
   - Backup embeddings regularly

4. **API Authentication**
   - Implement JWT tokens
   - Rate limiting
   - API key management

5. **Network Security**
   - Firewall rules
   - VPN for remote access
   - Disable SSH password auth

## Maintenance

### Regular Tasks
- **Daily**: Check alerts and system status
- **Weekly**: Review detection history, update models
- **Monthly**: Backup database, check logs
- **Quarterly**: Update dependencies, audit security

### Backup
```bash
# Backup database
cp backend/guardzilla.db backups/guardzilla_$(date +%Y%m%d).db

# Backup config
cp backend/config.py backups/config_$(date +%Y%m%d).py
```

### Update Dependencies
```bash
pip list --outdated
pip install --upgrade -r requirements.txt
npm outdated
npm update
```

## Getting Help

- Check logs: `python app.py 2>&1 | tee guardzilla.log`
- API docs: http://localhost:8000/docs
- Review README.md for quick reference
- Check GitHub issues for common problems

## Next Steps

1. Enroll authorized users
2. Test motor tracking
3. Configure alerts (optional)
4. Set up monitoring dashboard
5. Deploy to production
6. Enable security features
7. Set up automated backups

---

**GUARDZILLA Setup Complete!** 🎉

Your AI-powered security system is ready. Start monitoring your space with real-time face detection and automatic camera tracking.
