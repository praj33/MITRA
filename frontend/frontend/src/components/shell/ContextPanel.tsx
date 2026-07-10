// components/shell/ContextPanel.tsx — Right panel: context items + status (responsive)
import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
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

/* ── Shared panel content ─────────────────────────────── */
const PanelContent: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  const { contextItems } = useCompanionStore();

  return (
    <>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border-subtle flex-shrink-0">
        <span className="text-2xs font-semibold text-text-muted uppercase tracking-wider">Context</span>
        <button
          onClick={onClose}
          className="w-8 h-8 flex items-center justify-center rounded-lg text-text-muted hover:text-text-secondary hover:bg-surface-overlay transition-colors"
          aria-label="Close context panel"
        >
          <X size={13} />
        </button>
      </div>

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3 overscroll-contain">
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
    </>
  );
};

/* ── Desktop Context Panel (grid-embedded) ─────────────── */
const DesktopContextPanel: React.FC = () => {
  const { contextPanel, toggleContextPanel, isMobile } = useCompanionStore();
  const open = contextPanel === 'open';

  // Don't render desktop version on mobile (it's controlled by the mobile sheet)
  if (isMobile) return null;

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
          <PanelContent onClose={toggleContextPanel} />
        </motion.aside>
      )}
    </AnimatePresence>
  );
};

/* ── Mobile Context Sheet (overlay slide-in from right) ── */
const MobileContextSheet: React.FC = () => {
  const { mobileContextOpen, setMobileContextOpen, isMobile } = useCompanionStore();

  if (!isMobile) return null;

  return (
    <AnimatePresence>
      {mobileContextOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="mobile-overlay-backdrop"
            onClick={() => setMobileContextOpen(false)}
            aria-hidden="true"
          />

          {/* Sheet */}
          <motion.aside
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 28, stiffness: 300 }}
            className="mobile-context-sheet"
            role="dialog"
            aria-label="Context panel"
          >
            <PanelContent onClose={() => setMobileContextOpen(false)} />
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
};

/* ── Exported ContextPanel ─────────────────────────────── */
const ContextPanel: React.FC = () => (
  <>
    <DesktopContextPanel />
    <MobileContextSheet />
  </>
);

export default ContextPanel;
