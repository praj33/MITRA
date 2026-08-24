// components/modals/MemoryMindMapModal.tsx — 60FPS Neural Brain Mind Map Visualizer with Upright Text & Zero Clipping
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Network, RefreshCw, MessageSquare, ZoomIn, ZoomOut, RotateCcw, Sparkles, Calendar, CheckSquare, Brain, Bell, Maximize2, Minimize2, ExternalLink, Play, Pause } from 'lucide-react';
import { useCompanionStore } from '../../store/companion.store';
import { CompanionService } from '../../services/companion.service';

interface NodeData {
  id: string;
  label: string;
  category: 'core' | 'memory' | 'task' | 'event' | 'reminder';
  baseAngle: number;
  radiusX: number;
  radiusY: number;
  detail: string;
  badge?: string;
}

export const MemoryMindMapModal: React.FC<{ isOpen: boolean; onClose: () => void }> = ({ isOpen, onClose }) => {
  const { userId, userName, memory } = useCompanionStore();
  const [nodes, setNodes] = useState<NodeData[]>([]);
  const [selectedNode, setSelectedNode] = useState<NodeData | null>(null);
  const [loading, setLoading] = useState(false);
  const [filterCategory, setFilterCategory] = useState<'all' | 'memory' | 'task' | 'event' | 'reminder'>('all');
  const [zoomScale, setZoomScale] = useState(1);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [autoRevolve, setAutoRevolve] = useState(true);

  // 60FPS Rotation State
  const [rotationAngle, setRotationAngle] = useState(0);
  const isDraggingRef = useRef(false);
  const dragStartXRef = useRef(0);
  const startAngleRef = useRef(0);
  const animFrameRef = useRef<number | null>(null);

  // Canvas ViewBox (800x580) - Center at (400, 290) - Perfect spacing for outer 300px orbit
  const centerX = 400;
  const centerY = 290;

  // 60FPS Smooth Revolving Loop
  useEffect(() => {
    if (!isOpen) return;

    let lastTime = performance.now();
    const updateOrbit = (now: number) => {
      const delta = (now - lastTime) / 1000;
      lastTime = now;

      if (autoRevolve && !isDraggingRef.current) {
        setRotationAngle(prev => (prev + delta * 0.25) % (Math.PI * 2));
      }
      animFrameRef.current = requestAnimationFrame(updateOrbit);
    };

    animFrameRef.current = requestAnimationFrame(updateOrbit);
    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [isOpen, autoRevolve]);

  const generateGraph = useCallback(async () => {
    setLoading(true);
    const newNodes: NodeData[] = [];

    // Orbit 1: Memory Facts (Rx: 120, Ry: 90)
    const facts: any = memory || {};
    const factKeys = Object.keys(facts);
    const memList = factKeys.length > 0 ? factKeys : ['User Preferences', 'Assistant Context', 'Active Intelligence'];
    
    memList.slice(0, 5).forEach((key, idx) => {
      const angle = (idx / Math.max(1, memList.length)) * 2 * Math.PI - Math.PI / 2;
      const val = facts[key] || 'Learned fact node';

      newNodes.push({
        id: `mem_${key}`,
        label: `🧠 ${key}`,
        category: 'memory',
        baseAngle: angle,
        radiusX: 120,
        radiusY: 90,
        detail: `Learned Fact: ${key} = ${val}`,
        badge: 'Memory',
      });
    });

    try {
      // Orbit 2: Tasks (Rx: 180, Ry: 135) - Staggered offset angle (Math.PI / 5)
      const tasksRes = await CompanionService.getTasks(userId);
      const tasks = (tasksRes && tasksRes.tasks && tasksRes.tasks.length > 0)
        ? tasksRes.tasks
        : [
            { id: 't1', title: 'Complete Mitra Phase 2', status: 'in_progress' },
            { id: 't2', title: 'Review Daily Briefing', status: 'pending' },
          ];

      tasks.slice(0, 4).forEach((t: any, idx: number) => {
        const angle = (idx / Math.max(1, tasks.slice(0, 4).length)) * 2 * Math.PI + Math.PI / 5;

        newNodes.push({
          id: `task_${t.id}`,
          label: `⚡ ${t.title}`,
          category: 'task',
          baseAngle: angle,
          radiusX: 180,
          radiusY: 135,
          detail: `Task (${t.status || 'active'}): ${t.title}`,
          badge: 'Task',
        });
      });

      // Orbit 3: Events (Rx: 240, Ry: 180) - Staggered offset angle (Math.PI / 3)
      const calRes = await CompanionService.getCalendarEvents(userId);
      const events = (calRes && calRes.events && calRes.events.length > 0)
        ? calRes.events
        : [
            { id: 'e1', title: 'Mitra Sync Meeting', start_time: 'Today' },
            { id: 'e2', title: 'Sprint Review', start_time: 'Tomorrow' },
          ];

      events.slice(0, 3).forEach((e: any, idx: number) => {
        const angle = (idx / Math.max(1, events.slice(0, 3).length)) * 2 * Math.PI + Math.PI / 3;

        newNodes.push({
          id: `cal_${e.id}`,
          label: `📅 ${e.title}`,
          category: 'event',
          baseAngle: angle,
          radiusX: 240,
          radiusY: 180,
          detail: `Calendar Event: ${e.title} (${e.start_time || 'Scheduled'})`,
          badge: 'Event',
        });
      });

      // Orbit 4: Reminders (Rx: 300, Ry: 225) - Staggered offset angle (Math.PI / 2)
      const remRes = await CompanionService.getReminders(userId);
      const reminders = (remRes && remRes.reminders && remRes.reminders.length > 0)
        ? remRes.reminders
        : [
            { id: 'r1', message: 'Hydrate & Take Focus Break', time: 'Every 2 Hours' },
            { id: 'r2', message: 'Evening Reflection & Notes', time: '8:00 PM' },
          ];

      reminders.slice(0, 4).forEach((r: any, idx: number) => {
        const angle = (idx / Math.max(1, reminders.slice(0, 4).length)) * 2 * Math.PI + Math.PI / 2;

        newNodes.push({
          id: `rem_${r.id}`,
          label: `🔔 ${r.message}`,
          category: 'reminder',
          baseAngle: angle,
          radiusX: 300,
          radiusY: 225,
          detail: `Reminder: ${r.message} (${r.time || 'Scheduled'})`,
          badge: 'Reminder',
        });
      });

    } catch (err) {
      console.warn('Failed to fetch mindmap entities:', err);
    }

    setNodes(newNodes);
    setLoading(false);
  }, [memory, userId]);

  useEffect(() => {
    if (isOpen) {
      generateGraph();
      setZoomScale(1);
      setSelectedNode(null);
      setIsFullscreen(false);
      setRotationAngle(0);
    }
  }, [isOpen, generateGraph]);

  // Smooth Drag Handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    isDraggingRef.current = true;
    dragStartXRef.current = e.clientX;
    startAngleRef.current = rotationAngle;
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDraggingRef.current) return;
    const dx = e.clientX - dragStartXRef.current;
    setRotationAngle(startAngleRef.current + dx * 0.008);
  };

  const handleMouseUp = () => {
    isDraggingRef.current = false;
  };

  const handleTouchStart = (e: React.TouchEvent) => {
    if (e.touches.length > 0) {
      isDraggingRef.current = true;
      dragStartXRef.current = e.touches[0].clientX;
      startAngleRef.current = rotationAngle;
    }
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (!isDraggingRef.current || e.touches.length === 0) return;
    const dx = e.touches[0].clientX - dragStartXRef.current;
    setRotationAngle(startAngleRef.current + dx * 0.008);
  };

  if (!isOpen) return null;

  const filteredNodes = nodes.filter(n => filterCategory === 'all' || n.category === filterCategory);

  // Compute Upright 2D Position for each node at current rotation angle
  const calculatedNodes = filteredNodes.map(n => {
    const currentAngle = n.baseAngle + rotationAngle;
    const x = centerX + Math.cos(currentAngle) * n.radiusX;
    const y = centerY + Math.sin(currentAngle) * n.radiusY;
    const zDepth = Math.sin(currentAngle);

    return {
      ...n,
      x,
      y,
      zDepth,
    };
  });

  const handleAskMitra = (node: NodeData) => {
    onClose();
    const sendFn = (window as any).__MITRA_SEND__;
    const navFn = (window as any).__MITRA_NAV__;
    if (navFn) navFn('chat');
    if (sendFn) sendFn(`Tell me more about "${node.detail}" and help me optimize it.`);
  };

  const handleJumpToSection = (node: NodeData) => {
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
            isFullscreen ? 'w-screen h-screen rounded-none border-none' : 'w-full max-w-4xl max-h-[94vh]'
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
                  Neural Brain Mind Map <Sparkles size={14} className="text-brand-light animate-pulse" />
                </h3>
                <p className="text-2xs text-text-muted">Interactive revolving solar system of memory, tasks & reminders</p>
              </div>
            </div>

            <div className="flex items-center gap-1.5">
              <button
                onClick={() => setAutoRevolve(!autoRevolve)}
                className={`px-2.5 py-1 rounded-lg text-2xs font-semibold flex items-center gap-1.5 border transition-all cursor-pointer ${
                  autoRevolve
                    ? 'bg-brand/20 border-brand/40 text-brand-light'
                    : 'bg-surface-overlay border-border-subtle text-text-muted hover:text-text-primary'
                }`}
                title={autoRevolve ? 'Pause Auto Revolution' : 'Start Auto Revolution'}
              >
                {autoRevolve ? <Pause size={12} /> : <Play size={12} />}
                <span>{autoRevolve ? 'Orbiting' : 'Paused'}</span>
              </button>
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
                title="Refresh Graph"
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
                onClick={() => {
                  setZoomScale(1);
                  setRotationAngle(0);
                }}
                className="p-1.5 rounded-lg bg-surface-overlay text-text-muted hover:text-text-primary border border-border-subtle transition-all active:scale-95"
                title="Reset View"
              >
                <RotateCcw size={13} />
              </button>
            </div>
          </div>

          {/* Dynamic Upright SVG Mind Map Canvas */}
          <div
            className="relative flex-1 bg-surface-base/90 p-2 sm:p-4 min-h-[440px] max-h-[660px] flex items-center justify-center overflow-hidden cursor-grab active:cursor-grabbing"
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
            onTouchStart={handleTouchStart}
            onTouchMove={handleTouchMove}
            onTouchEnd={handleMouseUp}
          >
            <svg
              viewBox="0 0 800 580"
              className="w-full h-full max-h-[580px] transition-transform duration-300 ease-out"
              style={{ transform: `scale(${zoomScale})` }}
            >
              <defs>
                <radialGradient id="coreGlowUpright" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stopColor="var(--brand)" stopOpacity="0.9" />
                  <stop offset="100%" stopColor="var(--brand)" stopOpacity="0" />
                </radialGradient>
              </defs>

              {/* Background Stars */}
              {[
                { cx: 90, cy: 70, r: 1 }, { cx: 720, cy: 110, r: 1.5 }, { cx: 140, cy: 500, r: 1 },
                { cx: 750, cy: 490, r: 1.2 }, { cx: 240, cy: 50, r: 1 }, { cx: 620, cy: 520, r: 1.5 }
              ].map((p, i) => (
                <circle key={`star_${i}`} cx={p.cx} cy={p.cy} r={p.r} fill="#ffffff" opacity="0.3" className="animate-pulse" />
              ))}

              {/* Orbit Ellipse Guides */}
              {(filterCategory === 'all' || filterCategory === 'memory') && (
                <ellipse cx={centerX} cy={centerY} rx="120" ry="90" fill="none" stroke="var(--border-subtle)" strokeDasharray="3 3" opacity="0.6" />
              )}
              {(filterCategory === 'all' || filterCategory === 'task') && (
                <ellipse cx={centerX} cy={centerY} rx="180" ry="135" fill="none" stroke="var(--border-subtle)" strokeDasharray="3 3" opacity="0.45" />
              )}
              {(filterCategory === 'all' || filterCategory === 'event') && (
                <ellipse cx={centerX} cy={centerY} rx="240" ry="180" fill="none" stroke="var(--border-subtle)" strokeDasharray="3 3" opacity="0.35" />
              )}
              {(filterCategory === 'all' || filterCategory === 'reminder') && (
                <ellipse cx={centerX} cy={centerY} rx="300" ry="225" fill="none" stroke="var(--border-subtle)" strokeDasharray="3 3" opacity="0.25" />
              )}

              {/* Connecting Rays from Central Core to Each Revolving Node */}
              {calculatedNodes.map(n => {
                const color = n.category === 'memory'
                  ? '#7c6ff7'
                  : n.category === 'task'
                  ? '#10b981'
                  : n.category === 'event'
                  ? '#f59e0b'
                  : '#f43f5e';

                return (
                  <line
                    key={`ray_${n.id}`}
                    x1={centerX}
                    y1={centerY}
                    x2={n.x}
                    y2={n.y}
                    stroke={color}
                    strokeOpacity={selectedNode?.id === n.id ? 0.9 : 0.45}
                    strokeWidth={selectedNode?.id === n.id ? 2.5 : 1.5}
                    strokeDasharray={selectedNode?.id === n.id ? 'none' : '4 4'}
                  />
                );
              })}

              {/* Fixed Central Core Node (User Hub) */}
              <g className="cursor-pointer">
                <circle cx={centerX} cy={centerY} r={52} fill="url(#coreGlowUpright)" className="animate-pulse" />
                <circle cx={centerX} cy={centerY} r={30} fill="var(--brand)" stroke="#ffffff" strokeWidth="2.5" />
                <text x={centerX} y={centerY + 4} textAnchor="middle" fill="#ffffff" fontSize="14" fontWeight="bold" className="pointer-events-none">
                  ⚡
                </text>
                <text x={centerX} y={centerY + 48} textAnchor="middle" fill="var(--text-primary)" fontSize="12.5" fontWeight="bold" className="select-none pointer-events-none drop-shadow-md">
                  {userName || 'User Core'}
                </text>
              </g>

              {/* Render Nodes at Upright Calculated Coordinates */}
              {calculatedNodes.map(n => {
                const isSelected = selectedNode?.id === n.id;
                const color = n.category === 'memory'
                  ? '#7c6ff7'
                  : n.category === 'task'
                  ? '#10b981'
                  : n.category === 'event'
                  ? '#f59e0b'
                  : '#f43f5e';

                return (
                  <g
                    key={n.id}
                    onClick={(e) => { e.stopPropagation(); setSelectedNode(n); }}
                    className="cursor-pointer transition-transform duration-100 hover:scale-125"
                  >
                    {/* Active Selection Glow */}
                    {isSelected && (
                      <circle cx={n.x} cy={n.y} r="26" fill={color} opacity="0.35" className="animate-ping" />
                    )}

                    {/* Node Sphere */}
                    <circle
                      cx={n.x}
                      cy={n.y}
                      r="17"
                      fill={color}
                      stroke="#ffffff"
                      strokeWidth={isSelected ? 3 : 1.5}
                    />

                    {/* Upright Text Label (Always perfectly horizontal & 100% readable) */}
                    <text
                      x={n.x}
                      y={n.y + 30}
                      textAnchor="middle"
                      fill="var(--text-primary)"
                      fontSize="10.5"
                      fontWeight={isSelected ? 'bold' : '600'}
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
                  <Brain size={14} className="text-brand-light" /> Drag canvas to revolve solar system. Tap any node to inspect memory links.
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
