import { AssistantRequest, AssistantResponse, Task } from '../types';

const getBaseUrl = () => {
  const url = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  if (url.startsWith('http')) return url;
  return `https://${url}`;
};

const API_BASE_URL = getBaseUrl();
const API_KEY = process.env.REACT_APP_API_KEY || '';
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
      const preferredLanguage = localStorage.getItem('mitra_language') || 'en';

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
          session_id: 'default',
          preferred_language: preferredLanguage
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

      if (json.status === 'error') {
        throw new Error(json.error?.message || json.error || 'Backend returned an error');
      }

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
    try {
      const response = await fetch(`${API_BASE_URL}/api/tasks`, {
        method: 'GET',
        headers: this.getHeaders(),
      });
      if (!response.ok) return [];
      const data = await response.json();
      return Array.isArray(data) ? data : data.tasks || [];
    } catch {
      return [];
    }
  }

  async updateTaskStatus(taskId: string, status: string): Promise<Task> {
    const response = await fetch(`${API_BASE_URL}/api/tasks/${taskId}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify({ status }),
    });
    if (!response.ok) throw new Error(`Failed to update task: ${response.statusText}`);
    return await response.json();
  }



  /**
   * Web Search API - delegates to backend for search
   */
  async search(request: import('../types').SearchRequest): Promise<import('../types').SearchResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/search`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(request),
      });
      if (!response.ok) {
        // Fallback: use assistant to answer search queries
        const assistantResponse = await this.sendMessage({
          message: `Search for: ${request.query}`,
          platform: 'web',
        });
        return {
          query: request.query,
          results: [{
            title: 'Search Result',
            url: '',
            snippet: assistantResponse.data?.decision?.response || 'No results found',
            relevance: 1.0,
          }],
        };
      }
      return await response.json();
    } catch {
      return { query: request.query, results: [] };
    }
  }

  /**
   * Web Research API - delegates to backend for deep research
   */
  async research(request: import('../types').ResearchRequest): Promise<import('../types').ResearchResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/research`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(request),
      });
      if (!response.ok) {
        // Fallback: use assistant for research queries
        const assistantResponse = await this.sendMessage({
          message: `Research this topic thoroughly: ${request.query}`,
          platform: 'web',
        });
        return {
          topic: request.query,
          summary: assistantResponse.data?.decision?.response || 'Research not available',
          key_findings: [],
          sources: [],
          depth: 1,
        };
      }
      return await response.json();
    } catch (error) {
      if (error instanceof Error) throw error;
      throw new Error('Research failed');
    }
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
   */
  async getSystemInfo(): Promise<import('../types').SystemInfo> {
    try {
      const response = await fetch(`${API_BASE_URL}/health/system`, {
        method: 'GET',
        headers: this.getHeaders(),
      });
      if (!response.ok) throw new Error(`Failed to get system info: ${response.statusText}`);
      const data = await response.json();
      return {
        platform: data.platform || 'unknown',
        python_version: data.python_version || 'unknown',
        working_directory: data.working_directory || 'unknown',
        available_space: data.available_space || 'unknown',
        memory_usage: data.memory_usage || { total: 0, available: 0, percent: 0, used: 0 },
      };
    } catch (error) {
      if (error instanceof Error) throw error;
      throw new Error('Failed to get system info');
    }
  }

  /**
   * System Statistics API
   */
  async getSystemStats(): Promise<import('../types').SystemStats> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/metrics/system`, {
        method: 'GET',
        headers: this.getHeaders(),
      });
      if (!response.ok) throw new Error(`Failed to get system stats: ${response.statusText}`);
      const data = await response.json();
      return {
        memory_stats: data.memory_stats || { total_entries: 0, users: 0 },
        task_queue_status: data.task_queue_status || { pending: 0, running: 0, completed: 0 },
        safety_stats: data.safety_stats || { total_evaluations: 0, blocked_count: 0 },
        policy_violations: data.policy_violations || { total: 0 },
        performance_metrics: data.performance_metrics || 0,
      };
    } catch (error) {
      if (error instanceof Error) throw error;
      throw new Error('Failed to get system stats');
    }
  }

  /**
   * Performance Insights API
   */
  async getPerformanceInsights(): Promise<import('../types').PerformanceInsights> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/metrics`, {
        method: 'GET',
        headers: this.getHeaders(),
      });
      if (!response.ok) throw new Error(`Failed to get performance insights: ${response.statusText}`);
      const data = await response.json();
      return {
        performance_metrics: data.performance_metrics || {
          total_interactions: 0,
          successful_interactions: 0,
          average_response_time: 0,
          average_satisfaction: 0,
          improvement_areas: [],
        },
        patterns: data.patterns || [],
        recommendations: data.recommendations || [],
      };
    } catch (error) {
      if (error instanceof Error) throw error;
      throw new Error('Failed to get performance insights');
    }
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

  /**
   * Stream a message via SSE for real-time responses
   */
  async sendMessageStream(
    request: AssistantRequest,
    onChunk: (chunk: any) => void,
    onDone: () => void,
    onError: (error: Error) => void,
  ): Promise<void> {
    try {
      const preferredLanguage = localStorage.getItem('mitra_language') || 'en';
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
          session_id: 'default',
          preferred_language: preferredLanguage
        }
      };

      const response = await fetch(`${API_BASE_URL}/api/assistant/stream`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(requestPayload),
      });

      if (!response.ok) {
        throw new Error(`Stream request failed: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response body');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            const eventType = line.slice(7).trim();
            if (eventType === 'done') {
              onDone();
              return;
            }
            if (eventType === 'error') {
              onError(new Error('Stream error event'));
              return;
            }
          }
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              onChunk(data);
            } catch {
              // Ignore non-JSON lines
            }
          }
        }
      }
      onDone();
    } catch (error) {
      onError(error instanceof Error ? error : new Error('Stream failed'));
    }
  }

}

export const apiService = new ApiService();

