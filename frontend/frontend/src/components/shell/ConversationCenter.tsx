import React, { useEffect, useRef, useCallback, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Zap, Calendar, CheckSquare, Bell, ArrowRight, UserPlus,
  Clock, ShieldCheck, ChevronRight
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
    <div className="w-full max-w-2xl mx-auto flex flex-col gap-4 sm:gap-5 py-2 sm:py-4 px-2 sm:px-4">
      {/* ── Section A: Greeting & Compact Daily Status ───────────── */}
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-2xl bg-gradient-to-r from-brand/15 via-surface-elevated to-surface-elevated border border-brand/25 p-4 sm:p-5 shadow-lg flex flex-col gap-3.5 backdrop-blur-md"
      >
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-3xs font-bold uppercase tracking-wider text-brand-light">Personal AI Companion</span>
              <span className="w-1.5 h-1.5 rounded-full bg-state-success" />
            </div>
            <h1 className="text-base sm:text-xl font-bold text-text-primary mt-1 tracking-tight">
              {authStatus === 'LOADING' ? (
                <span className="inline-flex items-center gap-2">
                  {getGreetingTime()}, <span className="inline-block w-24 h-5 sm:h-6 bg-surface-raised animate-pulse rounded-md align-middle" /> 👋
                </span>
              ) : (
                `${getGreetingTime()}, ${userFirstName} 👋`
              )}
            </h1>
            <p className="text-2xs sm:text-xs text-text-muted mt-0.5">{currentDateDisplay}</p>
          </div>

          <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-brand/15 border border-brand/30 flex items-center justify-center flex-shrink-0">
            <Zap size={18} className="text-brand-light" />
          </div>
        </div>

        {/* Compact Daily Status Summary */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
          {/* Calendar Status */}
          <div className="p-2.5 rounded-xl bg-surface-overlay/80 border border-border-subtle flex flex-col gap-1">
            <div className="flex items-center gap-1.5 text-text-muted">
              <Calendar size={13} className="text-brand-light flex-shrink-0" />
              <span className="text-3xs font-medium uppercase tracking-wider truncate">Calendar</span>
            </div>
            <div className="text-xs font-semibold text-text-primary truncate">
              {briefing && briefing.today_events_count !== undefined
                ? briefing.today_events_count > 0
                  ? `${briefing.today_events_count} events today`
                  : 'No events today'
                : calendarConnected || 'No calendar connected'}
            </div>
          </div>

          {/* Tasks Status */}
          <div className="p-2.5 rounded-xl bg-surface-overlay/80 border border-border-subtle flex flex-col gap-1">
            <div className="flex items-center gap-1.5 text-text-muted">
              <CheckSquare size={13} className="text-emerald-400 flex-shrink-0" />
              <span className="text-3xs font-medium uppercase tracking-wider truncate">Tasks</span>
            </div>
            <div className="text-xs font-semibold text-text-primary truncate">
              {briefing && briefing.pending_tasks_count !== undefined
                ? briefing.pending_tasks_count > 0
                  ? `${briefing.pending_tasks_count} pending`
                  : 'No tasks yet'
                : 'No tasks yet'}
            </div>
          </div>

          {/* Reminders Status */}
          <div className="p-2.5 rounded-xl bg-surface-overlay/80 border border-border-subtle flex flex-col gap-1">
            <div className="flex items-center gap-1.5 text-text-muted">
              <Bell size={13} className="text-amber-400 flex-shrink-0" />
              <span className="text-3xs font-medium uppercase tracking-wider truncate">Reminders</span>
            </div>
            <div className="text-xs font-semibold text-text-primary truncate">
              {briefing && briefing.active_reminders_count !== undefined
                ? briefing.active_reminders_count > 0
                  ? `${briefing.active_reminders_count} active`
                  : 'No reminders today'
                : 'No reminders today'}
            </div>
          </div>

          {/* Cloud Sync Provider Status */}
          <div className="p-2.5 rounded-xl bg-surface-overlay/80 border border-border-subtle flex flex-col gap-1">
            <div className="flex items-center gap-1.5 text-text-muted">
              <ShieldCheck size={13} className="text-indigo-400 flex-shrink-0" />
              <span className="text-3xs font-medium uppercase tracking-wider truncate">Sync</span>
            </div>
            <div className="text-xs font-semibold text-text-primary truncate">
              {calendarConnected === 'Google Calendar connected'
                ? 'Google Cloud'
                : calendarConnected === 'Outlook Calendar connected'
                ? 'Microsoft 365'
                : 'Local Mitra'}
            </div>
          </div>
        </div>
      </motion.div>

      {/* ── Section E: Guest Account Conversion Banner (Non-intrusive) ──── */}
      {isGuest && !guestDismissed && (
        <motion.div
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, height: 0 }}
          className="p-3.5 sm:p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs"
        >
          <div className="flex items-start gap-2.5 min-w-0 flex-1">
            <div className="w-8 h-8 rounded-xl bg-amber-500/20 border border-amber-500/30 flex items-center justify-center text-amber-300 flex-shrink-0 mt-0.5">
              <UserPlus size={16} />
            </div>
            <div className="min-w-0">
              <div className="font-semibold text-amber-200">Save Your Companion Workspace</div>
              <p className="text-2xs text-amber-300/80 leading-relaxed mt-0.5">
                You are using a temporary guest session. Create an account to save your conversations, tasks, reminders, and integrations.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-shrink-0 w-full sm:w-auto justify-end">
            <button
              onClick={dismissGuestBanner}
              className="px-3 py-1.5 rounded-xl text-2xs text-text-muted hover:text-text-primary hover:bg-surface-overlay transition-colors cursor-pointer"
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

      {/* ── Section B: Main Assistant Area ────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="flex flex-col items-center justify-center py-4 text-center px-4 select-none"
      >
        <div className="w-11 h-11 sm:w-12 sm:h-12 rounded-2xl bg-brand/15 border border-brand/35 flex items-center justify-center mb-2.5 shadow-glow">
          <Zap size={22} className="text-brand-light" />
        </div>
        <h2 className="text-base sm:text-lg font-bold text-text-primary">
          How can I help you today?
        </h2>
        <p className="text-xs sm:text-sm text-text-muted max-w-sm leading-relaxed mt-1">
          I'm Mitra — your personal AI companion. Ask questions, manage your schedule, plan tasks, or run workflows.
        </p>
      </motion.div>

      {/* ── Section C: Compact Quick Actions ───────────────────────── */}
      <div>
        <div className="text-3xs font-bold uppercase tracking-wider text-text-muted mb-2 px-1">
          Quick Actions
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
              className="companion-quick-chip group flex items-center justify-between text-left p-3 rounded-xl border border-border-subtle bg-surface-overlay hover:border-brand/40 hover:bg-surface-hover transition-all cursor-pointer active:scale-95"
            >
              <span className="text-xs font-medium text-text-secondary group-hover:text-text-primary truncate">
                {action.label}
              </span>
              <ChevronRight size={13} className="text-text-muted group-hover:text-brand-light group-hover:translate-x-0.5 transition-all flex-shrink-0 ml-1" />
            </button>
          ))}
        </div>
      </div>

      {/* ── Section D: Recent Activity ────────────────────────────── */}
      <div className="pt-2">
        <div className="text-3xs font-bold uppercase tracking-wider text-text-muted mb-2 px-1 flex items-center justify-between">
          <span>Recent Activity</span>
          <span className="text-3xs text-text-muted font-normal">Live Log</span>
        </div>

        {briefing && briefing.today_events && briefing.today_events.length > 0 ? (
          <div className="flex flex-col gap-2">
            {briefing.today_events.slice(0, 2).map((ev: any, idx: number) => (
              <div
                key={idx}
                className="p-3 rounded-xl bg-surface-elevated border border-border-subtle flex items-center justify-between text-xs"
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <Calendar size={14} className="text-brand-light flex-shrink-0" />
                  <span className="font-semibold text-text-primary truncate">{ev.title || 'Scheduled Event'}</span>
                </div>
                <span className="text-2xs text-text-muted flex-shrink-0">
                  {ev.start ? new Date(ev.start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Today'}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-4 rounded-xl bg-surface-overlay/50 border border-border-subtle/60 text-center text-xs text-text-muted flex flex-col items-center gap-1">
            <Clock size={16} className="opacity-40 text-text-muted mb-0.5" />
            <span>No recent activity yet. Your upcoming schedule and tasks will appear here.</span>
          </div>
        )}
      </div>
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

