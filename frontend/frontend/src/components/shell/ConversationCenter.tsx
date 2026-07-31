// components/shell/ConversationCenter.tsx — Main chat thread panel (responsive)
import React, { useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useCompanionStore } from '../../store/companion.store';
import ConversationCard from '../cards/ConversationCard';
import { Zap } from 'lucide-react';

const ThinkingIndicator = () => (
  <motion.div
    initial={{ opacity: 0, y: 6 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -4 }}
    className="flex items-center gap-3"
  >
    <div className="w-7 h-7 rounded-full bg-brand-muted border border-brand/30 flex items-center justify-center text-xs font-semibold text-brand-light flex-shrink-0">
      M
    </div>
    <div className="px-3.5 py-2.5 rounded-lg rounded-tl-sm bg-surface-elevated border border-border-subtle">
      <span className="inline-flex items-center gap-0.5">
        <span className="thinking-dot" />
        <span className="thinking-dot" />
        <span className="thinking-dot" />
      </span>
    </div>
  </motion.div>
);

const EmptyState = () => {
  const userName = useCompanionStore(s => s.userName);
  const displayName = !userName || ['there', 'user_default', 'using', 'anonymous'].includes(userName.toLowerCase()) ? '' : `, ${userName}`;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
      className="flex flex-col items-center justify-center h-full gap-4 sm:gap-5 text-center px-5 sm:px-8 select-none"
    >
      <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-2xl bg-brand-muted border border-brand/30 flex items-center justify-center">
        <Zap size={24} className="text-brand-light sm:hidden" />
        <Zap size={28} className="text-brand-light hidden sm:block" />
      </div>
      <div>
        <h2 className="text-lg sm:text-xl font-semibold text-text-primary mb-1 sm:mb-1.5">
          Good to see you{displayName} 👋
        </h2>
        <p className="text-xs sm:text-sm text-text-muted max-w-xs leading-relaxed">
          I'm Mitra — your AI companion. Ask me anything, run a workflow, or let me help you get things done.
        </p>
      </div>
      <div className="flex flex-wrap justify-center gap-1.5 sm:gap-2">
        {[
          'What\'s on my calendar today?',
          'Summarize my emails',
          'Create a reminder',
          'Run morning briefing',
        ].map(s => (
          <button key={s} onClick={() => {
            const store = (window as any).__MITRA_SEND__;
            if (store) store(s);
          }} className="text-2xs px-2.5 sm:px-3 py-1 sm:py-1.5 rounded-full border border-border-subtle text-text-muted bg-surface-overlay hover:border-brand/40 hover:text-brand-light transition-all cursor-pointer active:scale-95">
            {s}
          </button>
        ))}
      </div>
    </motion.div>
  );
};

const ConversationCenter: React.FC = () => {
  const { messages, status } = useCompanionStore();
  const bottomRef = useRef<HTMLDivElement>(null);
  const isThinking = status === 'thinking';

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isThinking]);

  // Handle action button clicks from capability result cards
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
      // For any other action, send it as a chat message
      send(action);
    }
  }, []);

  return (
    <main className="zone-center flex flex-col overflow-hidden bg-surface-base">
      <div className="flex-1 overflow-y-auto px-3 py-4 sm:px-6 sm:py-6 space-y-3 sm:space-y-4 overscroll-contain">
        {messages.length === 0 ? (
          <EmptyState />
        ) : (
          <AnimatePresence initial={false}>
            {messages.map(msg => (
              <ConversationCard key={msg.id} message={msg} onActionConfirm={handleActionConfirm} />
            ))}
            {isThinking && (
              <ThinkingIndicator key="thinking" />
            )}
          </AnimatePresence>
        )}
        <div ref={bottomRef} />
      </div>
    </main>
  );
};

export default ConversationCenter;

