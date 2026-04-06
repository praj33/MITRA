import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { PerformanceInsights } from '../types';

interface PerformancePanelProps {
    className?: string;
}

const PerformancePanel: React.FC<PerformancePanelProps> = ({ className = '' }) => {
    const [insights, setInsights] = useState<PerformanceInsights | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchInsights = async () => {
        setIsLoading(true);
        setError(null);

        try {
            const data = await apiService.getPerformanceInsights();
            setInsights(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch performance insights');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchInsights();
    }, []);

    const successRate = insights
        ? ((insights.performance_metrics.successful_interactions / insights.performance_metrics.total_interactions) * 100).toFixed(1)
        : '0';

    return (
        <div className={`${className}`}>
            {/* Header */}
            <div className="backdrop-blur-xl bg-white/60 dark:bg-iosGray-800/60 rounded-3xl p-6 shadow-ios-lg border border-white/20 dark:border-iosGray-700/30 mb-6">
                <div className="flex items-center justify-between">
                    <h2 className="text-2xl font-semibold text-iosGray-900 dark:text-white font-sf">
                        Performance Insights
                    </h2>
                    <button
                        onClick={fetchInsights}
                        disabled={isLoading}
                        className="px-4 py-2 bg-iosBlue-500 text-white rounded-xl font-medium font-sf hover:bg-iosBlue-600 active:bg-iosBlue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm"
                    >
                        {isLoading ? 'Loading...' : 'Refresh'}
                    </button>
                </div>
            </div>

            {/* Error Message */}
            {error && (
                <div className="backdrop-blur-xl bg-red-500/10 dark:bg-red-500/20 rounded-3xl p-4 mb-6 border border-red-500/30">
                    <p className="text-red-600 dark:text-red-400 font-sf">{error}</p>
                </div>
            )}

            {/* Loading State */}
            {isLoading && !insights && (
                <div className="backdrop-blur-xl bg-white/60 dark:bg-iosGray-800/60 rounded-3xl p-12 shadow-ios-lg border border-white/20 dark:border-iosGray-700/30 text-center">
                    <div className="flex items-center justify-center space-x-3 mb-4">
                        <div className="w-3 h-3 bg-iosBlue-500 rounded-full animate-bounce"></div>
                        <div className="w-3 h-3 bg-iosBlue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                        <div className="w-3 h-3 bg-iosBlue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                    <p className="text-iosGray-600 dark:text-iosGray-400 font-sf">Loading performance insights...</p>
                </div>
            )}

            {/* Performance Metrics */}
            {insights && (
                <div className="space-y-6">
                    {/* Key Metrics */}
                    <div className="backdrop-blur-xl bg-white/60 dark:bg-iosGray-800/60 rounded-3xl p-6 shadow-ios-lg border border-white/20 dark:border-iosGray-700/30">
                        <h3 className="text-xl font-semibold text-iosGray-900 dark:text-white mb-4 font-sf">
                            Key Metrics
                        </h3>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div className="p-4 bg-gradient-to-br from-blue-500/10 to-blue-600/10 dark:from-blue-500/20 dark:to-blue-600/20 rounded-2xl border border-blue-500/30">
                                <p className="text-3xl font-bold text-blue-600 dark:text-blue-500 font-sf">
                                    {insights.performance_metrics.total_interactions}
                                </p>
                                <p className="text-sm text-blue-600 dark:text-blue-500 font-sf mt-1">Total Interactions</p>
                            </div>
                            <div className="p-4 bg-gradient-to-br from-green-500/10 to-green-600/10 dark:from-green-500/20 dark:to-green-600/20 rounded-2xl border border-green-500/30">
                                <p className="text-3xl font-bold text-green-600 dark:text-green-500 font-sf">
                                    {insights.performance_metrics.successful_interactions}
                                </p>
                                <p className="text-sm text-green-600 dark:text-green-500 font-sf mt-1">Successful</p>
                            </div>
                            <div className="p-4 bg-gradient-to-br from-purple-500/10 to-purple-600/10 dark:from-purple-500/20 dark:to-purple-600/20 rounded-2xl border border-purple-500/30">
                                <p className="text-3xl font-bold text-purple-600 dark:text-purple-500 font-sf">
                                    {successRate}%
                                </p>
                                <p className="text-sm text-purple-600 dark:text-purple-500 font-sf mt-1">Success Rate</p>
                            </div>
                            <div className="p-4 bg-gradient-to-br from-orange-500/10 to-orange-600/10 dark:from-orange-500/20 dark:to-orange-600/20 rounded-2xl border border-orange-500/30">
                                <p className="text-3xl font-bold text-orange-600 dark:text-orange-500 font-sf">
                                    {insights.performance_metrics.average_response_time.toFixed(2)}s
                                </p>
                                <p className="text-sm text-orange-600 dark:text-orange-500 font-sf mt-1">Avg Response Time</p>
                            </div>
                        </div>

                        <div className="mt-4 p-4 bg-white/40 dark:bg-iosGray-900/40 rounded-2xl">
                            <div className="flex items-center justify-between">
                                <p className="text-sm text-iosGray-600 dark:text-iosGray-400 font-sf">Average Satisfaction</p>
                                <p className="text-lg font-semibold text-iosGray-900 dark:text-white font-sf">
                                    {(insights.performance_metrics.average_satisfaction * 100).toFixed(1)}%
                                </p>
                            </div>
                            <div className="mt-2 w-full bg-iosGray-200 dark:bg-iosGray-700 rounded-full h-2">
                                <div
                                    className="bg-gradient-to-r from-iosBlue-500 to-green-500 h-2 rounded-full transition-all"
                                    style={{ width: `${insights.performance_metrics.average_satisfaction * 100}%` }}
                                ></div>
                            </div>
                        </div>
                    </div>

                    {/* Improvement Areas */}
                    {insights.performance_metrics.improvement_areas.length > 0 && (
                        <div className="backdrop-blur-xl bg-white/60 dark:bg-iosGray-800/60 rounded-3xl p-6 shadow-ios-lg border border-white/20 dark:border-iosGray-700/30">
                            <h3 className="text-xl font-semibold text-iosGray-900 dark:text-white mb-4 font-sf">
                                Improvement Areas
                            </h3>
                            <div className="space-y-2">
                                {insights.performance_metrics.improvement_areas.map((area, index) => (
                                    <div key={index} className="p-3 bg-yellow-500/10 dark:bg-yellow-500/20 rounded-xl border border-yellow-500/30">
                                        <p className="text-yellow-700 dark:text-yellow-400 font-sf">{area}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Patterns */}
                    {insights.patterns && insights.patterns.length > 0 && (
                        <div className="backdrop-blur-xl bg-white/60 dark:bg-iosGray-800/60 rounded-3xl p-6 shadow-ios-lg border border-white/20 dark:border-iosGray-700/30">
                            <h3 className="text-xl font-semibold text-iosGray-900 dark:text-white mb-4 font-sf">
                                Identified Patterns
                            </h3>
                            <div className="space-y-3">
                                {insights.patterns.map((pattern, index) => (
                                    <div key={index} className="p-4 bg-white/40 dark:bg-iosGray-900/40 rounded-2xl border border-iosGray-200/50 dark:border-iosGray-700/50">
                                        <div className="flex items-start justify-between mb-2">
                                            <h4 className="text-base font-medium text-iosGray-900 dark:text-white font-sf">
                                                {pattern.pattern_type}
                                            </h4>
                                            <span className="px-3 py-1 bg-iosBlue-500/10 text-iosBlue-500 rounded-lg text-sm font-sf">
                                                x{pattern.frequency}
                                            </span>
                                        </div>
                                        <p className="text-sm text-iosGray-600 dark:text-iosGray-400 font-sf">
                                            {pattern.description}
                                        </p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Recommendations */}
                    {insights.recommendations && insights.recommendations.length > 0 && (
                        <div className="backdrop-blur-xl bg-white/60 dark:bg-iosGray-800/60 rounded-3xl p-6 shadow-ios-lg border border-white/20 dark:border-iosGray-700/30">
                            <h3 className="text-xl font-semibold text-iosGray-900 dark:text-white mb-4 font-sf">
                                Recommendations
                            </h3>
                            <div className="space-y-3">
                                {insights.recommendations.map((recommendation, index) => (
                                    <div key={index} className="flex items-start p-4 bg-green-500/10 dark:bg-green-500/20 rounded-2xl border border-green-500/30">
                                        <svg className="w-5 h-5 text-green-600 dark:text-green-500 mt-0.5 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                        </svg>
                                        <p className="text-green-700 dark:text-green-400 font-sf">{recommendation}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default PerformancePanel;
