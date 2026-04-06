import React, { useState } from 'react';
import { apiService } from '../services/api';
import { ResearchRequest, ResearchResponse } from '../types';

interface ResearchPanelProps {
    className?: string;
}

const ResearchPanel: React.FC<ResearchPanelProps> = ({ className = '' }) => {
    const [query, setQuery] = useState('');
    const [maxResults, setMaxResults] = useState(5);
    const [results, setResults] = useState<ResearchResponse | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleResearch = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim()) return;

        setIsLoading(true);
        setError(null);

        try {
            const request: ResearchRequest = {
                query: query.trim(),
                max_results: maxResults,
            };
            const response = await apiService.research(request);
            setResults(response);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Research failed');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className={`${className}`}>
            {/* Research Form */}
            <form onSubmit={handleResearch} className="mb-6">
                <div className="backdrop-blur-xl bg-white/60 dark:bg-iosGray-800/60 rounded-3xl p-6 shadow-ios-lg border border-white/20 dark:border-iosGray-700/30">
                    <h2 className="text-2xl font-semibold text-iosGray-900 dark:text-white mb-4 font-sf">
                        Deep Research
                    </h2>

                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-iosGray-700 dark:text-iosGray-300 mb-2 font-sf">
                                Research Topic
                            </label>
                            <input
                                type="text"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                placeholder="Enter topic to research..."
                                className="w-full px-4 py-3 rounded-2xl bg-white dark:bg-iosGray-900 border border-iosGray-200 dark:border-iosGray-700 text-iosGray-900 dark:text-white placeholder-iosGray-400 focus:outline-none focus:ring-2 focus:ring-iosBlue-500 font-sf"
                                disabled={isLoading}
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-iosGray-700 dark:text-iosGray-300 mb-2 font-sf">
                                Research Depth: {maxResults}
                            </label>
                            <input
                                type="range"
                                min="1"
                                max="5"
                                value={maxResults}
                                onChange={(e) => setMaxResults(Number(e.target.value))}
                                className="w-full h-2 bg-iosGray-200 dark:bg-iosGray-700 rounded-lg appearance-none cursor-pointer accent-iosBlue-500"
                                disabled={isLoading}
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={isLoading || !query.trim()}
                            className="w-full px-6 py-3 bg-iosBlue-500 text-white rounded-2xl font-medium font-sf hover:bg-iosBlue-600 active:bg-iosBlue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-ios"
                        >
                            {isLoading ? 'Researching...' : 'Start Research'}
                        </button>
                    </div>
                </div>
            </form>

            {/* Error Message */}
            {error && (
                <div className="backdrop-blur-xl bg-red-500/10 dark:bg-red-500/20 rounded-3xl p-4 mb-6 border border-red-500/30">
                    <p className="text-red-600 dark:text-red-400 font-sf">{error}</p>
                </div>
            )}

            {/* Loading State */}
            {isLoading && (
                <div className="backdrop-blur-xl bg-white/60 dark:bg-iosGray-800/60 rounded-3xl p-6 shadow-ios-lg border border-white/20 dark:border-iosGray-700/30">
                    <div className="flex items-center justify-center space-x-3">
                        <div className="w-3 h-3 bg-iosBlue-500 rounded-full animate-bounce"></div>
                        <div className="w-3 h-3 bg-iosBlue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                        <div className="w-3 h-3 bg-iosBlue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                    <p className="text-center text-iosGray-600 dark:text-iosGray-400 mt-4 font-sf">
                        Conducting deep research...
                    </p>
                </div>
            )}

            {/* Results */}
            {results && !isLoading && (
                <div className="space-y-6">
                    {/* Summary */}
                    <div className="backdrop-blur-xl bg-white/60 dark:bg-iosGray-800/60 rounded-3xl p-6 shadow-ios-lg border border-white/20 dark:border-iosGray-700/30">
                        <h3 className="text-xl font-semibold text-iosGray-900 dark:text-white mb-3 font-sf">
                            Research Summary: {results.topic}
                        </h3>
                        <p className="text-iosGray-700 dark:text-iosGray-300 font-sf leading-relaxed">
                            {results.summary}
                        </p>
                    </div>

                    {/* Key Findings */}
                    {results.key_findings && results.key_findings.length > 0 && (
                        <div className="backdrop-blur-xl bg-white/60 dark:bg-iosGray-800/60 rounded-3xl p-6 shadow-ios-lg border border-white/20 dark:border-iosGray-700/30">
                            <h3 className="text-xl font-semibold text-iosGray-900 dark:text-white mb-4 font-sf">
                                Key Findings
                            </h3>
                            <ul className="space-y-2">
                                {results.key_findings.map((finding, index) => (
                                    <li key={index} className="flex items-start">
                                        <span className="inline-block w-2 h-2 bg-iosBlue-500 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                                        <span className="text-iosGray-700 dark:text-iosGray-300 font-sf">{finding}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {/* Sources */}
                    {results.sources && results.sources.length > 0 && (
                        <div className="backdrop-blur-xl bg-white/60 dark:bg-iosGray-800/60 rounded-3xl p-6 shadow-ios-lg border border-white/20 dark:border-iosGray-700/30">
                            <h3 className="text-xl font-semibold text-iosGray-900 dark:text-white mb-4 font-sf">
                                Sources
                            </h3>
                            <div className="space-y-3">
                                {results.sources.map((source, index) => (
                                    <div
                                        key={index}
                                        className="p-4 bg-white/40 dark:bg-iosGray-900/40 rounded-2xl border border-iosGray-200/50 dark:border-iosGray-700/50"
                                    >
                                        <a
                                            href={source.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="block group"
                                        >
                                            <h4 className="text-base font-medium text-iosBlue-500 group-hover:text-iosBlue-600 mb-1 font-sf">
                                                {source.title}
                                            </h4>
                                            <div className="flex items-center justify-between text-xs text-iosGray-500 dark:text-iosGray-500 font-sf">
                                                <span className="truncate">{source.url}</span>
                                                <span className="ml-2 px-2 py-1 bg-iosBlue-500/10 text-iosBlue-500 rounded-lg">
                                                    {(source.relevance * 100).toFixed(0)}%
                                                </span>
                                            </div>
                                        </a>
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

export default ResearchPanel;
