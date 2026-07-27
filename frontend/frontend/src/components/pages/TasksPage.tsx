// components/pages/TasksPage.tsx — Kanban-style task board
import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { CheckSquare, Plus, Clock, AlertTriangle, CheckCircle2, Circle } from 'lucide-react';
import { CompanionService } from '../../services/companion.service';

interface Task {
  id: string; title: string; status: string;
  priority: string; due_date: string | null; category: string;
}

const priorityColors: Record<string, string> = {
  high: '#ef4444', medium: '#f59e0b', low: '#10b981',
};

const statusIcons: Record<string, React.ReactNode> = {
  pending: <Circle size={14} className="text-text-muted" />,
  in_progress: <Clock size={14} className="text-amber-400" />,
  completed: <CheckCircle2 size={14} className="text-emerald-400" />,
};

const TasksPage: React.FC<{ onChatNavigate: (msg: string) => void }> = ({ onChatNavigate }) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    (async () => {
      try {
        const data = await CompanionService.getTasks();
        setTasks(data.tasks || []);
      } catch { setTasks([]); }
      setLoading(false);
    })();
  }, []);

  const toggleStatus = async (task: Task) => {
    const newStatus = task.status === 'completed' ? 'pending' : 'completed';
    setTasks(prev => prev.map(t => t.id === task.id ? { ...t, status: newStatus } : t));
    try { await CompanionService.updateTask(task.id, newStatus); } catch {}
  };

  const filtered = filter === 'all' ? tasks : tasks.filter(t => t.status === filter);
  const counts = {
    all: tasks.length,
    pending: tasks.filter(t => t.status === 'pending').length,
    in_progress: tasks.filter(t => t.status === 'in_progress').length,
    completed: tasks.filter(t => t.status === 'completed').length,
  };

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="page-container">
      <div className="page-header">
        <div className="flex items-center gap-3">
          <div className="page-icon" style={{ background: 'rgba(16,185,129,0.15)', color: '#10b981' }}><CheckSquare size={20} /></div>
          <div>
            <h1 className="page-title">Tasks</h1>
            <p className="page-subtitle">{counts.pending} pending · {counts.in_progress} in progress · {counts.completed} done</p>
          </div>
        </div>
        <button onClick={() => onChatNavigate('Create a new task')} className="page-btn-primary"><Plus size={14} /> Add Task</button>
      </div>

      {/* Filter tabs */}
      <div className="page-tabs">
        {(['all', 'pending', 'in_progress', 'completed'] as const).map(f => (
          <button key={f} onClick={() => setFilter(f)}
            className={`page-tab ${filter === f ? 'active' : ''}`}>
            {f.replace('_', ' ')} ({counts[f]})
          </button>
        ))}
      </div>

      {/* Task list */}
      {loading ? (
        <div className="page-loading">Loading tasks...</div>
      ) : filtered.length === 0 ? (
        <div className="page-empty">
          <CheckSquare size={32} className="text-text-muted" />
          <p>No tasks found</p>
          <button onClick={() => onChatNavigate('Create a task to review code')} className="page-btn-primary mt-2"><Plus size={14} /> Create Task</button>
        </div>
      ) : (
        <div className="page-card-list">
          {filtered.map(task => (
            <motion.div key={task.id} className="page-card task-card" whileHover={{ scale: 1.01 }}>
              <div className="flex items-start gap-3">
                <button onClick={() => toggleStatus(task)} className="task-check-btn mt-0.5">
                  {statusIcons[task.status] || statusIcons.pending}
                </button>
                <div className="flex-1 min-w-0">
                  <h4 className={`page-card-title ${task.status === 'completed' ? 'line-through opacity-50' : ''}`}>{task.title}</h4>
                  <div className="flex items-center gap-2 mt-1 flex-wrap">
                    <span className="page-card-badge" style={{ background: (priorityColors[task.priority] || '#888') + '22', color: priorityColors[task.priority] || '#888' }}>
                      {task.priority === 'high' && <AlertTriangle size={10} />} {task.priority}
                    </span>
                    <span className="page-card-badge">{task.category}</span>
                    {task.due_date && (
                      <span className="page-card-meta"><Clock size={10} /> {new Date(task.due_date).toLocaleDateString()}</span>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </motion.div>
  );
};

export default TasksPage;
