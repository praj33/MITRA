import { AssistantRequest, AssistantResponse, Task } from '../types';

const getBaseUrl = () => {
  const url = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  if (url.startsWith('http')) return url;
  return `https://${url}`;
};

const API_BASE_URL = getBaseUrl();
const API_KEY = process.env.REACT_APP_API_KEY || 'localtest';
const getToken = (): string | null => localStorage.getItem('authToken');

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

  /**
   * Send a message to the assistant API endpoint.
   * 
   * Request format (v3.0.0 contract):
   * - version: "3.0.0"
   * - input: { message: string, summarized_payload: null }
   * - context: { platform: string, device: string, session_id: null, voice_input: boolean }
   * 
   * Response format (v3.0.0 contract):
   * - version: "3.0.0"
   * - status: "success" | "error"
   * - result: { type, response, task?, enforcement?, safety? }
   * - processed_at: string
   */
  async sendMessage(request: AssistantRequest): Promise<AssistantResponse> {
    try {
      // Build request payload for AI-BEING-FINAL backend (V3.0.0 Contract)
      // The backend expects a unified single endpoint /api/assistant
      const requestPayload = {
        version: "3.0.0",
        input: {
          message: request.message,
          summarized_payload: null
        },
        context: {
          platform: request.platform || 'web',
          device: request.device_context || 'desktop',
          voice_input: request.voice_input || false,
          session_id: 'default'
        }
      };

      // Add timeout to prevent hanging
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 90000); // 90 second timeout

      // Call the correct endpoint: /api/assistant
      const response = await fetch(`${API_BASE_URL}/api/assistant`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(requestPayload),
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

      // MAPPING: Convert Backend V3 Response to Frontend AssistantResponse
      // Backend returns: { version, status, result: { type, response, task, enforcement, safety }, processed_at }

      const result = json.result;
      const isWorkflow = result.type === 'workflow';
      const mitra = result.mitra || {};
      const enforcement = result.enforcement || mitra.enforcement_output || {};
      const policyDecision = mitra.policy_decision || {};
      const safety = result.safety || {
        decision: policyDecision.decision === 'BLOCK'
          ? 'hard_deny'
          : policyDecision.decision === 'REWRITE'
            ? 'soft_rewrite'
            : 'allow',
        level: policyDecision.decision === 'BLOCK'
          ? 'blocked'
          : policyDecision.decision === 'REWRITE'
            ? 'soft_risk'
            : 'safe',
        confidence: typeof policyDecision.confidence === 'number' ? policyDecision.confidence : 1.0,
        score: typeof policyDecision.confidence === 'number' ? policyDecision.confidence : 1.0,
      };

      return {
        status: 'success',
        data: {
          intent: {
            intent: isWorkflow ? 'task_creation' : 'general',
            confidence: 1.0,
          },
          enforcement: {
            decision: (enforcement.decision || 'ALLOW').toLowerCase(),
            reason: enforcement.reason || enforcement.reason_code || null,
            trace_id: enforcement.trace_id || mitra.trace_id || json.trace_id || undefined,
          } as any,
          safety: {
            score: safety.score || safety.confidence || 1.0,
            confidence: safety.confidence || safety.score || 1.0,
            level: safety.level || 'safe',
            flags: safety.level ? [safety.level] : []
          } as any,
          task: result.task,
          decision: {
            final_decision: 'response_generated',
            response: result.response,
            task_created: isWorkflow ? result.task : undefined,
          },
          execution: {
            status: 'completed',
            stage: 'response_generation',
            error: undefined,
          },
          processed_at: json.processed_at || new Date().toISOString(),
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

