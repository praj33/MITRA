import { AssistantRequest, AssistantResponse, Task } from '../types';
import { getApiBase, getAuthHeaders } from './apiConfig';

class ApiService {
  private getHeaders(): Record<string, string> {
    return getAuthHeaders();
  }

  /**
   * Check backend health status
   */
  async checkHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${getApiBase()}/health`, {
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
   */
  async sendMessage(request: AssistantRequest): Promise<AssistantResponse> {
    try {
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

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 90000); // 90 second timeout

      const response = await fetch(`${getApiBase()}/api/assistant`, {
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
    console.warn('getTasks: Not supported by current backend version');
    return [];
  }

  async updateTaskStatus(taskId: number, status: string): Promise<Task> {
    throw new Error('Task updates not supported by this backend');
  }

  async search(request: import('../types').SearchRequest): Promise<import('../types').SearchResponse> {
    console.warn('Search API not supported by this backend');
    return { query: request.query, results: [] };
  }

  async research(request: import('../types').ResearchRequest): Promise<import('../types').ResearchResponse> {
    console.warn('Research API not supported by this backend');
    throw new Error('Deep Research is not available in this environment.');
  }

  async createTask(request: import('../types').TaskRequest): Promise<import('../types').TaskCreateResponse> {
    try {
      const response = await fetch(`${getApiBase()}/api/tasks`, {
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

  async getTaskStatus(taskId: string): Promise<import('../types').TaskStatusResponse> {
    try {
      const response = await fetch(`${getApiBase()}/api/tasks/${encodeURIComponent(taskId)}`, {
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

  async getSystemInfo(): Promise<import('../types').SystemInfo> {
    try {
      const response = await fetch(`${getApiBase()}/api/system/info`, {
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

  async getSystemStats(): Promise<import('../types').SystemStats> {
    try {
      const response = await fetch(`${getApiBase()}/api/system/stats`, {
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

  async getPerformanceInsights(): Promise<import('../types').PerformanceInsights> {
    throw new Error('Analytics not supported');
  }

  async generateTTS(text: string, language: string = 'en'): Promise<string> {
    try {
      const response = await fetch(`${getApiBase()}/api/tts`, {
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
