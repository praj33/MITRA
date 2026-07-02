// components/cards/ConversationCard.tsx — Chat message bubble
import React from 'react';
import { motion } from 'framer-motion';
import { cn, formatTime } from '../../lib/utils';
import { Message } from '../../store/companion.store';
import ActionCard from './ActionCard';

interface Props {
  message: Message;
  onActionConfirm?: (action: string, messageId: string) => void;
}

const ThinkingDots = () => (
  <span className="inline-flex items-center gap-0.5 ml-1">
    <span className="thinking-dot" />
    <span className="thinking-dot" />
    <span className="thinking-dot" />
  </span>
);

const ConversationCard: React.FC<Props> = ({ message, onActionConfirm }) => {
  const isAssistant = message.role === 'assistant';

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.18, ease: 'easeOut' }}
      className={cn(
        'flex gap-3 w-full',
        isAssistant ? 'flex-row' : 'flex-row-reverse',
      )}
    >
      {/* Avatar */}
      <div className={cn(
        'flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold select-none',
        isAssistant
          ? 'bg-brand-muted text-brand-light border border-brand/30'
          : 'bg-surface-elevated text-text-secondary border border-border-subtle',
      )}>
        {isAssistant ? 'M' : 'U'}
      </div>

      {/* Content column */}
      <div className={cn(
        'flex flex-col gap-2 max-w-[72%]',
        isAssistant ? 'items-start' : 'items-end',
      )}>
        {/* Bubble */}
        <div className={cn(
          'px-3.5 py-2.5 rounded-lg text-sm leading-relaxed',
          isAssistant
            ? 'bg-surface-elevated border border-border-subtle text-text-primary rounded-tl-sm'
            : 'bg-brand-dim text-text-primary border border-brand/30 rounded-tr-sm',
        )}>
          {message.content}
        </div>

        {/* Inline capability result */}
        {isAssistant && message.capabilityResult && (
          <ActionCard
            capability={message.capabilityResult.capability}
            intent={message.capabilityResult.intent}
            status={message.capabilityResult.status}
            summary={message.capabilityResult.summary}
            data={message.capabilityResult.data}
            actions={message.suggestedActions?.map(a => ({ label: a, action: a })) || []}
            onAction={(action) => onActionConfirm?.(action, message.id)}
            compact
          />
        )}

        {/* Timestamp */}
        <span className="text-2xs text-text-muted select-none">
          {formatTime(message.timestamp)}
        </span>
      </div>
    </motion.div>
  );
};

export default ConversationCard;
