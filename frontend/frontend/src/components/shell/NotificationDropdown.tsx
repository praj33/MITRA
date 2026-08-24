// components/NotificationDropdown.tsx — Notification bell dropdown
import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bell, Check, X, Info, AlertTriangle, CheckCircle2, XCircle } from 'lucide-react';
import { useCompanionStore } from '../../store/companion.store';

const iconMap: Record<string, React.ReactNode> = {
  info:    <Info size={14} className="text-blue-400" />,
  success: <CheckCircle2 size={14} className="text-emerald-400" />,
  warning: <AlertTriangle size={14} className="text-amber-400" />,
  error:   <XCircle size={14} className="text-red-400" />,
};

interface Props {
  open: boolean;
  onClose: () => void;
}

const NotificationDropdown: React.FC<Props> = ({ open, onClose }) => {
  const { notifications, markAllRead } = useCompanionStore();

  const timeAgo = (ts: string) => {
    const diff = Date.now() - new Date(ts).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  };

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <div className="notif-backdrop" onClick={onClose} />
          
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.95 }}
            transition={{ duration: 0.15 }}
            className="notif-dropdown"
          >
            {/* Header */}
            <div className="notif-header">
              <span className="notif-title">Notifications</span>
              <div className="flex items-center gap-2">
                {notifications.some(n => !n.read) && (
                  <button onClick={markAllRead} className="notif-mark-read">
                    <Check size={12} /> Mark all read
                  </button>
                )}
                <button onClick={onClose} className="notif-close"><X size={14} /></button>
              </div>
            </div>

            {/* List */}
            <div className="notif-list">
              {notifications.length === 0 ? (
                <div className="notif-empty">
                  <Bell size={20} className="text-text-muted" />
                  <p>No notifications yet</p>
                </div>
              ) : (
                notifications.slice(0, 10).map(n => (
                  <div key={n.id} className={`notif-item ${n.read ? 'read' : ''}`}>
                    <div className="notif-icon">{iconMap[n.type] || iconMap.info}</div>
                    <div className="notif-content">
                      <span className="notif-item-title">{n.title}</span>
                      {n.body && <span className="notif-item-body">{n.body}</span>}
                      <span className="notif-item-time">{timeAgo(n.timestamp)}</span>
                    </div>
                    {!n.read && <span className="notif-unread-dot" />}
                  </div>
                ))
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default NotificationDropdown;
