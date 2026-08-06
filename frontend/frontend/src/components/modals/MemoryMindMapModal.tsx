// components/modals/MemoryMindMapModal.tsx — Interactive Brain Mind Map Visualizer with Dynamic Orbit Engine
import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Network, RefreshCw, MessageSquare, ZoomIn, ZoomOut, RotateCcw, Sparkles, Calendar, CheckSquare, Brain } from 'lucide-react';
import { useCompanionStore } from '../../store/companion.store';
import { CompanionService } from '../../services/companion.service';

interface NodeItem {
  id: string;
  label: string;
  category: 'core' | 'memory' | 'task' | 'event';
  x: number;
  y: number;
  detail: string;
  badge?: string;
}

export const MemoryMindMapModal: React.FC<{ isOpen: boolean; onClose: () => void }> = ({ isOpen, onClose }) => {
  const { userId, userName, memory } = useCompanionStore();
  const [nodes, setNodes] = useState<NodeItem[]>([]);
  const [selectedNode, setSelectedNode] = useState<NodeItem | null>(null);
  const [loading, setLoading] = useState(false);
  const [filterCategory, setFilterCategory] = useState<'all' | 'memory' | 'task' | 'event'>('all');
  const [zoomScale, setZoomScale] = useState(1);

  const centerX = 300;
  const centerY = 190;

  const generateGraph = useCallback(async () => {
    setLoading(true);
    const newNodes: NodeItem[] = [
      {
        id: 'core',
        label: userName || 'User Core',
        category: 'core',
        x: centerX,
        y: centerY,
        detail: `Central node for ${userName || 'User'}'s Mitra AI companion context.`,
        badge: 'Neural Hub',
      },
    ];

    // Orbit 1: Memory Facts (Radius 100)
    const facts: any = memory || {};
    const factKeys = Object.keys(facts);
    const memList = factKeys.length > 0 ? factKeys : ['User Preferences', 'Active Assistant Context', 'Mitra Intelligence'];
    
    memList.slice(0, 5).forEach((key, idx) => {
      const angle = (idx / Math.max(1, memList.length)) * 2 * Math.PI - Math.PI / 2;
      const radius = 105;
      const val = facts[key] || 'Active Memory Node';
      newNodes.push({
        id: `mem_${key}`,
        label: `🧠 ${key}`,
        category: 'memory',
        x: centerX + Math.cos(angle) * radius,
        y: centerY + Math.sin(angle) * radius,
        detail: `Learned Fact: ${key} = ${val}`,
        badge: 'Memory',
      });
    });

    // Fetch Tasks & Events from Companion Service
    try {
      const tasksRes = await CompanionService.getTasks(userId);
      const tasks = (tasksRes && tasksRes.tasks && tasksRes.tasks.length > 0)
        ? tasksRes.tasks
        : [
            { id: 't1', title: 'Complete Mitra Phase 2', status: 'in_progress' },
            { id: 't2', title: 'Daily Briefing & Tasks', status: 'pending' },
          ];

      // Orbit 2: Tasks (Radius 155)
      tasks.slice(0, 4).forEach((t: any, idx: number) => {
        const angle = (idx / Math.max(1, tasks.slice(0, 4).length)) * 2 * Math.PI + Math.PI / 4;
        const radius = 155;
        newNodes.push({
          id: `task_${t.id}`,
          label: `⚡ ${t.title}`,
          category: 'task',
          x: centerX + Math.cos(angle) * radius,
          y: centerY + Math.sin(angle) * radius,
          detail: `Task (${t.status || 'active'}): ${t.title}`,
          badge: 'Task',
        });
      });

      const calRes = await CompanionService.getCalendarEvents(userId);
      const events = (calRes && calRes.events && calRes.events.length > 0)
        ? calRes.events
        : [
            { id: 'e1', title: 'Mitra Integration Review', start_time: 'Today' },
            { id: 'e2', title: 'Weekly Sync', start_time: 'Tomorrow' },
          ];

      // Orbit 3: Events (Radius 195)
      events.slice(0, 3).forEach((e: any, idx: number) => {
        const angle = (idx / Math.max(1, events.slice(0, 3).length)) * 2 * Math.PI - Math.PI / 3;
        const radius = 195;
        newNodes.push({
          id: `cal_${e.id}`,
          label: `📅 ${e.title}`,
          category: 'event',
          x: centerX + Math.cos(angle) * radius,
          y: centerY + Math.sin(angle) * radius,
          detail: `Calendar Event: ${e.title} (${e.start_time || 'Scheduled'})`,
          badge: 'Event',
        });
      });
    } catch (err) {
      console.warn('Failed to fetch tasks/events for MindMap:', err);
    }

    setNodes(newNodes);
    setLoading(false);
  }, [memory, userId, userName]);

  useEffect(() => {
    if (isOpen) {
      generateGraph();
      setZoomScale(1);
      setSelectedNode(null);
    }
  }, [isOpen, generateGraph]);

  if (!isOpen) return null;

  const coreNode = nodes.find(n => n.category === 'core') || { x: centerX, y: centerY, label: 'User Core', id: 'core' };
  const filteredNodes = nodes.filter(n => filterCategory === 'all' || n.category === 'core' || n.category === filterCategory);

  const handleAskMitra = (node: NodeItem) => {
    onClose();
    const sendFn = (window as any).__MITRA_SEND__;
    const navFn = (window as any).__MITRA_NAV__;
    if (navFn) navFn('chat');
    if (sendFn) sendFn(`Tell me more about "${node.detail}" and help me optimize it.`);
  };

  const handleJumpToSection = (node: NodeItem) => {
    onClose();
    const navFn = (window as any).__MITRA_NAV__;
    if (navFn) {
      if (node.category === 'task') navFn('tasks');
      else if (node.category === 'event') navFn('calendar');
      else navFn('chat');
    }
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/80 backdrop-blur-md select-none overflow-hidden">
        <motion.div
          initial={{ opacity: 0, scale: 0.94, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.94, y: 10 }}
          className="bg-surface-raised border border-border-default rounded-2xl w-full max-w-2xl max-h-[92vh] flex flex-col overflow-hidden shadow-2xl"
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 sm:px-5 sm:py-3.5 border-b border-border-subtle bg-surface-elevated">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-brand/20 border border-brand/40 flex items-center justify-center text-brand-light shadow-sm">
                <Network size={18} />
              </div>
              <div>
                <h3 className="text-xs sm:text-sm font-bold text-text-primary flex items-center gap-1.5">
                  Brain Mind Map Visualizer <Sparkles size={14} className="text-brand-light animate-pulse" />
                </h3>
                <p className="text-2xs text-text-muted">Interactive neural graph of your memories, tasks & events</p>
              </div>
            </div>

            <div className="flex items-center gap-1.5">
              <button
                onClick={generateGraph}
                className="p-1.5 rounded-lg hover:bg-surface-overlay text-text-muted hover:text-text-primary transition-colors cursor-pointer"
                title="Refresh Graph Nodes"
              >
                <RefreshCw size={14} className={loading ? 'animate-spin text-brand-light' : ''} />
              </button>
              <button
                onClick={onClose}
                className="p-1.5 rounded-lg hover:bg-surface-overlay text-text-muted hover:text-text-primary transition-colors cursor-pointer"
              >
                <X size={16} />
              </button>
            </div>
          </div>

          {/* Filter Bar & Zoom Controls */}
          <div className="px-4 py-2 bg-surface-elevated/70 border-b border-border-subtle flex items-center justify-between gap-2 overflow-x-auto">
            <div className="flex items-center gap-1.5">
              {(['all', 'memory', 'task', 'event'] as const).map(cat => (
                <button
                  key={cat}
                  onClick={() => setFilterCategory(cat)}
                  className={`px-2.5 py-1 rounded-full text-2xs font-semibold capitalize transition-all cursor-pointer ${
                    filterCategory === cat
                      ? 'bg-brand text-white shadow-md'
                      : 'bg-surface-overlay text-text-muted hover:text-text-primary border border-border-subtle'
                  }`}
                >
                  {cat === 'all' ? '🌐 All Nodes' : cat === 'memory' ? '🧠 Memory' : cat === 'task' ? '⚡ Tasks' : '📅 Events'}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={() => setZoomScale(prev => Math.min(1.6, prev + 0.15))}
                className="p-1.5 rounded-lg bg-surface-overlay text-text-muted hover:text-text-primary border border-border-subtle transition-all active:scale-95"
                title="Zoom In"
              >
                <ZoomIn size={14} />
              </button>
              <button
                onClick={() => setZoomScale(prev => Math.max(0.6, prev - 0.15))}
                className="p-1.5 rounded-lg bg-surface-overlay text-text-muted hover:text-text-primary border border-border-subtle transition-all active:scale-95"
                title="Zoom Out"
              >
                <ZoomOut size={14} />
              </button>
              <button
                onClick={() => setZoomScale(1)}
                className="p-1.5 rounded-lg bg-surface-overlay text-text-muted hover:text-text-primary border border-border-subtle transition-all active:scale-95"
                title="Reset View"
              >
                <RotateCcw size={13} />
              </button>
            </div>
          </div>

          {/* Dynamic SVG Mind Map Canvas */}
          <div className="relative flex-1 bg-surface-base/90 p-2 sm:p-4 min-h-[350px] max-h-[460px] flex items-center justify-center overflow-hidden">
            <svg
              viewBox="0 0 600 380"
              className="w-full h-full max-h-[380px] transition-transform duration-300 ease-out"
              style={{ transform: `scale(${zoomScale})` }}
            >
              <defs>
                <radialGradient id="coreGlow" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stopColor="var(--brand)" stopOpacity="0.8" />
                  <stop offset="100%" stopColor="var(--brand)" stopOpacity="0" />
                </radialGradient>
              </defs>

              {/* Concentric Orbit Guide Rings */}
              <circle cx={centerX} cy={centerY} r="105" fill="none" stroke="var(--border-subtle)" strokeDasharray="3 3" opacity="0.6" />
              <circle cx={centerX} cy={centerY} r="155" fill="none" stroke="var(--border-subtle)" strokeDasharray="3 3" opacity="0.4" />
              <circle cx={centerX} cy={centerY} r="195" fill="none" stroke="var(--border-subtle)" strokeDasharray="3 3" opacity="0.3" />

              {/* Pulsing Neural Rays to Core */}
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
                      strokeOpacity={selectedNode?.id === n.id ? '0.9' : '0.45'}
                      strokeWidth={selectedNode?.id === n.id ? '2.5' : '1.5'}
                      strokeDasharray={selectedNode?.id === n.id ? 'none' : '4 4'}
                    />
                  )
              )}

              {/* Render Mind Map Nodes */}
              {filteredNodes.map(n => {
                const isSelected = selectedNode?.id === n.id;
                const isCore = n.category === 'core';
                const color = isCore
                  ? 'var(--brand)'
                  : n.category === 'memory'
                  ? '#7c6ff7'
                  : n.category === 'task'
                  ? '#10b981'
                  : '#f59e0b';

                return (
                  <g
                    key={n.id}
                    onClick={() => setSelectedNode(n)}
                    className="cursor-pointer transition-all duration-200"
                  >
                    {/* Background Glow */}
                    {isCore && (
                      <circle cx={n.x} cy={n.y} r={42} fill="url(#coreGlow)" className="animate-pulse" />
                    )}
                    {isSelected && (
                      <circle cx={n.x} cy={n.y} r={isCore ? 34 : 24} fill={color} opacity="0.3" className="animate-ping" />
                    )}

                    {/* Node Circle */}
                    <circle
                      cx={n.x}
                      cy={n.y}
                      r={isCore ? 26 : 16}
                      fill={color}
                      fillOpacity={isSelected ? 1 : 0.9}
                      stroke="#ffffff"
                      strokeWidth={isSelected ? 3 : 1.5}
                      className="transition-all hover:scale-110"
                    />

                    {/* Node Icon inside */}
                    {isCore ? (
                      <text x={n.x} y={n.y + 4} textAnchor="middle" fill="#ffffff" fontSize="11" fontWeight="bold" className="pointer-events-none">
                        ⚡
                      </text>
                    ) : null}

                    {/* Node Label Text */}
                    <text
                      x={n.x}
                      y={n.y + (isCore ? 40 : 30)}
                      textAnchor="middle"
                      fill="var(--text-primary)"
                      fontSize={isCore ? '11' : '9.5'}
                      fontWeight={isCore || isSelected ? 'bold' : '500'}
                      className="select-none pointer-events-none drop-shadow-md"
                    >
                      {n.label.length > 20 ? n.label.substring(0, 18) + '...' : n.label}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>

          {/* Selected Node Details Drawer */}
          <div className="p-3 sm:p-4 bg-surface-elevated border-t border-border-subtle flex items-center justify-between gap-3">
            {selectedNode ? (
              <div className="flex items-center justify-between w-full gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="px-2 py-0.5 rounded-full text-3xs font-bold uppercase tracking-wider bg-brand/20 text-brand-light border border-brand/30">
                      {selectedNode.badge || selectedNode.category}
                    </span>
                    <span className="text-2xs text-text-muted truncate">{selectedNode.label}</span>
                  </div>
                  <p className="text-xs text-text-primary font-medium truncate">{selectedNode.detail}</p>
                </div>
                <div className="flex items-center gap-1.5 flex-shrink-0">
                  <button
                    onClick={() => handleAskMitra(selectedNode)}
                    className="px-2.5 py-1.5 rounded-xl bg-brand hover:bg-brand-light text-white text-2xs font-semibold flex items-center gap-1 shadow-sm transition-all active:scale-95 cursor-pointer"
                  >
                    <MessageSquare size={12} /> Ask Mitra
                  </button>
                  <button
                    onClick={() => handleJumpToSection(selectedNode)}
                    className="px-2.5 py-1.5 rounded-xl bg-surface-overlay hover:bg-surface-hover text-text-primary text-2xs font-semibold border border-border-subtle transition-all active:scale-95 cursor-pointer"
                  >
                    Open Panel
                  </button>
                  <button
                    onClick={() => setSelectedNode(null)}
                    className="p-1 rounded-lg text-text-muted hover:text-text-primary text-xs"
                  >
                    <X size={14} />
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-between w-full text-2xs text-text-muted">
                <span className="flex items-center gap-1.5">
                  <Brain size={14} className="text-brand-light" /> Tap any node to inspect memory links or launch AI actions
                </span>
                <div className="flex items-center gap-3">
                  <span className="flex items-center gap-1 text-emerald-400"><CheckSquare size={12} /> Tasks</span>
                  <span className="flex items-center gap-1 text-amber-400"><Calendar size={12} /> Events</span>
                </div>
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

export default MemoryMindMapModal;
