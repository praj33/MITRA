import { useCompanionStore, getUserId as getStoredUserId } from '../store/companion.store';

const getCurrentUserId = () => {
  try {
    const storeId = useCompanionStore.getState().userId;
    if (storeId) return storeId;
  } catch {}
  return getStoredUserId();
};

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

  async getDailyBriefing(userId = getCurrentUserId()): Promise<{
    user_id: string;
    user_name: string;
    greeting: string;
    period: string;
    date_display: string;
    today_events_count: number;
    today_events: any[];
    pending_tasks_count: number;
    high_priority_count: number;
    active_reminders_count: number;
    summary_text: string;
    quick_actions: Array<{ id: string; label: string; prompt: string }>;
  }> {
    const resp = await fetch(`${getBase()}/api/companion/briefing/${userId}`, {
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

  async setMemoryFact(userId: string, key: string, value: string): Promise<any> {
    const resp = await fetch(`${getBase()}/api/companion/memory/${userId}`, {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({ key, value, source: 'user' }),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  },

  async deleteMemoryFact(userId: string, key: string): Promise<any> {
    const resp = await fetch(`${getBase()}/api/companion/memory/${userId}/${encodeURIComponent(key)}`, {
      method: 'DELETE',
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
  async getCalendarEvents(userId = getCurrentUserId()): Promise<{ events: any[] }> {
    const resp = await fetch(`${getBase()}/api/pages/calendar/events?user_id=${userId}`, {
      headers: headers(),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  },

  async deleteCalendarEvent(eventId: string, userId = getCurrentUserId()): Promise<any> {
    const resp = await fetch(`${getBase()}/api/pages/calendar/events/${eventId}?user_id=${userId}`, {
      method: 'DELETE',
      headers: headers(),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  },

  async createCalendarEvent(title: string, start: string, end?: string, location = '', description = '', color = '#7c5cfc', userId = getCurrentUserId()): Promise<any> {
    const resp = await fetch(`${getBase()}/api/pages/calendar/events?user_id=${userId}`, {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({ title, start, end, location, description, color }),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  },

  async clearPastCalendarEvents(userId = getCurrentUserId()): Promise<{ deleted_count: number }> {
    const resp = await fetch(`${getBase()}/api/pages/calendar/events/cleanup/past?user_id=${userId}`, {
      method: 'DELETE',
      headers: headers(),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  },

  async getTasks(userId = getCurrentUserId()): Promise<{ tasks: any[] }> {
    const resp = await fetch(`${getBase()}/api/pages/tasks/list?user_id=${userId}`, {
      headers: headers(),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  },

  async createTask(title: string, priority = 'medium', category = 'general', userId = getCurrentUserId()): Promise<any> {
    const resp = await fetch(`${getBase()}/api/pages/tasks/create?user_id=${userId}`, {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({ title, priority, category }),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  },

  async updateTask(taskId: string, status: string, userId = getCurrentUserId()): Promise<any> {
    const resp = await fetch(`${getBase()}/api/pages/tasks/update?task_id=${taskId}&status=${status}&user_id=${userId}`, {
      method: 'POST',
      headers: headers(),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  },

  async deleteTask(taskId: string, userId = getCurrentUserId()): Promise<any> {
    const resp = await fetch(`${getBase()}/api/pages/tasks/${taskId}?user_id=${userId}`, {
      method: 'DELETE',
      headers: headers(),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  },

  async getReminders(userId = getCurrentUserId()): Promise<{ reminders: any[] }> {
    const resp = await fetch(`${getBase()}/api/pages/reminders/list?user_id=${userId}`, {
      headers: headers(),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  },

  async createReminder(message: string, time: string, repeat?: string, userId = getCurrentUserId()): Promise<any> {
    const resp = await fetch(`${getBase()}/api/pages/reminders/create?user_id=${userId}`, {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({ message, time, repeat }),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  },

  async deleteReminder(reminderId: string, userId = getCurrentUserId()): Promise<any> {
    const resp = await fetch(`${getBase()}/api/pages/reminders/${reminderId}?user_id=${userId}`, {
      method: 'DELETE',
      headers: headers(),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  },

  async getWorkflows(userId = getCurrentUserId()): Promise<{ workflows: any[] }> {
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

  // ── Authentication API ──────────────────────────────────────
  async signup(name: string, email: string, password: string): Promise<{ token: string; user: { id: string; name: string; email: string } }> {
    const resp = await fetch(`${getBase()}/api/auth/signup`, {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({ name, email, password }),
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: 'Signup failed' }));
      throw new Error(err.detail || `HTTP ${resp.status}`);
    }
    return resp.json();
  },

  async login(email: string, password: string): Promise<{ token: string; user: { id: string; name: string; email: string } }> {
    const resp = await fetch(`${getBase()}/api/auth/login`, {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({ email, password }),
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: 'Invalid email or password' }));
      throw new Error(err.detail || `HTTP ${resp.status}`);
    }
    return resp.json();
  },

  async getMe(token: string): Promise<{ user: { id: string; name: string; email: string } }> {
    const resp = await fetch(`${getBase()}/api/auth/me`, {
      headers: {
        ...headers(),
        Authorization: `Bearer ${token}`,
      },
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  },

  async logout(): Promise<any> {
    const resp = await fetch(`${getBase()}/api/auth/logout`, {
      method: 'POST',
      headers: headers(),
    });
    return resp.json().catch(() => ({}));
  },
};
