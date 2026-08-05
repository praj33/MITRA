import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sun, Moon, Sunrise, Calendar, CheckSquare, Bell, ChevronDown, ChevronUp, Sparkles, ArrowRight } from 'lucide-react';
import { CompanionService } from '../../services/companion.service';
import { useCompanionStore } from '../../store/companion.store';

interface DailyBriefingData {
  user_id: string;
  user_name: string;
  greeting: string;
  period: string;
  date_display: string;
  today_events_count: number;
  today_events: any[];
  pending_tasks_count: number;
  high_priority_count: number;
  active_reminders_count: number;
  summary_text: string;
  quick_actions: Array<{ id: string; label: string; prompt: string }>;
}

interface DailyBriefingCardProps {
  onActionClick: (prompt: string) => void;
}

export const DailyBriefingCard: React.FC<DailyBriefingCardProps> = ({ onActionClick }) => {
  const userId = useCompanionStore(s => s.userId);
  const [briefing, setBriefing] = useState<DailyBriefingData | null>(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(true);

  useEffect(() => {
    let isMounted = true;
    const fetchBriefing = async () => {
      try {
        const data = await CompanionService.getDailyBriefing(userId);
        if (isMounted) setBriefing(data);
      } catch (err) {
        console.warn('Daily briefing fetch failed:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };
    fetchBriefing();
    return () => { isMounted = false; };
  }, [userId]);

  if (loading || !briefing) return null;

  const getPeriodIcon = () => {
    if (briefing.period === 'morning') return <Sunrise size={18} className="text-amber-400" />;
    if (briefing.period === 'afternoon') return <Sun size={18} className="text-amber-400" />;
    return <Moon size={18} className="text-indigo-400" />;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full mb-4 rounded-2xl bg-gradient-to-r from-brand/10 via-surface-elevated to-surface-elevated border border-brand/25 p-3.5 sm:p-4 shadow-xl overflow-hidden backdrop-blur-md"
    >
      {/* Top Banner Row */}
      <div className="flex items-center justify-between gap-2 border-b border-border-subtle/60 pb-2.5">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-8 h-8 rounded-xl bg-brand/15 border border-brand/30 flex items-center justify-center flex-shrink-0">
            {getPeriodIcon()}
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-1.5">
              <h3 className="text-xs sm:text-sm font-bold text-text-primary truncate">{briefing.greeting}</h3>
              <Sparkles size={13} className="text-brand-light flex-shrink-0 animate-pulse" />
            </div>
            <p className="text-2xs text-text-muted font-medium">{briefing.date_display}</p>
          </div>
        </div>

        <button
          onClick={() => setExpanded(prev => !prev)}
          className="p-1 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-overlay transition-colors flex-shrink-0"
          aria-label="Toggle briefing"
        >
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
      </div>

      {/* Expanded Content */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="flex flex-col gap-3 pt-3"
          >
            <p className="text-xs text-text-secondary leading-relaxed font-normal">
              {briefing.summary_text}
            </p>

            {/* Quick Status Badges */}
            <div className="flex items-center gap-2 flex-wrap text-2xs font-semibold">
              <span className="px-2.5 py-1 rounded-full bg-brand/10 text-brand-light border border-brand/20 flex items-center gap-1">
                <Calendar size={12} /> {briefing.today_events_count} Events Today
              </span>
              <span className="px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center gap-1">
                <CheckSquare size={12} /> {briefing.pending_tasks_count} Pending Tasks
              </span>
              <span className="px-2.5 py-1 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center gap-1">
                <Bell size={12} /> {briefing.active_reminders_count} Active Reminders
              </span>
            </div>

            {/* Quick Action Buttons */}
            {briefing.quick_actions && briefing.quick_actions.length > 0 && (
              <div className="flex items-center gap-2 pt-1 flex-wrap">
                {briefing.quick_actions.map(action => (
                  <button
                    key={action.id}
                    onClick={() => onActionClick(action.prompt)}
                    className="px-3 py-1.5 rounded-xl bg-surface-overlay hover:bg-brand/20 border border-border-subtle hover:border-brand/40 text-xs font-semibold text-text-primary hover:text-brand-light transition-all flex items-center gap-1.5 shadow-sm active:scale-95"
                  >
                    <span>{action.label}</span>
                    <ArrowRight size={12} className="opacity-70" />
                  </button>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};
