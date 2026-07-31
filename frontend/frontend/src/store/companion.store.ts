// store/companion.store.ts — Mitra Zustand global state
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { useEffect } from 'react';

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
  userEmail: string;
  authToken: string;
  isAuthenticated: boolean;
  authModalOpen:   boolean;
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

  // Mobile state
  isMobile:         boolean;
  mobileMenuOpen:   boolean;
  mobileContextOpen: boolean;

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

  // Mobile actions
  setIsMobile:          (v: boolean) => void;
  setMobileMenuOpen:    (v: boolean) => void;
  setMobileContextOpen: (v: boolean) => void;
  toggleMobileMenu:     () => void;
  toggleMobileContext:  () => void;

  addMessage:    (msg: Omit<Message, 'id' | 'timestamp'>) => void;
  clearMessages: () => void;

  setContextItems:  (items: ContextItem[]) => void;
  addContextItem:   (item: ContextItem) => void;
  clearContextItems: () => void;

  addNotification:    (n: Omit<Notification, 'id' | 'timestamp'>) => void;
  markAllRead:        () => void;

  setMemory: (m: Partial<UserMemory>) => void;
  setUserName: (name: string) => void;

  setAuth: (user: { id: string; name: string; email: string }, token: string) => void;
  logoutUser: () => void;
  setAuthModalOpen: (open: boolean) => void;
}

export const getUserId = (): string => {
  if (typeof window === 'undefined') return 'user_default';
  let stored = localStorage.getItem('mitra_user_id');
  if (!stored) {
    stored = 'usr_' + Math.random().toString(36).substring(2, 8);
    localStorage.setItem('mitra_user_id', stored);
  }
  return stored;
};

// ── Store Implementation ────────────────────────────────
export const useCompanionStore = create<CompanionStore>()(
  devtools(
    (set, get) => ({
      // Defaults
      userId:          localStorage.getItem('mitra_user_id') || getUserId(),
      userName:        localStorage.getItem('mitra_user_name') || 'User',
      userEmail:       localStorage.getItem('mitra_user_email') || '',
      authToken:       localStorage.getItem('mitra_auth_token') || '',
      isAuthenticated: Boolean(localStorage.getItem('mitra_auth_token')),
      authModalOpen:   false,
      apiKey:    process.env.REACT_APP_API_KEY || '',
      apiBase:   process.env.REACT_APP_API_URL || 'http://localhost:8000',

      status:    'active',
      sessionId: null,

      messages:  [],
      isLoading: false,

      sidebar:      'expanded',
      contextPanel: 'open',

      // Mobile defaults
      isMobile:         false,
      mobileMenuOpen:   false,
      mobileContextOpen: false,

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
      toggleContextPanel: () => {
        const { isMobile } = get();
        if (isMobile) {
          set(s => ({ mobileContextOpen: !s.mobileContextOpen }));
        } else {
          set(s => ({ contextPanel: s.contextPanel === 'open' ? 'closed' : 'open' }));
        }
      },

      // ── Mobile ─────────────────────────────────────
      setIsMobile:          (isMobile)         => set({ isMobile }),
      setMobileMenuOpen:    (mobileMenuOpen)   => set({ mobileMenuOpen }),
      setMobileContextOpen: (mobileContextOpen) => set({ mobileContextOpen }),
      toggleMobileMenu:     () => set(s => ({ mobileMenuOpen: !s.mobileMenuOpen })),
      toggleMobileContext:  () => set(s => ({ mobileContextOpen: !s.mobileContextOpen })),

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
      setUserName: (name) => {
        if (name) localStorage.setItem('mitra_user_name', name);
        set({ userName: name });
      },

      // ── Authentication Actions ───────────────────────
      setAuthModalOpen: (open) => set({ authModalOpen: open }),

      setAuth: (user, token) => {
        if (user.id) localStorage.setItem('mitra_user_id', user.id);
        if (user.name) localStorage.setItem('mitra_user_name', user.name);
        if (user.email) localStorage.setItem('mitra_user_email', user.email);
        if (token) localStorage.setItem('mitra_auth_token', token);
        set({
          userId:          user.id || getUserId(),
          userName:        user.name || 'User',
          userEmail:       user.email || '',
          authToken:       token,
          isAuthenticated: true,
          authModalOpen:   false,
        });
      },

      logoutUser: () => {
        localStorage.removeItem('mitra_auth_token');
        localStorage.removeItem('mitra_user_email');
        localStorage.removeItem('mitra_user_name');
        localStorage.removeItem('mitra_user_id');
        const newId = getUserId();
        set({
          userId:          newId,
          userName:        'User',
          userEmail:       '',
          authToken:       '',
          isAuthenticated: false,
          messages:        [],
        });
      },
    }),
    { name: 'MitraCompanion' }
  )
);

// ── Custom hook: sync isMobile/tablet with window resize ──
export function useIsMobile() {
  const setIsMobile = useCompanionStore(s => s.setIsMobile);
  const setSidebar = useCompanionStore(s => s.setSidebar);
  const setContextPanel = useCompanionStore(s => s.setContextPanel);
  const isMobile = useCompanionStore(s => s.isMobile);

  useEffect(() => {
    const mobileMql = window.matchMedia('(max-width: 767px)');
    const tabletMql = window.matchMedia('(min-width: 768px) and (max-width: 1023px)');

    const handleResize = () => {
      const mobile = mobileMql.matches;
      const tablet = tabletMql.matches;
      setIsMobile(mobile);

      if (mobile) {
        // Mobile: sidebar hidden via CSS, context hidden via CSS
        setSidebar('collapsed');
        setContextPanel('closed');
      } else if (tablet) {
        // Tablet: collapsed icon sidebar, context panel closed by default (opens as overlay)
        setSidebar('collapsed');
        setContextPanel('closed');
      }
      // Desktop: keep user's preference (don't auto-change)
    };

    // Set initial value
    handleResize();

    mobileMql.addEventListener('change', handleResize);
    tabletMql.addEventListener('change', handleResize);
    return () => {
      mobileMql.removeEventListener('change', handleResize);
      tabletMql.removeEventListener('change', handleResize);
    };
  }, [setIsMobile, setSidebar, setContextPanel]);

  return isMobile;
}
