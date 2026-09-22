import React, { useEffect, useRef, useCallback, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Zap, Calendar, ArrowRight, UserPlus,
  ShieldCheck, ChevronRight
} from 'lucide-react';
import { useCompanionStore } from '../../store/companion.store';
import { CompanionService } from '../../services/companion.service';
import { authApi } from '../../services/authApi';
import ConversationCard from '../cards/ConversationCard';
import { DailyBriefingCard } from '../cards/DailyBriefingCard';

const ThinkingIndicator = () => (
  <motion.div
    initial={{ opacity: 0, y: 6 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -4 }}
    className="flex items-center gap-3 py-2"
  >
    <div className="w-7 h-7 rounded-full bg-brand-muted border border-brand/30 flex items-center justify-center text-xs font-semibold text-brand-light flex-shrink-0">
      <Zap size={13} className="text-brand-light animate-pulse" />
    </div>
    <div className="px-3.5 py-2.5 rounded-2xl rounded-tl-sm bg-surface-elevated border border-border-subtle">
      <span className="inline-flex items-center gap-1">
        <span className="thinking-dot" />
        <span className="thinking-dot" />
        <span className="thinking-dot" />
      </span>
    </div>
  </motion.div>
);

const CompanionHomeView: React.FC<{
  onAction: (prompt: string) => void;
  onNavigate: (section: string) => void;
}> = ({ onAction, onNavigate }) => {
  const { userName, userEmail, isGuest, authStatus, setAuthModalOpen, userId } = useCompanionStore();
  const userFirstName = isGuest
    ? 'Guest User'
    : (userName ? userName.trim().split(' ')[0] : (userEmail ? userEmail.split('@')[0] : 'Mitra User'));

  // Guest conversion banner dismissal state (persisted per session)
  const [guestDismissed, setGuestDismissed] = useState(() => {
    return sessionStorage.getItem('mitra_guest_conversion_dismissed') === 'true';
  });

  // Briefing and status summary data
  const [briefing, setBriefing] = useState<any>(null);
  const [calendarConnected, setCalendarConnected] = useState<string | null>(null);

  // Fetch live briefing data and calendar connection status
  useEffect(() => {
    let isMounted = true;
    const loadStatus = async () => {
      try {
        const [briefingData, connData] = await Promise.all([
          CompanionService.getDailyBriefing(userId).catch(() => null),
          authApi.getConnections().catch(() => ({ connections: [] })),
        ]);

        if (!isMounted) return;

        if (briefingData) setBriefing(briefingData);

        const g = connData?.connections?.find((c: any) => c.provider.toLowerCase() === 'google' && c.status === 'active');
        const m = connData?.connections?.find((c: any) => c.provider.toLowerCase() === 'microsoft' && c.status === 'active');

        if (g) {
          setCalendarConnected('Google Calendar connected');
        } else if (m) {
          setCalendarConnected('Outlook Calendar connected');
        } else {
          setCalendarConnected('No calendar connected');
        }
      } catch {
        if (isMounted) setCalendarConnected('No calendar connected');
      }
    };

    loadStatus();
    return () => { isMounted = false; };
  }, [userId]);

  // Dynamic time-of-day greeting
  const getGreetingTime = () => {
    const hour = new Date().getHours();
    if (hour >= 5 && hour < 12) return 'Good morning';
    if (hour >= 12 && hour < 17) return 'Good afternoon';
    if (hour >= 17 && hour < 22) return 'Good evening';
    return 'Good night';
  };

  const currentDateDisplay = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'short',
    day: 'numeric',
  });

  const dismissGuestBanner = () => {
    setGuestDismissed(true);
    sessionStorage.setItem('mitra_guest_conversion_dismissed', 'true');
  };

  // Quick Action items as specified in user requirements
  const quickActionsList = [
    { id: 'cal_q',     label: "What's on my calendar today?", type: 'prompt', value: "What's on my calendar today?" },
    { id: 'tasks_q',   label: 'Summarize my tasks',           type: 'prompt', value: 'Summarize my tasks' },
    { id: 'remind_q',  label: 'Create a reminder',            type: 'prompt', value: 'Create a reminder' },
    { id: 'briefing_q',label: 'Run morning briefing',         type: 'prompt', value: 'Run my morning briefing' },
    { id: 'plan',      label: 'Plan my day',                  type: 'prompt', value: 'Plan my day' },
    { id: 'open_cal',  label: 'Open calendar',                type: 'nav',    value: 'calendar' },
  ];

  return (
    <div className="w-full max-w-2xl mx-auto flex flex-col gap-5 py-4 sm:py-6 px-3 sm:px-4">
      {/* ── 1. MITRA Companion Greeting ── */}
      <motion.div
        initial={{ opacity: 0, y: -6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
        className="flex items-center justify-between gap-4 p-4 sm:p-5 rounded-2xl bg-surface-elevated/80 border border-border-subtle/80 backdrop-blur-md shadow-sm"
      >
        <div className="flex items-center gap-3.5 min-w-0">
          <div className="w-11 h-11 rounded-2xl bg-brand/15 border border-brand/30 flex items-center justify-center text-brand-light flex-shrink-0 shadow-sm">
            <Zap size={22} className="text-brand-light" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-3xs font-bold uppercase tracking-wider text-brand-light">Personal AI Companion</span>
              <span className="w-1.5 h-1.5 rounded-full bg-state-success" />
            </div>
            <h1 className="text-base sm:text-lg font-bold text-text-primary tracking-tight truncate mt-0.5">
              {authStatus === 'LOADING' ? (
                <span className="inline-flex items-center gap-2">
                  {getGreetingTime()}, <span className="inline-block w-20 h-5 bg-surface-raised animate-pulse rounded align-middle" /> 👋
                </span>
              ) : (
                `${getGreetingTime()}, ${userFirstName} 👋`
              )}
            </h1>
            <p className="text-2xs text-text-muted mt-0.5">{currentDateDisplay}</p>
          </div>
        </div>

        {/* Subtle Sync Indicator Pill */}
        <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-surface-overlay border border-border-subtle text-2xs text-text-muted flex-shrink-0">
          <ShieldCheck size={13} className="text-brand-light" />
          <span className="font-medium text-text-secondary">
            {calendarConnected || 'MITRA Core'}
          </span>
        </div>
      </motion.div>

      {/* ── Guest Session Banner (dismissible) ── */}
      {isGuest && !guestDismissed && (
        <motion.div
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, height: 0 }}
          className="p-3.5 sm:p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs"
        >
          <div className="flex items-start gap-2.5 min-w-0 flex-1">
            <div className="w-8 h-8 rounded-xl bg-amber-500/20 border border-amber-500/30 flex items-center justify-center text-amber-300 flex-shrink-0 mt-0.5">
              <UserPlus size={15} />
            </div>
            <div className="min-w-0">
              <div className="font-semibold text-amber-200">Save Your Companion Workspace</div>
              <p className="text-2xs text-amber-300/80 leading-relaxed mt-0.5">
                You are in a guest session. Create an account to preserve conversations, schedule, and connected accounts.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-shrink-0 w-full sm:w-auto justify-end">
            <button
              onClick={dismissGuestBanner}
              className="px-2.5 py-1.5 rounded-xl text-2xs text-text-muted hover:text-text-primary hover:bg-surface-overlay transition-colors cursor-pointer"
            >
              Continue as guest
            </button>
            <button
              onClick={() => setAuthModalOpen(true)}
              className="px-3 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-black text-xs font-semibold shadow-md transition-all active:scale-95 cursor-pointer flex items-center gap-1"
            >
              <span>Create account</span>
              <ArrowRight size={12} />
            </button>
          </div>
        </motion.div>
      )}

      {/* ── 2. Primary Conversation Prompt Area ── */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.08, duration: 0.2 }}
        className="flex flex-col items-center justify-center py-6 sm:py-8 text-center px-4 select-none"
      >
        <div className="w-12 h-12 rounded-2xl bg-brand/10 border border-brand/25 flex items-center justify-center mb-3 shadow-glow">
          <Zap size={24} className="text-brand-light" />
        </div>
        <h2 className="text-lg sm:text-xl font-bold text-text-primary tracking-tight">
          How can I help you today?
        </h2>
        <p className="text-xs sm:text-sm text-text-muted max-w-md leading-relaxed mt-1.5">
          Ask questions, plan your daily agenda, manage tasks, or trigger workflows.
        </p>
      </motion.div>

      {/* ── 3. Secondary Contextual Actions (Subtle Chips) ── */}
      <div>
        <div className="text-3xs font-bold uppercase tracking-wider text-text-muted mb-2 px-1">
          Suggested Actions
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 w-full">
          {quickActionsList.map(action => (
            <button
              key={action.id}
              onClick={() => {
                if (action.type === 'nav') {
                  onNavigate(action.value);
                } else {
                  onAction(action.value);
                }
              }}
              className="companion-quick-chip group flex items-center justify-between text-left p-2.5 sm:p-3 rounded-xl border border-border-subtle bg-surface-overlay/80 hover:border-brand/40 hover:bg-surface-hover transition-all cursor-pointer active:scale-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
            >
              <span className="text-xs font-medium text-text-secondary group-hover:text-text-primary truncate">
                {action.label}
              </span>
              <ChevronRight size={13} className="text-text-muted group-hover:text-brand-light group-hover:translate-x-0.5 transition-all flex-shrink-0 ml-1 opacity-70" />
            </button>
          ))}
        </div>
      </div>

      {/* ── 4. Meaningful Schedule Context (Rendered only when events exist) ── */}
      {briefing && briefing.today_events && briefing.today_events.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          className="pt-2"
        >
          <div className="text-3xs font-bold uppercase tracking-wider text-text-muted mb-2 px-1 flex items-center justify-between">
            <span>Today's Schedule</span>
            <span className="text-3xs text-brand-light font-medium cursor-pointer hover:underline" onClick={() => onNavigate('calendar')}>
              View Calendar
            </span>
          </div>

          <div className="flex flex-col gap-2">
            {briefing.today_events.slice(0, 3).map((ev: any, idx: number) => (
              <div
                key={idx}
                className="p-3 rounded-xl bg-surface-elevated border border-border-subtle flex items-center justify-between text-xs hover:border-border-default transition-colors"
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <Calendar size={14} className="text-brand-light flex-shrink-0" />
                  <span className="font-semibold text-text-primary truncate">{ev.title || 'Scheduled Event'}</span>
                </div>
                <span className="text-2xs text-text-muted flex-shrink-0 font-medium">
                  {ev.start ? new Date(ev.start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Today'}
                </span>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
};

const ConversationCenter: React.FC = () => {
  const { messages, status } = useCompanionStore();
  const bottomRef = useRef<HTMLDivElement>(null);
  const isThinking = status === 'thinking';

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isThinking]);

  // Handle action prompt execution
  const handleActionSend = useCallback((prompt: string) => {
    const send = (window as any).__MITRA_SEND__;
    if (send) send(prompt);
  }, []);

  const handleNavigate = useCallback((section: string) => {
    const nav = (window as any).__MITRA_NAV__;
    if (nav) nav(section);
  }, []);

  const handleActionConfirm = useCallback((action: string, _messageId: string) => {
    const nav = (window as any).__MITRA_NAV__;
    const send = (window as any).__MITRA_SEND__;
    const actionLower = action.toLowerCase();

    if (actionLower.includes('calendar') || actionLower.includes('view_event') || actionLower.includes('view event')) {
      if (nav) nav('calendar');
    } else if (actionLower.includes('task') || actionLower.includes('view_task') || actionLower.includes('board')) {
      if (nav) nav('tasks');
    } else if (actionLower.includes('reminder') || actionLower.includes('create_reminder')) {
      if (nav) nav('reminders');
    } else if (actionLower.includes('workflow')) {
      if (nav) nav('workflows');
    } else if (send) {
      send(action);
    }
  }, []);

  return (
    <main className="zone-center flex flex-col overflow-hidden bg-surface-base w-full">
      <div className="flex-1 overflow-y-auto px-2.5 sm:px-6 py-4 overscroll-contain">
        <div className="companion-container">
          {messages.length === 0 ? (
            <CompanionHomeView
              onAction={handleActionSend}
              onNavigate={handleNavigate}
            />
          ) : (
            <div className="space-y-3 sm:space-y-4">
              <AnimatePresence initial={false}>
                <DailyBriefingCard onActionClick={handleActionSend} />
                {messages.map(msg => (
                  <ConversationCard
                    key={msg.id}
                    message={msg}
                    onActionConfirm={handleActionConfirm}
                  />
                ))}
                {isThinking && (
                  <ThinkingIndicator key="thinking" />
                )}
              </AnimatePresence>
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      </div>
    </main>
  );
};

export default ConversationCenter;

