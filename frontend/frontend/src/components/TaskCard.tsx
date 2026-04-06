import React from 'react';
import { Task } from '../types';
import StatusIndicator from './StatusIndicator';

interface TaskCardProps {
  task: Task;
  onStatusUpdate?: (taskId: number, newStatus: string) => void;
}

const TaskCard: React.FC<TaskCardProps> = ({ task, onStatusUpdate }) => {
  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateString;
    }
  };

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 hover:border-orange-500/50 transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <StatusIndicator status={task.status} />
          </div>
          <p className="text-gray-200 text-sm leading-relaxed">{task.description}</p>
        </div>
      </div>
      
      <div className="flex items-center justify-between text-xs text-gray-500 pt-3 border-t border-gray-700">
        <div className="flex items-center gap-4">
          <span>Created: <span className="text-gray-400">{formatDate(task.created_at)}</span></span>
          {task.updated_at !== task.created_at && (
            <span>Updated: <span className="text-gray-400">{formatDate(task.updated_at)}</span></span>
          )}
        </div>
      </div>
    </div>
  );
};

export default TaskCard;
