import React, { useState } from 'react';
import { AssistantResponse } from '../types';
import StatusIndicator from './StatusIndicator';
import TaskCard from './TaskCard';
import EnforcementBadge from './EnforcementBadge';
import SafetyLabel from './SafetyLabel';
import { 
  translateIntent, 
  translateTaskType, 
  translateActionStatus,
  formatFriendlyTimestamp 
} from '../utils/translations';

interface CommandExecutionProps {
  response: AssistantResponse;
  userCommand: string;
  timestamp: string;
  executionNumber: number;
}

const CommandExecution: React.FC<CommandExecutionProps> = ({
  response,
  userCommand,
  timestamp,
  executionNumber,
}) => {
  const [showAdvancedDetails, setShowAdvancedDetails] = useState(false);

  if (response.status === 'error') {
    return (
      <div className="bg-gray-900 border border-red-500/30 rounded-lg overflow-hidden">
        <div className="bg-red-900/20 border-b border-red-500/30 px-6 py-3">
          <div className="flex items-center justify-between">
            <StatusIndicator status="failed" label="Something went wrong" />
            <span className="text-xs text-gray-500">{formatFriendlyTimestamp(timestamp)}</span>
          </div>
        </div>
        <div className="p-6">
          <div className="mb-4">
            <div className="bg-gray-800 border border-gray-700 rounded px-4 py-2 text-gray-300 text-sm">
              {userCommand}
            </div>
          </div>
          <div className="bg-red-900/10 border border-red-500/30 rounded px-4 py-3">
            <p className="text-red-300 text-sm">{response.error || 'Something went wrong. Please try again.'}</p>
          </div>
        </div>
      </div>
    );
  }

  const { data } = response;
  const { enforcement, safety } = data;
  const intent = data.intent?.intent || 'unknown';
  const taskType = data.task?.task_type || null;
  const finalDecision = data.decision?.final_decision || 'unknown';
  const assistantResponse = data.decision?.response || data.summary?.summary || 'No response generated';
  const taskCreated = data.decision?.task_created;
  const processedAt = data.processed_at || timestamp;

  // Determine status based on decision and execution state
  const getActionStatus = (): 'executed' | 'completed' | 'executing' | 'pending' | 'failed' | 'skipped' => {
    // Check execution state first if available
    const execStatus = data.execution?.status;
    if (execStatus) {
      if (execStatus === 'completed') return 'completed';
      if (execStatus === 'executing') return 'executing';
      if (execStatus === 'failed') return 'failed';
      if (execStatus === 'skipped') return 'skipped';
    }
    
    // Fallback to enforcement and decision logic
    if (enforcement?.decision === 'block') return 'skipped';
    if (response.status === 'error') return 'failed';
    if (finalDecision.includes('task_created')) return 'completed';
    if (finalDecision.includes('generated') || finalDecision.includes('response')) return 'completed';
    if (finalDecision === 'bhiv_core') return 'executing';
    return 'pending';
  };

  const getActionLabel = () => {
    return translateActionStatus(status, finalDecision);
  };

  const status = getActionStatus();
  const statusForStyle = status as 'completed' | 'executing' | 'failed' | 'pending' | 'skipped';
  
  // Get execution error if available
  const executionError = data.execution?.error;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden shadow-xl">
      {/* Message Header */}
      <div className={`border-b-2 px-6 py-4 ${
          statusForStyle === 'completed' ? 'bg-green-900/30 border-green-500/50' :
          statusForStyle === 'executing' ? 'bg-blue-900/30 border-blue-500/50' :
          statusForStyle === 'failed' ? 'bg-red-900/30 border-red-500/50' :
          statusForStyle === 'skipped' ? 'bg-orange-900/30 border-orange-500/50' :
          'bg-gray-800/50 border-gray-700'
        }`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 flex-wrap">
            <StatusIndicator status={status} label={getActionLabel()} />
            {executionError && (
              <>
                <span className="text-xs text-gray-600">•</span>
                <span className="text-xs text-red-400 font-medium">Error</span>
              </>
            )}
          </div>
          <span className="text-xs text-gray-500">{formatFriendlyTimestamp(processedAt)}</span>
        </div>
        
        {/* Error Display */}
        {executionError && (
          <div className="mt-3 pt-3 border-t border-red-500/30">
            <div className="text-xs text-red-300 font-medium">Here's what happened:</div>
            <div className="text-xs text-red-400/80 mt-1">{executionError}</div>
          </div>
        )}
      </div>

      <div className="p-6 space-y-6">
        {/* User Message */}
        <div>
          <div className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 shadow-sm">
            <p className="text-gray-200 text-sm leading-relaxed">{userCommand}</p>
          </div>
        </div>

        {/* Pipeline Arrow */}
        <div className="flex justify-center -my-2">
          <div className="w-0.5 h-8 bg-gray-700"></div>
        </div>

        {/* Safety Messages (if needed) */}
        {enforcement && (enforcement.decision === 'block' || enforcement.decision === 'rewrite') && (
          <div className="ml-8">
            <div className={`rounded-lg px-4 py-3 ${
              enforcement.decision === 'block' 
                ? 'bg-red-900/20 border border-red-500/30' 
                : 'bg-yellow-900/20 border border-yellow-500/30'
            }`}>
              <p className={`text-sm ${
                enforcement.decision === 'block' ? 'text-red-300' : 'text-yellow-300'
              }`}>
                {enforcement.decision === 'block' 
                  ? "I can't help with that request. Let me know if there's something else I can do."
                  : "I rephrased this to keep things safe and clear."}
              </p>
            </div>
          </div>
        )}

        {safety && (safety.level === 'blocked' || safety.level === 'high_risk') && (
          <div className="ml-8">
            <div className={`rounded-lg px-4 py-3 ${
              safety.level === 'blocked'
                ? 'bg-red-900/20 border border-red-500/30'
                : 'bg-orange-900/20 border border-orange-500/30'
            }`}>
              <p className={`text-sm ${
                safety.level === 'blocked' ? 'text-red-300' : 'text-orange-300'
              }`}>
                {safety.level === 'blocked'
                  ? "I can't provide that content."
                  : "I'm being careful with this response."}
              </p>
            </div>
          </div>
        )}

        {/* Advanced Details Toggle */}
        {(enforcement || safety) && (
          <div className="ml-8">
            <button
              onClick={() => setShowAdvancedDetails(!showAdvancedDetails)}
              className="text-xs text-gray-500 hover:text-gray-400 underline"
            >
              {showAdvancedDetails ? 'Hide' : 'Show'} advanced details
            </button>
            {showAdvancedDetails && (
              <div className="mt-2 bg-gray-800/80 border border-gray-700 rounded-lg px-4 py-3">
                {enforcement && (
                  <div className="mb-3">
                    <div className="text-xs text-gray-400 mb-2">Safety Check</div>
                    <EnforcementBadge
                      decision={enforcement.decision}
                      reason={enforcement.reason}
                      traceId={enforcement.trace_id}
                    />
                  </div>
                )}
                {safety && (
                  <div>
                    <div className="text-xs text-gray-400 mb-2">Safety Assessment</div>
                    <SafetyLabel
                      level={safety.level}
                      score={safety.score}
                      confidence={safety.confidence}
                    />
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Pipeline Arrow */}
        <div className="flex justify-center -my-2">
          <div className="w-0.5 h-8 bg-gray-700"></div>
        </div>

        {/* Intent Understanding */}
        {intent !== 'unknown' && (
          <div className="ml-8">
            <div className="text-sm text-gray-400 italic">
              I understand you want to {translateIntent(intent).toLowerCase()}
              {taskType && ` • ${translateTaskType(taskType)}`}
            </div>
          </div>
        )}

        {/* Pipeline Arrow */}
        <div className="flex justify-center -my-2">
          <div className="w-0.5 h-8 bg-gray-700"></div>
        </div>

        {/* Status (only show if not completed or if there's an error) */}
        {(statusForStyle !== 'completed' || executionError) && (
          <div className="ml-8">
            <StatusIndicator status={status} label={getActionLabel()} />
            {statusForStyle === 'skipped' && enforcement?.decision === 'block' && (
              <div className="mt-2 text-xs text-orange-400/80 italic">
                I can't do that, but I'm here to help with other things.
              </div>
            )}
          </div>
        )}

        {/* Pipeline Arrow */}
        {assistantResponse && (
          <div className="flex justify-center -my-2">
            <div className="w-0.5 h-8 bg-gray-700"></div>
          </div>
        )}

        {/* Assistant Response */}
        {assistantResponse && (
          <div className="ml-8">
            <div className={`border rounded-lg px-4 py-3 ${
              enforcement?.decision === 'rewrite' 
                ? 'bg-yellow-900/10 border-yellow-500/30' 
                : 'bg-gray-800 border-gray-700'
            }`}>
              <p className="text-gray-300 whitespace-pre-wrap text-sm leading-relaxed">{assistantResponse}</p>
            </div>
          </div>
        )}

        {/* Created Task */}
        {taskCreated && (
          <>
            <div className="flex justify-center -my-2">
              <div className="w-0.5 h-8 bg-gray-700"></div>
            </div>
            <div className="ml-8">
              <div className="text-sm text-gray-400 mb-2">I've created a task for you:</div>
              <TaskCard task={taskCreated} />
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default CommandExecution;

