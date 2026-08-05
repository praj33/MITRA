// components/shell/InputBar.tsx — Message input with send + voice + attach (responsive)
import React, { useState, useRef, KeyboardEvent } from 'react';
import { motion } from 'framer-motion';
import { Send, Mic, Paperclip, Zap, X, Check } from 'lucide-react';
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
  const autoSendTimerRef = useRef<NodeJS.Timeout | null>(null);

  const isThinking = status === 'thinking';

  const clearAutoSendTimer = () => {
    if (autoSendTimerRef.current) {
      clearTimeout(autoSendTimerRef.current);
      autoSendTimerRef.current = null;
    }
  };

  const handleSend = () => {
    clearAutoSendTimer();
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
    clearAutoSendTimer();
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

  // ── Cancel Voice Input (Stops & Discards) ─────
  const cancelVoiceInput = () => {
    clearAutoSendTimer();
    setIsListening(false);
    if ((window as any)._activeRecognition) {
      try {
        (window as any)._activeRecognition.onend = null;
        (window as any)._activeRecognition.abort();
      } catch {}
      (window as any)._activeRecognition = null;
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      try {
        mediaRecorderRef.current.onstop = null;
        mediaRecorderRef.current.stop();
      } catch {}
    }
    stopActiveStream();
    transcriptRef.current = '';
    setValue('');
    showToast('info', 'Voice input cancelled.');
  };

  // ── Finish & Send Voice Input ─────
  const stopAndSendVoiceInput = () => {
    clearAutoSendTimer();
    setIsListening(false);
    if ((window as any)._activeRecognition) {
      try { (window as any)._activeRecognition.stop(); } catch {}
      (window as any)._activeRecognition = null;
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
    } else {
      showToast('info', 'No speech detected.');
    }
  };

  // ── Toggle Voice Input (Start or Finish) ─────
  const toggleVoiceInput = () => {
    clearAutoSendTimer();
    if (isListening) {
      stopAndSendVoiceInput();
      return;
    }

    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    // ── Strategy A: Native Web Speech API ─────
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
          showToast('info', '🎙️ Listening... Speak now');
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
          if (err.error !== 'aborted') {
            setIsListening(false);
            try { (window as any)._activeRecognition?.stop(); } catch {}
            (window as any)._activeRecognition = null;
            startMediaRecorderFallback();
          }
        };

        recognition.onend = () => {
          setIsListening(false);
          const finalSpeech = transcriptRef.current.trim() || value.trim();
          if (finalSpeech) {
            setValue(finalSpeech);
            showToast('info', 'Voice captured! Auto-sending in 5s — tap X to cancel.', 'reminder');
            clearAutoSendTimer();
            autoSendTimerRef.current = setTimeout(() => {
              const currentVal = transcriptRef.current.trim() || value.trim() || finalSpeech;
              if (currentVal) {
                onSend(currentVal, true);
                setValue('');
                transcriptRef.current = '';
                if (textareaRef.current) textareaRef.current.style.height = 'auto';
              }
            }, 5000);
          } else {
            // If Web Speech yielded no text, try MediaRecorder fallback
            startMediaRecorderFallback();
          }
        };

        recognition.start();
        return;
      } catch (err) {
        console.warn('SpeechRecognition failed to start, falling back to MediaRecorder:', err);
      }
    }

    // ── Strategy B: MediaRecorder + Backend STT Whisper Fallback ─────
    startMediaRecorderFallback();
  };

  const startMediaRecorderFallback = async () => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      showToast('error', 'Microphone is not supported on this browser.');
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      activeStreamRef.current = stream;
      audioChunksRef.current = [];

      const supportedMime = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/mp4',
        'audio/aac',
        'audio/ogg'
      ].find(type => typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported(type)) || '';

      const mediaRecorder = supportedMime
        ? new MediaRecorder(stream, { mimeType: supportedMime })
        : new MediaRecorder(stream);

      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        stopActiveStream();
        setIsListening(false);

        const existingVal = value.trim();
        if (existingVal) {
          showToast('info', 'Voice captured! Tap check to send or X to cancel.');
          return;
        }

        if (audioChunksRef.current.length > 0) {
          showToast('info', 'Transcribing speech audio...');
          try {
            const actualType = mediaRecorder.mimeType || supportedMime || 'audio/mp4';
            const ext = actualType.includes('webm') ? 'webm' : actualType.includes('mp4') ? 'mp4' : actualType.includes('aac') ? 'aac' : 'm4a';
            const blob = new Blob(audioChunksRef.current, { type: actualType });
            const formData = new FormData();
            formData.append('file', blob, `voice_${Date.now()}.${ext}`);

            // Primary active backend endpoint & relative fallback
            const sttEndpoints = [
              '/api/stt',
              'https://mitra-backend-q1f3.onrender.com/api/stt',
              'https://ai-assistant-backend-8hur.onrender.com/api/stt'
            ];

            let data: any = null;
            let success = false;

            for (const endpoint of sttEndpoints) {
              try {
                const response = await fetch(endpoint, {
                  method: 'POST',
                  body: formData,
                });
                if (response.ok) {
                  data = await response.json();
                  success = true;
                  break;
                }
              } catch (e) {
                console.warn(`STT endpoint ${endpoint} failed, trying next fallback...`);
              }
            }

            if (success && data && data.text && data.text.trim()) {
              const transcribedText = data.text.trim();
              setValue(transcribedText);
              transcriptRef.current = transcribedText;
              showToast('info', 'Voice transcribed! Auto-sending in 5s — tap X to cancel.', 'reminder');
              clearAutoSendTimer();
              autoSendTimerRef.current = setTimeout(() => {
                const currentVal = transcriptRef.current.trim() || value.trim() || transcribedText;
                if (currentVal) {
                  onSend(currentVal, true);
                  setValue('');
                  transcriptRef.current = '';
                  if (textareaRef.current) textareaRef.current.style.height = 'auto';
                }
              }, 5000);
            } else {
              showToast('error', 'Could not transcribe speech. Please speak clearly and try again.');
            }
          } catch (err) {
            console.warn('STT API request failed:', err);
            showToast('error', 'Speech transcription service unavailable.');
          }
        }
      };

      mediaRecorder.start(250);
      setIsListening(true);
      showToast('info', '🎙️ Recording voice... Speak now');
    } catch (err: any) {
      stopActiveStream();
      setIsListening(false);
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        showToast('error', 'Microphone permission denied in browser settings.');
      } else {
        showToast('error', 'Could not start audio recorder on this device.');
      }
    }
  };

  return (
    <div className="zone-input bg-surface-raised border-t border-border-subtle px-3 sm:px-4 py-2 sm:py-2.5 flex flex-col gap-1.5 sm:gap-2">
      {/* Quick actions */}
      {showQuick && !value && !isListening && (
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
      <div className="flex items-center gap-1.5 sm:gap-2">
        {/* Quick action toggle */}
        {!isListening && (
          <button
            onClick={() => setShowQuick(!showQuick)}
            className={cn(
              'flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-lg transition-colors',
              showQuick ? 'bg-brand-muted text-brand-light' : 'text-text-muted hover:text-text-secondary hover:bg-surface-overlay',
            )}
            aria-label="Quick actions"
            title="Quick prompts"
          >
            <Zap size={14} />
          </button>
        )}

        {/* Textarea wrapper */}
        <div className="flex-1 relative min-w-0 flex items-center">
          <textarea
            ref={textareaRef}
            rows={1}
            value={value}
            onChange={handleChange}
            onKeyDown={handleKey}
            placeholder={isListening ? 'Listening... Speak into your mic' : disabled ? 'Processing...' : 'Ask Mitra anything...'}
            disabled={disabled || isThinking}
            className={cn(
              'w-full bg-surface-overlay text-text-primary text-xs sm:text-sm rounded-lg px-3 py-2 border transition-colors resize-none overflow-y-auto leading-relaxed placeholder:text-text-muted/60',
              isListening ? 'border-red-500/60 bg-red-500/5 text-red-300 animate-pulse' : 'border-border-subtle focus:outline-none focus:border-brand/50',
            )}
            style={{ maxHeight: isMobile ? '100px' : '120px' }}
          />
        </div>

        {/* Attach file (desktop) */}
        {!isListening && (
          <button
            id="inputbar-attach"
            className="flex-shrink-0 w-8 h-8 items-center justify-center rounded-lg text-text-muted hover:text-text-secondary hover:bg-surface-overlay transition-colors hidden sm:flex"
            aria-label="Attach file"
          >
            <Paperclip size={14} />
          </button>
        )}

        {/* Live Audio Waveform Animation when recording */}
        {isListening && (
          <div className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-red-500/15 border border-red-500/30 flex-shrink-0">
            <span className="w-1 h-3 bg-red-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
            <span className="w-1 h-4 bg-red-500 rounded-full animate-bounce [animation-delay:-0.15s]" />
            <span className="w-1 h-5 bg-red-400 rounded-full animate-bounce" />
            <span className="w-1 h-3 bg-red-500 rounded-full animate-bounce [animation-delay:-0.2s]" />
            <span className="w-1 h-4 bg-red-400 rounded-full animate-bounce [animation-delay:-0.4s]" />
          </div>
        )}

        {/* Listening / Recorded Controls: Cancel (X) & Finish (Check) */}
        {isListening || value.trim() ? (
          <div className="flex items-center gap-1 flex-shrink-0">
            {/* Cancel Button */}
            <button
              type="button"
              onClick={cancelVoiceInput}
              className="w-8 h-8 flex items-center justify-center rounded-lg bg-red-500/20 text-red-400 border border-red-500/40 hover:bg-red-500/30 transition-colors cursor-pointer"
              title="Cancel & clear text"
              aria-label="Cancel & clear text"
            >
              <X size={14} />
            </button>
            {/* Send / Stop Button */}
            <button
              type="button"
              onClick={stopAndSendVoiceInput}
              className="w-8 h-8 flex items-center justify-center rounded-lg bg-green-500/20 text-green-400 border border-green-500/40 hover:bg-green-500/30 transition-colors cursor-pointer"
              title="Finish and send voice message"
              aria-label="Finish and send voice message"
            >
              <Check size={14} />
            </button>
          </div>
        ) : (
          /* Mic Button */
          <button
            id="inputbar-voice"
            onClick={toggleVoiceInput}
            className="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-lg text-text-muted hover:text-brand-light hover:bg-brand-muted transition-colors cursor-pointer"
            aria-label="Voice input"
            title="Click to speak (Voice STT)"
          >
            <Mic size={14} />
          </button>
        )}

        {/* Send Button */}
        {!isListening && (
          <button
            id="inputbar-send"
            onClick={handleSend}
            disabled={!value.trim() || disabled || isThinking}
            className={cn(
              'flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-lg transition-all duration-150 active:scale-95',
              value.trim() && !disabled && !isThinking
                ? 'bg-brand text-white hover:bg-brand-light shadow-glow-sm cursor-pointer'
                : 'bg-surface-overlay text-text-muted cursor-not-allowed',
            )}
            aria-label="Send message"
          >
            <Send size={13} />
          </button>
        )}
      </div>

      {/* Hint — only on desktop */}
      <div className="flex items-center justify-between text-2xs text-text-muted hidden md:flex px-1">
        <span>
          Press <kbd className="px-1 py-0.5 bg-surface-overlay border border-border-subtle rounded text-2xs">Enter</kbd> to send · <kbd className="px-1 py-0.5 bg-surface-overlay border border-border-subtle rounded text-2xs">Shift+Enter</kbd> for line break
        </span>
        <span className="flex items-center gap-1 opacity-70">
          <span>Press</span>
          <kbd className="px-1 py-0.5 bg-surface-overlay border border-border-subtle rounded text-2xs">Ctrl + K</kbd>
          <span>for Command Palette</span>
        </span>
      </div>
    </div>
  );
};

export default InputBar;
