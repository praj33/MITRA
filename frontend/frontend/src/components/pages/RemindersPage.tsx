// components/pages/RemindersPage.tsx — Active reminders with countdown + built-in Add Reminder form
import React, { useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bell, Plus, Clock, Repeat, Trash2, X, Check } from 'lucide-react';
import { CompanionService } from '../../services/companion.service';
import { useCompanionStore } from '../../store/companion.store';
import { showToast } from '../shell/Toast';

interface Reminder {
  id: string; message: string; time: string;
  status: string; repeat: string | null;
}

const RemindersPage: React.FC<{ onChatNavigate: (msg: string) => void }> = ({ onChatNavigate }) => {
  const userId = useCompanionStore(s => s.userId);
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [loading, setLoading] = useState(true);
  const [now, setNow] = useState(Date.now());

  // Add Reminder Form state
  const [showAddForm, setShowAddForm] = useState(false);
  const [newMessage, setNewMessage] = useState('');
  const [newDate, setNewDate] = useState(new Date().toISOString().split('T')[0]);
  const [newTime, setNewTime] = useState('17:00');
  const [submitting, setSubmitting] = useState(false);

  const fetchReminders = useCallback(async () => {
    try {
      const data = await CompanionService.getReminders(userId);
      setReminders(data.reminders || []);
    } catch { setReminders([]); }
    setLoading(false);
  }, [userId]);

  useEffect(() => {
    fetchReminders();
  }, [fetchReminders]);

  // Tick every minute for countdown
  useEffect(() => {
    const iv = setInterval(() => setNow(Date.now()), 60000);
    return () => clearInterval(iv);
  }, []);

  const handleCreateReminder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || submitting) return;

    setSubmitting(true);
    try {
      const timeIso = `${newDate}T${newTime}:00`;
      const res = await CompanionService.createReminder(newMessage.trim(), timeIso, undefined, userId);

      if (res && res.reminder) {
        setReminders(prev => [res.reminder, ...prev]);
      } else {
        await fetchReminders();
      }

      showToast('success', 'Reminder Set', `Reminder set for ${newDate} at ${newTime}`);
      setNewMessage('');
      setShowAddForm(false);
    } catch (err) {
      console.error('Failed to create reminder:', err);
      showToast('error', 'Error', 'Failed to create reminder.');
    } finally {
      setSubmitting(false);
    }
  };

  const getCountdown = (time: string) => {
    const diff = new Date(time).getTime() - now;
    if (diff <= 0) return 'Due now!';
    const mins = Math.floor(diff / 60000);
    const hrs = Math.floor(mins / 60);
    const days = Math.floor(hrs / 24);
    if (days > 0) return `${days}d ${hrs % 24}h`;
    if (hrs > 0) return `${hrs}h ${mins % 60}m`;
    return `${mins}m`;
  };

  const removeReminder = async (id: string) => {
    try {
      setReminders(prev => prev.filter(r => r.id !== id));
      await CompanionService.deleteReminder(id, userId);
      showToast('info', 'Reminder Deleted', 'Reminder removed.');
    } catch (err) {
      console.error('Failed to delete reminder:', err);
      showToast('error', 'Error', 'Failed to delete reminder.');
    }
  };

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="page-container pb-20">
      <div className="page-header">
        <div className="flex items-center gap-3">
          <div className="page-icon" style={{ background: 'rgba(245,158,11,0.15)', color: '#f59e0b' }}><Bell size={20} /></div>
          <div>
            <h1 className="page-title">Reminders</h1>
            <p className="page-subtitle">{reminders.filter(r => r.status === 'active').length} active reminders</p>
          </div>
        </div>
        <button onClick={() => setShowAddForm(prev => !prev)} className="page-btn-primary"><Plus size={14} /> Add Reminder</button>
      </div>

      {/* Inline Add Reminder Form */}
      <AnimatePresence>
        {showAddForm && (
          <motion.form
            initial={{ opacity: 0, height: 0, y: -10 }}
            animate={{ opacity: 1, height: 'auto', y: 0 }}
            exit={{ opacity: 0, height: 0, y: -10 }}
            onSubmit={handleCreateReminder}
            className="mb-6 p-4 rounded-xl bg-surface-elevated border border-amber-500/30 flex flex-col gap-3 shadow-xl"
          >
            <div className="flex items-center justify-between border-b border-border-subtle pb-2">
              <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2">
                <Bell size={16} className="text-amber-400" /> Create New Reminder
              </h3>
              <button
                type="button"
                onClick={() => setShowAddForm(false)}
                className="text-text-muted hover:text-text-primary"
              >
                <X size={16} />
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="sm:col-span-1">
                <label className="block text-2xs text-text-muted mb-1 font-medium">Reminder Message *</label>
                <input
                  type="text"
                  required
                  value={newMessage}
                  onChange={e => setNewMessage(e.target.value)}
                  placeholder="e.g. Check messages / Pay electric bill"
                  className="w-full bg-surface-overlay border border-border-subtle rounded-lg px-3 py-1.5 text-xs text-text-primary focus:outline-none focus:border-amber-400"
                />
              </div>

              <div>
                <label className="block text-2xs text-text-muted mb-1 font-medium">Date *</label>
                <input
                  type="date"
                  required
                  value={newDate}
                  onChange={e => setNewDate(e.target.value)}
                  className="w-full bg-surface-overlay border border-border-subtle rounded-lg px-3 py-1.5 text-xs text-text-primary focus:outline-none focus:border-amber-400"
                />
              </div>

              <div>
                <label className="block text-2xs text-text-muted mb-1 font-medium">Time *</label>
                <input
                  type="time"
                  required
                  value={newTime}
                  onChange={e => setNewTime(e.target.value)}
                  className="w-full bg-surface-overlay border border-border-subtle rounded-lg px-3 py-1.5 text-xs text-text-primary focus:outline-none focus:border-amber-400"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowAddForm(false)}
                className="px-3 py-1.5 rounded-lg border border-border-subtle text-xs text-text-muted hover:bg-surface-overlay"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting || !newMessage.trim()}
                className="px-4 py-1.5 rounded-lg bg-amber-500 text-black font-medium text-xs hover:bg-amber-400 transition-colors flex items-center gap-1.5"
              >
                <Check size={14} /> {submitting ? 'Setting...' : 'Set Reminder'}
              </button>
            </div>
          </motion.form>
        )}
      </AnimatePresence>

      {loading ? (
        <div className="page-loading">Loading reminders...</div>
      ) : reminders.length === 0 ? (
        <div className="page-empty">
          <Bell size={32} className="text-text-muted" />
          <p>No active reminders</p>
          <button onClick={() => setShowAddForm(true)} className="page-btn-primary mt-2">
            <Plus size={14} /> Create Reminder
          </button>
        </div>
      ) : (
        <div className="page-card-list">
          {reminders.map(rem => {
            const isPast = new Date(rem.time).getTime() <= now;
            return (
              <motion.div key={rem.id} className={`page-card reminder-card ${isPast ? 'reminder-due' : ''}`} whileHover={{ scale: 1.01 }}>
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3 flex-1 min-w-0">
                    <div className={`reminder-icon ${isPast ? 'pulsing' : ''}`}>
                      <Bell size={16} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="page-card-title">{rem.message}</h4>
                      <div className="flex items-center gap-3 mt-1 flex-wrap">
                        <span className={`page-card-badge ${isPast ? 'badge-urgent' : ''}`}>
                          <Clock size={10} /> {getCountdown(rem.time)}
                        </span>
                        <span className="page-card-meta">
                          {new Date(rem.time).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                        </span>
                        {rem.repeat && (
                          <span className="page-card-badge"><Repeat size={10} /> {rem.repeat}</span>
                        )}
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => removeReminder(rem.id)}
                    className="text-text-muted hover:text-red-400 p-1.5 rounded-lg hover:bg-red-500/10 transition-colors"
                    title="Delete reminder"
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </motion.div>
  );
};

export default RemindersPage;
