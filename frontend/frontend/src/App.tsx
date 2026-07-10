// App.tsx — Mitra v4 Companion Shell (fully responsive)
import React, { useEffect, useState, useCallback } from 'react';
import { useCompanionStore, useIsMobile } from './store/companion.store';
import { CompanionService } from './services/companion.service';
import {
  MessageCircle, Calendar, CheckSquare, Bell,
  LayoutGrid, PanelRight,
} from 'lucide-react';
import { cn } from './lib/utils';

// Shell components
import TopBar            from './components/shell/TopBar';
import Sidebar           from './components/shell/Sidebar';
import ConversationCenter from './components/shell/ConversationCenter';
import ContextPanel      from './components/shell/ContextPanel';
import InputBar          from './components/shell/InputBar';

const USER_ID = process.env.REACT_APP_USER_ID || 'user_default';

/* ── Bottom Navigation (Mobile Only) ──────────────────── */
interface BottomNavProps {
  activeSection: string;
  onSectionChange: (id: string) => void;
}

const bottomNavItems = [
  { id: 'chat',      icon: MessageCircle, label: 'Chat' },
  { id: 'calendar',  icon: Calendar,      label: 'Calendar' },
  { id: 'tasks',     icon: CheckSquare,   label: 'Tasks' },
  { id: 'reminders', icon: Bell,          label: 'Reminders' },
  { id: 'more',      icon: LayoutGrid,    label: 'More' },
];

const BottomNav: React.FC<BottomNavProps> = ({ activeSection, onSectionChange }) => {
  const { toggleMobileMenu, toggleMobileContext } = useCompanionStore();

  const handleTap = (id: string) => {
    if (id === 'more') {
      toggleMobileMenu();
    } else {
      onSectionChange(id);
    }
  };

  return (
    <nav className="bottom-nav zone-bottomnav" role="navigation" aria-label="Bottom navigation">
      {bottomNavItems.map(item => {
        const active = activeSection === item.id;
        const Icon = item.icon;
        return (
          <button
            key={item.id}
            id={`bottomnav-${item.id}`}
            onClick={() => handleTap(item.id)}
            className={cn('bottom-nav-item', active && 'active')}
            aria-current={active ? 'page' : undefined}
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
    sidebar, contextPanel, isMobile,
    setStatus, setSessionId, setUserName, setMemory,
    addMessage, addNotification, addContextItem,
  } = useCompanionStore();

  const [activeSection, setActiveSection] = useState('chat');

  // Sync isMobile with window size
  useIsMobile();

  // ── Startup: load greeting + memory ────────────────────
  useEffect(() => {
    const init = async () => {
      try {
        // Greeting
        const { greeting } = await CompanionService.getGreeting(USER_ID);
        addMessage({ role: 'assistant', content: greeting });

        // Memory
        const { facts } = await CompanionService.getMemory(USER_ID);
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
  const handleSend = useCallback(async (message: string) => {
    addMessage({ role: 'user', content: message });
    setStatus('thinking');

    try {
      const resp = await CompanionService.chat(USER_ID, message);
      setStatus('active');
      if (resp.session_id) setSessionId(resp.session_id);

      addMessage({
        role:             'assistant',
        content:          resp.message,
        intent:           resp.intent,
        capabilityResult: resp.capability_result || null,
        suggestedActions: resp.suggested_actions || [],
      });

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
      }
    } catch (err) {
      setStatus('error');
      addMessage({
        role:    'assistant',
        content: "I ran into a small issue — could you try again? I'm working on it.",
      });
      setTimeout(() => setStatus('active'), 3000);
    }
  }, [addMessage, addContextItem, setStatus, setSessionId]);

  // ── Shell class names ───────────────────────────────────
  const shellClass = [
    'mitra-shell',
    sidebar      === 'collapsed' ? 'sidebar-collapsed'  : '',
    contextPanel === 'closed'    ? 'context-hidden'     : '',
  ].filter(Boolean).join(' ');

  return (
    <div className={shellClass}>
      <TopBar />
      <Sidebar activeSection={activeSection} onSectionChange={setActiveSection} />
      <ConversationCenter />
      <InputBar onSend={handleSend} />
      <ContextPanel />
      {/* Mobile bottom navigation */}
      {isMobile && (
        <BottomNav activeSection={activeSection} onSectionChange={setActiveSection} />
      )}
    </div>
  );
};

export default App;
