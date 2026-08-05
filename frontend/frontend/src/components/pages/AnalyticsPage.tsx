// components/pages/AnalyticsPage.tsx — Productivity Insights & Habit Tracker
import React, { useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, Award, Flame, CheckCircle2, Clock, Zap, Target, Plus, Trash2 } from 'lucide-react';
import { CompanionService } from '../../services/companion.service';
import { useCompanionStore } from '../../store/companion.store';

interface Habit {
  id: string;
  name: string;
  streak: number;
  completedToday: boolean;
}

const defaultHabits: Habit[] = [
  { id: 'h1', name: '🎯 25m Focus Session', streak: 4, completedToday: false },
  { id: 'h2', name: '📖 Read Tech Article / Docs', streak: 7, completedToday: false },
  { id: 'h3', name: '💧 Drink 2L Water', streak: 3, completedToday: false },
  { id: 'h4', name: '🌅 Morning Briefing Check', streak: 12, completedToday: false },
];

const getTodayKey = () => `mitra_habits_${new Date().toISOString().split('T')[0]}`;

const AnalyticsPage: React.FC<{ onChatNavigate: (msg: string) => void }> = ({ onChatNavigate }) => {
  const userId = useCompanionStore(s => s.userId);
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [habits, setHabits] = useState<Habit[]>(() => {
    try {
      const saved = localStorage.getItem(getTodayKey());
      if (saved) {
        const completedIds: string[] = JSON.parse(saved);
        return defaultHabits.map(h => ({
          ...h,
          completedToday: completedIds.includes(h.id),
        }));
      }
    } catch {}
    return defaultHabits;
  });
  const [newHabitName, setNewHabitName] = useState('');
  const [showAddHabit, setShowAddHabit] = useState(false);

  const loadAnalytics = useCallback(async () => {
    try {
      const res = await CompanionService.getAnalytics(userId);
      setData(res);
    } catch {
      setData(null);
    }
    setLoading(false);
  }, [userId]);

  useEffect(() => {
    loadAnalytics();
  }, [loadAnalytics]);

  const saveHabitsState = (updated: Habit[]) => {
    try {
      const completedIds = updated.filter(h => h.completedToday).map(h => h.id);
      localStorage.setItem(getTodayKey(), JSON.stringify(completedIds));
    } catch {}
  };

  const toggleHabit = (id: string) => {
    setHabits(prev => {
      const updated = prev.map(h => {
        if (h.id === id) {
          const nextState = !h.completedToday;
          return {
            ...h,
            completedToday: nextState,
            streak: nextState ? h.streak + 1 : Math.max(0, h.streak - 1),
          };
        }
        return h;
      });
      saveHabitsState(updated);
      return updated;
    });
  };

  const addHabit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newHabitName.trim()) return;
    setHabits(prev => {
      const updated = [
        ...prev,
        { id: 'h_' + Date.now(), name: newHabitName.trim(), streak: 1, completedToday: true },
      ];
      saveHabitsState(updated);
      return updated;
    });
    setNewHabitName('');
    setShowAddHabit(false);
  };

  const deleteHabit = (id: string) => {
    setHabits(prev => prev.filter(h => h.id !== id));
  };

  const score = data?.productivity_score || 88;
  const completionRate = data?.completion_rate || 85.0;
  const focusHours = data?.focus_hours_this_week || 4.5;
  const peakWindow = data?.peak_focus_window || '9:00 AM – 11:30 AM';

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="page-container pb-20">
      {/* Header */}
      <div className="page-header">
        <div className="flex items-center gap-3">
          <div className="page-icon" style={{ background: 'rgba(124,111,247,0.15)', color: '#7c6ff7' }}>
            <TrendingUp size={20} />
          </div>
          <div>
            <h1 className="page-title">Productivity & Habits</h1>
            <p className="page-subtitle">Personalized AI insights & habit tracker</p>
          </div>
        </div>
        <button
          onClick={() => onChatNavigate("Give me a deep evaluation of my productivity performance this week")}
          className="page-btn-primary"
        >
          <Zap size={13} /> Ask Mitra Coaching Tip
        </button>
      </div>

      {loading ? (
        <div className="page-loading">Calculating companion intelligence metrics...</div>
      ) : (
        <div className="flex flex-col gap-5 w-full max-w-full min-w-0">
          {/* Metrics Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 w-full min-w-0">
            {/* Score */}
            <div className="bg-surface-elevated border border-border-subtle rounded-xl p-4 flex flex-col justify-between relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-2xs font-semibold text-text-muted uppercase tracking-wider">Productivity Score</span>
                <Award size={16} className="text-brand-light" />
              </div>
              <div className="my-2 flex items-baseline gap-2">
                <span className="text-3xl font-extrabold text-text-primary tracking-tight">{score}</span>
                <span className="text-xs text-emerald-400 font-medium">/ 100</span>
              </div>
              <div className="w-full bg-surface-overlay h-1.5 rounded-full overflow-hidden">
                <div className="bg-gradient-to-r from-brand to-emerald-400 h-full rounded-full" style={{ width: `${score}%` }} />
              </div>
            </div>

            {/* Completion Rate */}
            <div className="bg-surface-elevated border border-border-subtle rounded-xl p-4 flex flex-col justify-between relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-2xs font-semibold text-text-muted uppercase tracking-wider">Task Completion</span>
                <CheckCircle2 size={16} className="text-emerald-400" />
              </div>
              <div className="my-2 flex items-baseline gap-2">
                <span className="text-3xl font-extrabold text-text-primary tracking-tight">{completionRate}%</span>
              </div>
              <p className="text-2xs text-text-muted">{data?.completed_tasks || 0} of {data?.total_tasks || 0} tasks completed</p>
            </div>

            {/* Peak Focus Window */}
            <div className="bg-surface-elevated border border-border-subtle rounded-xl p-4 flex flex-col justify-between relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-2xs font-semibold text-text-muted uppercase tracking-wider">Peak Focus Hours</span>
                <Clock size={16} className="text-amber-400" />
              </div>
              <div className="my-2">
                <span className="text-sm font-bold text-amber-300 block">{peakWindow}</span>
                <span className="text-xs text-text-muted">{focusHours} hrs focused this week</span>
              </div>
            </div>
          </div>

          {/* Weekly Focus Breakdown */}
          <div className="bg-surface-elevated border border-border-subtle rounded-xl p-4">
            <h3 className="text-xs font-semibold text-text-primary mb-3 flex items-center gap-2">
              <Target size={14} className="text-brand-light" /> Weekly Activity Velocity
            </h3>
            <div className="flex items-end justify-between gap-2 h-28 pt-4 px-2">
              {(data?.weekly_activity || [
                { day: 'Mon', focus_mins: 90 },
                { day: 'Tue', focus_mins: 120 },
                { day: 'Wed', focus_mins: 75 },
                { day: 'Thu', focus_mins: 110 },
                { day: 'Fri', focus_mins: 60 },
                { day: 'Sat', focus_mins: 45 },
                { day: 'Sun', focus_mins: 30 },
              ]).map((item: any) => {
                const heightPercent = Math.min(100, Math.max(15, (item.focus_mins / 120) * 100));
                return (
                  <div key={item.day} className="flex-1 flex flex-col items-center gap-1.5 h-full justify-end">
                    <div className="w-full bg-surface-overlay rounded-t-md relative flex items-end overflow-hidden" style={{ height: '70px' }}>
                      <motion.div
                        initial={{ height: 0 }}
                        animate={{ height: `${heightPercent}%` }}
                        className="w-full bg-gradient-to-t from-brand/50 to-brand-light rounded-t-md"
                      />
                    </div>
                    <span className="text-2xs text-text-muted font-medium">{item.day}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Habits & Daily Routines */}
          <div className="bg-surface-elevated border border-border-subtle rounded-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-semibold text-text-primary flex items-center gap-2">
                <Flame size={15} className="text-orange-400" /> Daily Habits & Streaks
              </h3>
              <button
                onClick={() => setShowAddHabit(!showAddHabit)}
                className="page-btn-sm flex items-center gap-1"
              >
                <Plus size={12} /> Add Habit
              </button>
            </div>

            {/* Add habit inline form */}
            {showAddHabit && (
              <form onSubmit={addHabit} className="mb-3 flex items-center gap-2">
                <input
                  type="text"
                  placeholder="Habit title (e.g. 🎯 Exercise 30m)..."
                  value={newHabitName}
                  onChange={e => setNewHabitName(e.target.value)}
                  className="flex-1 bg-surface-overlay border border-border-subtle rounded-lg px-3 py-1.5 text-xs text-text-primary outline-none focus:border-brand"
                  autoFocus
                />
                <button type="submit" className="page-btn-primary text-xs py-1.5">Save</button>
              </form>
            )}

            <div className="flex flex-col gap-2">
              {habits.map(habit => (
                <div
                  key={habit.id}
                  className="flex items-center justify-between p-2.5 rounded-lg bg-surface-overlay border border-border-subtle"
                >
                  <div className="flex items-center gap-2.5 flex-1 min-w-0">
                    <button
                      onClick={() => toggleHabit(habit.id)}
                      className={`w-5 h-5 rounded-md flex items-center justify-center border transition-all ${
                        habit.completedToday
                          ? 'bg-emerald-500 border-emerald-500 text-white'
                          : 'border-border-default text-transparent hover:border-brand'
                      }`}
                    >
                      <CheckCircle2 size={13} />
                    </button>
                    <span className={`text-xs font-medium truncate ${habit.completedToday ? 'line-through text-text-muted' : 'text-text-primary'}`}>
                      {habit.name}
                    </span>
                  </div>

                  <div className="flex items-center gap-3 flex-shrink-0">
                    <span className="inline-flex items-center gap-1 text-2xs font-semibold px-2 py-0.5 rounded-full bg-orange-500/10 text-orange-400 border border-orange-500/20">
                      <Flame size={11} /> {habit.streak}d
                    </span>
                    <button
                      onClick={() => deleteHabit(habit.id)}
                      className="text-text-muted hover:text-red-400 transition-colors"
                      title="Delete habit"
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </motion.div>
  );
};

export default AnalyticsPage;
