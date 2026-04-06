import React, { useState, useRef, useCallback } from 'react';

interface MessageInputProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
}

const MAX_CHARS = 2000;

const MessageInput: React.FC<MessageInputProps> = ({ onSendMessage, isLoading }) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  const adjustTextareaHeight = useCallback(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      const newHeight = Math.min(textarea.scrollHeight, 140);
      textarea.style.height = `${Math.max(newHeight, 56)}px`;
    }
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    if (value.length <= MAX_CHARS) {
      setMessage(value);
      // Use requestAnimationFrame for smoother resizing
      requestAnimationFrame(adjustTextareaHeight);
    }
  };

  const handleSend = useCallback(() => {
    const trimmedMessage = message.trim();
    if (trimmedMessage && !isLoading) {
      onSendMessage(trimmedMessage);
      setMessage('');
      // Reset height
      if (textareaRef.current) {
        textareaRef.current.style.height = '56px';
      }
    }
  }, [message, isLoading, onSendMessage]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const charCount = message.length;
  const isNearLimit = charCount > MAX_CHARS * 0.9;

  return (
    <div className="w-full backdrop-blur-xl bg-white/80 dark:bg-iosGray-900/80 border-t border-iosGray-200/50 dark:border-iosGray-800/50 px-4 py-4 z-10">
      <div className="max-w-5xl mx-auto">
        <div className="relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder="Type your message..."
            disabled={isLoading}
            maxLength={MAX_CHARS}
            rows={1}
            className="w-full pl-4 sm:pl-5 pr-20 sm:pr-24 py-4 backdrop-blur-md bg-iosGray-100/80 dark:bg-iosGray-800/80 border border-iosGray-200/50 dark:border-iosGray-700/50 text-iosGray-900 dark:text-white rounded-2xl focus:ring-2 focus:ring-iosBlue-500/50 focus:border-iosBlue-500/50 resize-none min-h-[56px] max-h-36 overflow-y-auto text-sm placeholder-iosGray-500 font-sf shadow-ios transition-all disabled:opacity-60"
            aria-label="Message input"
            aria-multiline="true"
          />
          
          {/* Character count - shown when near limit */}
          {isNearLimit && (
            <div className="absolute right-4 bottom-14 text-xs font-sf text-orange-500">
              {charCount}/{MAX_CHARS}
            </div>
          )}
          
          <button
            onClick={handleSend}
            disabled={!message.trim() || isLoading}
            className="absolute right-2 bottom-2 px-3 sm:px-5 py-2 sm:py-2.5 bg-iosBlue-500 text-white rounded-xl hover:bg-iosBlue-600 active:bg-iosBlue-700 disabled:bg-iosGray-300 dark:disabled:bg-iosGray-700 disabled:text-iosGray-500 dark:disabled:text-iosGray-500 disabled:cursor-not-allowed transition-all text-sm font-semibold flex items-center gap-1.5 sm:gap-2 shadow-ios active:scale-95"
            aria-label={isLoading ? 'Sending message' : 'Send message'}
          >
            {isLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" role="status" aria-label="Loading" />
                <span className="hidden sm:inline">Sending...</span>
              </>
            ) : (
              <>
                <span className="hidden sm:inline">Send</span>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </>
            )}
          </button>
        </div>
        
        <div className="mt-2 flex items-center justify-between">
          <p className="text-xs text-iosGray-500 dark:text-iosGray-500 font-sf">
            Press <kbd className="px-1.5 py-0.5 backdrop-blur-sm bg-iosGray-200/50 dark:bg-iosGray-800/50 border border-iosGray-300/30 dark:border-iosGray-700/30 rounded text-iosGray-600 dark:text-iosGray-400 font-sans">Enter</kbd> to send, <kbd className="px-1.5 py-0.5 backdrop-blur-sm bg-iosGray-200/50 dark:bg-iosGray-800/50 border border-iosGray-300/30 dark:border-iosGray-700/30 rounded text-iosGray-600 dark:text-iosGray-400 font-sans">Shift+Enter</kbd> for new line
          </p>
          
          {/* Mobile character count */}
          <span className={`sm:hidden text-xs font-sf ${isNearLimit ? 'text-orange-500' : 'text-iosGray-400'}`}>
            {charCount}/{MAX_CHARS}
          </span>
        </div>
      </div>
    </div>
  );
};

export default MessageInput;
