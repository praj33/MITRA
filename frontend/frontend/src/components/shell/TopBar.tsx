// components/shell/TopBar.tsx — Mitra top navigation bar
import React from 'react';
import { motion } from 'framer-motion';
import { Search, Bell, PanelRight, Zap } from 'lucide-react';
import { cn } from '../../lib/utils';
import { useCompanionStore } from '../../store/companion.store';
import CompanionDot from '../primitives/CompanionDot';

interface Props { onSearch?: () => void; }

const statusLabel = { active: 'Active', thinking: 'Thinking…', away: 'Away', error: 'Error' };

const TopBar: React.FC<Props> = ({ onSearch }) => {
  const { status, userName, notifications, toggleContextPanel, contextPanel } = useCompanionStore();
  const unread = notifications.filter(n => !n.read).length;

  return (
    <header className="zone-topbar glass flex items-center px-4 gap-3 select-none">
      {/* Brand */}
      <div className="flex items-center gap-2.5 flex-shrink-0">
        <div className="w-7 h-7 rounded-lg bg-brand-muted border border-brand/30 flex items-center justify-center">
          <Zap size={14} className="text-brand-light" />
        </div>
        <span className="text-sm font-semibold text-text-primary tracking-tight">Mitra</span>
      </div>

      {/* Companion status pill */}
      <motion.div
        animate={{ opacity: 1 }}
        className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-surface-overlay border border-border-subtle"
      >
        <CompanionDot status={status} size="sm" />
        <span className={cn(
          'text-2xs font-medium',
          status === 'active'   ? 'text-state-success' :
          status === 'thinking' ? 'text-brand-light' :
          status === 'error'    ? 'text-state-error' :
          'text-text-muted',
        )}>
          {statusLabel[status]}
        </span>
      </motion.div>

      {/* Spacer */}
      <div className="flex-1" />

      {/* User greeting */}
      <span className="text-xs text-text-muted hidden md:block">
        Hey, {userName} 👋
      </span>

      {/* Search */}
      <button
        id="topbar-search"
        onClick={onSearch}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-overlay border border-border-subtle text-text-muted hover:border-border-default hover:text-text-secondary transition-all duration-150 text-xs"
      >
        <Search size={12} />
        <span className="hidden lg:inline">Search…</span>
        <span className="hidden lg:inline text-2xs opacity-60 ml-1">⌘K</span>
      </button>

      {/* Notifications */}
      <button
        id="topbar-notifications"
        className="relative w-8 h-8 flex items-center justify-center rounded-lg hover:bg-surface-overlay transition-colors"
        aria-label={`${unread} unread notifications`}
      >
        <Bell size={15} className="text-text-secondary" />
        {unread > 0 && (
          <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-brand rounded-full flex items-center justify-center text-2xs text-white font-semibold">
            {unread > 9 ? '9+' : unread}
          </span>
        )}
      </button>

      {/* Context panel toggle */}
      <button
        id="topbar-context-toggle"
        onClick={toggleContextPanel}
        className={cn(
          'w-8 h-8 flex items-center justify-center rounded-lg transition-colors',
          contextPanel === 'open'
            ? 'bg-brand-muted text-brand-light'
            : 'hover:bg-surface-overlay text-text-muted',
        )}
        aria-label="Toggle context panel"
      >
        <PanelRight size={15} />
      </button>
    </header>
  );
};

export default TopBar;
