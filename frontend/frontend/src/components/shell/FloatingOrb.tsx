import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, MessageSquare, Sparkles } from 'lucide-react';
import { cn } from '../../lib/utils';
import { useCompanionStore } from '../../store/companion.store';

export const FloatingOrb: React.FC = () => {
  const [isExpanded, setIsExpanded] = useState(false);
  const { setStatus, addMessage } = useCompanionStore();
  const [inputValue, setInputValue] = useState('');

  const handleToggle = () => {
    setIsExpanded(!isExpanded);
  };

  const handleSend = () => {
    if (!inputValue.trim()) return;
    
    // Switch to chat page or handle the action inline
    addMessage({ role: 'user', content: inputValue });
    setStatus('thinking');
    
    setInputValue('');
    setIsExpanded(false);
    
    // Simulate navigation/action
    if (typeof (window as any).__MITRA_NAV__ === 'function') {
      (window as any).__MITRA_NAV__('chat');
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.9 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="mb-4 w-[350px] bg-surface-raised border border-border-subtle rounded-xl shadow-glow overflow-hidden"
          >
            <div className="bg-surface p-4 flex justify-between items-center border-b border-border-subtle">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 rounded-full bg-brand-main/20 flex items-center justify-center text-brand-light">
                  <Sparkles size={16} />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-text-primary">Mitra Companion</h3>
                  <p className="text-xs text-text-muted">AI Being</p>
                </div>
              </div>
              <button 
                onClick={handleToggle}
                className="text-text-muted hover:text-text-primary transition-colors"
              >
                <X size={18} />
              </button>
            </div>
            <div className="p-4 h-[250px] overflow-y-auto bg-surface flex flex-col justify-end">
              {/* Mini chat view */}
              <div className="text-center text-sm text-text-muted mb-4">
                Start a conversation...
              </div>
            </div>
            <div className="p-3 bg-surface-raised border-t border-border-subtle">
              <div className="relative flex items-center">
                <input 
                  type="text" 
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                  placeholder="Ask me anything..."
                  className="w-full bg-surface border border-border-subtle rounded-full py-2 pl-4 pr-10 text-sm focus:outline-none focus:border-brand-main/50 text-text-primary placeholder:text-text-muted"
                />
                <button 
                  onClick={handleSend}
                  className="absolute right-2 text-brand-light hover:text-brand-main p-1 rounded-full transition-colors"
                >
                  <MessageSquare size={16} />
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.button
        onClick={handleToggle}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        className={cn(
          "w-14 h-14 rounded-full flex items-center justify-center shadow-glow transition-all duration-300 relative overflow-hidden",
          isExpanded ? "bg-surface border border-border-subtle" : "bg-gradient-to-br from-brand-main to-brand-dark"
        )}
      >
        {!isExpanded && (
          <div className="absolute inset-0 bg-brand-light/20 blur-md animate-pulse"></div>
        )}
        
        {isExpanded ? (
          <X className="text-text-primary" size={24} />
        ) : (
          <Sparkles className="text-white z-10" size={24} />
        )}
      </motion.button>
    </div>
  );
};
