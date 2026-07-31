import React, { useEffect, useState, useCallback } from 'react';
import Sidebar from './components/shell/Sidebar';
import TopBar from './components/shell/TopBar';
import ConversationCenter from './components/shell/ConversationCenter';
import ContextPanel from './components/shell/ContextPanel';
import InputBar from './components/shell/InputBar';
import SettingsModal from './components/shell/SettingsModal';
import AuthModal from './components/shell/AuthModal';
import Toast, { showToast } from './components/shell/Toast';
import CalendarPage from './components/pages/CalendarPage';
import TasksPage from './components/pages/TasksPage';
import RemindersPage from './components/pages/RemindersPage';
import WorkflowsPage from './components/pages/WorkflowsPage';
import KnowledgePage from './components/pages/KnowledgePage';
import { useCompanionStore } from './store/companion.store';
import { CompanionService } from './services/companion.service';
import { cn } from './lib/utils';
import { LayoutDashboard, Calendar, CheckSquare, BookOpen, PlayCircle, PanelRight } from 'lucide-react';

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

/* Helper for speaking voice responses out loud */
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

/* Mobile bottom nav items */
const mobileNavItems = [
  { id: 'chat',      label: 'Chat',      icon: LayoutDashboard },
  { id: 'calendar',  label: 'Calendar',  icon: Calendar },
  { id: 'tasks',     label: 'Tasks',     icon: CheckSquare },
  { id: 'knowledge', label: 'Knowledge', icon: BookOpen },
  { id: 'workflows', label: 'Workflows', icon: PlayCircle },
];

/* ── Mobile Bottom Navigation ─────────────────────────── */
const MobileBottomNav: React.FC<{
  active: string;
  onSelect: (id: string) => void;
}> = ({ active, onSelect }) => {
  const toggleMobileContext = useCompanionStore(s => s.toggleMobileContext);

  return (
    <nav className="zone-bottomnav mobile-bottom-nav bottom-nav flex flex-row items-center justify-around w-full bg-surface-raised border-t border-border-subtle py-1.5 px-2">
      {mobileNavItems.map(item => {
        const Icon = item.icon;
        const isActive = active === item.id;
        return (
          <button
            key={item.id}
            onClick={() => onSelect(item.id)}
            className={`bottom-nav-item ${isActive ? 'active' : ''}`}
            aria-label={item.label}
          >
            <Icon size={20} className="bottom-nav-icon" />
            <span>{item.label}</span>
          </button>
        );
      })}
      {/* Context panel trigger on mobile */}
      <button
        id="bottomnav-context"
        onClick={toggleMobileContext}
        className="bottom-nav-item"
        aria-label="Context panel"
      >
        <PanelRight size={20} className="bottom-nav-icon" />
        <span>Context</span>
      </button>
    </nav>
  );
};

/* ── Main App ─────────────────────────────────────────── */
const App: React.FC = () => {
  const {
    userId, sidebar, contextPanel, isMobile, authModalOpen, setAuthModalOpen,
    setStatus, setSessionId, setUserName, setMemory,
    addMessage, addNotification, addContextItem,
  } = useCompanionStore();

  const [activeSection, setActiveSection] = useState('chat');
  const [settingsOpen, setSettingsOpen] = useState(false);

  useEffect(() => {
    (window as any).__MITRA_SETTINGS__ = () => setSettingsOpen(true);
  }, []);

  // Sync isMobile with window size
  useIsMobile();

  const sidebarCollapsed = sidebar === 'collapsed';
  const contextHidden = contextPanel === 'closed';

  // ── Startup: load greeting + memory ────────────────────
  useEffect(() => {
    const init = async () => {
      try {
        // Greeting
        const { greeting } = await CompanionService.getGreeting(userId);
        addMessage({ role: 'assistant', content: greeting });

        // Memory
        const { facts } = await CompanionService.getMemory(userId);
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
        // API not yet available — still show the shell with a fallback greeting
        addMessage({
          role: 'assistant',
          content: "Hey! I'm Mitra, your AI companion. I'm here whenever you need me — just say the word.",
        });
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

      // If sent via Voice, automatically speak response out loud!
      if (isVoice && resp.message) {
        speakAudioResponse(resp.message);
      }

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
        {activeSection === 'calendar' && <CalendarPage onChatNavigate={handleChatNavigate} />}
        {activeSection === 'tasks' && <TasksPage onChatNavigate={handleChatNavigate} />}
        {activeSection === 'reminders' && <RemindersPage onChatNavigate={handleChatNavigate} />}
        {activeSection === 'workflows' && <WorkflowsPage onChatNavigate={handleChatNavigate} />}
        {activeSection === 'knowledge' && <KnowledgePage onChatNavigate={handleChatNavigate} />}
      </div>

      {/* Bottom Chat Bar — grid-area 'input' */}
      {activeSection === 'chat' && <InputBar onSend={handleSend} />}

      {/* Right Zone — Context Panel (grid-area 'context') */}
      <ContextPanel />

      {/* Mobile Bottom Navigation (screens < 1024px) */}
      {isMobile && (
        <MobileBottomNav active={activeSection} onSelect={setActiveSection} />
      )}

      {/* Settings Modal */}
      <SettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} />

      {/* Auth Modal */}
      <AuthModal open={authModalOpen} onClose={() => setAuthModalOpen(false)} />

      {/* Global Toast Notifications */}
      <Toast />
    </div>
  );
};

export default App;
