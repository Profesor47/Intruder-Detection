"""
Database Service
SQLite-based storage for known faces, detections, and system logs
Lightweight and ideal for Raspberry Pi
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
import threading

logger = logging.getLogger(__name__)


class DatabaseService:
    """SQLite database management for GUARDZILLA."""
    
    def __init__(self, db_path: str = "guardzilla.db"):
        """Initialize database connection."""
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_connection()
    
    def _init_connection(self):
        """Initialize database connection."""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            logger.info(f"✓ Database connected: {self.db_path}")
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            raise
    
    def init_db(self):
        """Create database tables if they don't exist."""
        with self.lock:
            cursor = self.conn.cursor()
            
            try:
                # Known faces table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS known_faces (
                        person_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        embedding TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Detections table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS detections (
                        detection_id TEXT PRIMARY KEY,
                        person_id TEXT,
                        face_confidence REAL,
                        detection_type TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        frame_number INTEGER,
                        bbox_x INTEGER,
                        bbox_y INTEGER,
                        bbox_w INTEGER,
                        bbox_h INTEGER,
                        video_clip_path TEXT,
                        snapshot_path TEXT,
                        FOREIGN KEY (person_id) REFERENCES known_faces(person_id)
                    )
                """)
                
                # Alerts table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS alerts (
                        alert_id TEXT PRIMARY KEY,
                        detection_id TEXT,
                        alert_type TEXT,
                        status TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        sent_at TIMESTAMP,
                        recipient_email TEXT,
                        FOREIGN KEY (detection_id) REFERENCES detections(detection_id)
                    )
                """)
                
                # System logs table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS system_logs (
                        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        level TEXT,
                        message TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Settings table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                self.conn.commit()
                logger.info("✓ Database tables initialized")
            
            except Exception as e:
                logger.error(f"Database initialization error: {str(e)}")
                self.conn.rollback()
                raise
    
    def save_known_face(
        self,
        name: str,
        embedding: List[float],
        person_id: Optional[str] = None
    ) -> str:
        """
        Save a known face to database.
        
        Returns:
            person_id
        """
        import uuid
        
        if not person_id:
            person_id = str(uuid.uuid4())
        
        with self.lock:
            cursor = self.conn.cursor()
            
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO known_faces
                    (person_id, name, embedding, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (person_id, name, json.dumps(embedding)))
                
                self.conn.commit()
                logger.info(f"Saved known face: {name} ({person_id})")
                return person_id
            
            except Exception as e:
                logger.error(f"Save face error: {str(e)}")
                self.conn.rollback()
                raise
    
    def get_known_faces(self) -> List[Dict]:
        """Get all known faces from database."""
        with self.lock:
            cursor = self.conn.cursor()
            
            try:
                cursor.execute("""
                    SELECT person_id, name, created_at, updated_at
                    FROM known_faces
                    ORDER BY created_at DESC
                """)
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            
            except Exception as e:
                logger.error(f"Get faces error: {str(e)}")
                return []
    
    def get_known_face_embeddings(self) -> Dict[str, List[float]]:
        """Get all known face embeddings."""
        with self.lock:
            cursor = self.conn.cursor()
            
            try:
                cursor.execute("""
                    SELECT person_id, embedding
                    FROM known_faces
                """)
                
                embeddings = {}
                for row in cursor.fetchall():
                    embeddings[row[0]] = json.loads(row[1])
                
                return embeddings
            
            except Exception as e:
                logger.error(f"Get embeddings error: {str(e)}")
                return {}
    
    def delete_known_face(self, person_id: str):
        """Delete a known face."""
        with self.lock:
            cursor = self.conn.cursor()
            
            try:
                cursor.execute("DELETE FROM known_faces WHERE person_id = ?", (person_id,))
                self.conn.commit()
                logger.info(f"Deleted known face: {person_id}")
            
            except Exception as e:
                logger.error(f"Delete face error: {str(e)}")
                self.conn.rollback()
    
    def log_detection(
        self,
        person_id: Optional[str],
        face_confidence: float,
        detection_type: str = "unknown",
        frame_number: int = 0,
        bbox: tuple = (0, 0, 0, 0)
    ) -> str:
        """
        Log a face detection.
        
        Returns:
            detection_id
        """
        import uuid
        
        detection_id = str(uuid.uuid4())
        
        with self.lock:
            cursor = self.conn.cursor()
            
            try:
                cursor.execute("""
                    INSERT INTO detections
                    (detection_id, person_id, face_confidence, detection_type,
                     frame_number, bbox_x, bbox_y, bbox_w, bbox_h)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    detection_id, person_id, face_confidence, detection_type,
                    frame_number, bbox[0], bbox[1], bbox[2], bbox[3]
                ))
                
                self.conn.commit()
                return detection_id
            
            except Exception as e:
                logger.error(f"Log detection error: {str(e)}")
                self.conn.rollback()
                return ""
    
    def get_detections(
        self,
        limit: int = 100,
        offset: int = 0,
        person_id: Optional[str] = None
    ) -> List[Dict]:
        """Get detection history."""
        with self.lock:
            cursor = self.conn.cursor()
            
            try:
                query = "SELECT * FROM detections"
                params = []
                
                if person_id:
                    query += " WHERE person_id = ?"
                    params.append(person_id)
                
                query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            
            except Exception as e:
                logger.error(f"Get detections error: {str(e)}")
                return []
    
    def count_detections(self) -> int:
        """Count total detections."""
        with self.lock:
            cursor = self.conn.cursor()
            
            try:
                cursor.execute("SELECT COUNT(*) FROM detections")
                return cursor.fetchone()[0]
            
            except Exception as e:
                logger.error(f"Count detections error: {str(e)}")
                return 0
    
    def log_alert(
        self,
        detection_id: str,
        alert_type: str = "email",
        recipient_email: str = ""
    ) -> str:
        """Log an alert."""
        import uuid
        
        alert_id = str(uuid.uuid4())
        
        with self.lock:
            cursor = self.conn.cursor()
            
            try:
                cursor.execute("""
                    INSERT INTO alerts
                    (alert_id, detection_id, alert_type, status, recipient_email)
                    VALUES (?, ?, ?, ?, ?)
                """, (alert_id, detection_id, alert_type, "created", recipient_email))
                
                self.conn.commit()
                return alert_id
            
            except Exception as e:
                logger.error(f"Log alert error: {str(e)}")
                self.conn.rollback()
                return ""
    
    def get_alerts(self, limit: int = 50) -> List[Dict]:
        """Get recent alerts."""
        with self.lock:
            cursor = self.conn.cursor()
            
            try:
                cursor.execute("""
                    SELECT * FROM alerts
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (limit,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            
            except Exception as e:
                logger.error(f"Get alerts error: {str(e)}")
                return []
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database closed")
