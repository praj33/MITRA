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
import InstallPwaBanner from './components/shell/InstallPwaBanner';
import Toast, { showToast } from './components/shell/Toast';
import CalendarPage from './components/pages/CalendarPage';
import TasksPage from './components/pages/TasksPage';
import RemindersPage from './components/pages/RemindersPage';
import WorkflowsPage from './components/pages/WorkflowsPage';
import KnowledgePage from './components/pages/KnowledgePage';
import AnalyticsPage from './components/pages/AnalyticsPage';
import { useCompanionStore } from './store/companion.store';
import { CompanionService } from './services/companion.service';
import { cn } from './lib/utils';
import { LayoutDashboard, Calendar, CheckSquare, PlayCircle, TrendingUp } from 'lucide-react';

const useIsMobile = () => {
  const setIsMobile = useCompanionStore(s => s.setIsMobile);
  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 1024);
    check();
    window.addEventListener('resize', check);
    return () => window.removeEventListener('resize', check);
  }, [setIsMobile]);
};

const speakAudioResponse = async (text: string) => {
  if (!text) return;
  try {
    const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    const apiKey = process.env.REACT_APP_API_KEY || '';
    const res = await fetch(`${apiUrl}/api/tts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': apiKey },
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
    console.warn('TTS service unavailable, falling back to Web Speech API:', err);
  }

  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    if (window.speechSynthesis.paused) window.speechSynthesis.resume();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    window.speechSynthesis.speak(utterance);
  }
};

const mobileNavItems = [
  { id: 'chat',      label: 'Chat',      icon: LayoutDashboard },
  { id: 'analytics', label: 'Analytics', icon: TrendingUp },
  { id: 'calendar',  label: 'Calendar',  icon: Calendar },
  { id: 'tasks',     label: 'Tasks',     icon: CheckSquare },
  { id: 'workflows', label: 'Workflows', icon: PlayCircle },
];

const MobileBottomNav: React.FC<{
  active: string;
  onSelect: (id: string) => void;
}> = ({ active, onSelect }) => {
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 grid grid-cols-5 items-center w-full bg-white/80 dark:bg-iosGray-900/80 backdrop-blur-xl border-t border-iosGray-200/50 dark:border-iosGray-800/50 py-1.5 px-0.5 select-none lg:hidden">
      {mobileNavItems.map(item => {
        const Icon = item.icon;
        const isActive = active === item.id;
        return (
          <button
            key={item.id}
            onClick={() => onSelect(item.id)}
            className={cn(
              "flex flex-col items-center justify-center py-1 px-1 transition-all relative cursor-pointer min-h-[44px]",
              isActive ? "text-iosBlue-500 font-semibold" : "text-iosGray-500 hover:text-iosGray-700"
            )}
            aria-label={item.label}
          >
            <Icon size={18} className={cn("transition-transform mb-0.5", isActive && "scale-110 text-iosBlue-500")} />
            <span className="text-[10px] tracking-tight truncate w-full text-center">{item.label}</span>
            {isActive && (
              <motion.div
                layoutId="activeTabIndicator"
                className="absolute bottom-0 w-5 h-0.5 bg-iosBlue-500 rounded-full"
              />
            )}
          </button>
        );
      })}
    </nav>
  );
};

const App: React.FC = () => {
  const {
    userId, sidebar, contextPanel, isMobile, authModalOpen, setAuthModalOpen,
    setStatus, setSessionId, setUserName, setMemory, setAuth,
    addMessage, addNotification, addContextItem,
  } = useCompanionStore();

  const [activeSection, setActiveSection] = useState('chat');
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [focusOpen, setFocusOpen] = useState(false);
  const [cmdOpen, setCmdOpen] = useState(false);
  const [memoryOpen, setMemoryOpen] = useState(false);
  const [voiceTalkOpen, setVoiceTalkOpen] = useState(false);
  const [mindMapOpen, setMindMapOpen] = useState(false);

  useEffect(() => {
    (window as any).__MITRA_SETTINGS__ = () => setSettingsOpen(true);
  }, []);

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

  useIsMobile();

  const sidebarCollapsed = sidebar === 'collapsed';
  const contextHidden = contextPanel === 'closed';

  useEffect(() => {
    const init = async () => {
      const existingToken = localStorage.getItem('mitra_auth_token');
      if (existingToken) {
        try {
          const res = await CompanionService.getMe(existingToken);
          if (res?.user) setAuth(res.user, existingToken);
        } catch { /* Token expired */ }
      }

      const activeUserId = useCompanionStore.getState().userId;

      try {
        const { facts } = await CompanionService.getMemory(activeUserId);
        if (facts?.name) setUserName(facts.name);
        setMemory(facts);

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
        // API fallback
      }
    };
    init();
  }, []);

  const handleSend = useCallback(async (message: string, _isVoice = false) => {
    setActiveSection('chat');
    addMessage({ role: 'user', content: message });
    setStatus('thinking');

    try {
      const resp = await CompanionService.chat(userId, message);
      setStatus('active');
      if (resp.session_id) setSessionId(resp.session_id);

      addMessage({
        role: 'assistant',
        content: resp.message,
        intent: resp.intent,
        capabilityResult: resp.capability_result || null,
        suggestedActions: resp.suggested_actions || [],
      });

      if (resp.capability_result?.data) {
        addContextItem({
          id: `ctx_cap_${Date.now()}`,
          type: (resp.capability_result.capability === 'calendar' ? 'calendar' :
                 resp.capability_result.capability === 'email'    ? 'email'    :
                 resp.capability_result.capability === 'task'     ? 'task'     : 'note'),
          title: resp.capability_result.summary,
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
        role: 'assistant',
        content: "I ran into a small issue - could you try again? I'm working on it.",
      });
      setTimeout(() => setStatus('active'), 3000);
    }
  }, [userId, addMessage, addContextItem, setStatus, setSessionId, setActiveSection]);

  useEffect(() => { (window as any).__MITRA_SEND__ = handleSend; }, [handleSend]);
  useEffect(() => { (window as any).__MITRA_SETTINGS__ = () => setSettingsOpen(true); }, []);
  useEffect(() => { (window as any).__MITRA_FOCUS__ = () => setFocusOpen(prev => !prev); }, []);
  useEffect(() => { (window as any).__MITRA_SEARCH__ = () => setCmdOpen(true); }, []);
  useEffect(() => { (window as any).__MITRA_MEMORY__ = () => setMemoryOpen(prev => !prev); }, []);
  useEffect(() => { (window as any).__MITRA_VOICE_TALK__ = () => setVoiceTalkOpen(prev => !prev); }, []);
  useEffect(() => { (window as any).__MITRA_MINDMAP__ = () => setMindMapOpen(prev => !prev); }, []);
  useEffect(() => { (window as any).__MITRA_NAV__ = setActiveSection; }, [setActiveSection]);

  const handleChatNavigate = useCallback((msg: string) => {
    setActiveSection('chat');
    handleSend(msg);
  }, [handleSend]);

  return (
    <div className={cn(
      'h-screen flex overflow-hidden bg-gradient-to-b from-iosGray-100 to-white dark:from-black dark:to-iosGray-900 font-sf',
      sidebarCollapsed && 'lg:pl-16',
      contextHidden && 'lg:pr-0'
    )}>
      <TopBar />
      <Sidebar activeSection={activeSection} onSectionChange={setActiveSection} />

      <div className={cn("flex-1 flex flex-col min-w-0 transition-all duration-300", activeSection === 'chat' ? 'overflow-hidden' : 'overflow-y-auto pb-24 sm:pb-20')}>
        {activeSection === 'chat' && <ConversationCenter />}
        {activeSection === 'analytics' && <AnalyticsPage onChatNavigate={handleChatNavigate} />}
        {activeSection === 'calendar' && <CalendarPage onChatNavigate={handleChatNavigate} />}
        {activeSection === 'tasks' && <TasksPage onChatNavigate={handleChatNavigate} />}
        {activeSection === 'reminders' && <RemindersPage onChatNavigate={handleChatNavigate} />}
        {activeSection === 'workflows' && <WorkflowsPage onChatNavigate={handleChatNavigate} />}
        {activeSection === 'knowledge' && <KnowledgePage onChatNavigate={handleChatNavigate} />}
      </div>

      {activeSection === 'chat' && <InputBar onSend={handleSend} />}

      <ContextPanel />

      {isMobile && <MobileBottomNav active={activeSection} onSelect={setActiveSection} />}

      <CommandPaletteModal isOpen={cmdOpen} onClose={() => setCmdOpen(false)} />
      <MemoryDashboardModal isOpen={memoryOpen} onClose={() => setMemoryOpen(false)} />
      <VoiceTalkModal isOpen={voiceTalkOpen} onClose={() => setVoiceTalkOpen(false)} />
      <MemoryMindMapModal isOpen={mindMapOpen} onClose={() => setMindMapOpen(false)} />
      <FocusTimerModal isOpen={focusOpen} onClose={() => setFocusOpen(false)} />
      <SettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} />
      <AuthModal open={authModalOpen} onClose={() => setAuthModalOpen(false)} />
      <InstallPwaBanner />
      <Toast />
    </div>
  );
};

export default App;
