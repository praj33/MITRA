import React, { useState } from 'react';
import { apiService } from '../services/api';
import { SearchRequest, SearchResponse } from '../types';

interface SearchPanelProps {
    className?: string;
}

const SearchPanel: React.FC<SearchPanelProps> = ({ className = '' }) => {
    const [query, setQuery] = useState('');
    const [maxResults, setMaxResults] = useState(5);
    const [results, setResults] = useState<SearchResponse | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim()) return;

        setIsLoading(true);
        setError(null);

        try {
            const request: SearchRequest = {
                query: query.trim(),
                max_results: maxResults,
            };
            const response = await apiService.search(request);
            setResults(response);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Search failed');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className={`${className}`}>
            {/* Search Form */}
            <form onSubmit={handleSearch} className="mb-6">
                <div className="backdrop-blur-xl bg-white/60 dark:bg-iosGray-800/60 rounded-3xl p-6 shadow-ios-lg border border-white/20 dark:border-iosGray-700/30">
                    <h2 className="text-2xl font-semibold text-iosGray-900 dark:text-white mb-4 font-sf">
                        Web Search
                    </h2>

                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-iosGray-700 dark:text-iosGray-300 mb-2 font-sf">
                                Search Query
                            </label>
                            <input
                                type="text"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                placeholder="Enter your search query..."
                                className="w-full px-4 py-3 rounded-2xl bg-white dark:bg-iosGray-900 border border-iosGray-200 dark:border-iosGray-700 text-iosGray-900 dark:text-white placeholder-iosGray-400 focus:outline-none focus:ring-2 focus:ring-iosBlue-500 font-sf"
                                disabled={isLoading}
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-iosGray-700 dark:text-iosGray-300 mb-2 font-sf">
                                Max Results: {maxResults}
                            </label>
                            <input
                                type="range"
                                min="1"
                                max="20"
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
                            {isLoading ? 'Searching...' : 'Search'}
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

            {/* Results */}
            {results && (
                <div className="backdrop-blur-xl bg-white/60 dark:bg-iosGray-800/60 rounded-3xl p-6 shadow-ios-lg border border-white/20 dark:border-iosGray-700/30">
                    <h3 className="text-xl font-semibold text-iosGray-900 dark:text-white mb-4 font-sf">
                        Search Results for "{results.query}"
                    </h3>

                    {results.results.length === 0 ? (
                        <p className="text-iosGray-600 dark:text-iosGray-400 font-sf">No results found.</p>
                    ) : (
                        <div className="space-y-4">
                            {results.results.map((result, index) => (
                                <div
                                    key={index}
                                    className="p-4 bg-white/40 dark:bg-iosGray-900/40 rounded-2xl border border-iosGray-200/50 dark:border-iosGray-700/50"
                                >
                                    <a
                                        href={result.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="block group"
                                    >
                                        <h4 className="text-lg font-medium text-iosBlue-500 group-hover:text-iosBlue-600 mb-2 font-sf">
                                            {result.title}
                                        </h4>
                                        <p className="text-sm text-iosGray-600 dark:text-iosGray-400 mb-2 font-sf">
                                            {result.snippet}
                                        </p>
                                        <div className="flex items-center justify-between text-xs text-iosGray-500 dark:text-iosGray-500 font-sf">
                                            <span className="truncate">{result.url}</span>
                                            <span className="ml-2 px-2 py-1 bg-iosBlue-500/10 text-iosBlue-500 rounded-lg">
                                                {(result.relevance * 100).toFixed(0)}% relevant
                                            </span>
                                        </div>
                                    </a>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default SearchPanel;
