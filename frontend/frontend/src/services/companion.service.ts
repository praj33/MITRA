// services/companion.service.ts — Mitra API client (expanded)

const getBase = () => {
  if (process.env.REACT_APP_API_URL) return process.env.REACT_APP_API_URL;
  if (typeof window !== 'undefined' && window.location.hostname !== 'localhost') {
    return 'https://mitra-backend-q1f3.onrender.com';
  }
  return 'http://localhost:8000';
};

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
  // ── Core Chat ──────────────────────────────────────
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

  // ── Page Data Endpoints ────────────────────────────
  async getCalendarEvents(userId = 'user_default'): Promise<{ events: any[] }> {
    const resp = await fetch(`${getBase()}/api/pages/calendar/events?user_id=${userId}`, {
      headers: headers(),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  },

  async deleteCalendarEvent(eventId: string, userId = 'user_default'): Promise<any> {
    const resp = await fetch(`${getBase()}/api/pages/calendar/events/${eventId}?user_id=${userId}`, {
      method: 'DELETE',
      headers: headers(),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  },

  async getTasks(userId = 'user_default'): Promise<{ tasks: any[] }> {
    const resp = await fetch(`${getBase()}/api/pages/tasks/list?user_id=${userId}`, {
      headers: headers(),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  },

  async updateTask(taskId: string, status: string, userId = 'user_default'): Promise<any> {
    const resp = await fetch(`${getBase()}/api/pages/tasks/update?task_id=${taskId}&status=${status}&user_id=${userId}`, {
      method: 'POST',
      headers: headers(),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  },

  async deleteTask(taskId: string, userId = 'user_default'): Promise<any> {
    const resp = await fetch(`${getBase()}/api/pages/tasks/${taskId}?user_id=${userId}`, {
      method: 'DELETE',
      headers: headers(),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  },

  async getReminders(userId = 'user_default'): Promise<{ reminders: any[] }> {
    const resp = await fetch(`${getBase()}/api/pages/reminders/list?user_id=${userId}`, {
      headers: headers(),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  },

  async deleteReminder(reminderId: string, userId = 'user_default'): Promise<any> {
    const resp = await fetch(`${getBase()}/api/pages/reminders/${reminderId}?user_id=${userId}`, {
      method: 'DELETE',
      headers: headers(),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  },

  async getWorkflows(userId = 'user_default'): Promise<{ workflows: any[] }> {
    const resp = await fetch(`${getBase()}/api/pages/workflows/list?user_id=${userId}`, {
      headers: headers(),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  },

  async getHealth(): Promise<{ status: string; version: string }> {
    const resp = await fetch(`${getBase()}/health`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  },
};
