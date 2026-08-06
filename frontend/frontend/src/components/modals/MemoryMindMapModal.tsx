// components/modals/MemoryMindMapModal.tsx — Next-Level Neural Brain Mind Map Visualizer with Reminders & Fullscreen Physics
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Network, RefreshCw, MessageSquare, ZoomIn, ZoomOut, RotateCcw, Sparkles, Calendar, CheckSquare, Brain, Bell, Maximize2, Minimize2, ExternalLink } from 'lucide-react';
import { useCompanionStore } from '../../store/companion.store';
import { CompanionService } from '../../services/companion.service';

interface NodeItem {
  id: string;
  label: string;
  category: 'core' | 'memory' | 'task' | 'event' | 'reminder';
  x: number;
  y: number;
  targetX: number;
  targetY: number;
  detail: string;
  badge?: string;
  linkedId?: string;
}

export const MemoryMindMapModal: React.FC<{ isOpen: boolean; onClose: () => void }> = ({ isOpen, onClose }) => {
  const { userId, userName, memory } = useCompanionStore();
  const [nodes, setNodes] = useState<NodeItem[]>([]);
  const [selectedNode, setSelectedNode] = useState<NodeItem | null>(null);
  const [loading, setLoading] = useState(false);
  const [filterCategory, setFilterCategory] = useState<'all' | 'memory' | 'task' | 'event' | 'reminder'>('all');
  const [zoomScale, setZoomScale] = useState(1);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [animTime, setAnimTime] = useState(0);

  const requestRef = useRef<number | null>(null);

  const centerX = 340;
  const centerY = 210;

  // Gentle floating animation loop
  useEffect(() => {
    if (!isOpen) return;
    const animate = () => {
      setAnimTime(prev => prev + 0.03);
      requestRef.current = requestAnimationFrame(animate);
    };
    requestRef.current = requestAnimationFrame(animate);
    return () => {
      if (requestRef.current) cancelAnimationFrame(requestRef.current);
    };
  }, [isOpen]);

  const generateGraph = useCallback(async () => {
    setLoading(true);
    const newNodes: NodeItem[] = [
      {
        id: 'core',
        label: userName || 'User Core',
        category: 'core',
        x: centerX,
        y: centerY,
        targetX: centerX,
        targetY: centerY,
        detail: `Central neural hub for ${userName || 'User'}'s Mitra AI companion context.`,
        badge: 'Neural Core',
      },
    ];

    // Orbit 1: Memory Facts (Radius 100)
    const facts: any = memory || {};
    const factKeys = Object.keys(facts);
    const memList = factKeys.length > 0 ? factKeys : ['User Preferences', 'Assistant Context', 'Active Intelligence'];
    
    memList.slice(0, 5).forEach((key, idx) => {
      const angle = (idx / Math.max(1, memList.length)) * 2 * Math.PI - Math.PI / 2;
      const radius = 105;
      const val = facts[key] || 'Learned fact node';
      const tx = centerX + Math.cos(angle) * radius;
      const ty = centerY + Math.sin(angle) * radius;
      newNodes.push({
        id: `mem_${key}`,
        label: `🧠 ${key}`,
        category: 'memory',
        x: tx,
        y: ty,
        targetX: tx,
        targetY: ty,
        detail: `Learned Fact: ${key} = ${val}`,
        badge: 'Memory',
      });
    });

    // Orbit 2: Tasks (Radius 155)
    try {
      const tasksRes = await CompanionService.getTasks(userId);
      const tasks = (tasksRes && tasksRes.tasks && tasksRes.tasks.length > 0)
        ? tasksRes.tasks
        : [
            { id: 't1', title: 'Complete Mitra Upgrade', status: 'in_progress' },
            { id: 't2', title: 'Review Daily Briefing', status: 'pending' },
          ];

      tasks.slice(0, 4).forEach((t: any, idx: number) => {
        const angle = (idx / Math.max(1, tasks.slice(0, 4).length)) * 2 * Math.PI + Math.PI / 4;
        const radius = 155;
        const tx = centerX + Math.cos(angle) * radius;
        const ty = centerY + Math.sin(angle) * radius;
        newNodes.push({
          id: `task_${t.id}`,
          label: `⚡ ${t.title}`,
          category: 'task',
          x: tx,
          y: ty,
          targetX: tx,
          targetY: ty,
          detail: `Task (${t.status || 'active'}): ${t.title}`,
          badge: 'Task',
          linkedId: `mem_${memList[idx % memList.length]}`,
        });
      });

      // Orbit 3: Events (Radius 195)
      const calRes = await CompanionService.getCalendarEvents(userId);
      const events = (calRes && calRes.events && calRes.events.length > 0)
        ? calRes.events
        : [
            { id: 'e1', title: 'Mitra Sync Meeting', start_time: 'Today' },
            { id: 'e2', title: 'Sprint Review', start_time: 'Tomorrow' },
          ];

      events.slice(0, 3).forEach((e: any, idx: number) => {
        const angle = (idx / Math.max(1, events.slice(0, 3).length)) * 2 * Math.PI - Math.PI / 3;
        const radius = 195;
        const tx = centerX + Math.cos(angle) * radius;
        const ty = centerY + Math.sin(angle) * radius;
        newNodes.push({
          id: `cal_${e.id}`,
          label: `📅 ${e.title}`,
          category: 'event',
          x: tx,
          y: ty,
          targetX: tx,
          targetY: ty,
          detail: `Calendar Event: ${e.title} (${e.start_time || 'Scheduled'})`,
          badge: 'Event',
        });
      });

      // Orbit 4: Reminders (Radius 235)
      const remRes = await CompanionService.getReminders(userId);
      const reminders = (remRes && remRes.reminders && remRes.reminders.length > 0)
        ? remRes.reminders
        : [
            { id: 'r1', message: 'Hydrate & Take Focus Break', time: 'Every 2 Hours' },
            { id: 'r2', message: 'Evening Reflection & Notes', time: '8:00 PM' },
          ];

      reminders.slice(0, 3).forEach((r: any, idx: number) => {
        const angle = (idx / Math.max(1, reminders.slice(0, 3).length)) * 2 * Math.PI + (Math.PI * 2 / 3);
        const radius = 235;
        const tx = centerX + Math.cos(angle) * radius;
        const ty = centerY + Math.sin(angle) * radius;
        newNodes.push({
          id: `rem_${r.id}`,
          label: `🔔 ${r.message}`,
          category: 'reminder',
          x: tx,
          y: ty,
          targetX: tx,
          targetY: ty,
          detail: `Reminder: ${r.message} (${r.time || 'Scheduled'})`,
          badge: 'Reminder',
        });
      });

    } catch (err) {
      console.warn('Failed to fetch mindmap entities:', err);
    }

    setNodes(newNodes);
    setLoading(false);
  }, [memory, userId, userName]);

  useEffect(() => {
    if (isOpen) {
      generateGraph();
      setZoomScale(1);
      setSelectedNode(null);
      setIsFullscreen(false);
    }
  }, [isOpen, generateGraph]);

  if (!isOpen) return null;

  const coreNode = nodes.find(n => n.category === 'core') || { targetX: centerX, targetY: centerY, label: 'User Core', id: 'core' };
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
      else if (node.category === 'reminder') navFn('reminders');
      else navFn('chat');
    }
  };

  return (
    <AnimatePresence>
      <div className={`fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 bg-black/85 backdrop-blur-xl select-none overflow-hidden transition-all duration-300 ${isFullscreen ? 'p-0' : ''}`}>
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 12 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 12 }}
          className={`bg-surface-raised border border-border-default rounded-2xl flex flex-col overflow-hidden shadow-2xl transition-all duration-300 ${
            isFullscreen ? 'w-screen h-screen rounded-none border-none' : 'w-full max-w-3xl max-h-[92vh]'
          }`}
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
                <p className="text-2xs text-text-muted">Interactive neural graph across Memory, Tasks, Events & Reminders</p>
              </div>
            </div>

            <div className="flex items-center gap-1.5">
              <button
                onClick={() => setIsFullscreen(!isFullscreen)}
                className="p-1.5 rounded-lg hover:bg-surface-overlay text-text-muted hover:text-text-primary transition-colors cursor-pointer"
                title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
              >
                {isFullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
              </button>
              <button
                onClick={generateGraph}
                className="p-1.5 rounded-lg hover:bg-surface-overlay text-text-muted hover:text-text-primary transition-colors cursor-pointer"
                title="Refresh Neural Nodes"
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
              {(['all', 'memory', 'task', 'event', 'reminder'] as const).map(cat => (
                <button
                  key={cat}
                  onClick={() => setFilterCategory(cat)}
                  className={`px-2.5 py-1 rounded-full text-2xs font-semibold capitalize transition-all cursor-pointer flex items-center gap-1 ${
                    filterCategory === cat
                      ? 'bg-brand text-white shadow-md'
                      : 'bg-surface-overlay text-text-muted hover:text-text-primary border border-border-subtle'
                  }`}
                >
                  {cat === 'all' && '🌐 All'}
                  {cat === 'memory' && '🧠 Memory'}
                  {cat === 'task' && '⚡ Tasks'}
                  {cat === 'event' && '📅 Events'}
                  {cat === 'reminder' && '🔔 Reminders'}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={() => setZoomScale(prev => Math.min(1.8, prev + 0.15))}
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
          <div className="relative flex-1 bg-surface-base/90 p-2 sm:p-4 min-h-[380px] max-h-[600px] flex items-center justify-center overflow-hidden">
            <svg
              viewBox="0 0 680 420"
              className="w-full h-full max-h-[500px] transition-transform duration-300 ease-out"
              style={{ transform: `scale(${zoomScale})` }}
            >
              <defs>
                <radialGradient id="coreGlow" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stopColor="var(--brand)" stopOpacity="0.85" />
                  <stop offset="100%" stopColor="var(--brand)" stopOpacity="0" />
                </radialGradient>
              </defs>

              {/* Background Particle Stars */}
              {[
                { cx: 80, cy: 60, r: 1 }, { cx: 580, cy: 90, r: 1.5 }, { cx: 120, cy: 360, r: 1 },
                { cx: 610, cy: 340, r: 1.2 }, { cx: 200, cy: 40, r: 1 }, { cx: 480, cy: 380, r: 1.5 }
              ].map((p, i) => (
                <circle key={`star_${i}`} cx={p.cx} cy={p.cy} r={p.r} fill="#ffffff" opacity="0.35" className="animate-pulse" />
              ))}

              {/* Concentric Orbit Guide Rings */}
              <circle cx={centerX} cy={centerY} r="105" fill="none" stroke="var(--border-subtle)" strokeDasharray="3 3" opacity="0.5" />
              <circle cx={centerX} cy={centerY} r="155" fill="none" stroke="var(--border-subtle)" strokeDasharray="3 3" opacity="0.4" />
              <circle cx={centerX} cy={centerY} r="195" fill="none" stroke="var(--border-subtle)" strokeDasharray="3 3" opacity="0.3" />
              <circle cx={centerX} cy={centerY} r="235" fill="none" stroke="var(--border-subtle)" strokeDasharray="3 3" opacity="0.2" />

              {/* Pulsing Neural Rays to Core */}
              {filteredNodes.map((n, i) => {
                if (n.category === 'core') return null;

                // Subtle floating wave per node
                const floatY = Math.sin(animTime + i) * 3.5;
                const floatX = Math.cos(animTime + i * 0.7) * 2;
                const nx = n.targetX + floatX;
                const ny = n.targetY + floatY;

                const color = n.category === 'memory'
                  ? '#7c6ff7'
                  : n.category === 'task'
                  ? '#10b981'
                  : n.category === 'event'
                  ? '#f59e0b'
                  : '#f43f5e';

                return (
                  <g key={`ray_${n.id}`}>
                    <line
                      x1={coreNode.targetX}
                      y1={coreNode.targetY}
                      x2={nx}
                      y2={ny}
                      stroke={color}
                      strokeOpacity={selectedNode?.id === n.id ? '0.9' : '0.45'}
                      strokeWidth={selectedNode?.id === n.id ? '2.5' : '1.5'}
                      strokeDasharray={selectedNode?.id === n.id ? 'none' : '4 4'}
                    />

                    {/* Secondary Interlink Line to Memory */}
                    {n.linkedId && (
                      <path
                        d={`M ${nx} ${ny} Q ${centerX + 40} ${centerY - 40} ${centerX - 70} ${centerY - 70}`}
                        fill="none"
                        stroke="#7c6ff7"
                        strokeOpacity="0.25"
                        strokeWidth="1"
                        strokeDasharray="2 2"
                      />
                    )}
                  </g>
                );
              })}

              {/* Render Mind Map Nodes */}
              {filteredNodes.map((n, i) => {
                const isSelected = selectedNode?.id === n.id;
                const isCore = n.category === 'core';
                
                const floatY = isCore ? 0 : Math.sin(animTime + i) * 3.5;
                const floatX = isCore ? 0 : Math.cos(animTime + i * 0.7) * 2;
                const nx = n.targetX + floatX;
                const ny = n.targetY + floatY;

                const color = isCore
                  ? 'var(--brand)'
                  : n.category === 'memory'
                  ? '#7c6ff7'
                  : n.category === 'task'
                  ? '#10b981'
                  : n.category === 'event'
                  ? '#f59e0b'
                  : '#f43f5e';

                return (
                  <g
                    key={n.id}
                    onClick={() => setSelectedNode(n)}
                    className="cursor-pointer transition-all duration-200"
                  >
                    {/* Background Glow */}
                    {isCore && (
                      <circle cx={nx} cy={ny} r={46} fill="url(#coreGlow)" className="animate-pulse" />
                    )}
                    {isSelected && (
                      <circle cx={nx} cy={ny} r={isCore ? 34 : 24} fill={color} opacity="0.35" className="animate-ping" />
                    )}

                    {/* Node Circle */}
                    <circle
                      cx={nx}
                      cy={ny}
                      r={isCore ? 28 : 16}
                      fill={color}
                      fillOpacity={isSelected ? 1 : 0.9}
                      stroke="#ffffff"
                      strokeWidth={isSelected ? 3 : 1.5}
                      className="transition-all hover:scale-110"
                    />

                    {/* Node Icon inside */}
                    {isCore ? (
                      <text x={nx} y={ny + 4} textAnchor="middle" fill="#ffffff" fontSize="12" fontWeight="bold" className="pointer-events-none">
                        ⚡
                      </text>
                    ) : null}

                    {/* Node Label Text */}
                    <text
                      x={nx}
                      y={ny + (isCore ? 42 : 30)}
                      textAnchor="middle"
                      fill="var(--text-primary)"
                      fontSize={isCore ? '11.5' : '9.5'}
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
                    <span className={`px-2 py-0.5 rounded-full text-3xs font-bold uppercase tracking-wider ${
                      selectedNode.category === 'reminder'
                        ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                        : selectedNode.category === 'task'
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        : selectedNode.category === 'event'
                        ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                        : 'bg-brand/20 text-brand-light border border-brand/30'
                    }`}>
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
                    className="px-2.5 py-1.5 rounded-xl bg-surface-overlay hover:bg-surface-hover text-text-primary text-2xs font-semibold border border-border-subtle flex items-center gap-1 transition-all active:scale-95 cursor-pointer"
                  >
                    <ExternalLink size={11} /> Open Panel
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
                  <Brain size={14} className="text-brand-light" /> Tap any neural node to inspect memory links or launch AI actions
                </span>
                <div className="flex items-center gap-3">
                  <span className="flex items-center gap-1 text-emerald-400"><CheckSquare size={12} /> Tasks</span>
                  <span className="flex items-center gap-1 text-amber-400"><Calendar size={12} /> Events</span>
                  <span className="flex items-center gap-1 text-rose-400"><Bell size={12} /> Reminders</span>
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
