import React, { useState, useEffect, useCallback } from 'react';

interface SystemHealth {
  status: string;
  version: string;
  mongodb: string;
  timestamp: string;
  uptime?: { seconds: number; hours: number };
  requests?: { total: number; errors: number; success_rate: number };
}

export const SystemHealthPanel: React.FC = () => {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchHealth = useCallback(async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/health`);
      const data = await response.json();
      setHealth(data);
    } catch (e) {
      setHealth(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 10000);
    return () => clearInterval(interval);
  }, [fetchHealth]);

  if (loading) {
    return (
      <div className="p-4 bg-gray-800/50 rounded-xl border border-gray-700 animate-pulse">
        <div className="h-4 bg-gray-700 rounded w-1/3 mb-3"></div>
        <div className="h-3 bg-gray-700 rounded w-1/2"></div>
      </div>
    );
  }

  const isHealthy = health?.status === 'ok';

  return (
    <div className="p-6 bg-gray-800/50 rounded-xl border border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">System Health</h3>
        <div className="flex items-center gap-2">
          <div
            className={`w-3 h-3 rounded-full ${isHealthy ? 'bg-green-500' : 'bg-red-500 animate-pulse'}`}
          />
          <span className={`text-sm ${isHealthy ? 'text-green-400' : 'text-red-400'}`}>
            {isHealthy ? 'Healthy' : 'Degraded'}
          </span>
        </div>
      </div>

      {health && (
        <div className="space-y-3">
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Version</span>
            <span className="text-gray-300 font-mono">{health.version}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">MongoDB</span>
            <span className={`font-mono ${health.mongodb === 'ok' ? 'text-green-400' : 'text-red-400'}`}>
              {health.mongodb}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Last Check</span>
            <span className="text-gray-300 font-mono text-xs">
              {new Date(health.timestamp).toLocaleTimeString()}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default SystemHealthPanel;
