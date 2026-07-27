// components/shell/Toast.tsx — Toast notification system
import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, AlertTriangle, Info, XCircle, X } from 'lucide-react';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

interface ToastItem {
  id: string;
  type: ToastType;
  title: string;
  body?: string;
  duration?: number;
}

const iconMap: Record<ToastType, React.ReactNode> = {
  success: <CheckCircle2 size={16} className="text-emerald-400" />,
  error:   <XCircle size={16} className="text-red-400" />,
  warning: <AlertTriangle size={16} className="text-amber-400" />,
  info:    <Info size={16} className="text-blue-400" />,
};

const bgMap: Record<ToastType, string> = {
  success: 'toast-success',
  error:   'toast-error',
  warning: 'toast-warning',
  info:    'toast-info',
};

// Global toast queue
let _addToast: ((t: Omit<ToastItem, 'id'>) => void) | null = null;

export function showToast(type: ToastType, title: string, body?: string, duration = 4000) {
  if (_addToast) _addToast({ type, title, body, duration });
}

const ToastContainer: React.FC = () => {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  useEffect(() => {
    _addToast = (t) => {
      const id = `toast_${Date.now()}_${Math.random().toString(36).slice(2, 5)}`;
      setToasts(prev => [...prev, { ...t, id }]);
      setTimeout(() => {
        setToasts(prev => prev.filter(x => x.id !== id));
      }, t.duration || 4000);
    };
    return () => { _addToast = null; };
  }, []);

  const dismiss = (id: string) => {
    setToasts(prev => prev.filter(x => x.id !== id));
  };

  return (
    <div className="toast-container">
      <AnimatePresence>
        {toasts.map(t => (
          <motion.div
            key={t.id}
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            className={`toast-item ${bgMap[t.type]}`}
          >
            <div className="toast-icon">{iconMap[t.type]}</div>
            <div className="toast-content">
              <span className="toast-title">{t.title}</span>
              {t.body && <span className="toast-body">{t.body}</span>}
            </div>
            <button onClick={() => dismiss(t.id)} className="toast-dismiss">
              <X size={12} />
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
};

export default ToastContainer;
