// components/shell/InputBar.tsx — Message input with send + voice + attach (responsive)
import React, { useState, useRef, KeyboardEvent } from 'react';
import { motion } from 'framer-motion';
import { Send, Mic, Paperclip, Zap } from 'lucide-react';
import { cn } from '../../lib/utils';
import { useCompanionStore } from '../../store/companion.store';

interface Props {
  onSend:     (message: string) => void;
  disabled?:  boolean;
}

const quickActions = [
  { label: '📋 Briefing',     value: 'Run my morning briefing' },
  { label: '📧 Email',        value: 'Check my recent emails' },
  { label: '📅 Schedule',     value: 'What\'s on my calendar today?' },
  { label: '✅ Tasks',        value: 'Show my pending tasks' },
];

const InputBar: React.FC<Props> = ({ onSend, disabled }) => {
  const [value, setValue] = useState('');
  const [showQuick, setShowQuick] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { status, isMobile } = useCompanionStore();

  const isThinking = status === 'thinking';

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled || isThinking) return;
    onSend(trimmed);
    setValue('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  };

  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // On mobile, Enter should create a newline (Send button is always visible)
    if (e.key === 'Enter' && !e.shiftKey && !isMobile) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setValue(e.target.value);
    // Auto-grow
    const ta = e.target;
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, isMobile ? 100 : 120) + 'px';
  };

  return (
    <div className="zone-input bg-surface-raised border-t border-border-subtle px-3 sm:px-4 py-2 sm:py-2.5 flex flex-col gap-1.5 sm:gap-2">
      {/* Quick actions */}
      {showQuick && !value && (
        <motion.div
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 4 }}
          className="flex gap-1.5 flex-wrap"
        >
          {quickActions.map(qa => (
            <button
              key={qa.value}
              onClick={() => { onSend(qa.value); setShowQuick(false); }}
              className="text-2xs px-2 sm:px-2.5 py-1 rounded-full bg-surface-overlay border border-border-subtle text-text-secondary hover:border-brand/40 hover:text-brand-light transition-all duration-150 active:scale-95"
            >
              {qa.label}
            </button>
          ))}
        </motion.div>
      )}

      {/* Input row */}
      <div className="flex items-end gap-1.5 sm:gap-2">
        {/* Quick actions trigger */}
        <button
          id="inputbar-quick-actions"
          onClick={() => setShowQuick(!showQuick)}
          className={cn(
            'flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-lg transition-colors mb-0.5',
            showQuick
              ? 'bg-brand-muted text-brand-light'
              : 'text-text-muted hover:text-text-secondary hover:bg-surface-overlay',
          )}
          aria-label="Quick actions"
        >
          <Zap size={14} />
        </button>

        {/* Textarea */}
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            id="companion-input"
            value={value}
            onChange={handleChange}
            onKeyDown={handleKey}
            disabled={disabled || isThinking}
            rows={1}
            placeholder={isThinking ? 'Mitra is thinking…' : 'Ask Mitra anything…'}
            className={cn(
              'w-full resize-none bg-surface-overlay border border-border-subtle rounded-xl px-3 sm:px-3.5 py-2',
              'text-sm text-text-primary placeholder:text-text-muted',
              'focus:outline-none focus:border-brand/50 focus:ring-1 focus:ring-brand/30',
              'transition-all duration-150 leading-relaxed',
              'max-h-[100px] sm:max-h-[120px] overflow-y-auto',
              (disabled || isThinking) && 'opacity-50 cursor-not-allowed',
            )}
            style={{ fontSize: '16px' }} /* Prevents iOS zoom on focus */
          />
        </div>

        {/* Attach — hidden on very small screens */}
        <button
          id="inputbar-attach"
          className="flex-shrink-0 w-8 h-8 items-center justify-center rounded-lg text-text-muted hover:text-text-secondary hover:bg-surface-overlay transition-colors mb-0.5 hidden sm:flex"
          aria-label="Attach file"
        >
          <Paperclip size={14} />
        </button>

        {/* Voice */}
        <button
          id="inputbar-voice"
          className="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-lg text-text-muted hover:text-text-secondary hover:bg-surface-overlay transition-colors mb-0.5"
          aria-label="Voice input"
        >
          <Mic size={14} />
        </button>

        {/* Send */}
        <button
          id="inputbar-send"
          onClick={handleSend}
          disabled={!value.trim() || disabled || isThinking}
          className={cn(
            'flex-shrink-0 w-8 h-8 sm:w-8 sm:h-8 flex items-center justify-center rounded-lg transition-all duration-150 active:scale-95 mb-0.5',
            value.trim() && !disabled && !isThinking
              ? 'bg-brand text-white hover:bg-brand-light shadow-glow-sm'
              : 'bg-surface-overlay text-text-muted cursor-not-allowed',
          )}
          aria-label="Send message"
        >
          <Send size={13} />
        </button>
      </div>

      {/* Hint — only on desktop */}
      <p className="text-2xs text-text-muted text-center hidden md:block">
        Press <kbd className="px-1 py-0.5 bg-surface-overlay border border-border-subtle rounded text-2xs">Enter</kbd> to send · <kbd className="px-1 py-0.5 bg-surface-overlay border border-border-subtle rounded text-2xs">Shift+Enter</kbd> for new line
      </p>
    </div>
  );
};

export default InputBar;
