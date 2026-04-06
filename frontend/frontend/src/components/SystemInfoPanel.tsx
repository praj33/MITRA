import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { SystemInfo, SystemStats } from '../types';

interface SystemInfoPanelProps {
    className?: string;
}

const SystemInfoPanel: React.FC<SystemInfoPanelProps> = ({ className = '' }) => {
    const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
    const [systemStats, setSystemStats] = useState<SystemStats | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [autoRefresh, setAutoRefresh] = useState(false);

    const fetchData = async () => {
        setIsLoading(true);
        setError(null);

        try {
            const [info, stats] = await Promise.all([
                apiService.getSystemInfo(),
                apiService.getSystemStats(),
            ]);
            setSystemInfo(info);
            setSystemStats(stats);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch system information');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    useEffect(() => {
        let interval: NodeJS.Timeout | null = null;
        if (autoRefresh) {
            interval = setInterval(fetchData, 5000); // Refresh every 5 seconds
        }
        return () => {
            if (interval) clearInterval(interval);
        };
    }, [autoRefresh]);

    return (
        <div className={`${className}`}>
            {/* Header with Refresh Controls */}
            <div className="backdrop-blur-xl bg-white/60 dark:bg-iosGray-800/60 rounded-3xl p-6 shadow-ios-lg border border-white/20 dark:border-iosGray-700/30 mb-6">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-2xl font-semibold text-iosGray-900 dark:text-white font-sf">
                        System Information
                    </h2>
                    <div className="flex items-center space-x-3">
                        <label className="flex items-center space-x-2 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={autoRefresh}
                                onChange={(e) => setAutoRefresh(e.target.checked)}
                                className="w-4 h-4 text-iosBlue-500 rounded focus:ring-2 focus:ring-iosBlue-500"
                            />
                            <span className="text-sm text-iosGray-700 dark:text-iosGray-300 font-sf">Auto-refresh</span>
                        </label>
                        <button
                            onClick={fetchData}
                            disabled={isLoading}
                            className="px-4 py-2 bg-iosBlue-500 text-white rounded-xl font-medium font-sf hover:bg-iosBlue-600 active:bg-iosBlue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm"
                        >
                            {isLoading ? 'Refreshing...' : 'Refresh'}
                        </button>
                    </div>
                </div>
                {autoRefresh && (
                    <p className="text-xs text-iosGray-500 dark:text-iosGray-500 font-sf">
                        Auto-refreshing every 5 seconds
                    </p>
                )}
            </div>

            {/* Error Message */}
            {error && (
                <div className="backdrop-blur-xl bg-red-500/10 dark:bg-red-500/20 rounded-3xl p-4 mb-6 border border-red-500/30">
                    <p className="text-red-600 dark:text-red-400 font-sf">{error}</p>
                </div>
            )}

            {/* System Information */}
            {systemInfo && (
                <div className="backdrop-blur-xl bg-white/60 dark:bg-iosGray-800/60 rounded-3xl p-6 shadow-ios-lg border border-white/20 dark:border-iosGray-700/30 mb-6">
                    <h3 className="text-xl font-semibold text-iosGray-900 dark:text-white mb-4 font-sf">
                        System Details
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="p-4 bg-white/40 dark:bg-iosGray-900/40 rounded-2xl">
                            <p className="text-sm text-iosGray-600 dark:text-iosGray-400 font-sf mb-1">Platform</p>
                            <p className="text-base font-medium text-iosGray-900 dark:text-white font-sf">{systemInfo.platform}</p>
                        </div>
                        <div className="p-4 bg-white/40 dark:bg-iosGray-900/40 rounded-2xl">
                            <p className="text-sm text-iosGray-600 dark:text-iosGray-400 font-sf mb-1">Python Version</p>
                            <p className="text-base font-medium text-iosGray-900 dark:text-white font-sf">{systemInfo.python_version}</p>
                        </div>
                        <div className="p-4 bg-white/40 dark:bg-iosGray-900/40 rounded-2xl md:col-span-2">
                            <p className="text-sm text-iosGray-600 dark:text-iosGray-400 font-sf mb-1">Working Directory</p>
                            <p className="text-base font-medium text-iosGray-900 dark:text-white font-sf break-all">{systemInfo.working_directory}</p>
                        </div>
                        <div className="p-4 bg-white/40 dark:bg-iosGray-900/40 rounded-2xl">
                            <p className="text-sm text-iosGray-600 dark:text-iosGray-400 font-sf mb-1">Available Space</p>
                            <p className="text-base font-medium text-iosGray-900 dark:text-white font-sf">{systemInfo.available_space}</p>
                        </div>
                        <div className="p-4 bg-white/40 dark:bg-iosGray-900/40 rounded-2xl">
                            <p className="text-sm text-iosGray-600 dark:text-iosGray-400 font-sf mb-1">Memory Usage</p>
                            <p className="text-base font-medium text-iosGray-900 dark:text-white font-sf">
                                {typeof systemInfo.memory_usage === 'string'
                                    ? systemInfo.memory_usage
                                    : `${systemInfo.memory_usage.percent.toFixed(1)}% (${(systemInfo.memory_usage.used / 1024 / 1024 / 1024).toFixed(2)} GB / ${(systemInfo.memory_usage.total / 1024 / 1024 / 1024).toFixed(2)} GB)`
                                }
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {/* System Statistics */}
            {systemStats && (
                <div className="space-y-6">
                    {/* Memory Stats */}
                    <div className="backdrop-blur-xl bg-white/60 dark:bg-iosGray-800/60 rounded-3xl p-6 shadow-ios-lg border border-white/20 dark:border-iosGray-700/30">
                        <h3 className="text-xl font-semibold text-iosGray-900 dark:text-white mb-4 font-sf">
                            Memory Statistics
                        </h3>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="p-4 bg-white/40 dark:bg-iosGray-900/40 rounded-2xl text-center">
                                <p className="text-2xl font-bold text-iosBlue-500 font-sf">{systemStats.memory_stats.total_entries}</p>
                                <p className="text-sm text-iosGray-600 dark:text-iosGray-400 font-sf mt-1">Total Entries</p>
                            </div>
                            <div className="p-4 bg-white/40 dark:bg-iosGray-900/40 rounded-2xl text-center">
                                <p className="text-2xl font-bold text-iosBlue-500 font-sf">{systemStats.memory_stats.users}</p>
                                <p className="text-sm text-iosGray-600 dark:text-iosGray-400 font-sf mt-1">Users</p>
                            </div>
                        </div>
                    </div>

                    {/* Task Queue */}
                    <div className="backdrop-blur-xl bg-white/60 dark:bg-iosGray-800/60 rounded-3xl p-6 shadow-ios-lg border border-white/20 dark:border-iosGray-700/30">
                        <h3 className="text-xl font-semibold text-iosGray-900 dark:text-white mb-4 font-sf">
                            Task Queue Status
                        </h3>
                        <div className="grid grid-cols-3 gap-4">
                            <div className="p-4 bg-yellow-500/10 dark:bg-yellow-500/20 rounded-2xl text-center border border-yellow-500/30">
                                <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-500 font-sf">{systemStats.task_queue_status.pending}</p>
                                <p className="text-sm text-yellow-600 dark:text-yellow-500 font-sf mt-1">Pending</p>
                            </div>
                            <div className="p-4 bg-blue-500/10 dark:bg-blue-500/20 rounded-2xl text-center border border-blue-500/30">
                                <p className="text-2xl font-bold text-blue-600 dark:text-blue-500 font-sf">{systemStats.task_queue_status.running}</p>
                                <p className="text-sm text-blue-600 dark:text-blue-500 font-sf mt-1">Running</p>
                            </div>
                            <div className="p-4 bg-green-500/10 dark:bg-green-500/20 rounded-2xl text-center border border-green-500/30">
                                <p className="text-2xl font-bold text-green-600 dark:text-green-500 font-sf">{systemStats.task_queue_status.completed}</p>
                                <p className="text-sm text-green-600 dark:text-green-500 font-sf mt-1">Completed</p>
                            </div>
                        </div>
                    </div>

                    {/* Safety Stats */}
                    <div className="backdrop-blur-xl bg-white/60 dark:bg-iosGray-800/60 rounded-3xl p-6 shadow-ios-lg border border-white/20 dark:border-iosGray-700/30">
                        <h3 className="text-xl font-semibold text-iosGray-900 dark:text-white mb-4 font-sf">
                            Safety & Policy
                        </h3>
                        <div className="grid grid-cols-3 gap-4">
                            <div className="p-4 bg-white/40 dark:bg-iosGray-900/40 rounded-2xl text-center">
                                <p className="text-2xl font-bold text-iosBlue-500 font-sf">{systemStats.safety_stats.total_evaluations}</p>
                                <p className="text-sm text-iosGray-600 dark:text-iosGray-400 font-sf mt-1">Total Evaluations</p>
                            </div>
                            <div className="p-4 bg-white/40 dark:bg-iosGray-900/40 rounded-2xl text-center">
                                <p className="text-2xl font-bold text-red-500 font-sf">{systemStats.safety_stats.blocked_count}</p>
                                <p className="text-sm text-iosGray-600 dark:text-iosGray-400 font-sf mt-1">Blocked</p>
                            </div>
                            <div className="p-4 bg-white/40 dark:bg-iosGray-900/40 rounded-2xl text-center">
                                <p className="text-2xl font-bold text-orange-500 font-sf">{systemStats.policy_violations.total}</p>
                                <p className="text-sm text-iosGray-600 dark:text-iosGray-400 font-sf mt-1">Violations</p>
                            </div>
                        </div>
                    </div>

                    {/* Performance */}
                    <div className="backdrop-blur-xl bg-white/60 dark:bg-iosGray-800/60 rounded-3xl p-6 shadow-ios-lg border border-white/20 dark:border-iosGray-700/30">
                        <h3 className="text-xl font-semibold text-iosGray-900 dark:text-white mb-4 font-sf">
                            Performance
                        </h3>
                        <div className="p-4 bg-white/40 dark:bg-iosGray-900/40 rounded-2xl text-center">
                            <p className="text-3xl font-bold text-iosBlue-500 font-sf">{systemStats.performance_metrics}</p>
                            <p className="text-sm text-iosGray-600 dark:text-iosGray-400 font-sf mt-1">Total Interactions</p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default SystemInfoPanel;
