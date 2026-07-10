// components/cards/ConversationCard.tsx — Chat message bubble (responsive)
import React from 'react';
import { motion } from 'framer-motion';
import { cn, formatTime } from '../../lib/utils';
import { Message } from '../../store/companion.store';
import ActionCard from './ActionCard';

interface Props {
  message: Message;
  onActionConfirm?: (action: string, messageId: string) => void;
}

const ConversationCard: React.FC<Props> = ({ message, onActionConfirm }) => {
  const isAssistant = message.role === 'assistant';

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.18, ease: 'easeOut' }}
      className={cn(
        'flex gap-2 sm:gap-3 w-full',
        isAssistant ? 'flex-row' : 'flex-row-reverse',
      )}
    >
      {/* Avatar */}
      <div className={cn(
        'flex-shrink-0 w-6 h-6 sm:w-7 sm:h-7 rounded-full flex items-center justify-center text-2xs sm:text-xs font-semibold select-none',
        isAssistant
          ? 'bg-brand-muted text-brand-light border border-brand/30'
          : 'bg-surface-elevated text-text-secondary border border-border-subtle',
      )}>
        {isAssistant ? 'M' : 'U'}
      </div>

      {/* Content column */}
      <div className={cn(
        'flex flex-col gap-1.5 sm:gap-2 max-w-[85%] sm:max-w-[75%] lg:max-w-[72%]',
        isAssistant ? 'items-start' : 'items-end',
      )}>
        {/* Bubble */}
        <div className={cn(
          'px-3 py-2 sm:px-3.5 sm:py-2.5 rounded-lg text-sm leading-relaxed break-words',
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
