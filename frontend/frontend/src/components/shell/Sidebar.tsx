// components/shell/Sidebar.tsx — Navigation + conversation history
import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MessageCircle, Calendar, CheckSquare, Bell, BookOpen,
  Settings, ChevronLeft, ChevronRight, Play,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { useCompanionStore } from '../../store/companion.store';

interface NavItem {
  id:    string;
  icon:  React.ReactNode;
  label: string;
  badge?: number;
}

const navItems: NavItem[] = [
  { id: 'chat',        icon: <MessageCircle size={15} />, label: 'Companion' },
  { id: 'calendar',    icon: <Calendar      size={15} />, label: 'Calendar' },
  { id: 'tasks',       icon: <CheckSquare   size={15} />, label: 'Tasks' },
  { id: 'reminders',   icon: <Bell          size={15} />, label: 'Reminders' },
  { id: 'knowledge',   icon: <BookOpen      size={15} />, label: 'Knowledge' },
  { id: 'workflows',   icon: <Play          size={15} />, label: 'Workflows' },
];

interface Props {
  activeSection?: string;
  onSectionChange?: (id: string) => void;
}

const Sidebar: React.FC<Props> = ({
  activeSection = 'chat', onSectionChange,
}) => {
  const { sidebar, toggleSidebar } = useCompanionStore();
  const collapsed = sidebar === 'collapsed';

  return (
    <aside className={cn(
      'zone-sidebar bg-surface-raised border-r border-border-subtle flex flex-col overflow-hidden transition-all duration-300',
    )}>
      {/* Nav items */}
      <nav className="flex-1 py-3 px-2 space-y-0.5" role="navigation" aria-label="Main navigation">
        {navItems.map(item => {
          const active = activeSection === item.id;
          return (
            <button
              key={item.id}
              id={`nav-${item.id}`}
              onClick={() => onSectionChange?.(item.id)}
              aria-current={active ? 'page' : undefined}
              className={cn(
                'w-full flex items-center gap-3 px-2.5 py-2 rounded-lg transition-all duration-150 text-left group',
                active
                  ? 'bg-brand-muted text-brand-light'
                  : 'text-text-muted hover:text-text-secondary hover:bg-surface-overlay',
              )}
            >
              <span className={cn('flex-shrink-0', active ? 'text-brand-light' : '')}>
                {item.icon}
              </span>
              <AnimatePresence>
                {!collapsed && (
                  <motion.span
                    initial={{ opacity: 0, width: 0 }}
                    animate={{ opacity: 1, width: 'auto' }}
                    exit={{ opacity: 0, width: 0 }}
                    transition={{ duration: 0.2 }}
                    className="text-xs font-medium whitespace-nowrap overflow-hidden"
                  >
                    {item.label}
                  </motion.span>
                )}
              </AnimatePresence>
              {item.badge && item.badge > 0 && (
                <span className="ml-auto w-4 h-4 bg-brand rounded-full text-2xs text-white flex items-center justify-center flex-shrink-0">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-2 pb-3 space-y-0.5 border-t border-border-subtle pt-2">
        <button className={cn(
          'w-full flex items-center gap-3 px-2.5 py-2 rounded-lg transition-all duration-150 text-text-muted hover:text-text-secondary hover:bg-surface-overlay',
        )}>
          <Settings size={15} />
          <AnimatePresence>
            {!collapsed && (
              <motion.span
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="text-xs font-medium"
              >
                Settings
              </motion.span>
            )}
          </AnimatePresence>
        </button>

        {/* Collapse toggle */}
        <button
          id="sidebar-collapse-toggle"
          onClick={toggleSidebar}
          className="w-full flex items-center gap-3 px-2.5 py-2 rounded-lg transition-all duration-150 text-text-muted hover:text-text-secondary hover:bg-surface-overlay"
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight size={15} /> : <ChevronLeft size={15} />}
          <AnimatePresence>
            {!collapsed && (
              <motion.span
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="text-xs font-medium"
              >
                Collapse
              </motion.span>
            )}
          </AnimatePresence>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
