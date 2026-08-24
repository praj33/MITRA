import React, { useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import Sidebar from './components/shell/Sidebar';
import TopBar from './components/shell/TopBar';
import ConversationCenter from './components/shell/ConversationCenter';
import ContextPanel from './components/shell/ContextPanel';
import InputBar from './components/shell/InputBar';
import SettingsModal from './components/shell/SettingsModal';
import AuthModal from './components/shell/AuthModal';
import { FocusTimerModal } from './components/modals/FocusTimerModal';
import { CommandPaletteModal } from './components/modals/CommandPaletteModal';
import { MemoryDashboardModal } from './components/modals/MemoryDashboardModal';
import { VoiceTalkModal } from './components/modals/VoiceTalkModal';
import { MemoryMindMapModal } from './components/modals/MemoryMindMapModal';
import { IntegrationsModal } from './components/modals/IntegrationsModal';
import InstallPwaBanner from './components/shell/InstallPwaBanner';
import Toast, { showToast } from './components/shell/Toast';
import CalendarPage from './components/pages/CalendarPage';
import TasksPage from './components/pages/TasksPage';
import RemindersPage from './components/pages/RemindersPage';
import WorkflowsPage from './components/pages/WorkflowsPage';
import KnowledgePage from './components/pages/KnowledgePage';
import AnalyticsPage from './components/pages/AnalyticsPage';
import Login from './components/auth/Login';
import { useCompanionStore } from './store/companion.store';
import { CompanionService } from './services/companion.service';
import { cn } from './lib/utils';
import { LayoutDashboard, Calendar, CheckSquare, PlayCircle, TrendingUp } from 'lucide-react';

/* Helper hook to keep isMobile store value in sync */
const useIsMobile = () => {
  const setIsMobile = useCompanionStore(s => s.setIsMobile);
  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 1024);
    check();
    window.addEventListener('resize', check);
    return () => window.removeEventListener('resize', check);
  }, [setIsMobile]);
};

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const speakAudioResponse = async (text: string) => {
  if (!text) return;
  try {
    const res = await fetch('https://ai-assistant-backend-8hur.onrender.com/api/tts', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': 'localtest',
      },
      body: JSON.stringify({ text, language: 'en' }),
    });
    const data = await res.json();
    if (data.audio_base64) {
      const audio = new Audio(`data:audio/${data.audio_format || 'wav'};base64,${data.audio_base64}`);
      audio.setAttribute('playsinline', 'true');
      await audio.play();
      return;
    }
  } catch (err) {
    console.warn('Nilesh TTS service unavailable, falling back to Web Speech API:', err);
  }

  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    if (window.speechSynthesis.paused) {
      window.speechSynthesis.resume();
    }
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    window.speechSynthesis.speak(utterance);
  }
};

/* Mobile bottom nav items — 5 primary tabs for clean mobile fit */
const mobileNavItems = [
  { id: 'chat',      label: 'Chat',      icon: LayoutDashboard },
  { id: 'analytics', label: 'Analytics', icon: TrendingUp },
  { id: 'calendar',  label: 'Calendar',  icon: Calendar },
  { id: 'tasks',     label: 'Tasks',     icon: CheckSquare },
  { id: 'workflows', label: 'Workflows', icon: PlayCircle },
];

/* ── Mobile Bottom Navigation ─────────────────────────── */
const MobileBottomNav: React.FC<{
  active: string;
  onSelect: (id: string) => void;
}> = ({ active, onSelect }) => {
  return (
    <nav className="zone-bottomnav mobile-bottom-nav bottom-nav grid grid-cols-5 items-center w-full bg-surface-raised border-t border-border-subtle py-1.5 px-0.5 select-none">
      {mobileNavItems.map(item => {
        const Icon = item.icon;
        const isActive = active === item.id;
        return (
          <button
            key={item.id}
            onClick={() => onSelect(item.id)}
            className={cn(
              "flex flex-col items-center justify-center py-1 px-1 transition-all relative cursor-pointer min-h-[44px]",
              isActive ? "text-brand-light font-semibold" : "text-text-muted hover:text-text-secondary"
            )}
            aria-label={item.label}
          >
            <Icon size={18} className={cn("transition-transform mb-0.5", isActive && "scale-110 text-brand-light")} />
            <span className="text-[10px] tracking-tight truncate w-full text-center">{item.label}</span>
            {isActive && (
              <motion.div
                layoutId="activeTabIndicator"
                className="absolute bottom-0 w-5 h-0.5 bg-brand-light rounded-full shadow-glow"
              />
            )}
          </button>
        );
      })}
    </nav>
  );
};

/* ── Main App ─────────────────────────────────────────── */
const App: React.FC = () => {
  const {
    userId, sidebar, contextPanel, isMobile, authModalOpen, setAuthModalOpen,
    setStatus, setSessionId, setUserName, setMemory, setAuth,
    addMessage, addNotification, addContextItem,
  } = useCompanionStore();

  const [activeSection, setActiveSection] = useState(() => {
    return (window.location.pathname === '/login' || window.location.hash === '#login') ? 'login' : 'chat';
  });
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [focusOpen, setFocusOpen] = useState(false);
  const [cmdOpen, setCmdOpen] = useState(false);
  const [memoryOpen, setMemoryOpen] = useState(false);
  const [voiceTalkOpen, setVoiceTalkOpen] = useState(false);
  const [mindMapOpen, setMindMapOpen] = useState(false);
  const [integrationsOpen, setIntegrationsOpen] = useState(false);

  useEffect(() => {
    (window as any).__MITRA_SETTINGS__ = () => setSettingsOpen(true);
    (window as any).__MITRA_INTEGRATIONS__ = () => setIntegrationsOpen(true);
  }, []);

  // Global Ctrl+K / Cmd+K listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setCmdOpen(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Sync isMobile with window size
  useIsMobile();

  const sidebarCollapsed = sidebar === 'collapsed';
  const contextHidden = contextPanel === 'closed';

  // ── Startup: load session + greeting + memory ───────────
  useEffect(() => {
    const init = async () => {
      // 1. Session recovery for logged-in user
      const existingToken = localStorage.getItem('mitra_auth_token');
      if (existingToken) {
        try {
          const res = await CompanionService.getMe(existingToken);
          if (res?.user) {
            setAuth(res.user, existingToken);
          }
        } catch {
          // Token expired or server restarted
        }
      }

      const activeUserId = useCompanionStore.getState().userId;

      try {
        // Memory
        const { facts } = await CompanionService.getMemory(activeUserId);
        if (facts?.name) setUserName(facts.name);
        setMemory(facts);

        // Seed a couple of context items
        addContextItem({
          id: 'ctx_cal_1', type: 'calendar',
          title: "Today's Calendar", subtitle: 'No events yet',
          timestamp: new Date().toISOString(),
        });
        addContextItem({
          id: 'ctx_task_1', type: 'task',
          title: 'Pending Tasks', subtitle: 'Open task board to see all',
          timestamp: new Date().toISOString(),
        });

        addNotification({
          type: 'success', title: 'Mitra is ready',
          body: 'Your AI companion is active and connected.', read: false,
        });
        showToast('success', 'Mitra Connected', 'All systems operational');
      } catch {
        // API fallback - keep messages clean so Welcome Screen renders
      }
    };
    init();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Send message handler ────────────────────────────────
  const handleSend = useCallback(async (message: string, isVoice = false) => {
    // If on another page, switch to chat first
    setActiveSection('chat');

    addMessage({ role: 'user', content: message });
    setStatus('thinking');

    try {
      const resp = await CompanionService.chat(userId, message);
      setStatus('active');
      if (resp.session_id) setSessionId(resp.session_id);

      addMessage({
        role:             'assistant',
        content:          resp.message,
        intent:           resp.intent,
        capabilityResult: resp.capability_result || null,
        suggestedActions: resp.suggested_actions || [],
      });

      // Auto TTS playback removed — TTS is off by default and only plays when user manually clicks speaker icon on message

      // Push capability result to context panel
      if (resp.capability_result?.data) {
        addContextItem({
          id:       `ctx_cap_${Date.now()}`,
          type:     (resp.capability_result.capability === 'calendar' ? 'calendar' :
                     resp.capability_result.capability === 'email'    ? 'email'    :
                     resp.capability_result.capability === 'task'     ? 'task'     : 'note'),
          title:    resp.capability_result.summary,
          subtitle: resp.capability_result.capability,
          timestamp: new Date().toISOString(),
        });
        showToast(
          resp.capability_result.status === 'success' ? 'success' : 'info',
          resp.capability_result.summary,
          resp.capability_result.capability
        );
      }
    } catch (err) {
      setStatus('error');
      addMessage({
        role:    'assistant',
        content: "I ran into a small issue — could you try again? I'm working on it.",
      });
      setTimeout(() => setStatus('active'), 3000);
    }
  }, [userId, addMessage, addContextItem, setStatus, setSessionId, setActiveSection]);

  // Expose handleSend for suggestion chips
  useEffect(() => { (window as any).__MITRA_SEND__ = handleSend; }, [handleSend]);
  // Expose settings toggle for Sidebar
  useEffect(() => { (window as any).__MITRA_SETTINGS__ = () => setSettingsOpen(true); }, []);
  // Expose focus toggle
  useEffect(() => { (window as any).__MITRA_FOCUS__ = () => setFocusOpen(prev => !prev); }, []);
  // Expose search / command palette toggle
  useEffect(() => { (window as any).__MITRA_SEARCH__ = () => setCmdOpen(true); }, []);
  // Expose memory dashboard toggle
  useEffect(() => { (window as any).__MITRA_MEMORY__ = () => setMemoryOpen(prev => !prev); }, []);
  // Expose full-screen voice talk mode
  useEffect(() => { (window as any).__MITRA_VOICE_TALK__ = () => setVoiceTalkOpen(prev => !prev); }, []);
  // Expose brain mind map visualizer
  useEffect(() => { (window as any).__MITRA_MINDMAP__ = () => setMindMapOpen(prev => !prev); }, []);
  // Expose page navigation for action buttons
  useEffect(() => { (window as any).__MITRA_NAV__ = setActiveSection; }, [setActiveSection]);

  // Navigate to chat with a pre-filled message from other pages
  const handleChatNavigate = useCallback((msg: string) => {
    setActiveSection('chat');
    handleSend(msg);
  }, [handleSend]);

  return (
    <div className={cn(
      'mitra-shell',
      sidebarCollapsed && 'sidebar-collapsed',
      contextHidden && 'context-hidden'
    )}>
      {/* Top Header */}
      <TopBar />

      {/* Left Zone — Sidebar */}
      <Sidebar activeSection={activeSection} onSectionChange={setActiveSection} />

      {/* Center Zone — Main Workspace (Chat or Full Page) */}
      <div className={cn("zone-center flex flex-col flex-1 min-w-0 h-full", activeSection === 'chat' ? 'overflow-hidden' : 'overflow-y-auto pb-24 sm:pb-20')}>
        {activeSection === 'chat' && <ConversationCenter />}
        {activeSection === 'analytics' && <AnalyticsPage onChatNavigate={handleChatNavigate} />}
        {activeSection === 'calendar' && <CalendarPage onChatNavigate={handleChatNavigate} />}
        {activeSection === 'tasks' && <TasksPage onChatNavigate={handleChatNavigate} />}
        {activeSection === 'reminders' && <RemindersPage onChatNavigate={handleChatNavigate} />}
        {activeSection === 'workflows' && <WorkflowsPage onChatNavigate={handleChatNavigate} />}
        {activeSection === 'knowledge' && <KnowledgePage onChatNavigate={handleChatNavigate} />}
        {activeSection === 'login' && <Login onToggleForm={() => setActiveSection('chat')} />}
      </div>

      {/* Bottom Chat Bar — grid-area 'input' */}
      {activeSection === 'chat' && <InputBar onSend={handleSend} />}

      {/* Right Zone — Context Panel (grid-area 'context') */}
      <ContextPanel />

      {/* Mobile Bottom Navigation (screens < 1024px) */}
      {isMobile && (
        <MobileBottomNav active={activeSection} onSelect={setActiveSection} />
      )}

      {/* Spotlight Command Palette (Ctrl + K) */}
      <CommandPaletteModal isOpen={cmdOpen} onClose={() => setCmdOpen(false)} />

      {/* Companion Memory Dashboard Modal */}
      <MemoryDashboardModal isOpen={memoryOpen} onClose={() => setMemoryOpen(false)} />

      {/* Full-Screen Hands-Free Voice Talk Mode */}
      <VoiceTalkModal isOpen={voiceTalkOpen} onClose={() => setVoiceTalkOpen(false)} />

      {/* Interactive Brain Mind Map Visualizer */}
      <MemoryMindMapModal isOpen={mindMapOpen} onClose={() => setMindMapOpen(false)} />

      {/* Focus Session & Soundscape Modal */}
      <FocusTimerModal isOpen={focusOpen} onClose={() => setFocusOpen(false)} />

      {/* Settings Modal */}
      <SettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} />

      {/* Auth Modal */}
      <AuthModal open={authModalOpen} onClose={() => setAuthModalOpen(false)} />

      {/* Integrations Modal */}
      <IntegrationsModal isOpen={integrationsOpen} onClose={() => setIntegrationsOpen(false)} />

      {/* Native PWA Install Banner */}
      <InstallPwaBanner />

      {/* Global Toast Notifications */}
      <Toast />
    </div>
  );
};

export default App;
