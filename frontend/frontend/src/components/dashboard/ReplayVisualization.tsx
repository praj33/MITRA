import React, { useState } from 'react';
import { apiService } from '../../services/api';

interface TraceStage {
  stage: string;
  timestamp: string;
  artifact_locator?: string;
}

interface ReplayResult {
  trace_id: string;
  stages_count: number;
  stages: TraceStage[];
}

export const ReplayVisualization: React.FC = () => {
  const [traceId, setTraceId] = useState('');
  const [stages, setStages] = useState<TraceStage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadStages = async () => {
    if (!traceId.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL}/api/replay/${traceId}/stages`,
        { headers: { 'X-API-Key': process.env.REACT_APP_API_KEY || '' } }
      );
      const data = await response.json();
      setStages(data.stages || []);
    } catch (e) {
      setError('Failed to load trace stages');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 bg-gray-800/50 rounded-xl border border-gray-700">
      <h3 className="text-lg font-semibold text-white mb-4">Replay Visualization</h3>

      <div className="flex gap-2 mb-6">
        <input
          type="text"
          value={traceId}
          onChange={(e) => setTraceId(e.target.value)}
          placeholder="Enter trace ID..."
          className="flex-1 px-4 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none"
        />
        <button
          onClick={loadStages}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition"
        >
          {loading ? 'Loading...' : 'Load'}
        </button>
      </div>

      {error && (
        <div className="bg-red-900/30 border border-red-500 rounded-lg p-3 mb-4 text-red-300 text-sm">
          {error}
        </div>
      )}

      {stages.length > 0 && (
        <div className="space-y-2">
          <p className="text-gray-400 text-sm mb-3">{stages.length} stages found</p>
          {stages.map((stage, idx) => (
            <div
              key={idx}
              className="flex items-center gap-3 p-3 bg-gray-700/50 rounded-lg"
            >
              <div className="w-8 h-8 rounded-full bg-blue-600/30 flex items-center justify-center text-blue-400 text-sm font-bold">
                {idx + 1}
              </div>
              <div className="flex-1">
                <p className="text-white font-medium">{stage.stage}</p>
                <p className="text-gray-400 text-xs">{stage.timestamp}</p>
              </div>
              {stage.artifact_locator && (
                <span className="text-xs bg-gray-600 text-gray-300 px-2 py-1 rounded">
                  {stage.artifact_locator}
                </span>
              )}
            </div>
          ))}
        </div>
      )}

      {stages.length === 0 && !loading && !error && (
        <p className="text-gray-500 text-center py-8">
          Enter a trace ID and click Load to visualize the request pipeline
        </p>
      )}
    </div>
  );
};

export default ReplayVisualization;
