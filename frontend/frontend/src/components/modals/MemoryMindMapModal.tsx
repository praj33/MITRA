// components/modals/MemoryMindMapModal.tsx — Interactive Canvas/SVG Node Graph for User Memory & Tasks
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Network, Brain, Calendar, CheckSquare, Sparkles, RefreshCw } from 'lucide-react';
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

  const generateGraph = async () => {
    setLoading(true);
    const newNodes: NodeItem[] = [
      {
        id: 'core',
        label: userName || 'User Core',
        category: 'core',
        x: 200,
        y: 180,
        detail: `Central node for ${userName || 'User'}'s Mitra AI companion context.`,
      },
    ];

    // Add memory facts
    const facts: any = memory || {};
    const keys = Object.keys(facts);
    keys.slice(0, 5).forEach((key, idx) => {
      const angle = (idx / Math.max(1, keys.length)) * 2 * Math.PI;
      const radius = 110;
      newNodes.push({
        id: `mem_${key}`,
        label: `🧠 ${key}: ${facts[key]}`,
        category: 'memory',
        x: 200 + Math.cos(angle) * radius,
        y: 180 + Math.sin(angle) * radius,
        detail: `Learned Fact: ${key} = ${facts[key]}`,
      });
    });

    try {
      const tasksRes = await CompanionService.getTasks(userId);
      const tasks = tasksRes.tasks || [];
      tasks.slice(0, 3).forEach((t: any, idx: number) => {
        newNodes.push({
          id: `task_${t.id}`,
          label: `⚡ ${t.title}`,
          category: 'task',
          x: 90 + idx * 110,
          y: 70,
          detail: `Task (${t.status}): ${t.title}`,
        });
      });
    } catch {}

    setNodes(newNodes);
    setLoading(false);
  };

  useEffect(() => {
    if (isOpen) {
      generateGraph();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const coreNode = nodes.find(n => n.category === 'core') || { x: 200, y: 180 };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md">
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

          {/* SVG Canvas Area */}
          <div className="relative flex-1 bg-surface-base p-4 min-h-[320px] flex items-center justify-center overflow-hidden">
            <svg className="w-full h-80">
              {/* Lines linking nodes to Core */}
              {nodes.map(
                n =>
                  n.category !== 'core' && (
                    <line
                      key={`line_${n.id}`}
                      x1={coreNode.x}
                      y1={coreNode.y}
                      x2={n.x}
                      y2={n.y}
                      stroke="var(--brand)"
                      strokeOpacity="0.3"
                      strokeWidth="2"
                      strokeDasharray="4 4"
                    />
                  )
              )}

              {/* Render Nodes */}
              {nodes.map(n => {
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
                          : '#10b981'
                      }
                      fillOpacity={isSelected ? 1 : 0.85}
                      stroke="#ffffff"
                      strokeWidth={isSelected ? 3 : 1}
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

          {/* Selected Node Details Drawer */}
          {selectedNode && (
            <div className="p-4 bg-surface-elevated border-t border-border-subtle flex items-center justify-between">
              <div>
                <span className="text-2xs font-semibold uppercase text-brand-light">Node Detail</span>
                <p className="text-xs text-text-primary font-medium">{selectedNode.detail}</p>
              </div>
              <button
                onClick={() => setSelectedNode(null)}
                className="text-2xs text-text-muted hover:text-text-primary underline"
              >
                Dismiss
              </button>
            </div>
          )}
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
