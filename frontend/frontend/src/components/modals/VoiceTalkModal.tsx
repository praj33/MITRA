// components/modals/VoiceTalkModal.tsx — Full-screen hands-free voice mode with 3D AI orb
import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, MicOff, Volume2, VolumeX, X, Sparkles, Zap } from 'lucide-react';
import { useCompanionStore } from '../../store/companion.store';
import { CompanionService } from '../../services/companion.service';
import { showToast } from '../shell/Toast';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export const VoiceTalkModal: React.FC<Props> = ({ isOpen, onClose }) => {
  const userId = useCompanionStore(s => s.userId);
  const [talkState, setTalkState] = useState<'idle' | 'listening' | 'thinking' | 'speaking'>('idle');
  const [transcript, setTranscript] = useState('');
  const [response, setResponse] = useState('');
  const [muted, setMuted] = useState(false);

  const recognitionRef = useRef<any>(null);

  // ── Speech Synthesis TTS ──────────────────────────────
  const speakText = (text: string) => {
    if (muted || !('speechSynthesis' in window)) {
      setTalkState('listening');
      startListening();
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    utterance.onstart = () => setTalkState('speaking');
    utterance.onend = () => {
      setTalkState('listening');
      startListening();
    };
    utterance.onerror = () => {
      setTalkState('listening');
      startListening();
    };

    window.speechSynthesis.speak(utterance);
  };

  // ── Process User Voice Input ──────────────────────────
  const processVoiceInput = async (userText: string) => {
    if (!userText.trim()) return;
    setTalkState('thinking');
    setResponse('Processing your request...');

    try {
      const res = await CompanionService.chat(userId, userText);
      const reply = res.message || 'I have completed that for you.';
      setResponse(reply);
      speakText(reply);
    } catch {
      const errReply = 'I had trouble fetching that. Could you say that again?';
      setResponse(errReply);
      speakText(errReply);
    }
  };

  // ── Start Speech Recognition ──────────────────────────
  const startListening = () => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) {
      showToast('error', 'Voice STT not supported on this browser.');
      return;
    }

    try {
      if (recognitionRef.current) {
        try { recognitionRef.current.abort(); } catch {}
      }

      const rec = new SR();
      rec.continuous = false;
      rec.interimResults = true;
      rec.lang = 'en-US';

      rec.onstart = () => {
        setTalkState('listening');
      };

      rec.onresult = (event: any) => {
        let finalStr = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            finalStr += event.results[i][0].transcript;
          } else {
            setTranscript(event.results[i][0].transcript);
          }
        }

        if (finalStr.trim()) {
          setTranscript(finalStr);
          rec.stop();
          processVoiceInput(finalStr);
        }
      };

      rec.onerror = () => {
        if (isOpen && talkState === 'listening') {
          setTimeout(startListening, 1500);
        }
      };

      rec.onend = () => {
        if (talkState === 'listening') {
          // Keep loop alive if still listening
        }
      };

      rec.start();
      recognitionRef.current = rec;
    } catch (e) {
      console.warn('SpeechRecognition start failed:', e);
    }
  };

  useEffect(() => {
    if (isOpen) {
      setTranscript('');
      setResponse('Say something to Mitra...');
      startListening();
    } else {
      if (recognitionRef.current) {
        try { recognitionRef.current.abort(); } catch {}
      }
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
      setTalkState('idle');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex flex-col items-center justify-between p-6 bg-slate-950/95 backdrop-blur-xl text-white select-none overflow-hidden"
      >
        {/* Top Header */}
        <div className="w-full flex items-center justify-between max-w-lg">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-brand/30 border border-brand/50 flex items-center justify-center">
              <Zap size={16} className="text-brand-light" />
            </div>
            <span className="text-sm font-bold tracking-tight">Mitra Live Talk</span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setMuted(!muted)}
              className="w-10 h-10 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-400 hover:text-white transition-colors"
              title={muted ? 'Unmute TTS' : 'Mute TTS'}
            >
              {muted ? <VolumeX size={18} /> : <Volume2 size={18} />}
            </button>
            <button
              onClick={onClose}
              className="w-10 h-10 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-400 hover:text-white transition-colors"
              title="Close Voice Mode"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* 3D Glowing Orb Visualizer */}
        <div className="relative my-auto flex flex-col items-center justify-center">
          {/* Outer Pulsing Aura Rings */}
          <div
            className={`absolute rounded-full transition-all duration-700 ${
              talkState === 'speaking'
                ? 'w-72 h-72 bg-brand/30 animate-ping opacity-30'
                : talkState === 'listening'
                ? 'w-64 h-64 bg-emerald-500/20 animate-pulse opacity-40'
                : talkState === 'thinking'
                ? 'w-64 h-64 bg-amber-500/20 animate-spin opacity-50'
                : 'w-56 h-56 bg-brand/10'
            }`}
          />
          <div
            className={`absolute rounded-full transition-all duration-500 ${
              talkState === 'speaking'
                ? 'w-60 h-60 bg-brand-light/30 blur-xl'
                : talkState === 'listening'
                ? 'w-52 h-52 bg-emerald-400/30 blur-xl'
                : 'w-48 h-48 bg-purple-500/20 blur-lg'
            }`}
          />

          {/* Central Sphere */}
          <motion.div
            animate={{
              scale: talkState === 'speaking' ? [1, 1.12, 1] : talkState === 'listening' ? [1, 1.05, 1] : 1,
            }}
            transition={{ repeat: Infinity, duration: 2 }}
            className={`relative w-36 h-36 rounded-full flex items-center justify-center shadow-2xl transition-all duration-500 cursor-pointer ${
              talkState === 'speaking'
                ? 'bg-gradient-to-tr from-brand to-purple-500 shadow-brand/50'
                : talkState === 'listening'
                ? 'bg-gradient-to-tr from-emerald-600 to-teal-400 shadow-emerald-500/50'
                : talkState === 'thinking'
                ? 'bg-gradient-to-tr from-amber-600 to-yellow-400 shadow-amber-500/50'
                : 'bg-slate-800'
            }`}
            onClick={startListening}
          >
            {talkState === 'listening' ? (
              <Mic size={40} className="text-white animate-bounce" />
            ) : talkState === 'thinking' ? (
              <Sparkles size={40} className="text-white animate-spin" />
            ) : talkState === 'speaking' ? (
              <Volume2 size={40} className="text-white animate-pulse" />
            ) : (
              <MicOff size={40} className="text-slate-400" />
            )}
          </motion.div>

          {/* Status Label */}
          <div className="mt-8 text-center">
            <span
              className={`inline-block text-xs font-semibold px-3.5 py-1 rounded-full uppercase tracking-wider ${
                talkState === 'listening'
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                  : talkState === 'thinking'
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                  : talkState === 'speaking'
                  ? 'bg-brand/30 text-brand-light border border-brand/50'
                  : 'bg-slate-800 text-slate-400'
              }`}
            >
              {talkState === 'listening'
                ? '🎙️ Listening...'
                : talkState === 'thinking'
                ? '⚡ Thinking...'
                : talkState === 'speaking'
                ? '🔊 Mitra Speaking'
                : 'Tap Orb to Speak'}
            </span>
          </div>
        </div>

        {/* Live Subtitles & Response Container */}
        <div className="w-full max-w-lg bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex flex-col gap-2 backdrop-blur-md">
          {transcript && (
            <div className="text-xs text-slate-400">
              <span className="font-semibold text-slate-300">You: </span>"{transcript}"
            </div>
          )}
          <div className="text-sm font-medium text-white leading-relaxed">
            <span className="text-brand-light font-semibold">Mitra: </span>
            {response || 'Listening for your command...'}
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};
