// components/pages/KnowledgePage.tsx — UniGuru knowledge search
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BookOpen, Search, Sparkles, Loader2 } from 'lucide-react';
import { CompanionService } from '../../services/companion.service';
import { useCompanionStore } from '../../store/companion.store';
import FormattedMarkdown from '../primitives/FormattedMarkdown';

const quickTopics = [
  { label: '🧠 How does AI work?', q: 'Explain how artificial intelligence works' },
  { label: '🔐 Cybersecurity basics', q: 'What are the fundamentals of cybersecurity' },
  { label: '📊 Data structures', q: 'Explain common data structures' },
  { label: '☁️ Cloud computing', q: 'What is cloud computing and its types' },
  { label: '🤖 Machine learning', q: 'Explain machine learning concepts' },
  { label: '🌐 How the internet works', q: 'Explain how the internet works' },
];

interface KnowledgeResult {
  query: string;
  answer: string;
  timestamp: string;
}

const KnowledgePage: React.FC<{ onChatNavigate: (msg: string) => void }> = ({ onChatNavigate }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<KnowledgeResult[]>([]);
  const [searching, setSearching] = useState(false);

  const doSearch = async (q: string) => {
    if (!q.trim()) return;
    setSearching(true);
    try {
      const userId = useCompanionStore.getState().userId;
      const resp = await CompanionService.chat(userId, `explain: ${q}`);
      setResults(prev => [{
        query: q, answer: resp.message, timestamp: new Date().toISOString(),
      }, ...prev]);
    } catch {
      setResults(prev => [{
        query: q, answer: 'Unable to fetch knowledge at this time. Please check your LLM API key configuration.',
        timestamp: new Date().toISOString(),
      }, ...prev]);
    }
    setSearching(false);
    setQuery('');
  };

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="page-container">
      <div className="page-header">
        <div className="flex items-center gap-3">
          <div className="page-icon" style={{ background: 'rgba(168,85,247,0.15)', color: '#a855f7' }}><BookOpen size={20} /></div>
          <div>
            <h1 className="page-title">Knowledge</h1>
            <p className="page-subtitle">Powered by UniGuru — ask anything</p>
          </div>
        </div>
      </div>

      {/* Search bar */}
      <div className="knowledge-search-bar">
        <Search size={16} className="text-text-muted flex-shrink-0" />
        <input
          type="text" value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && doSearch(query)}
          placeholder="Ask a question..."
          className="knowledge-search-input min-w-0"
        />
        <button onClick={() => doSearch(query)} disabled={!query.trim() || searching}
          className="page-btn-primary flex-shrink-0">
          {searching ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />} Search
        </button>
      </div>

      {/* Quick topics */}
      {results.length === 0 && (
        <div className="page-section">
          <h3 className="page-section-title">Quick Topics</h3>
          <div className="knowledge-topics-grid">
            {quickTopics.map(topic => (
              <button key={topic.q} onClick={() => doSearch(topic.q)} className="knowledge-topic-card">
                <span>{topic.label}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Results */}
      <AnimatePresence>
        {results.map((r, i) => (
          <motion.div key={r.timestamp + i} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
            className="knowledge-result-card">
            <div className="knowledge-result-query">
              <Search size={12} /> {r.query}
            </div>
            <div className="knowledge-result-answer">
              <FormattedMarkdown content={r.answer} />
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </motion.div>
  );
};

export default KnowledgePage;
