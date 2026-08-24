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
  const [quickToolsOpen, setQuickToolsOpen] = useState(false);

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

      {/* Action Icons Container — Clean & compact on mobile, expanded on desktop */}
      <div className="flex items-center gap-1 sm:gap-1.5 flex-shrink-0">
        {/* Search */}
        <button
          id="topbar-search"
          onClick={() => {
            if (onSearch) onSearch();
            const searchFn = (window as any).__MITRA_SEARCH__;
            if (searchFn) searchFn();
          }}
          className="w-7 h-7 sm:w-8 sm:h-8 flex items-center justify-center rounded-lg bg-surface-overlay border border-border-subtle text-text-muted hover:border-border-default hover:text-text-secondary transition-all text-xs"
          aria-label="Search"
          title="Search (⌘K)"
        >
          <Search size={13} />
        </button>

        {/* MOBILE ONLY: Single "Quick Tools (⚡)" Combined Launcher */}
        <div className="relative md:hidden">
          <button
            id="topbar-quick-tools-mobile"
            onClick={() => setQuickToolsOpen(!quickToolsOpen)}
            className="h-7 px-2 flex items-center gap-1 rounded-lg bg-brand-muted/80 border border-brand/30 text-brand-light hover:bg-brand/20 transition-all text-2xs font-semibold active:scale-95"
            aria-label="Quick AI Tools"
            title="Quick AI Tools Menu"
          >
            <span>⚡</span>
            <span>Tools</span>
          </button>

          {/* Quick Tools Dropdown */}
          {quickToolsOpen && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setQuickToolsOpen(false)} />
              <motion.div
                initial={{ opacity: 0, y: 8, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 8, scale: 0.95 }}
                className="absolute right-0 top-9 w-64 p-2 rounded-xl bg-surface-elevated border border-border-default shadow-2xl z-50 flex flex-col gap-1 select-none"
              >
                <div className="px-2 py-1 border-b border-border-subtle mb-1 flex items-center justify-between">
                  <span className="text-2xs font-bold text-text-secondary uppercase tracking-wider">Mitra AI Launchpad</span>
                  <span className="text-2xs text-brand-light font-medium">4 Tools</span>
                </div>

                <button
                  onClick={() => {
                    setQuickToolsOpen(false);
                    const fn = (window as any).__MITRA_VOICE_TALK__;
                    if (fn) fn();
                  }}
                  className="flex items-center gap-2.5 px-2.5 py-2 rounded-lg hover:bg-surface-overlay text-left transition-colors group"
                >
                  <span className="w-7 h-7 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-sm group-hover:scale-110 transition-transform">🎙️</span>
                  <div>
                    <div className="text-xs font-semibold text-text-primary">Hands-Free Voice</div>
                    <div className="text-[10px] text-text-muted">Real-time voice conversation</div>
                  </div>
                </button>

                <button
                  onClick={() => {
                    setQuickToolsOpen(false);
                    const fn = (window as any).__MITRA_FOCUS__;
                    if (fn) fn();
                  }}
                  className="flex items-center gap-2.5 px-2.5 py-2 rounded-lg hover:bg-surface-overlay text-left transition-colors group"
                >
                  <span className="w-7 h-7 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-sm group-hover:scale-110 transition-transform">⏱️</span>
                  <div>
                    <div className="text-xs font-semibold text-text-primary">Focus Mode & Sounds</div>
                    <div className="text-[10px] text-text-muted">Pomodoro timer & soundscapes</div>
                  </div>
                </button>

                <button
                  onClick={() => {
                    setQuickToolsOpen(false);
                    const fn = (window as any).__MITRA_MINDMAP__;
                    if (fn) fn();
                  }}
                  className="flex items-center gap-2.5 px-2.5 py-2 rounded-lg hover:bg-surface-overlay text-left transition-colors group"
                >
                  <span className="w-7 h-7 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-sm group-hover:scale-110 transition-transform">🕸️</span>
                  <div>
                    <div className="text-xs font-semibold text-text-primary">Brain Mind Map</div>
                    <div className="text-[10px] text-text-muted">Visual knowledge memory graph</div>
                  </div>
                </button>

                <button
                  onClick={() => {
                    setQuickToolsOpen(false);
                    const fn = (window as any).__MITRA_MEMORY__;
                    if (fn) fn();
                  }}
                  className="flex items-center gap-2.5 px-2.5 py-2 rounded-lg hover:bg-surface-overlay text-left transition-colors group"
                >
                  <span className="w-7 h-7 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-sm group-hover:scale-110 transition-transform">🧠</span>
                  <div>
                    <div className="text-xs font-semibold text-text-primary">Memory Dashboard</div>
                    <div className="text-[10px] text-text-muted">Manage saved facts & context</div>
                  </div>
                </button>
              </motion.div>
            </>
          )}
        </div>

        {/* DESKTOP ONLY: Individual Launcher Buttons */}
        <div className="hidden md:flex items-center gap-1.5">
          {/* Focus Mode */}
          <button
            id="topbar-focus-button"
            onClick={() => {
              const fn = (window as any).__MITRA_FOCUS__;
              if (fn) fn();
            }}
            className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-brand/20 text-text-secondary hover:text-brand-light transition-all active:scale-95 text-xs"
            aria-label="Focus Session"
            title="Focus Session & Soundscapes"
          >
            <span>⏱️</span>
          </button>

          {/* Voice Talk */}
          <button
            id="topbar-voice-talk-button"
            onClick={() => {
              const fn = (window as any).__MITRA_VOICE_TALK__;
              if (fn) fn();
            }}
            className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-emerald-500/20 text-text-secondary hover:text-emerald-400 transition-all active:scale-95 text-xs"
            aria-label="Hands-Free Voice Talk"
            title="Hands-Free Voice Talk Mode"
          >
            <span>🎙️</span>
          </button>

          {/* Mind Map */}
          <button
            id="topbar-mindmap-button"
            onClick={() => {
              const fn = (window as any).__MITRA_MINDMAP__;
              if (fn) fn();
            }}
            className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-purple-500/20 text-text-secondary hover:text-purple-400 transition-all active:scale-95 text-xs"
            aria-label="Brain Mind Map"
            title="Brain Mind Map Visualizer"
          >
            <span>🕸️</span>
          </button>

          {/* Memory Dashboard */}
          <button
            id="topbar-memory-button"
            onClick={() => {
              const fn = (window as any).__MITRA_MEMORY__;
              if (fn) fn();
            }}
            className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-brand/20 text-text-secondary hover:text-brand-light transition-all active:scale-95 text-xs"
            aria-label="Memory Dashboard"
            title="Companion Memory Dashboard"
          >
            <span>🧠</span>
          </button>
        </div>

        {/* Notifications */}
        <div className="relative">
          <button
            id="topbar-notifications"
            onClick={() => setNotifOpen(!notifOpen)}
            className="relative w-7 h-7 sm:w-8 sm:h-8 flex items-center justify-center rounded-lg hover:bg-surface-overlay transition-colors"
            aria-label={`${unread} unread notifications`}
            title="Notifications"
          >
            <Bell size={14} className="text-text-secondary" />
            {unread > 0 && (
              <span className="absolute -top-0.5 -right-0.5 w-3.5 h-3.5 bg-brand rounded-full flex items-center justify-center text-[9px] text-white font-semibold">
                {unread > 9 ? '9+' : unread}
              </span>
            )}
          </button>
          <NotificationDropdown open={notifOpen} onClose={() => setNotifOpen(false)} />
        </div>

        {/* Settings Trigger */}
        <button
          id="topbar-settings-button"
          onClick={() => {
            const fn = (window as any).__MITRA_SETTINGS__;
            if (fn) fn();
          }}
          className="w-7 h-7 sm:w-8 sm:h-8 flex items-center justify-center rounded-lg hover:bg-surface-overlay text-text-secondary hover:text-text-primary transition-colors"
          aria-label="Settings"
          title="Settings"
        >
          <Settings size={14} />
        </button>
      </div>

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
