"""
Face Recognition Module
Generates face embeddings and identifies known people vs intruders
Uses InsightFace ArcFace or dlib-based embeddings
"""

import cv2
import logging
import numpy as np
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import uuid

logger = logging.getLogger(__name__)


class FaceRecognizer:
    """
    Face recognition system using embeddings.
    Supports multiple embedding models and efficient similarity matching.
    """
    
    def __init__(
        self,
        model_name: str = "arcface",
        embedding_dim: int = 512,
        threshold: float = 0.6
    ):
        """
        Initialize face recognizer.
        
        Args:
            model_name: Embedding model ("arcface" or "facenet")
            embedding_dim: Dimension of embedding vector
            threshold: Cosine similarity threshold for matching
        """
        self.model_name = model_name
        self.embedding_dim = embedding_dim
        self.threshold = threshold
        
        self.model = None
        self.known_embeddings: Dict[str, np.ndarray] = {}  # person_id -> embedding
        self.known_names: Dict[str, str] = {}  # person_id -> name
        
        self.enrollment_samples: Dict[str, List[np.ndarray]] = defaultdict(list)
        self.enrollment_names: Dict[str, str] = {}
        
        self._load_model()
    
    def _load_model(self):
        """Load face embedding model."""
        try:
            if self.model_name == "arcface":
                self._load_arcface()
            elif self.model_name == "facenet":
                self._load_facenet()
            else:
                self._load_dlib()
        
        except Exception as e:
            logger.error(f"Failed to load {self.model_name} model: {str(e)}")
            logger.info("Falling back to simple template matching")
            self.model = None
    
    def _load_arcface(self):
        """Load InsightFace ArcFace model."""
        try:
            from insightface.app import FaceAnalysis
            
            self.model = FaceAnalysis(
                name="buffalo_l",  # Lightweight model for Pi
                providers=["CPUExecutionProvider"]  # CPU only
            )
            self.model.prepare(ctx_id=-1, det_size=(640, 640))
            logger.info("✓ InsightFace ArcFace model loaded")
        
        except ImportError:
            logger.warning("insightface not installed, trying face_recognition")
            self._load_dlib()
    
    def _load_facenet(self):
        """Load FaceNet model."""
        try:
            # Would require additional setup - using dlib as fallback
            self._load_dlib()
        
        except Exception as e:
            logger.error(f"FaceNet loading error: {str(e)}")
            self.model = None
    
    def _load_dlib(self):
        """Load dlib-based face recognition."""
        try:
            import face_recognition
            
            self.model = face_recognition
            logger.info("✓ dlib face_recognition model loaded")
        
        except ImportError:
            logger.warning("face_recognition not installed")
            self.model = None
    
    def get_embedding(
        self,
        frame: np.ndarray,
        detection: Dict
    ) -> Optional[np.ndarray]:
        """
        Generate face embedding for detected face.
        
        Args:
            frame: Full frame image
            detection: Detection dict with coordinates
        
        Returns:
            Embedding vector or None if extraction fails
        """
        try:
            # Extract face ROI
            x1, y1, x2, y2 = detection["x1"], detection["y1"], detection["x2"], detection["y2"]
            face_roi = frame[y1:y2, x1:x2]
            
            if face_roi.size == 0:
                return None
            
            if self.model_name == "arcface" and hasattr(self.model, 'get'):
                # InsightFace
                faces = self.model.get(frame, max_num=1)
                if faces and len(faces) > 0:
                    return faces[0].embedding
            
            elif self.model and hasattr(self.model, 'face_encodings'):
                # dlib face_recognition
                face_locations = self.model.face_locations(face_roi)
                if face_locations:
                    encodings = self.model.face_encodings(face_roi, face_locations)
                    if encodings and len(encodings) > 0:
                        return np.array(encodings[0])
            
            # Fallback: simple histogram-based embedding
            return self._get_histogram_embedding(face_roi)
        
        except Exception as e:
            logger.error(f"Embedding generation error: {str(e)}")
            return None
    
    def _get_histogram_embedding(self, face_roi: np.ndarray) -> np.ndarray:
        """Generate simple histogram-based embedding as fallback."""
        try:
            gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            hist = cv2.normalize(hist, hist).flatten()
            
            # Pad or truncate to embedding_dim
            if len(hist) < self.embedding_dim:
                hist = np.pad(hist, (0, self.embedding_dim - len(hist)))
            else:
                hist = hist[:self.embedding_dim]
            
            return hist / (np.linalg.norm(hist) + 1e-5)
        
        except Exception as e:
            logger.error(f"Histogram embedding error: {str(e)}")
            return np.zeros(self.embedding_dim)
    
    def recognize(
        self,
        frame: np.ndarray,
        detection: Dict
    ) -> Tuple[Optional[str], float]:
        """
        Recognize face in detection.
        
        Args:
            frame: Full frame image
            detection: Detection dict
        
        Returns:
            Tuple of (person_id, confidence) or (None, 0) if unknown
        """
        embedding = self.get_embedding(frame, detection)
        if embedding is None:
            return None, 0.0
        
        if len(self.known_embeddings) == 0:
            return None, 0.0  # No known faces
        
        # Find best match
        best_person_id = None
        best_similarity = 0.0
        
        for person_id, known_embedding in self.known_embeddings.items():
            similarity = self._cosine_similarity(embedding, known_embedding)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_person_id = person_id
        
        # Check if above threshold
        if best_similarity >= self.threshold:
            return best_person_id, best_similarity
        else:
            return None, best_similarity  # Unknown face
    
    def _cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        v1_norm = v1 / (np.linalg.norm(v1) + 1e-5)
        v2_norm = v2 / (np.linalg.norm(v2) + 1e-5)
        return float(np.dot(v1_norm, v2_norm))
    
    # ==================== ENROLLMENT METHODS ====================
    
    def start_enrollment(self, person_name: str) -> str:
        """Start enrollment process for new person."""
        enrollment_id = str(uuid.uuid4())
        self.enrollment_names[enrollment_id] = person_name
        self.enrollment_samples[enrollment_id] = []
        logger.info(f"Started enrollment for {person_name}: {enrollment_id}")
        return enrollment_id
    
    def add_enrollment_sample(self, enrollment_id: str, frame: np.ndarray) -> bool:
        """Add sample frame to enrollment."""
        try:
            if enrollment_id not in self.enrollment_names:
                return False
            
            # Would extract embedding here
            self.enrollment_samples[enrollment_id].append(frame)
            return True
        
        except Exception as e:
            logger.error(f"Add sample error: {str(e)}")
            return False
    
    def get_enrollment_samples(self, enrollment_id: str) -> int:
        """Get number of samples collected."""
        return len(self.enrollment_samples.get(enrollment_id, []))
    
    def get_enrollment_name(self, enrollment_id: str) -> str:
        """Get enrollment person name."""
        return self.enrollment_names.get(enrollment_id, "Unknown")
    
    def generate_embedding(self, enrollment_id: str) -> Optional[np.ndarray]:
        """Generate final embedding from enrollment samples."""
        try:
            samples = self.enrollment_samples.get(enrollment_id, [])
            
            if len(samples) < 3:  # Require at least 3 samples
                logger.warning(f"Insufficient samples: {len(samples)}")
                return None
            
            embeddings = []
            for sample_frame in samples:
                embedding = self.get_embedding(sample_frame, {
                    "x1": 0, "y1": 0,
                    "x2": sample_frame.shape[1],
                    "y2": sample_frame.shape[0]
                })
                if embedding is not None:
                    embeddings.append(embedding)
            
            if not embeddings:
                return None
            
            # Average embeddings
            final_embedding = np.mean(embeddings, axis=0)
            return final_embedding / (np.linalg.norm(final_embedding) + 1e-5)
        
        except Exception as e:
            logger.error(f"Generate embedding error: {str(e)}")
            return None
    
    def clear_enrollment(self, enrollment_id: str):
        """Clear enrollment data."""
        self.enrollment_samples.pop(enrollment_id, None)
        self.enrollment_names.pop(enrollment_id, None)
    
    def add_known_face(self, person_id: str, name: str, embedding: np.ndarray):
        """Add known face to database."""
        self.known_embeddings[person_id] = embedding / (np.linalg.norm(embedding) + 1e-5)
        self.known_names[person_id] = name
        logger.info(f"Added known face: {name} ({person_id})")
    
    def load_known_faces(self, faces_dict: Dict[str, Dict]):
        """Load known faces from database dict."""
        for person_id, data in faces_dict.items():
            embedding = np.array(data.get("embedding", []))
            if len(embedding) == self.embedding_dim:
                self.add_known_face(
                    person_id,
                    data.get("name", "Unknown"),
                    embedding
                )
