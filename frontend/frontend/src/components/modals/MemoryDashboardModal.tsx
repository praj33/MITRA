import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Brain, Search, Plus, Trash2, X, RefreshCw } from 'lucide-react';
import { CompanionService } from '../../services/companion.service';
import { useCompanionStore } from '../../store/companion.store';
import { showToast } from '../shell/Toast';

interface MemoryDashboardModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const MemoryDashboardModal: React.FC<MemoryDashboardModalProps> = ({ isOpen, onClose }) => {
  const userId = useCompanionStore(s => s.userId);
  const [facts, setFacts] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState('');
  const [newKey, setNewKey] = useState('');
  const [newValue, setNewValue] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);

  const fetchMemory = async () => {
    setLoading(true);
    try {
      const res = await CompanionService.getMemory(userId);
      setFacts(res.facts || {});
    } catch (err) {
      console.warn('Error fetching memory:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchMemory();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, userId]);

  const handleAddFact = async (e: React.FormEvent) => {
    e.preventDefault();
    const k = newKey.trim();
    const v = newValue.trim();
    if (!k || !v) return;

    try {
      await CompanionService.setMemoryFact(userId, k, v);
      showToast('success', `Memory saved: ${k}`);
      setNewKey('');
      setNewValue('');
      setShowAddForm(false);
      fetchMemory();
    } catch (err) {
      showToast('error', 'Failed to save memory fact');
    }
  };

  const handleDeleteFact = async (key: string) => {
    try {
      await CompanionService.deleteMemoryFact(userId, key);
      showToast('info', `Memory cleared: ${key}`);
      fetchMemory();
    } catch (err) {
      showToast('error', 'Failed to delete memory item');
    }
  };

  const filteredKeys = Object.keys(facts).filter(k =>
    k.toLowerCase().includes(query.toLowerCase()) ||
    String(facts[k]).toLowerCase().includes(query.toLowerCase())
  );

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm select-none" onClick={onClose}>
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          onClick={e => e.stopPropagation()}
          className="w-full max-w-lg rounded-2xl bg-surface-elevated border border-brand/30 shadow-2xl overflow-hidden flex flex-col max-h-[85vh]"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-border-subtle bg-surface-overlay/40">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-brand/15 border border-brand/30 flex items-center justify-center text-brand-light">
                <Brain size={18} />
              </div>
              <div>
                <h3 className="text-sm font-bold text-text-primary">Companion Memory Dashboard</h3>
                <p className="text-2xs text-text-muted">Facts & preferences stored by Mitra</p>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={fetchMemory}
                className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-overlay transition-colors"
                title="Refresh Memory"
              >
                <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
              </button>
              <button
                onClick={onClose}
                className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-overlay transition-colors"
              >
                <X size={16} />
              </button>
            </div>
          </div>

          {/* Search & Actions Bar */}
          <div className="p-3 border-b border-border-subtle flex items-center justify-between gap-2 bg-surface-overlay/20">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-surface-overlay border border-border-subtle flex-1">
              <Search size={14} className="text-text-muted flex-shrink-0" />
              <input
                type="text"
                value={query}
                onChange={e => setQuery(e.target.value)}
                placeholder="Search stored memory..."
                className="w-full bg-transparent text-xs text-text-primary placeholder:text-text-muted focus:outline-none"
              />
            </div>

            <button
              onClick={() => setShowAddForm(!showAddForm)}
              className="px-3 py-1.5 rounded-xl bg-brand text-white text-xs font-semibold hover:bg-brand-light flex items-center gap-1.5 shadow-sm transition-all active:scale-95 flex-shrink-0"
            >
              <Plus size={14} />
              <span>Teach Mitra</span>
            </button>
          </div>

          {/* Form to add a new memory fact */}
          <AnimatePresence>
            {showAddForm && (
              <motion.form
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                onSubmit={handleAddFact}
                className="p-3 border-b border-brand/20 bg-brand/5 flex flex-col gap-2"
              >
                <span className="text-2xs font-semibold text-brand-light uppercase tracking-wider">Add Custom Memory Fact</span>
                <div className="grid grid-cols-2 gap-2">
                  <input
                    type="text"
                    placeholder="Key (e.g. user_name)"
                    value={newKey}
                    onChange={e => setNewKey(e.target.value)}
                    className="px-2.5 py-1.5 text-xs rounded-lg bg-surface-overlay border border-border-subtle text-text-primary focus:outline-none focus:border-brand"
                    required
                  />
                  <input
                    type="text"
                    placeholder="Value (e.g. Ashmit)"
                    value={newValue}
                    onChange={e => setNewValue(e.target.value)}
                    className="px-2.5 py-1.5 text-xs rounded-lg bg-surface-overlay border border-border-subtle text-text-primary focus:outline-none focus:border-brand"
                    required
                  />
                </div>
                <div className="flex justify-end gap-2 pt-1">
                  <button
                    type="button"
                    onClick={() => setShowAddForm(false)}
                    className="px-2.5 py-1 rounded-lg text-2xs font-medium text-text-muted hover:text-text-primary"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-3 py-1 rounded-lg bg-brand text-white text-2xs font-semibold hover:bg-brand-light"
                  >
                    Save Memory
                  </button>
                </div>
              </motion.form>
            )}
          </AnimatePresence>

          {/* Memory List */}
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {loading ? (
              <div className="py-8 text-center text-xs text-text-muted">Loading memory...</div>
            ) : filteredKeys.length === 0 ? (
              <div className="py-8 text-center text-xs text-text-muted">
                {query ? `No memory facts matching "${query}"` : 'No stored facts yet. Mitra learns preferences automatically during chat!'}
              </div>
            ) : (
              filteredKeys.map(k => (
                <div
                  key={k}
                  className="flex items-center justify-between p-2.5 rounded-xl bg-surface-overlay/60 border border-border-subtle hover:border-brand/30 transition-all group"
                >
                  <div className="min-w-0 pr-2">
                    <span className="text-2xs font-mono font-bold text-brand-light uppercase tracking-wider block truncate">{k}</span>
                    <span className="text-xs text-text-primary font-medium block truncate leading-snug">{String(facts[k])}</span>
                  </div>

                  <button
                    onClick={() => handleDeleteFact(k)}
                    className="p-1.5 rounded-lg text-text-muted hover:text-red-400 hover:bg-red-500/10 transition-colors flex-shrink-0"
                    title={`Delete '${k}' from memory`}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          <div className="p-3 border-t border-border-subtle bg-surface-overlay/40 text-2xs text-text-muted flex items-center justify-between">
            <span>{Object.keys(facts).length} items remembered</span>
            <span>Privacy Controlled</span>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
