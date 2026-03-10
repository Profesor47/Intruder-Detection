/**
 * API Utilities for GUARDZILLA Backend Communication
 * All requests are proxied through Next.js rewrites to avoid CORS issues
 */

const API_BASE = '/api';

export interface AlertData {
  id?: string;
  timestamp?: string;
  type?: string;
  description?: string;
  severity?: string;
  person_detected?: string;
  confidence?: number;
}

export interface DetectionData {
  id?: string;
  timestamp?: string;
  person_name?: string;
  confidence?: number;
  location?: string;
}

export interface EnrollmentData {
  enrollment_id?: string;
  person_name?: string;
  status?: string;
  frames_captured?: number;
}

/**
 * Generic fetch wrapper with error handling
 */
async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  try {
    const url = `${API_BASE}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      console.error(`[API Error] ${response.status}: ${response.statusText}`);
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return await response.json() as T;
  } catch (error) {
    console.error(`[API] Error fetching ${endpoint}:`, error);
    throw error;
  }
}

/**
 * Alerts Endpoints
 */
export const alertsAPI = {
  /**
   * Get recent alerts
   */
  async getAlerts(limit: number = 10): Promise<AlertData[]> {
    try {
      const data = await fetchAPI<{ alerts: AlertData[] } | AlertData[]>(
        `/alerts?limit=${limit}`
      );
      return Array.isArray(data) ? data : (data.alerts || []);
    } catch (error) {
      console.warn('[Alerts API] Failed to fetch alerts, returning empty array');
      return [];
    }
  },

  /**
   * Get a specific alert
   */
  async getAlert(id: string): Promise<AlertData> {
    return fetchAPI<AlertData>(`/alerts/${id}`);
  },

  /**
   * Acknowledge an alert
   */
  async acknowledgeAlert(id: string): Promise<{ status: string }> {
    return fetchAPI<{ status: string }>(`/alerts/${id}/acknowledge`, {
      method: 'POST',
    });
  },
};

/**
 * Detection History Endpoints
 */
export const detectionsAPI = {
  /**
   * Get detection history
   */
  async getDetections(limit: number = 50): Promise<DetectionData[]> {
    try {
      const data = await fetchAPI<{ detections: DetectionData[] } | DetectionData[]>(
        `/detections?limit=${limit}`
      );
      return Array.isArray(data) ? data : (data.detections || []);
    } catch (error) {
      console.warn('[Detections API] Failed to fetch detections, returning empty array');
      return [];
    }
  },

  /**
   * Get detections for a specific person
   */
  async getDetectionsByPerson(personName: string): Promise<DetectionData[]> {
    return fetchAPI<DetectionData[]>(`/detections?person=${personName}`);
  },
};

/**
 * Face Enrollment Endpoints
 */
export const enrollmentAPI = {
  /**
   * Start a new enrollment session
   */
  async startEnrollment(personName: string): Promise<EnrollmentData> {
    return fetchAPI<EnrollmentData>(`/enrollment/start?person_name=${encodeURIComponent(personName)}`, {
      method: 'POST',
    });
  },

  /**
   * Capture a frame for enrollment
   */
  async captureFrame(enrollmentId: string): Promise<{ status: string; frames_captured: number }> {
    return fetchAPI<{ status: string; frames_captured: number }>(
      `/enrollment/capture?enrollment_id=${enrollmentId}`,
      { method: 'POST' }
    );
  },

  /**
   * Complete enrollment
   */
  async completeEnrollment(enrollmentId: string): Promise<{ status: string; person_name: string }> {
    return fetchAPI<{ status: string; person_name: string }>(
      `/enrollment/complete?enrollment_id=${enrollmentId}`,
      { method: 'POST' }
    );
  },

  /**
   * Cancel enrollment
   */
  async cancelEnrollment(enrollmentId: string): Promise<{ status: string }> {
    return fetchAPI<{ status: string }>(
      `/enrollment/cancel?enrollment_id=${enrollmentId}`,
      { method: 'POST' }
    );
  },

  /**
   * Get list of enrolled people
   */
  async getEnrolledPeople(): Promise<string[]> {
    try {
      const data = await fetchAPI<{ people: string[] } | string[]>('/enrollment/list');
      return Array.isArray(data) ? data : (data.people || []);
    } catch (error) {
      console.warn('[Enrollment API] Failed to fetch enrolled people');
      return [];
    }
  },
};

/**
 * Motor Control Endpoints
 */
export const motorAPI = {
  /**
   * Move camera in specified direction
   */
  async moveMotor(direction: string, speed: number = 200): Promise<{ status: string }> {
    return fetchAPI<{ status: string }>(
      `/motor/move?direction=${direction}&speed=${speed}`,
      { method: 'POST' }
    );
  },

  /**
   * Stop all motors
   */
  async stopMotors(): Promise<{ status: string }> {
    return fetchAPI<{ status: string }>('/motor/stop', { method: 'POST' });
  },

  /**
   * Enable/disable auto-tracking
   */
  async toggleAutoTrack(enabled: boolean): Promise<{ status: string; auto_track: boolean }> {
    return fetchAPI<{ status: string; auto_track: boolean }>(
      `/motor/auto-track?enabled=${enabled}`,
      { method: 'POST' }
    );
  },

  /**
   * Get motor status
   */
  async getMotorStatus(): Promise<{ auto_track: boolean; current_position: { pan: number; tilt: number } }> {
    return fetchAPI<{ auto_track: boolean; current_position: { pan: number; tilt: number } }>('/motor/status');
  },
};

/**
 * Video Stream Endpoints
 */
export const videoAPI = {
  /**
   * Get current frame snapshot
   */
  getSnapshotUrl(): string {
    return `${API_BASE}/video/snapshot`;
  },

  /**
   * Get HLS stream URL
   */
  getStreamUrl(): string {
    return `${API_BASE}/video/stream`;
  },
};

/**
 * System Endpoints
 */
export const systemAPI = {
  /**
   * Get system status
   */
  async getStatus(): Promise<{
    status: string;
    uptime?: number;
    version?: string;
  }> {
    try {
      return await fetchAPI<{ status: string; uptime?: number; version?: string }>('/status');
    } catch (error) {
      console.warn('[System API] Failed to fetch status');
      return { status: 'unknown' };
    }
  },

  /**
   * Health check
   */
  async healthCheck(): Promise<{ status: string }> {
    try {
      return await fetchAPI<{ status: string }>('/health');
    } catch (error) {
      console.warn('[System API] Health check failed');
      return { status: 'unhealthy' };
    }
  },
};
