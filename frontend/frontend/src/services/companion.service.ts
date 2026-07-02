// services/companion.service.ts — Mitra API client

const getBase = () =>
  process.env.REACT_APP_API_URL || 'http://localhost:8000';
const getKey = () =>
  process.env.REACT_APP_API_KEY || '';

const headers = () => ({
  'Content-Type': 'application/json',
  'X-API-Key':    getKey(),
});

export interface ChatResponse {
  message:          string;
  capability_result?: any;
  session_id?:      string;
  intent?:          string;
  suggested_actions?: string[];
}

export const CompanionService = {
  async chat(
    userId: string,
    message: string,
    platform = 'web',
  ): Promise<ChatResponse> {
    const resp = await fetch(`${getBase()}/api/companion/chat`, {
      method:  'POST',
      headers: headers(),
      body:    JSON.stringify({ user_id: userId, message, platform }),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  },

  async getGreeting(userId: string): Promise<{ greeting: string }> {
    const resp = await fetch(`${getBase()}/api/companion/greeting/${userId}`, {
      headers: headers(),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  },

  async getMemory(userId: string): Promise<{ facts: Record<string, any> }> {
    const resp = await fetch(`${getBase()}/api/companion/memory/${userId}`, {
      headers: headers(),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  },

  async listCapabilities(): Promise<{ capabilities: any[] }> {
    const resp = await fetch(`${getBase()}/api/companion/capabilities`, {
      headers: headers(),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  },

  async runWorkflow(
    workflowName: string,
    userId:       string,
    message?:     string,
  ): Promise<any> {
    const resp = await fetch(`${getBase()}/api/workflow/run`, {
      method:  'POST',
      headers: headers(),
      body:    JSON.stringify({ workflow_name: workflowName, user_id: userId, message }),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  },
};
