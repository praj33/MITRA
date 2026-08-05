// components/shell/TopBar.tsx — Mitra top navigation bar (responsive)
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Search, Bell, PanelRight, Zap, Menu, User, Settings } from 'lucide-react';
import { cn } from '../../lib/utils';
import { useCompanionStore } from '../../store/companion.store';
import CompanionDot from '../primitives/CompanionDot';
import NotificationDropdown from './NotificationDropdown';

interface Props { onSearch?: () => void; }

const statusLabel = { active: 'Active', thinking: 'Thinking…', away: 'Away', error: 'Error' };

const TopBar: React.FC<Props> = ({ onSearch }) => {
  const {
    status, userName, isAuthenticated, notifications,
    toggleContextPanel, contextPanel,
    isMobile, toggleMobileMenu,
  } = useCompanionStore();
  const unread = notifications.filter(n => !n.read).length;
  const [notifOpen, setNotifOpen] = useState(false);

  return (
    <header className="zone-topbar glass flex items-center px-3 sm:px-4 gap-2 sm:gap-3 select-none">
      {/* Mobile hamburger */}
      {isMobile && (
        <button
          id="topbar-mobile-menu"
          onClick={toggleMobileMenu}
          className="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-lg hover:bg-surface-overlay transition-colors"
          aria-label="Open menu"
        >
          <Menu size={18} className="text-text-secondary" />
        </button>
      )}

      {/* Brand */}
      <div className="flex items-center gap-2 sm:gap-2.5 flex-shrink-0">
        <div className="w-7 h-7 rounded-lg bg-brand-muted border border-brand/30 flex items-center justify-center">
          <Zap size={14} className="text-brand-light" />
        </div>
        <span className="text-sm font-semibold text-text-primary tracking-tight">Mitra</span>
      </div>

      {/* Companion status pill */}
      <motion.div
        animate={{ opacity: 1 }}
        className="flex items-center gap-1.5 px-2 sm:px-2.5 py-1 rounded-full bg-surface-overlay border border-border-subtle"
      >
        <CompanionDot status={status} size="sm" />
        <span className={cn(
          'text-2xs font-medium hidden xs:inline sm:inline',
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

      {/* User greeting — hidden on mobile & small tablets */}
      <span className="text-xs text-text-muted hidden lg:block">
        Hey, {!userName || ['there', 'user_default', 'using', 'anonymous'].includes(userName.toLowerCase()) ? 'User' : userName} 👋
      </span>

      {/* Search — compact on mobile */}
      <button
        id="topbar-search"
        onClick={() => {
          if (onSearch) onSearch();
          const searchFn = (window as any).__MITRA_SEARCH__;
          if (searchFn) searchFn();
        }}
        className="flex items-center gap-2 px-2 sm:px-3 py-1.5 rounded-lg bg-surface-overlay border border-border-subtle text-text-muted hover:border-border-default hover:text-text-secondary transition-all duration-150 text-xs"
      >
        <Search size={12} />
        <span className="hidden lg:inline">Search…</span>
        <span className="hidden lg:inline text-2xs opacity-60 ml-1">⌘K</span>
      </button>

      {/* Notifications */}
      <div className="relative">
        <button
          id="topbar-notifications"
          onClick={() => setNotifOpen(!notifOpen)}
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
        <NotificationDropdown open={notifOpen} onClose={() => setNotifOpen(false)} />
      </div>

      {/* Focus Mode Launcher */}
      <button
        id="topbar-focus-button"
        onClick={() => {
          const fn = (window as any).__MITRA_FOCUS__;
          if (fn) fn();
        }}
        className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-brand/20 text-text-secondary hover:text-brand-light transition-all active:scale-95"
        aria-label="Focus Session & Soundscapes"
        title="Focus Session & Ambient Soundscapes"
      >
        <span className="text-sm">⏱️</span>
      </button>

      {/* Settings Trigger */}
      <button
        id="topbar-settings-button"
        onClick={() => {
          const fn = (window as any).__MITRA_SETTINGS__;
          if (fn) fn();
        }}
        className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-surface-overlay text-text-secondary hover:text-text-primary transition-colors"
        aria-label="Settings"
        title="Settings"
      >
        <Settings size={15} />
      </button>

      {/* Account / Login Trigger */}
      <button
        id="topbar-auth-button"
        onClick={() => useCompanionStore.getState().setAuthModalOpen(true)}
        className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-surface-overlay border border-border-subtle hover:border-brand/40 text-text-primary text-xs transition-all"
        title={isAuthenticated ? `Account: ${userName}` : 'Log In / Sign Up'}
      >
        <div className="w-5 h-5 rounded-full bg-brand/20 border border-brand/40 flex items-center justify-center text-brand-light font-bold text-[10px]">
          {userName ? userName.charAt(0).toUpperCase() : <User size={12} />}
        </div>
        <span className="hidden sm:inline text-2xs font-medium">
          {isAuthenticated ? userName : 'Account'}
        </span>
      </button>

      {/* Context panel toggle — hidden on mobile (uses bottom nav or swipe) */}
      {!isMobile && (
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
      )}
    </header>
  );
};

export default TopBar;
