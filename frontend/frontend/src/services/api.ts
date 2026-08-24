import { AssistantRequest, AssistantResponse, Task } from '../types';

interface CompanionGreetingResponse {
  greeting: string;
  user_id: string;
}

interface CompanionMemoryResponse {
  user_id: string;
  facts: Record<string, unknown>;
  recent_summaries: unknown[];
}

interface CompanionSessionResponse {
  session_id: string;
  user_id: string;
  platform: string;
  device: string;
  started_at: string;
  last_active: string;
  turn_count: number;
  capabilities_used: string[];
}

interface CompanionCapabilitiesResponse {
  capabilities: Array<{
    name: string;
    description: string;
    intents: string[];
  }>;
}

interface PresenceResponse {
  user_id: string;
  status: string;
  product_id: string | null;
  last_seen: string | null;
}

interface HeartbeatResponse {
  status: string;
  user_id: string;
  presence: string;
}

const getBaseUrl = () => {
  const url = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  if (url.startsWith('http')) return url;
  return `https://${url}`;
};

const API_BASE_URL = getBaseUrl();
const API_KEY = process.env.REACT_APP_API_KEY || '';
const getToken = (): string | null => localStorage.getItem('authToken');

// Module-level session ID — set once after getSession resolves, reused for
// every subsequent sendMessage call so the backend maintains conversation state.
let _sessionId: string | null = null;

class ApiService {
  private getHeaders(): HeadersInit {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY,
    };
    const token = getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  }

  /**
   * Check backend health status
   */
  async checkHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/health`, {
        method: 'GET',
        headers: this.getHeaders(),
      });
      return response.ok;
    } catch (error) {
      console.error('Health check failed:', error);
      return false;
    }
  }

  /** Store the session ID returned by getSession so it is reused across all chat turns. */
  setSessionId(id: string): void {
    _sessionId = id;
  }

  getStoredSessionId(): string | null {
    return _sessionId;
  }

  /**
   * Send a message to the production companion chat endpoint.
   * Preserves the existing frontend-facing interface while mapping the
   * production response into the existing AssistantResponse contract.
   */
  async sendMessage(request: AssistantRequest): Promise<AssistantResponse> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 90000); // 90 second timeout

      // Include session_id when available so the backend maintains conversation continuity.
      const body: Record<string, unknown> = { message: request.message };
      if (_sessionId) body.session_id = _sessionId;

      const response = await fetch(`${API_BASE_URL}/api/companion/chat`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(body),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({
          error: `HTTP ${response.status}: ${response.statusText}`,
        }));

        const errorMessage = errorData.error?.message || errorData.detail || `API request failed (${response.status})`;
        throw new Error(errorMessage);
      }

      const json = await response.json();
      const responseText = typeof json.message === 'string'
        ? json.message
        : typeof json.response === 'string'
          ? json.response
          : 'Message processed successfully.';

      return {
        status: 'success',
        data: {
          intent: {
            intent: 'general',
            confidence: 1.0,
          },
          enforcement: {
            decision: 'allow',
            reason: undefined,
            trace_id: json.trace_id || undefined,
          },
          safety: {
            score: 1.0,
            confidence: 1.0,
            level: 'safe',
          },
          task: undefined,
          decision: {
            final_decision: 'response_generated',
            response: responseText,
            task_created: undefined,
          },
          execution: {
            status: 'completed',
            stage: 'response_generation',
            error: undefined,
          },
          processed_at: new Date().toISOString(),
        },
      };
    } catch (error) {
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new Error('Request timed out. Please try again.');
        }
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
          console.error('Fetch error:', error);
          throw new Error('Unable to connect to backend. Please check if the backend is running and reachable.');
        }
        throw error;
      }
      throw new Error('Something went wrong. Please try again.');
    }
  }

  async getGreeting(userId: string): Promise<CompanionGreetingResponse> {
    const response = await fetch(`${API_BASE_URL}/api/companion/greeting/${encodeURIComponent(userId)}`, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to get greeting: ${response.statusText}`);
    }

    return await response.json() as CompanionGreetingResponse;
  }

  async getMemory(userId: string): Promise<CompanionMemoryResponse> {
    const response = await fetch(`${API_BASE_URL}/api/companion/memory/${encodeURIComponent(userId)}`, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to get memory: ${response.statusText}`);
    }

    return await response.json() as CompanionMemoryResponse;
  }

  async getSession(userId: string): Promise<CompanionSessionResponse> {
    const response = await fetch(`${API_BASE_URL}/api/companion/session/${encodeURIComponent(userId)}`, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to get session: ${response.statusText}`);
    }

    return await response.json() as CompanionSessionResponse;
  }

  async getCapabilities(): Promise<CompanionCapabilitiesResponse> {
    const response = await fetch(`${API_BASE_URL}/api/companion/capabilities`, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to get capabilities: ${response.statusText}`);
    }

    return await response.json() as CompanionCapabilitiesResponse;
  }

  async getPresence(userId: string): Promise<PresenceResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/presence/${encodeURIComponent(userId)}`, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to get presence: ${response.statusText}`);
    }

    return await response.json() as PresenceResponse;
  }

  async sendHeartbeat(userId: string): Promise<HeartbeatResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/presence/heartbeat`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ user_id: userId }),
    });

    if (!response.ok) {
      throw new Error(`Failed to send heartbeat: ${response.statusText}`);
    }

    return await response.json() as HeartbeatResponse;
  }

  async getTasks(): Promise<Task[]> {
    // STUB: Backend v3.0.0 does not support independent task fetching
    console.warn('getTasks: Not supported by current backend version');
    return [];
  }

  async updateTaskStatus(taskId: number, status: string): Promise<Task> {
    // STUB: Backend v3.0.0 does not support task updates
    throw new Error('Task updates not supported by this backend');
  }



  /**
   * Web Search API
   * Search the web with a query
   */
  async search(request: import('../types').SearchRequest): Promise<import('../types').SearchResponse> {
    // STUB: Search not supported
    console.warn('Search API not supported by this backend');
    return { query: request.query, results: [] };
  }

  /**
   * Web Research API
   * Perform deep research on a topic
   */
  async research(request: import('../types').ResearchRequest): Promise<import('../types').ResearchResponse> {
    // STUB: Research not supported
    console.warn('Research API not supported by this backend');
    throw new Error('Deep Research is not available in this environment.');
  }



  /**
   * Create Task API
   * Create a new task for multi-agent processing
   */
  async createTask(request: import('../types').TaskRequest): Promise<import('../types').TaskCreateResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/tasks`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`Task creation failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Task creation failed');
    }
  }

  /**
   * Get Task Status API
   * Get the status of a specific task
   */
  async getTaskStatus(taskId: string): Promise<import('../types').TaskStatusResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/tasks/${taskId}`, {
        method: 'GET',
        headers: this.getHeaders(),
      });

      if (!response.ok) {
        throw new Error(`Failed to get task status: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Failed to get task status');
    }
  }

  /**
   * System Information API
   * Get system information
   */
  async getSystemInfo(): Promise<import('../types').SystemInfo> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/system/info`, {
        method: 'GET',
        headers: this.getHeaders(),
      });

      if (!response.ok) {
        throw new Error(`Failed to get system info: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Failed to get system info');
    }
  }

  /**
   * System Statistics API
   * Get system statistics
   */
  async getSystemStats(): Promise<import('../types').SystemStats> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/system/stats`, {
        method: 'GET',
        headers: this.getHeaders(),
      });

      if (!response.ok) {
        throw new Error(`Failed to get system stats: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Failed to get system stats');
    }
  }

  /**
   * Performance Insights API
   * Get performance metrics and recommendations
   */
  async getPerformanceInsights(): Promise<import('../types').PerformanceInsights> {
    // STUB: Analytics not supported
    throw new Error('Analytics not supported');
  }

  /**
   * Generate TTS API
   * Get high-quality AI speech audio for text
   */
  async generateTTS(text: string, language: string = 'en'): Promise<string> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/tts`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ text, language }),
      });

      if (!response.ok) {
        throw new Error('TTS generation failed');
      }

      const data = await response.json();
      return data.audio_base64;
    } catch (error) {
      console.error('TTS API error:', error);
      throw error;
    }
  }

}

export const apiService = new ApiService();

