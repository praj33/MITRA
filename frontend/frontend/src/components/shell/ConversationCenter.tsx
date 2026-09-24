import React, { useEffect, useRef, useCallback, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Zap, Calendar, ArrowRight, UserPlus,
  ChevronRight, Compass, CheckSquare, Bell,
  CheckCircle2, AlertTriangle, Circle, Ban
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { useCompanionStore } from '../../store/companion.store';
import { CompanionService } from '../../services/companion.service';
import { authApi } from '../../services/authApi';
import ConversationCard from '../cards/ConversationCard';
import { DailyBriefingCard } from '../cards/DailyBriefingCard';
import { MessageSquare } from 'lucide-react';

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

        const g = connData?.connections?.find((c: any) => c.provider.toLowerCase() === 'google' && (c.status === 'active' || c.status === 'connected'));
        const m = connData?.connections?.find((c: any) => c.provider.toLowerCase() === 'microsoft' && (c.status === 'active' || c.status === 'connected'));

        const hasGCalScope = Boolean(g?.scopes?.some((s: string) => s.toLowerCase().includes('calendar')));

        if (g && hasGCalScope) {
          setCalendarConnected('Google Calendar connected');
        } else if (g && !hasGCalScope) {
          setCalendarConnected('Needs authorization');
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

  const getCalendarStatusInfo = () => {
    if (!calendarConnected || calendarConnected === 'No calendar connected') {
      return {
        label: 'Not connected',
        icon: Circle,
        classes: 'text-text-muted bg-surface-overlay/80 border-border-subtle hover:border-brand/40',
      };
    }
    if (calendarConnected.includes('connected')) {
      return {
        label: calendarConnected.includes('Google') ? 'Google Calendar' : 'Outlook Calendar',
        icon: CheckCircle2,
        classes: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/25 hover:bg-emerald-500/15',
      };
    }
    if (calendarConnected.includes('Needs') || calendarConnected.includes('authorization')) {
      return {
        label: 'Needs authorization',
        icon: AlertTriangle,
        classes: 'text-amber-400 bg-amber-500/10 border-amber-500/25 hover:bg-amber-500/15',
      };
    }
    return {
      label: 'Sync unavailable',
      icon: Ban,
      classes: 'text-text-muted bg-surface-overlay/80 border-border-subtle',
    };
  };

  const calInfo = getCalendarStatusInfo();
  const CalIcon = calInfo.icon;

  // Rich Quick Action items as specified in user requirements
  const quickActionsList = [
    {
      id: 'briefing_q',
      label: 'Morning Briefing',
      desc: 'Summary of schedule & tasks',
      icon: Zap,
      color: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
      type: 'prompt',
      value: 'Run my morning briefing',
    },
    {
      id: 'plan',
      label: 'Plan My Day',
      desc: 'Prioritize tasks & routines',
      icon: Compass,
      color: 'text-brand-light bg-brand/10 border-brand/20',
      type: 'prompt',
      value: 'Plan my day',
    },
    {
      id: 'open_cal',
      label: 'Calendar Schedule',
      desc: 'Upcoming events & meetings',
      icon: Calendar,
      color: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
      type: 'nav',
      value: 'calendar',
    },
    {
      id: 'tasks_q',
      label: 'Tasks & To-Dos',
      desc: 'Open pending priority board',
      icon: CheckSquare,
      color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
      type: 'nav',
      value: 'tasks',
    },
    {
      id: 'remind_q',
      label: 'Create Reminder',
      desc: 'Set timed companion alert',
      icon: Bell,
      color: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
      type: 'prompt',
      value: 'Create a reminder',
    },
  ];

  return (
    <div className="w-full max-w-4xl flex flex-col gap-4 sm:gap-5 py-3 sm:py-5">
      {/* ── 1. Compact MITRA Companion Hero Header ── */}
      <motion.div
        initial={{ opacity: 0, y: -4 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.18 }}
        className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 sm:p-5 rounded-2xl bg-surface-elevated/90 border border-border-subtle shadow-sm"
      >
<<<<<<< HEAD
        <div className="w-20 h-20 sm:w-24 sm:h-24 rounded-3xl bg-surface-raised border border-border-subtle flex items-center justify-center shadow-glow">
          <MessageSquare size={40} className="text-brand-light" />
        </div>
        <div className="mt-4">
          <h2 className="text-xl sm:text-2xl font-bold text-text-primary mb-2">
            Start a conversation
          </h2>
          <p className="text-sm sm:text-base text-text-muted max-w-md leading-relaxed mx-auto">
            I'm your unified AI assistant with multi-agent capabilities, safety enforcement, and intelligent routing.
          </p>
=======
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-10 h-10 rounded-xl bg-brand/15 border border-brand/30 flex items-center justify-center text-brand-light flex-shrink-0 shadow-xs">
            <Zap size={18} className="text-brand-light" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-3xs font-bold uppercase tracking-wider text-brand-light">Personal AI Companion</span>
              <span className="w-1.5 h-1.5 rounded-full bg-state-success" />
            </div>
            <h1 className="text-base sm:text-lg font-bold text-text-primary tracking-tight truncate mt-0.5">
              {authStatus === 'LOADING' ? (
                <span className="inline-flex items-center gap-2">
                  {getGreetingTime()}, <span className="inline-block w-20 h-5 bg-surface-raised animate-pulse rounded align-middle" />
                </span>
              ) : (
                `${getGreetingTime()}, ${userFirstName}`
              )}
            </h1>
            <p className="text-2xs text-text-muted mt-0.5">{currentDateDisplay}</p>
          </div>
        </div>

        {/* Semantic Calendar Connection State Pill */}
        <div className="flex items-center gap-2 flex-shrink-0">
          <div
            onClick={() => onNavigate('calendar')}
            className={cn(
              "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-2xs font-semibold cursor-pointer transition-all active:scale-95",
              calInfo.classes
            )}
            title="Calendar synchronization status"
          >
            <CalIcon size={12} className="flex-shrink-0" />
            <span>{calInfo.label}</span>
          </div>
>>>>>>> origin/main
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
      <div className="pt-2 pb-1 select-none">
        <h2 className="text-lg sm:text-xl font-bold text-text-primary tracking-tight">
          How can I help you today?
        </h2>
        <p className="text-xs sm:text-sm text-text-muted max-w-xl leading-relaxed mt-1">
          Ask questions, plan your daily agenda, manage tasks, or run automated workflows.
        </p>
      </div>

      {/* ── 3. Suggested Actions (Rich MITRA Action Cards) ── */}
      <div>
        <div className="text-3xs font-bold uppercase tracking-wider text-text-muted mb-2 px-0.5">
          Suggested Actions
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5 w-full">
          {quickActionsList.map(action => {
            const Icon = action.icon;
            return (
              <button
                key={action.id}
                onClick={() => {
                  if (action.type === 'nav') {
                    onNavigate(action.value);
                  } else {
                    onAction(action.value);
                  }
                }}
                className="group flex items-center justify-between text-left p-3 rounded-2xl border border-border-subtle bg-surface-elevated/70 hover:border-brand/40 hover:bg-surface-hover hover:-translate-y-0.5 transition-all duration-150 cursor-pointer active:scale-[0.98] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand shadow-xs"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div className={cn("w-8 h-8 rounded-xl border flex items-center justify-center flex-shrink-0 transition-transform group-hover:scale-105", action.color)}>
                    <Icon size={15} />
                  </div>
                  <div className="min-w-0">
                    <div className="text-xs font-semibold text-text-primary group-hover:text-brand-light transition-colors truncate">
                      {action.label}
                    </div>
                    <div className="text-3xs text-text-muted truncate">
                      {action.desc}
                    </div>
                  </div>
                </div>
                <ChevronRight size={14} className="text-text-muted group-hover:text-brand-light group-hover:translate-x-0.5 transition-all flex-shrink-0 ml-2 opacity-60 group-hover:opacity-100" />
              </button>
            );
          })}
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

