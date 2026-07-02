// components/shell/ContextPanel.tsx — Right panel: context items + status
import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import { cn } from '../../lib/utils';
import { useCompanionStore } from '../../store/companion.store';
import ContextCard from '../cards/ContextCard';
import StatusCard from '../cards/StatusCard';
import RecommendationCard from '../cards/RecommendationCard';

const defaultStatus = [
  { name: 'Companion',  status: 'operational' as const },
  { name: 'UniGuru',    status: 'operational' as const },
  { name: 'Calendar',   status: 'operational' as const },
  { name: 'Email',      status: 'operational' as const },
];

const ContextPanel: React.FC = () => {
  const { contextPanel, contextItems, toggleContextPanel } = useCompanionStore();
  const open = contextPanel === 'open';

  return (
    <AnimatePresence>
      {open && (
        <motion.aside
          initial={{ opacity: 0, x: 24 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 24 }}
          transition={{ duration: 0.2, ease: 'easeOut' }}
          className="zone-context bg-surface-raised border-l border-border-subtle flex flex-col overflow-hidden"
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-border-subtle">
            <span className="text-2xs font-semibold text-text-muted uppercase tracking-wider">Context</span>
            <button
              onClick={toggleContextPanel}
              className="text-text-muted hover:text-text-secondary transition-colors"
              aria-label="Close context panel"
            >
              <X size={13} />
            </button>
          </div>

          {/* Scrollable content */}
          <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3 scrollbar-thin">
            {/* Context items */}
            {contextItems.length > 0 ? (
              <section>
                <p className="text-2xs font-medium text-text-muted uppercase tracking-wider mb-2">
                  Active Context
                </p>
                <div className="space-y-1.5">
                  {contextItems.map(item => (
                    <ContextCard key={item.id} item={item} />
                  ))}
                </div>
              </section>
            ) : (
              <section>
                <p className="text-2xs font-medium text-text-muted uppercase tracking-wider mb-2">
                  Active Context
                </p>
                <div className="px-3 py-4 text-center rounded-lg border border-dashed border-border-subtle">
                  <p className="text-xs text-text-muted">Context will appear here as you work</p>
                </div>
              </section>
            )}

            {/* Recommendation */}
            <RecommendationCard
              title="Try Morning Briefing"
              description="Get a daily summary of your calendar, emails, and tasks."
              action={{
                label: 'Run workflow',
                onClick: () => {},
              }}
            />

            {/* System status */}
            <StatusCard title="System Status" items={defaultStatus} />
          </div>
        </motion.aside>
      )}
    </AnimatePresence>
  );
};

export default ContextPanel;
