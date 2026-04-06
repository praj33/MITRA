import React from 'react';
import { Task } from '../types';
import { translateTaskStatus, translateTaskType, getTaskConfirmation } from '../utils/uxTranslations';
import { formatFriendlyTimestamp } from '../utils/translations';

interface ActionCardProps {
  task: Task;
  onStatusUpdate?: (taskId: number, newStatus: string) => void;
  showNextStep?: boolean;
}

const ActionCard: React.FC<ActionCardProps> = ({ task, showNextStep = true }) => {
  // Use UX translations for human-friendly display
  const taskStatus = translateTaskStatus(task.status);
  const taskType = translateTaskType((task as any).type || 'general_task');

  // Get status badge color classes
  const getStatusColorClasses = (color: string): string => {
    const colors: Record<string, string> = {
      'yellow': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
      'blue': 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
      'green': 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
      'red': 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
      'gray': 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300',
    };
    return colors[color] || colors['gray'];
  };

  return (
    <div className="backdrop-blur-xl bg-white/80 dark:bg-iosGray-800/80 border border-white/40 dark:border-iosGray-700/40 rounded-2xl p-5 hover:shadow-ios-lg transition-all duration-300">
      {/* Header with task type icon and status badge */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{taskType.icon}</span>
          <span className="text-sm font-semibold text-iosGray-700 dark:text-iosGray-300 font-sf">
            {taskType.label} Created
          </span>
        </div>
        <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${getStatusColorClasses(taskStatus.color)}`}>
          <span>{taskStatus.emoji}</span>
          <span>{taskStatus.label}</span>
        </span>
      </div>

      {/* Task description - prominent */}
      <div className="mb-4">
        <p className="text-iosGray-900 dark:text-white text-base leading-relaxed font-medium font-sf">
          "{task.description}"
        </p>
      </div>

      {/* Confirmation message */}
      <div className="bg-iosBlue-50 dark:bg-iosBlue-900/20 rounded-xl p-3 mb-4">
        <p className="text-sm text-iosBlue-700 dark:text-iosBlue-300 font-sf">
          {getTaskConfirmation((task as any).type || 'general_task', task.description)}
        </p>
      </div>

      {/* Next step hint */}
      {showNextStep && taskStatus.hint && (
        <div className="flex items-center gap-2 p-3 bg-iosGray-50 dark:bg-iosGray-900/50 rounded-xl">
          <span className="text-lg">👉</span>
          <div>
            <p className="text-xs text-iosGray-500 dark:text-iosGray-400 font-sf uppercase tracking-wide">Next Step</p>
            <p className="text-sm text-iosGray-700 dark:text-iosGray-300 font-sf">{taskStatus.hint}</p>
          </div>
        </div>
      )}

      {/* Timestamp footer */}
      <div className="flex items-center justify-between text-xs text-iosGray-500 dark:text-iosGray-500 pt-4 mt-4 border-t border-iosGray-200/50 dark:border-iosGray-700/50 font-sf">
        <span>Created {formatFriendlyTimestamp(task.created_at)}</span>
        {task.updated_at !== task.created_at && (
          <span>Updated {formatFriendlyTimestamp(task.updated_at)}</span>
        )}
      </div>
    </div>
  );
};

export default ActionCard;
