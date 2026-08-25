import React, { useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useCompanionStore } from '../../store/companion.store';
import ConversationCard from '../cards/ConversationCard';
import { DailyBriefingCard } from '../cards/DailyBriefingCard';
import { MessageSquare } from 'lucide-react';

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

const EmptyState: React.FC<{ onBriefingAction: (prompt: string) => void }> = ({ onBriefingAction }) => {
  const userName = useCompanionStore(s => s.userName);
  const displayName = !userName || ['there', 'user_default', 'using', 'anonymous'].includes(userName.toLowerCase()) ? 'User' : userName;

  return (
    <div className="flex flex-col gap-4">
      <DailyBriefingCard onActionClick={onBriefingAction} />
      
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="flex flex-col items-center justify-center py-6 gap-4 sm:gap-5 text-center px-5 sm:px-8 select-none"
      >
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
        </div>
      </motion.div>
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

  // Handle action button clicks
  const handleBriefingAction = useCallback((prompt: string) => {
    const send = (window as any).__MITRA_SEND__;
    if (send) send(prompt);
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
    <main className="zone-center flex flex-col overflow-hidden bg-surface-base">
      <div className="flex-1 overflow-y-auto px-3 py-4 sm:px-6 sm:py-6 overscroll-contain">
        {messages.length === 0 ? (
          <div className="min-h-full flex flex-col items-center justify-center py-2 sm:py-6">
            <EmptyState onBriefingAction={handleBriefingAction} />
          </div>
        ) : (
          <div className="space-y-3 sm:space-y-4">
            <AnimatePresence initial={false}>
              <DailyBriefingCard onActionClick={handleBriefingAction} />
              {messages.map(msg => (
                <ConversationCard key={msg.id} message={msg} onActionConfirm={handleActionConfirm} />
              ))}
              {isThinking && (
                <ThinkingIndicator key="thinking" />
              )}
            </AnimatePresence>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
    </main>
  );
};

export default ConversationCenter;

