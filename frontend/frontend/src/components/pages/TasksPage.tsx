import React, { useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { CheckSquare, Plus, Clock, AlertTriangle, CheckCircle2, Circle, Trash2, Send } from 'lucide-react';
import { CompanionService } from '../../services/companion.service';
import { useCompanionStore } from '../../store/companion.store';

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
  const userId = useCompanionStore(s => s.userId);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const fetchTasks = useCallback(async () => {
    try {
      const data = await CompanionService.getTasks(userId);
      setTasks(data.tasks || []);
    } catch { setTasks([]); }
    setLoading(false);
  }, [userId]);

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  const handleCreateTask = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!newTaskTitle.trim() || submitting) return;

    setSubmitting(true);
    try {
      const res = await CompanionService.createTask(newTaskTitle.trim(), 'medium', 'general', userId);
      if (res.task) {
        setTasks(prev => [res.task, ...prev]);
      } else {
        await fetchTasks();
      }
      setNewTaskTitle('');
      setShowAddForm(false);
    } catch (err) {
      console.error('Failed to create task:', err);
    }
    setSubmitting(false);
  };

  const toggleStatus = async (task: Task) => {
    const newStatus = task.status === 'completed' ? 'pending' : 'completed';
    setTasks(prev => prev.map(t => t.id === task.id ? { ...t, status: newStatus } : t));
    try { await CompanionService.updateTask(task.id, newStatus, userId); } catch (err) {
      console.error('Task update failed:', err);
    }
  };

  const deleteTask = async (taskId: string) => {
    try {
      setTasks(prev => prev.filter(t => t.id !== taskId));
      await CompanionService.deleteTask(taskId, userId);
    } catch (err) {
      console.error('Task delete failed:', err);
    }
  };

  const filtered = filter === 'all' ? tasks : tasks.filter(t => t.status === filter);
  const counts = {
    all: tasks.length,
    pending: tasks.filter(t => t.status === 'pending').length,
    in_progress: tasks.filter(t => t.status === 'in_progress').length,
    completed: tasks.filter(t => t.status === 'completed').length,
  };

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="page-container pb-20">
      <div className="page-header">
        <div className="flex items-center gap-3">
          <div className="page-icon" style={{ background: 'rgba(16,185,129,0.15)', color: '#10b981' }}><CheckSquare size={20} /></div>
          <div>
            <h1 className="page-title">Tasks</h1>
            <p className="page-subtitle">{counts.pending} pending · {counts.in_progress} in progress · {counts.completed} done</p>
          </div>
        </div>
        <button onClick={() => setShowAddForm(prev => !prev)} className="page-btn-primary"><Plus size={14} /> Add Task</button>
      </div>

      {/* Quick Add Task Input Form */}
      {showAddForm && (
        <form onSubmit={handleCreateTask} className="mb-4 flex items-center gap-2 bg-surface-elevated p-3 rounded-lg border border-border-default">
          <input
            type="text"
            placeholder="Type task title and press Enter..."
            value={newTaskTitle}
            onChange={e => setNewTaskTitle(e.target.value)}
            className="flex-1 bg-transparent text-text-primary outline-none placeholder:text-text-muted text-sm"
            autoFocus
          />
          <button
            type="submit"
            disabled={!newTaskTitle.trim() || submitting}
            className="page-btn-primary disabled:opacity-40"
          >
            {submitting ? 'Adding...' : <><Send size={12} /> Save Task</>}
          </button>
        </form>
      )}

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
          <button onClick={() => setShowAddForm(true)} className="page-btn-primary mt-2"><Plus size={14} /> Create Task</button>
        </div>
      ) : (
        <div className="page-card-list">
          {filtered.map(task => (
            <motion.div key={task.id} className="page-card task-card" whileHover={{ scale: 1.01 }}>
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3 flex-1 min-w-0">
                  <button onClick={() => toggleStatus(task)} className="task-check-btn mt-0.5" title="Toggle status">
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
                <button onClick={() => deleteTask(task.id)} className="page-btn-icon text-text-muted hover:text-red-400" title="Delete Task">
                  <Trash2 size={14} />
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </motion.div>
  );
};

export default TasksPage;
