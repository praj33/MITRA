// components/pages/WorkflowsPage.tsx — Available workflows with run buttons
import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Play, Loader2, CheckCircle2, Clock } from 'lucide-react';
import { CompanionService } from '../../services/companion.service';
import { useCompanionStore } from '../../store/companion.store';

interface Workflow {
  id: string; name: string; description: string;
  icon: string; status: string; last_run?: string;
}

const defaultWorkflows: Workflow[] = [
  { id: 'wf_briefing', name: 'Morning Briefing', description: 'Summarize today\'s schedule, priority tasks, and key reminders', icon: '🌅', status: 'idle' },
  { id: 'wf_email_sync', name: 'Email Audit & Digest', description: 'Review recent unread messages and highlight action items', icon: '📧', status: 'idle' },
  { id: 'wf_task_triage', name: 'Task Triage', description: 'Organize high priority pending tasks and clear completed ones', icon: '⚡', status: 'idle' },
  { id: 'wf_calendar_sync', name: 'Calendar Guard', description: 'Check upcoming meetings and set automatic reminder alerts', icon: '📅', status: 'idle' },
];

const WorkflowsPage: React.FC<{ onChatNavigate: (msg: string) => void }> = ({ onChatNavigate }) => {
  const [workflows, setWorkflows] = useState<Workflow[]>(defaultWorkflows);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState<string | null>(null);
  const [results, setResults] = useState<Record<string, string>>({});

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const data = await Promise.race([
          CompanionService.getWorkflows(),
          new Promise<any>((_, reject) => setTimeout(() => reject(new Error('timeout')), 2500))
        ]);
        if (active && data?.workflows && data.workflows.length > 0) {
          setWorkflows(data.workflows);
        }
      } catch {
        if (active) setWorkflows(defaultWorkflows);
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => { active = false; };
  }, []);

  const runWorkflow = async (wf: Workflow) => {
    setRunning(wf.id);
    try {
      const userId = useCompanionStore.getState().userId;
      const resp = await CompanionService.runWorkflow(wf.name.toLowerCase().replace(/\s+/g, '_'), userId);
      setResults(prev => ({ ...prev, [wf.id]: resp.message || resp.result || 'Workflow completed successfully' }));
      setWorkflows(prev => prev.map(w => w.id === wf.id ? { ...w, status: 'completed', last_run: new Date().toISOString() } : w));
    } catch {
      setResults(prev => ({ ...prev, [wf.id]: 'Workflow requires LLM API key configuration.' }));
    }
    setRunning(null);
  };

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="page-container">
      <div className="page-header">
        <div className="flex items-center gap-3">
          <div className="page-icon" style={{ background: 'rgba(59,130,246,0.15)', color: '#3b82f6' }}><Play size={20} /></div>
          <div>
            <h1 className="page-title">Workflows</h1>
            <p className="page-subtitle">Automate your daily routines</p>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="page-loading py-8 text-center text-xs text-text-muted">Loading workflows...</div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4 w-full">
          {workflows.map(wf => (
            <motion.div
              key={wf.id}
              className="p-4 rounded-2xl bg-surface-elevated border border-border-subtle hover:border-brand/40 transition-all flex flex-col justify-between shadow-sm"
              whileHover={{ y: -2 }}
            >
              <div>
                <div className="w-10 h-10 rounded-xl bg-brand/10 border border-brand/20 flex items-center justify-center text-xl mb-3">
                  {wf.icon}
                </div>
                <h4 className="text-sm font-bold text-text-primary mb-1">{wf.name}</h4>
                <p className="text-xs text-text-muted leading-relaxed mb-3">{wf.description}</p>
              </div>

              <div>
                {wf.last_run && (
                  <p className="text-3xs text-text-muted flex items-center gap-1 mb-3">
                    <Clock size={11} className="text-brand-light" /> Last run: {new Date(wf.last_run).toLocaleDateString()}
                  </p>
                )}
                <button
                  onClick={() => runWorkflow(wf)}
                  disabled={running === wf.id}
                  className={`w-full py-2 px-3 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-all cursor-pointer active:scale-95 disabled:opacity-50 ${
                    results[wf.id]
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      : 'bg-brand text-white hover:bg-brand-light shadow-glow-sm'
                  }`}
                  aria-label={`Run ${wf.name} workflow`}
                >
                  {running === wf.id ? (
                    <><Loader2 size={13} className="animate-spin" /> Running...</>
                  ) : results[wf.id] ? (
                    <><CheckCircle2 size={13} /> Completed</>
                  ) : (
                    <><Play size={13} /> Run Routine</>
                  )}
                </button>
                {results[wf.id] && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    className="mt-2.5 p-2.5 rounded-xl bg-surface-overlay border border-border-subtle text-2xs text-text-secondary leading-relaxed"
                  >
                    {results[wf.id]}
                  </motion.div>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </motion.div>
  );
};

export default WorkflowsPage;
