// components/pages/RemindersPage.tsx — Active reminders with mobile responsive design
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
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="page-container pb-24 px-3 sm:px-6">
      {/* Responsive Header */}
      <div className="flex flex-col sm:flex-row gap-3 sm:items-center justify-between mb-4 border-b border-border-subtle pb-4">
        <div className="flex items-center gap-3">
          <div className="page-icon" style={{ background: 'rgba(245,158,11,0.15)', color: '#f59e0b' }}><Bell size={20} /></div>
          <div>
            <h1 className="page-title text-base sm:text-xl font-bold">Reminders</h1>
            <p className="page-subtitle text-xs text-text-muted">{reminders.filter(r => r.status === 'active').length} active reminders</p>
          </div>
        </div>
        <button
          onClick={() => setShowAddForm(prev => !prev)}
          className="page-btn-primary text-xs py-1.5 px-3 flex items-center gap-1 self-start sm:self-auto"
        >
          <Plus size={14} /> Add Reminder
        </button>
      </div>

      {/* Mobile-Optimized Inline Add Reminder Form */}
      <AnimatePresence>
        {showAddForm && (
          <motion.form
            initial={{ opacity: 0, height: 0, y: -10 }}
            animate={{ opacity: 1, height: 'auto', y: 0 }}
            exit={{ opacity: 0, height: 0, y: -10 }}
            onSubmit={handleCreateReminder}
            className="mb-6 p-3 sm:p-4 rounded-xl bg-surface-elevated border border-amber-500/30 flex flex-col gap-3 shadow-xl w-full max-w-full overflow-hidden"
          >
            <div className="flex items-center justify-between border-b border-border-subtle pb-2">
              <h3 className="text-xs sm:text-sm font-semibold text-text-primary flex items-center gap-2">
                <Bell size={16} className="text-amber-400 flex-shrink-0" /> Create New Reminder
              </h3>
              <button
                type="button"
                onClick={() => setShowAddForm(false)}
                className="text-text-muted hover:text-text-primary p-1 flex-shrink-0"
              >
                <X size={16} />
              </button>
            </div>

            <div className="flex flex-col gap-2.5 w-full max-w-full min-w-0 overflow-hidden">
              <div className="min-w-0 w-full overflow-hidden">
                <label className="block text-2xs text-text-muted mb-1 font-medium truncate">Reminder Message *</label>
                <input
                  type="text"
                  required
                  value={newMessage}
                  onChange={e => setNewMessage(e.target.value)}
                  placeholder="e.g. Check messages / Pay electric bill"
                  className="form-input-responsive bg-surface-overlay border border-border-subtle rounded-lg px-3 py-2 text-xs text-text-primary focus:outline-none focus:border-amber-400 w-full max-w-full min-w-0"
                />
              </div>

              <div className="grid grid-cols-2 gap-2 sm:gap-3 w-full max-w-full min-w-0 overflow-hidden box-border">
                <div className="min-w-0 w-full overflow-hidden date-time-input-container">
                  <label className="block text-2xs text-text-muted mb-1 font-medium truncate text-center">Date *</label>
                  <input
                    type="date"
                    required
                    value={newDate}
                    onChange={e => setNewDate(e.target.value)}
                    className="bg-surface-overlay border border-border-subtle rounded-xl px-2 py-2 text-xs text-text-primary focus:outline-none focus:border-amber-400 w-full min-w-0 max-w-full text-center font-medium box-border"
                  />
                </div>

                <div className="min-w-0 w-full overflow-hidden date-time-input-container">
                  <label className="block text-2xs text-text-muted mb-1 font-medium truncate text-center">Time *</label>
                  <input
                    type="time"
                    required
                    value={newTime}
                    onChange={e => setNewTime(e.target.value)}
                    className="bg-surface-overlay border border-border-subtle rounded-xl px-2 py-2 text-xs text-text-primary focus:outline-none focus:border-amber-400 w-full min-w-0 max-w-full text-center font-medium box-border"
                  />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 w-full pt-3 border-t border-border-subtle/50">
              <button
                type="button"
                onClick={() => setShowAddForm(false)}
                className="w-full py-2 rounded-xl border border-border-subtle text-xs text-text-muted hover:bg-surface-overlay font-medium transition-all text-center cursor-pointer active:scale-95"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting || !newMessage.trim()}
                className="w-full py-2 rounded-xl bg-amber-500 text-black font-semibold text-xs hover:bg-amber-400 transition-all flex items-center justify-center gap-1.5 shadow-md cursor-pointer active:scale-95 disabled:opacity-50"
              >
                <Check size={14} /> {submitting ? 'Setting...' : 'Set Reminder'}
              </button>
            </div>
          </motion.form>
        )}
      </AnimatePresence>

      {loading ? (
        <div className="page-loading py-8 text-center text-xs text-text-muted">Loading reminders...</div>
      ) : reminders.length === 0 ? (
        <div className="page-empty py-10 flex flex-col items-center gap-2">
          <Bell size={32} className="text-text-muted" />
          <p className="text-xs text-text-muted">No active reminders</p>
          <button onClick={() => setShowAddForm(true)} className="page-btn-primary mt-1 text-xs py-1.5 px-3">
            <Plus size={14} /> Create Reminder
          </button>
        </div>
      ) : (
        <div className="page-card-list flex flex-col gap-2.5">
          {reminders.map(rem => {
            const isPast = new Date(rem.time).getTime() <= now;
            return (
              <motion.div key={rem.id} className={`page-card p-3 rounded-xl bg-surface-elevated border border-border-subtle ${isPast ? 'border-amber-500/40 bg-amber-500/5' : ''}`} whileHover={{ scale: 1.005 }}>
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-start gap-2.5 flex-1 min-w-0">
                    <div className={`p-2 rounded-lg flex-shrink-0 mt-0.5 ${isPast ? 'bg-amber-500/20 text-amber-400 animate-pulse' : 'bg-surface-overlay text-text-secondary'}`}>
                      <Bell size={15} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="page-card-title text-xs font-semibold text-text-primary break-words">{rem.message}</h4>
                      <div className="flex items-center gap-2 mt-1 flex-wrap">
                        <span className={`text-2xs font-semibold px-2 py-0.5 rounded-full flex items-center gap-1 ${isPast ? 'bg-red-500/20 text-red-400' : 'bg-amber-500/10 text-amber-400'}`}>
                          <Clock size={10} /> {getCountdown(rem.time)}
                        </span>
                        <span className="text-2xs text-text-muted">
                          {new Date(rem.time).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                        </span>
                        {rem.repeat && (
                          <span className="text-2xs text-text-muted flex items-center gap-1"><Repeat size={10} /> {rem.repeat}</span>
                        )}
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => removeReminder(rem.id)}
                    className="text-text-muted hover:text-red-400 p-1.5 rounded-lg hover:bg-red-500/10 transition-colors flex-shrink-0"
                    title="Delete reminder"
                  >
                    <Trash2 size={14} />
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
