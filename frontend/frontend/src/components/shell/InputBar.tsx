// components/shell/InputBar.tsx — Message input with send + voice + attach (responsive)
import React, { useState, useRef, KeyboardEvent } from 'react';
import { motion } from 'framer-motion';
import { Send, Mic, MicOff, Paperclip, Zap } from 'lucide-react';
import { cn } from '../../lib/utils';
import { useCompanionStore } from '../../store/companion.store';
import { showToast } from './Toast';

interface Props {
  onSend:     (message: string, isVoice?: boolean) => void;
  disabled?:  boolean;
}

const quickActions = [
  { label: '📋 Briefing',     value: 'Run my morning briefing' },
  { label: '📧 Email',        value: 'Check my recent emails' },
  { label: '📅 Schedule',     value: 'What\'s on my calendar today?' },
  { label: '✅ Tasks',        value: 'Show my pending tasks' },
];

const InputBar: React.FC<Props> = ({ onSend, disabled }) => {
  const [value, setValue] = useState('');
  const [showQuick, setShowQuick] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { status, isMobile } = useCompanionStore();
  const transcriptRef = useRef('');

  const isThinking = status === 'thinking';

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled || isThinking) return;
    onSend(trimmed, false);
    setValue('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  };

  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && !isMobile) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setValue(e.target.value);
    const ta = e.target;
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, isMobile ? 100 : 120) + 'px';
  };

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const activeStreamRef = useRef<MediaStream | null>(null);

  const stopActiveStream = () => {
    if (activeStreamRef.current) {
      activeStreamRef.current.getTracks().forEach(track => {
        try { track.stop(); } catch {}
      });
      activeStreamRef.current = null;
    }
  };

  const toggleVoiceInput = async () => {
    // If currently recording, stop and process
    if (isListening) {
      setIsListening(false);
      if ((window as any)._activeRecognition) {
        try { (window as any)._activeRecognition.stop(); } catch {}
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        try { mediaRecorderRef.current.stop(); } catch {}
      }
      stopActiveStream();
      const textToSend = transcriptRef.current.trim() || value.trim();
      if (textToSend) {
        onSend(textToSend, true);
        setValue('');
        transcriptRef.current = '';
        if (textareaRef.current) textareaRef.current.style.height = 'auto';
      }
      return;
    }

    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    // ── Strategy A: Web Speech API (iOS Safari & Android Chrome) ─────
    if (SR) {
      try {
        transcriptRef.current = '';
        const recognition = new SR();
        (window as any)._activeRecognition = recognition;

        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.maxAlternatives = 1;
        recognition.lang = 'en-US';

        recognition.onstart = () => {
          setIsListening(true);
          showToast('info', '🎙️ Listening... Speak now into your mic');
        };

        recognition.onresult = (event: any) => {
          let currentText = '';
          for (let i = event.resultIndex; i < event.results.length; ++i) {
            currentText += event.results[i][0].transcript;
          }
          if (currentText) {
            transcriptRef.current = currentText;
            setValue(currentText);
          }
        };

        recognition.onerror = (err: any) => {
          console.warn('SpeechRecognition notice:', err.error);
          if (err.error === 'not-allowed' || err.error === 'service-not-allowed') {
            showToast('error', 'Microphone access denied in browser settings.');
          } else if (err.error === 'no-speech') {
            showToast('info', 'No speech heard. Please try speaking again.');
          }
          setIsListening(false);
        };

        recognition.onend = () => {
          setIsListening(false);
          const finalSpeech = transcriptRef.current.trim();
          if (finalSpeech) {
            onSend(finalSpeech, true);
            setValue('');
            transcriptRef.current = '';
            if (textareaRef.current) textareaRef.current.style.height = 'auto';
          }
        };

        recognition.start();
        return;
      } catch (err) {
        console.warn('SpeechRecognition failed, attempting MediaRecorder fallback:', err);
      }
    }

    // ── Strategy B: MediaRecorder Fallback ──────────────────────────
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        activeStreamRef.current = stream;
        audioChunksRef.current = [];

        const mimeType = MediaRecorder.isTypeSupported('audio/webm')
          ? 'audio/webm'
          : MediaRecorder.isTypeSupported('audio/mp4')
          ? 'audio/mp4'
          : '';

        const mediaRecorder = mimeType
          ? new MediaRecorder(stream, { mimeType })
          : new MediaRecorder(stream);

        mediaRecorderRef.current = mediaRecorder;

        mediaRecorder.ondataavailable = (e) => {
          if (e.data && e.data.size > 0) audioChunksRef.current.push(e.data);
        };

        mediaRecorder.onstop = () => {
          stopActiveStream();
          setIsListening(false);
          const textVal = value.trim();
          if (textVal) {
            onSend(textVal, true);
            setValue('');
          } else if (audioChunksRef.current.length > 0) {
            onSend("Voice recording received. Please answer my audio query.", true);
            setValue('');
          }
        };

        mediaRecorder.start(250);
        setIsListening(true);
        showToast('info', '🎙️ Recording voice... Tap mic icon to finish.');
      } catch (err) {
        stopActiveStream();
        setIsListening(false);
        showToast('error', 'Microphone permission denied. Please allow mic in settings.');
      }
    } else {
      showToast('error', 'Microphone recording is not supported on this browser.');
    }
  };

  return (
    <div className="zone-input bg-surface-raised border-t border-border-subtle px-3 sm:px-4 py-2 sm:py-2.5 flex flex-col gap-1.5 sm:gap-2">
      {/* Visual Live Recording Banner */}
      {isListening && (
        <div className="flex items-center justify-between bg-red-500/10 border border-red-500/30 rounded-lg px-3 py-1.5 text-xs text-red-500 animate-pulse select-none">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-ping" />
            <span className="font-medium text-xs">Listening to your voice... Speak now</span>
          </div>
          <button
            onClick={toggleVoiceInput}
            className="text-2xs bg-red-500 text-white px-2.5 py-1 rounded font-semibold hover:bg-red-600 transition-colors cursor-pointer"
          >
            Finish & Send
          </button>
        </div>
      )}
      {/* Quick actions */}
      {showQuick && !value && (
        <motion.div
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 4 }}
          className="flex gap-1.5 flex-wrap"
        >
          {quickActions.map(qa => (
            <button
              key={qa.value}
              onClick={() => { onSend(qa.value); setShowQuick(false); }}
              className="text-2xs px-2.5 py-1 rounded-md bg-surface-elevated border border-border-subtle hover:border-brand/40 hover:text-brand-light text-text-muted transition-colors cursor-pointer"
            >
              {qa.label}
            </button>
          ))}
        </motion.div>
      )}

      {/* Input container */}
      <div className="flex items-end gap-1.5 sm:gap-2">
        {/* Quick action toggle */}
        <button
          onClick={() => setShowQuick(!showQuick)}
          className={cn(
            'flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-lg transition-colors mb-0.5',
            showQuick ? 'bg-brand-muted text-brand-light' : 'text-text-muted hover:text-text-secondary hover:bg-surface-overlay',
          )}
          aria-label="Quick actions"
          title="Quick prompts"
        >
          <Zap size={14} />
        </button>

        {/* Textarea wrapper */}
        <div className="flex-1 relative min-w-0">
          <textarea
            ref={textareaRef}
            rows={1}
            value={value}
            onChange={handleChange}
            onKeyDown={handleKey}
            placeholder={isListening ? 'Listening to your voice... Speak now!' : disabled ? 'Processing...' : 'Ask Mitra anything...'}
            disabled={disabled || isThinking}
            className={cn(
              'w-full bg-surface-overlay text-text-primary text-xs sm:text-sm rounded-lg px-3 py-2 border border-border-subtle focus:outline-none focus:border-brand/50 transition-colors resize-none overflow-y-auto leading-relaxed placeholder:text-text-muted/60',
              isListening ? 'border-brand text-brand-light animate-pulse' : '',
            )}
            style={{ maxHeight: isMobile ? '100px' : '120px' }}
          />
        </div>

        {/* Attach file */}
        <button
          id="inputbar-attach"
          className="flex-shrink-0 w-8 h-8 items-center justify-center rounded-lg text-text-muted hover:text-text-secondary hover:bg-surface-overlay transition-colors mb-0.5 hidden sm:flex"
          aria-label="Attach file"
        >
          <Paperclip size={14} />
        </button>

        {/* Voice Input — Nilesh Duplex / Web Speech STT */}
        <button
          id="inputbar-voice"
          onClick={toggleVoiceInput}
          className={cn(
            'flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-lg transition-colors mb-0.5',
            isListening ? 'bg-red-500/20 text-red-400 border border-red-500/40 animate-pulse' : 'text-text-muted hover:text-brand-light hover:bg-brand-muted',
          )}
          aria-label="Voice input"
          title={isListening ? 'Listening... click to stop' : 'Click to speak (Voice STT)'}
        >
          {isListening ? <MicOff size={14} className="text-red-400" /> : <Mic size={14} />}
        </button>

        {/* Send */}
        <button
          id="inputbar-send"
          onClick={handleSend}
          disabled={!value.trim() || disabled || isThinking}
          className={cn(
            'flex-shrink-0 w-8 h-8 sm:w-8 sm:h-8 flex items-center justify-center rounded-lg transition-all duration-150 active:scale-95 mb-0.5',
            value.trim() && !disabled && !isThinking
              ? 'bg-brand text-white hover:bg-brand-light shadow-glow-sm'
              : 'bg-surface-overlay text-text-muted cursor-not-allowed',
          )}
          aria-label="Send message"
        >
          <Send size={13} />
        </button>
      </div>

      {/* Hint — only on desktop */}
      <p className="text-2xs text-text-muted text-center hidden md:block">
        Press <kbd className="px-1 py-0.5 bg-surface-overlay border border-border-subtle rounded text-2xs">Enter</kbd> to send · <kbd className="px-1 py-0.5 bg-surface-overlay border border-border-subtle rounded text-2xs">Shift+Enter</kbd> for new line
      </p>
    </div>
  );
};

export default InputBar;
