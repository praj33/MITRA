// components/shell/ConversationCenter.tsx — Main chat thread panel (responsive)
import React, { useEffect, useRef } from 'react';
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

const EmptyState = () => (
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
      <h2 className="text-lg sm:text-xl font-semibold text-text-primary mb-1 sm:mb-1.5">Good to see you</h2>
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
        <span key={s} className="text-2xs px-2.5 sm:px-3 py-1 sm:py-1.5 rounded-full border border-border-subtle text-text-muted bg-surface-overlay">
          {s}
        </span>
      ))}
    </div>
  </motion.div>
);

const ConversationCenter: React.FC = () => {
  const { messages, status } = useCompanionStore();
  const bottomRef = useRef<HTMLDivElement>(null);
  const isThinking = status === 'thinking';

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isThinking]);

  return (
    <main className="zone-center flex flex-col overflow-hidden bg-surface-base">
      <div className="flex-1 overflow-y-auto px-3 py-4 sm:px-6 sm:py-6 space-y-3 sm:space-y-4 overscroll-contain">
        {messages.length === 0 ? (
          <EmptyState />
        ) : (
          <AnimatePresence initial={false}>
            {messages.map(msg => (
              <ConversationCard key={msg.id} message={msg} />
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
