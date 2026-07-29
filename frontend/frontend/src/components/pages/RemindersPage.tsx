// components/pages/RemindersPage.tsx — Active reminders with countdown
import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Bell, Plus, Clock, Repeat, Trash2 } from 'lucide-react';
import { CompanionService } from '../../services/companion.service';

interface Reminder {
  id: string; message: string; time: string;
  status: string; repeat: string | null;
}

const RemindersPage: React.FC<{ onChatNavigate: (msg: string) => void }> = ({ onChatNavigate }) => {
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [loading, setLoading] = useState(true);
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    (async () => {
      try {
        const data = await CompanionService.getReminders();
        setReminders(data.reminders || []);
      } catch { setReminders([]); }
      setLoading(false);
    })();
  }, []);

  // Tick every minute for countdown
  useEffect(() => {
    const iv = setInterval(() => setNow(Date.now()), 60000);
    return () => clearInterval(iv);
  }, []);

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
      await CompanionService.deleteReminder(id);
    } catch (err) {
      console.error('Failed to delete reminder:', err);
    }
  };

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="page-container">
      <div className="page-header">
        <div className="flex items-center gap-3">
          <div className="page-icon" style={{ background: 'rgba(245,158,11,0.15)', color: '#f59e0b' }}><Bell size={20} /></div>
          <div>
            <h1 className="page-title">Reminders</h1>
            <p className="page-subtitle">{reminders.filter(r => r.status === 'active').length} active reminders</p>
          </div>
        </div>
        <button onClick={() => onChatNavigate('Remind me in 30 minutes to check messages')} className="page-btn-primary"><Plus size={14} /> Add Reminder</button>
      </div>

      {loading ? (
        <div className="page-loading">Loading reminders...</div>
      ) : reminders.length === 0 ? (
        <div className="page-empty">
          <Bell size={32} className="text-text-muted" />
          <p>No active reminders</p>
          <button onClick={() => onChatNavigate('Set a reminder for 5pm')} className="page-btn-primary mt-2"><Plus size={14} /> Create Reminder</button>
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
                  <button onClick={() => removeReminder(rem.id)} className="page-btn-icon text-text-muted hover:text-red-400" title="Delete Reminder"><Trash2 size={14} /></button>
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
