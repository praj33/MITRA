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
        <div className="page-loading">Loading workflows...</div>
      ) : (
        <div className="workflows-grid">
          {workflows.map(wf => (
            <motion.div key={wf.id} className="workflow-card" whileHover={{ scale: 1.02 }}>
              <div className="workflow-icon">{wf.icon}</div>
              <h4 className="workflow-name">{wf.name}</h4>
              <p className="workflow-desc">{wf.description}</p>
              {wf.last_run && (
                <p className="workflow-meta"><Clock size={10} /> Last: {new Date(wf.last_run).toLocaleDateString()}</p>
              )}
              <button
                onClick={() => runWorkflow(wf)}
                disabled={running === wf.id}
                className={`workflow-run-btn ${results[wf.id] ? 'completed' : ''}`}
              >
                {running === wf.id ? (
                  <><Loader2 size={14} className="animate-spin" /> Running...</>
                ) : results[wf.id] ? (
                  <><CheckCircle2 size={14} /> Done</>
                ) : (
                  <><Play size={14} /> Run</>
                )}
              </button>
              {results[wf.id] && (
                <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}
                  className="workflow-result">
                  {results[wf.id]}
                </motion.div>
              )}
            </motion.div>
          ))}
        </div>
      )}
    </motion.div>
  );
};

export default WorkflowsPage;
