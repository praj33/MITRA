import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, Pause, RotateCcw, Volume2, VolumeX, CloudRain, Sparkles, Wind, X } from 'lucide-react';
import { AmbientSoundService } from '../../services/ambientSound.service';

interface FocusTimerModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const FocusTimerModal: React.FC<FocusTimerModalProps> = ({ isOpen, onClose }) => {
  const [timeLeft, setTimeLeft] = useState(25 * 60);
  const [isRunning, setIsRunning] = useState(false);
  const [timerMode, setTimerMode] = useState<'work' | 'shortBreak' | 'longBreak'>('work');
  const [activeSound, setActiveSound] = useState<string | null>(null);
  const [volume, setVolume] = useState(0.4);

  // Timer loop
  useEffect(() => {
    let interval: any = null;
    if (isRunning && timeLeft > 0) {
      interval = setInterval(() => {
        setTimeLeft(prev => prev - 1);
      }, 1000);
    } else if (timeLeft === 0 && isRunning) {
      setIsRunning(false);
      AmbientSoundService.stop();
      setActiveSound(null);
    }
    return () => clearInterval(interval);
  }, [isRunning, timeLeft]);

  const switchMode = (mode: 'work' | 'shortBreak' | 'longBreak') => {
    setTimerMode(mode);
    setIsRunning(false);
    if (mode === 'work') setTimeLeft(25 * 60);
    else if (mode === 'shortBreak') setTimeLeft(5 * 60);
    else setTimeLeft(15 * 60);
  };

  const toggleSound = (soundId: string) => {
    if (activeSound === soundId) {
      AmbientSoundService.stop();
      setActiveSound(null);
    } else {
      AmbientSoundService.play(soundId, volume);
      setActiveSound(soundId);
    }
  };

  const handleVolumeChange = (v: number) => {
    setVolume(v);
    AmbientSoundService.setVolume(v);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 10 }}
        className="fixed bottom-20 right-4 sm:right-6 z-50 w-80 sm:w-96 rounded-2xl bg-surface-elevated/95 border border-brand/30 shadow-2xl backdrop-blur-xl p-4 flex flex-col gap-4 select-none"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border-subtle pb-2.5">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-brand animate-ping" />
            <h3 className="text-xs sm:text-sm font-bold text-text-primary">Focus Session & Soundscapes</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-overlay transition-colors"
          >
            <X size={16} />
          </button>
        </div>

        {/* Mode Selector */}
        <div className="grid grid-cols-3 gap-1 bg-surface-overlay p-1 rounded-xl border border-border-subtle">
          <button
            onClick={() => switchMode('work')}
            className={`py-1.5 text-2xs font-semibold rounded-lg transition-all ${
              timerMode === 'work' ? 'bg-brand text-white shadow-sm' : 'text-text-muted hover:text-text-primary'
            }`}
          >
            Focus (25m)
          </button>
          <button
            onClick={() => switchMode('shortBreak')}
            className={`py-1.5 text-2xs font-semibold rounded-lg transition-all ${
              timerMode === 'shortBreak' ? 'bg-amber-500 text-white shadow-sm' : 'text-text-muted hover:text-text-primary'
            }`}
          >
            Break (5m)
          </button>
          <button
            onClick={() => switchMode('longBreak')}
            className={`py-1.5 text-2xs font-semibold rounded-lg transition-all ${
              timerMode === 'longBreak' ? 'bg-indigo-500 text-white shadow-sm' : 'text-text-muted hover:text-text-primary'
            }`}
          >
            Rest (15m)
          </button>
        </div>

        {/* Big Digital Timer Display */}
        <div className="flex flex-col items-center justify-center py-3 bg-surface-base/50 rounded-2xl border border-border-subtle/40">
          <span className="text-4xl sm:text-5xl font-extrabold tracking-widest text-text-primary font-mono">
            {formatTime(timeLeft)}
          </span>
          <span className="text-2xs text-text-muted mt-1 uppercase tracking-wider font-semibold">
            {isRunning ? 'Session Active' : 'Paused'}
          </span>
        </div>

        {/* Play / Pause / Reset Controls */}
        <div className="flex items-center justify-center gap-3">
          <button
            onClick={() => {
              setIsRunning(!isRunning);
              if (!isRunning && !activeSound) {
                toggleSound('rain');
              }
            }}
            className="w-12 h-12 rounded-2xl bg-brand hover:bg-brand-light text-white flex items-center justify-center shadow-lg transition-all active:scale-95"
          >
            {isRunning ? <Pause size={20} /> : <Play size={20} className="ml-0.5" />}
          </button>

          <button
            onClick={() => {
              setIsRunning(false);
              setTimeLeft(timerMode === 'work' ? 25 * 60 : timerMode === 'shortBreak' ? 5 * 60 : 15 * 60);
              AmbientSoundService.stop();
              setActiveSound(null);
            }}
            className="w-10 h-10 rounded-xl bg-surface-overlay hover:bg-surface-overlay/80 border border-border-subtle text-text-muted hover:text-text-primary flex items-center justify-center transition-all active:scale-95"
          >
            <RotateCcw size={16} />
          </button>
        </div>

        {/* Ambient Soundscapes */}
        <div className="border-t border-border-subtle pt-3 flex flex-col gap-2">
          <label className="text-2xs text-text-muted font-semibold uppercase tracking-wider">
            Ambient Soundscape
          </label>
          <div className="grid grid-cols-3 gap-2">
            <button
              onClick={() => toggleSound('rain')}
              className={`p-2 rounded-xl border flex flex-col items-center gap-1 text-2xs font-medium transition-all ${
                activeSound === 'rain'
                  ? 'border-brand bg-brand/15 text-brand-light'
                  : 'border-border-subtle bg-surface-overlay text-text-muted hover:text-text-primary'
              }`}
            >
              <CloudRain size={16} />
              <span>Rain</span>
            </button>

            <button
              onClick={() => toggleSound('space')}
              className={`p-2 rounded-xl border flex flex-col items-center gap-1 text-2xs font-medium transition-all ${
                activeSound === 'space'
                  ? 'border-indigo-500 bg-indigo-500/15 text-indigo-400'
                  : 'border-border-subtle bg-surface-overlay text-text-muted hover:text-text-primary'
              }`}
            >
              <Sparkles size={16} />
              <span>Deep Space</span>
            </button>

            <button
              onClick={() => toggleSound('white')}
              className={`p-2 rounded-xl border flex flex-col items-center gap-1 text-2xs font-medium transition-all ${
                activeSound === 'white'
                  ? 'border-amber-400 bg-amber-400/15 text-amber-400'
                  : 'border-border-subtle bg-surface-overlay text-text-muted hover:text-text-primary'
              }`}
            >
              <Wind size={16} />
              <span>Soft Focus</span>
            </button>
          </div>

          {/* Volume Slider */}
          {activeSound && (
            <div className="flex items-center gap-2 pt-1 px-1">
              <button
                onClick={() => handleVolumeChange(volume === 0 ? 0.4 : 0)}
                className="text-text-muted hover:text-text-primary"
              >
                {volume === 0 ? <VolumeX size={14} /> : <Volume2 size={14} />}
              </button>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={volume}
                onChange={e => handleVolumeChange(parseFloat(e.target.value))}
                className="w-full accent-brand h-1 rounded-lg cursor-pointer bg-surface-overlay"
              />
            </div>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
};
