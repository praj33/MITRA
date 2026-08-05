// components/modals/MemoryMindMapModal.tsx — Interactive Canvas/SVG Node Graph for User Memory & Tasks
import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Network, RefreshCw, MessageSquare, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';
import { useCompanionStore } from '../../store/companion.store';
import { CompanionService } from '../../services/companion.service';

interface NodeItem {
  id: string;
  label: string;
  category: 'core' | 'memory' | 'task' | 'event';
  x: number;
  y: number;
  detail: string;
}

export const MemoryMindMapModal: React.FC<{ isOpen: boolean; onClose: () => void }> = ({ isOpen, onClose }) => {
  const { userId, userName, memory } = useCompanionStore();
  const [nodes, setNodes] = useState<NodeItem[]>([]);
  const [selectedNode, setSelectedNode] = useState<NodeItem | null>(null);
  const [loading, setLoading] = useState(false);
  const [filterCategory, setFilterCategory] = useState<'all' | 'memory' | 'task' | 'event'>('all');
  const [zoomScale, setZoomScale] = useState(1);

  const generateGraph = useCallback(async () => {
    setLoading(true);
    const newNodes: NodeItem[] = [
      {
        id: 'core',
        label: userName || 'User Core',
        category: 'core',
        x: 220,
        y: 180,
        detail: `Central node for ${userName || 'User'}'s Mitra AI companion context.`,
      },
    ];

    // Add memory facts
    const facts: any = memory || {};
    const keys = Object.keys(facts);
    keys.slice(0, 6).forEach((key, idx) => {
      const angle = (idx / Math.max(1, keys.length)) * 2 * Math.PI;
      const radius = 120;
      newNodes.push({
        id: `mem_${key}`,
        label: `🧠 ${key}: ${facts[key]}`,
        category: 'memory',
        x: 220 + Math.cos(angle) * radius,
        y: 180 + Math.sin(angle) * radius,
        detail: `Learned Fact: ${key} = ${facts[key]}`,
      });
    });

    try {
      const tasksRes = await CompanionService.getTasks(userId);
      const tasks = tasksRes.tasks || [];
      tasks.slice(0, 4).forEach((t: any, idx: number) => {
        newNodes.push({
          id: `task_${t.id}`,
          label: `⚡ ${t.title}`,
          category: 'task',
          x: 70 + idx * 100,
          y: 60,
          detail: `Task (${t.status}): ${t.title}`,
        });
      });

      const calRes = await CompanionService.getCalendarEvents(userId);
      const events = calRes.events || [];
      events.slice(0, 3).forEach((e: any, idx: number) => {
        newNodes.push({
          id: `cal_${e.id}`,
          label: `📅 ${e.title}`,
          category: 'event',
          x: 90 + idx * 120,
          y: 300,
          detail: `Calendar Event: ${e.title} (${e.start_time || 'Today'})`,
        });
      });
    } catch {}

    setNodes(newNodes);
    setLoading(false);
  }, [memory, userId, userName]);

  useEffect(() => {
    if (isOpen) {
      generateGraph();
      setZoomScale(1);
    }
  }, [isOpen, generateGraph]);

  if (!isOpen) return null;

  const coreNode = nodes.find(n => n.category === 'core') || { x: 220, y: 180 };

  const filteredNodes = nodes.filter(n => filterCategory === 'all' || n.category === 'core' || n.category === filterCategory);

  const handleAskMitra = (node: NodeItem) => {
    onClose();
    const sendFn = (window as any).__MITRA_SEND__;
    const navFn = (window as any).__MITRA_NAV__;
    if (navFn) navFn('chat');
    if (sendFn) sendFn(`Tell me more about ${node.label} and help me optimize it.`);
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md select-none">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="bg-surface-raised border border-border-default rounded-2xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden shadow-2xl"
        >
          {/* Header */}
          <div className="flex items-center justify-between px-5 py-4 border-b border-border-subtle">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-brand-muted border border-brand/30 flex items-center justify-center">
                <Network size={16} className="text-brand-light" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-text-primary">Brain Mind Map Visualizer</h3>
                <p className="text-2xs text-text-muted">Interactive memory & task graph</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={generateGraph}
                className="w-8 h-8 rounded-lg hover:bg-surface-overlay flex items-center justify-center text-text-muted transition-colors"
                title="Refresh Graph"
              >
                <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
              </button>
              <button
                onClick={onClose}
                className="w-8 h-8 rounded-lg hover:bg-surface-overlay flex items-center justify-center text-text-muted transition-colors"
              >
                <X size={16} />
              </button>
            </div>
          </div>

          {/* Filter Bar & Zoom Controls */}
          <div className="px-4 py-2 bg-surface-elevated border-b border-border-subtle flex items-center justify-between gap-2 overflow-x-auto">
            <div className="flex items-center gap-1.5">
              {(['all', 'memory', 'task', 'event'] as const).map(cat => (
                <button
                  key={cat}
                  onClick={() => setFilterCategory(cat)}
                  className={`px-2.5 py-1 rounded-full text-2xs font-semibold capitalize transition-all ${
                    filterCategory === cat
                      ? 'bg-brand text-white'
                      : 'bg-surface-overlay text-text-muted hover:text-text-primary'
                  }`}
                >
                  {cat === 'all' ? '🌐 All' : cat === 'memory' ? '🧠 Memory' : cat === 'task' ? '⚡ Tasks' : '📅 Events'}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={() => setZoomScale(prev => Math.min(1.5, prev + 0.15))}
                className="p-1 rounded bg-surface-overlay text-text-muted hover:text-text-primary"
                title="Zoom In"
              >
                <ZoomIn size={14} />
              </button>
              <button
                onClick={() => setZoomScale(prev => Math.max(0.7, prev - 0.15))}
                className="p-1 rounded bg-surface-overlay text-text-muted hover:text-text-primary"
                title="Zoom Out"
              >
                <ZoomOut size={14} />
              </button>
              <button
                onClick={() => setZoomScale(1)}
                className="p-1 rounded bg-surface-overlay text-text-muted hover:text-text-primary"
                title="Reset Zoom"
              >
                <RotateCcw size={13} />
              </button>
            </div>
          </div>

          {/* SVG Canvas Area */}
          <div className="relative flex-1 bg-surface-base p-4 min-h-[340px] flex items-center justify-center overflow-hidden">
            <svg className="w-full h-88 transition-transform duration-300" style={{ transform: `scale(${zoomScale})` }}>
              {/* Lines linking nodes to Core */}
              {filteredNodes.map(
                n =>
                  n.category !== 'core' && (
                    <line
                      key={`line_${n.id}`}
                      x1={coreNode.x}
                      y1={coreNode.y}
                      x2={n.x}
                      y2={n.y}
                      stroke={
                        n.category === 'memory' ? '#7c6ff7' : n.category === 'task' ? '#10b981' : '#f59e0b'
                      }
                      strokeOpacity="0.4"
                      strokeWidth="2"
                      strokeDasharray="4 4"
                    />
                  )
              )}

              {/* Render Nodes */}
              {filteredNodes.map(n => {
                const isSelected = selectedNode?.id === n.id;
                const isCore = n.category === 'core';

                return (
                  <g
                    key={n.id}
                    onClick={() => setSelectedNode(n)}
                    className="cursor-pointer transition-all duration-200 hover:scale-110"
                  >
                    <circle
                      cx={n.x}
                      cy={n.y}
                      r={isCore ? 28 : 18}
                      fill={
                        isCore
                          ? 'var(--brand)'
                          : n.category === 'memory'
                          ? '#7c6ff7'
                          : n.category === 'task'
                          ? '#10b981'
                          : '#f59e0b'
                      }
                      fillOpacity={isSelected ? 1 : 0.85}
                      stroke="#ffffff"
                      strokeWidth={isSelected ? 3 : 1.5}
                    />
                    <text
                      x={n.x}
                      y={n.y + (isCore ? 42 : 32)}
                      textAnchor="middle"
                      fill="var(--text-primary)"
                      fontSize="10"
                      fontWeight={isCore ? 'bold' : 'normal'}
                      className="select-none pointer-events-none"
                    >
                      {n.label.length > 18 ? n.label.substring(0, 16) + '...' : n.label}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>

          {/* Selected Node Details Drawer with Chat Action */}
          {selectedNode && (
            <div className="p-4 bg-surface-elevated border-t border-border-subtle flex items-center justify-between gap-3">
              <div className="min-w-0 flex-1">
                <span className="text-2xs font-semibold uppercase text-brand-light">Node Detail</span>
                <p className="text-xs text-text-primary font-medium truncate">{selectedNode.detail}</p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleAskMitra(selectedNode)}
                  className="page-btn-primary text-xs py-1.5 flex items-center gap-1.5"
                >
                  <MessageSquare size={12} /> Ask Mitra
                </button>
                <button
                  onClick={() => setSelectedNode(null)}
                  className="text-2xs text-text-muted hover:text-text-primary underline px-1"
                >
                  Dismiss
                </button>
              </div>
            </div>
          )}
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
