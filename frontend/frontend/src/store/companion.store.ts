// store/companion.store.ts — Mitra Zustand global state
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

// ── Types ────────────────────────────────────────────────
export type CompanionStatus = 'active' | 'thinking' | 'away' | 'error';
export type MessageRole = 'user' | 'assistant';
export type SidebarState = 'expanded' | 'collapsed';
export type PanelState = 'open' | 'closed';

export interface Message {
  id:               string;
  role:             MessageRole;
  content:          string;
  timestamp:        string;
  intent?:          string;
  capabilityResult?: CapabilityResult | null;
  suggestedActions?: string[];
}

export interface CapabilityResult {
  capability: string;
  intent:     string;
  status:     'success' | 'error' | 'pending';
  summary:    string;
  data?:      Record<string, any>;
}

export interface ContextItem {
  id:       string;
  type:     'calendar' | 'email' | 'task' | 'note' | 'contact' | 'knowledge';
  title:    string;
  subtitle?: string;
  value?:   string;
  badge?:   string;
  timestamp?: string;
}

export interface Notification {
  id:        string;
  type:      'info' | 'success' | 'warning' | 'error';
  title:     string;
  body?:     string;
  read:      boolean;
  timestamp: string;
}

export interface UserMemory {
  name?:        string;
  preferences?: Record<string, any>;
  facts?:       Record<string, any>;
}

// ── Store Interface ─────────────────────────────────────
interface CompanionStore {
  // Identity
  userId:    string;
  userName:  string;
  apiKey:    string;
  apiBase:   string;

  // Companion status
  status:    CompanionStatus;
  sessionId: string | null;

  // Conversation
  messages:  Message[];
  isLoading: boolean;

  // Layout state
  sidebar:      SidebarState;
  contextPanel: PanelState;

  // Context items (right panel)
  contextItems: ContextItem[];

  // Notifications
  notifications: Notification[];

  // Memory
  memory: UserMemory;

  // ── Actions ──────────────────────────────────────────
  setStatus:    (s: CompanionStatus) => void;
  setSessionId: (id: string) => void;
  setSidebar:   (s: SidebarState) => void;
  setContextPanel: (s: PanelState) => void;
  toggleSidebar: () => void;
  toggleContextPanel: () => void;

  addMessage:    (msg: Omit<Message, 'id' | 'timestamp'>) => void;
  clearMessages: () => void;

  setContextItems:  (items: ContextItem[]) => void;
  addContextItem:   (item: ContextItem) => void;
  clearContextItems: () => void;

  addNotification:    (n: Omit<Notification, 'id' | 'timestamp'>) => void;
  markAllRead:        () => void;

  setMemory: (m: Partial<UserMemory>) => void;
  setUserName: (name: string) => void;
}

// ── Store Implementation ────────────────────────────────
export const useCompanionStore = create<CompanionStore>()(
  devtools(
    (set, get) => ({
      // Defaults
      userId:    'user_default',
      userName:  'there',
      apiKey:    process.env.REACT_APP_API_KEY || '',
      apiBase:   process.env.REACT_APP_API_URL || 'http://localhost:8000',

      status:    'active',
      sessionId: null,

      messages:  [],
      isLoading: false,

      sidebar:      'expanded',
      contextPanel: 'open',

      contextItems: [],
      notifications: [],
      memory: {},

      // ── Status ─────────────────────────────────────
      setStatus:    (status)    => set({ status }),
      setSessionId: (sessionId) => set({ sessionId }),

      // ── Layout ─────────────────────────────────────
      setSidebar:      (sidebar)      => set({ sidebar }),
      setContextPanel: (contextPanel) => set({ contextPanel }),
      toggleSidebar:   () => set(s => ({
        sidebar: s.sidebar === 'expanded' ? 'collapsed' : 'expanded'
      })),
      toggleContextPanel: () => set(s => ({
        contextPanel: s.contextPanel === 'open' ? 'closed' : 'open'
      })),

      // ── Messages ────────────────────────────────────
      addMessage: (msg) => set(s => ({
        messages: [
          ...s.messages,
          {
            ...msg,
            id:        `msg_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
            timestamp: new Date().toISOString(),
          },
        ],
      })),
      clearMessages: () => set({ messages: [] }),

      // ── Context Panel ───────────────────────────────
      setContextItems:   (contextItems)  => set({ contextItems }),
      addContextItem:    (item)          => set(s => ({ contextItems: [...s.contextItems, item] })),
      clearContextItems: ()              => set({ contextItems: [] }),

      // ── Notifications ───────────────────────────────
      addNotification: (n) => set(s => ({
        notifications: [
          {
            ...n,
            id:        `notif_${Date.now()}`,
            timestamp: new Date().toISOString(),
          },
          ...s.notifications,
        ],
      })),
      markAllRead: () => set(s => ({
        notifications: s.notifications.map(n => ({ ...n, read: true })),
      })),

      // ── Memory ──────────────────────────────────────
      setMemory:   (m)    => set(s => ({ memory: { ...s.memory, ...m } })),
      setUserName: (name) => set({ userName: name }),
    }),
    { name: 'MitraCompanion' }
  )
);
