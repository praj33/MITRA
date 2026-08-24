// components/cards/NotificationCard.tsx
import React from 'react';
import { motion } from 'framer-motion';
import { cn, formatRelative } from '../../lib/utils';
import { Notification } from '../../store/companion.store';
import { Bell, CheckCircle, AlertTriangle, Info, X } from 'lucide-react';

interface Props {
  notification: Notification;
  onDismiss?:   (id: string) => void;
  className?:   string;
}

const icons = {
  info:    <Info          size={14} className="text-state-info" />,
  success: <CheckCircle  size={14} className="text-state-success" />,
  warning: <AlertTriangle size={14} className="text-state-warning" />,
  error:   <X            size={14} className="text-state-error" />,
};

const NotificationCard: React.FC<Props> = ({ notification, onDismiss, className }) => (
  <motion.div
    layout
    initial={{ opacity: 0, x: -8 }}
    animate={{ opacity: 1, x: 0 }}
    exit={{ opacity: 0, x: 8, height: 0 }}
    transition={{ duration: 0.15 }}
    className={cn(
      'flex items-start gap-3 p-3 rounded-lg border transition-all duration-150',
      notification.read
        ? 'bg-surface-raised border-border-subtle opacity-60'
        : 'bg-surface-elevated border-border-default',
      className,
    )}
  >
    <div className="flex-shrink-0 mt-0.5">{icons[notification.type]}</div>
    <div className="flex-1 min-w-0">
      <p className={cn('text-xs font-medium', notification.read ? 'text-text-secondary' : 'text-text-primary')}>
        {notification.title}
      </p>
      {notification.body && (
        <p className="text-2xs text-text-muted mt-0.5 truncate">{notification.body}</p>
      )}
      <span className="text-2xs text-text-muted mt-1 block">
        {formatRelative(notification.timestamp)}
      </span>
    </div>
    {onDismiss && (
      <button
        onClick={() => onDismiss(notification.id)}
        className="flex-shrink-0 text-text-muted hover:text-text-secondary transition-colors"
      >
        <X size={12} />
      </button>
    )}
  </motion.div>
);

export default NotificationCard;
