import React from 'react';
import { AssistantResponse } from '../types';
import StatusIndicator from './StatusIndicator';
import TaskCard from './TaskCard';

interface ResponsePanelProps {
  response: AssistantResponse;
  userMessage: string;
  timestamp: string;
}

const ResponsePanel: React.FC<ResponsePanelProps> = ({
  response,
  userMessage,
  timestamp,
}) => {
  const formatTimestamp = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch {
      return dateString;
    }
  };

  if (response.status === 'error') {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-2">
          <StatusIndicator status="failed" label="Error" />
          <span className="text-xs text-gray-500">{formatTimestamp(timestamp)}</span>
        </div>
        <p className="text-red-700 text-sm">{response.error || 'An error occurred'}</p>
      </div>
    );
  }

  const { data } = response;
  const intent = data.intent?.intent || 'unknown';
  const taskType = data.task?.task_type || null;
  const finalDecision = data.decision?.final_decision || 'unknown';
  const assistantResponse = data.decision?.response || data.summary?.summary || 'No response generated';
  const taskCreated = data.decision?.task_created;
  const processedAt = data.processed_at || timestamp;

  // Determine status based on decision
  const getActionStatus = () => {
    if (finalDecision.includes('task_created')) return 'executed';
    if (finalDecision.includes('generated') || finalDecision.includes('response')) return 'executed';
    if (finalDecision === 'bhiv_core') return 'processing';
    return 'pending';
  };

  return (
    <div className="space-y-4">
      {/* User Message */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xs font-medium text-blue-700">You</span>
          <span className="text-xs text-gray-500">{formatTimestamp(timestamp)}</span>
        </div>
        <p className="text-gray-900">{userMessage}</p>
      </div>

      {/* Assistant Response */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs font-medium text-gray-700">Assistant</span>
          <span className="text-xs text-gray-500">{formatTimestamp(processedAt)}</span>
        </div>
        
        <div className="mb-4">
          <p className="text-gray-900 whitespace-pre-wrap">{assistantResponse}</p>
        </div>

        {/* Metadata Section */}
        <div className="border-t border-gray-100 pt-3 space-y-2">
          <div className="flex flex-wrap items-center gap-3 text-sm">
            <div>
              <span className="text-gray-500">Intent:</span>
              <span className="ml-2 font-medium text-gray-900 capitalize">{intent}</span>
            </div>
            
            {taskType && (
              <div>
                <span className="text-gray-500">Task Type:</span>
                <span className="ml-2 font-medium text-gray-900">{taskType.replace('_', ' ')}</span>
              </div>
            )}
            
            <div>
              <span className="text-gray-500">Action:</span>
              <span className="ml-2">
                <StatusIndicator status={getActionStatus()} label={finalDecision.replace('_', ' ')} />
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Task Created Card */}
      {taskCreated && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2">Created Task:</h4>
          <TaskCard task={taskCreated} />
        </div>
      )}
    </div>
  );
};

export default ResponsePanel;

