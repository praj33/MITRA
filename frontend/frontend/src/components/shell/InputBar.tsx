// components/shell/InputBar.tsx — Message input with send + voice + attach (responsive)
import React, { useState, useRef, KeyboardEvent } from 'react';
import { motion } from 'framer-motion';
import { Send, Mic, MicOff, Paperclip, Zap } from 'lucide-react';
import { cn } from '../../lib/utils';
import { useCompanionStore } from '../../store/companion.store';

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

  const startMediaRecorderFallback = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach(t => t.stop());
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        try {
          const formData = new FormData();
          formData.append('file', audioBlob, 'voice.webm');
          const res = await fetch('https://ai-assistant-backend-8hur.onrender.com/api/stt', {
            method: 'POST',
            body: formData,
          });
          const data = await res.json();
          if (data.text) {
            onSend(data.text, true);
          } else {
            onSend('Voice message captured', true);
          }
        } catch {
          onSend('Voice message captured', true);
        }
      };

      mediaRecorder.start();
      setIsListening(true);
    } catch (err) {
      console.error('MediaRecorder fallback error:', err);
      alert('Unable to access microphone on this device.');
    }
  };

  const toggleVoiceInput = async () => {
    if (isListening) {
      setIsListening(false);
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
      }
      return;
    }

    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    // Test microphone permission & immediately release stream so mic track is unlocked
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      try {
        const testStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        testStream.getTracks().forEach(t => t.stop());
      } catch (err) {
        console.warn('Microphone permission denied:', err);
        alert('Microphone access is required for voice input. Please enable microphone permissions in your browser settings.');
        return;
      }
    }

    if (SR) {
      try {
        transcriptRef.current = '';
        const recognition = new SR();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onstart = () => setIsListening(true);
        recognition.onresult = (event: any) => {
          const transcript = Array.from(event.results)
            .map((r: any) => r[0].transcript)
            .join('');
          transcriptRef.current = transcript;
          setValue(transcript);
        };
        recognition.onerror = (err: any) => {
          console.warn('Speech recognition error on mobile:', err);
          setIsListening(false);
          startMediaRecorderFallback();
        };
        recognition.onend = () => {
          setIsListening(false);
          const finalSpeech = transcriptRef.current.trim();
          if (finalSpeech) {
            onSend(finalSpeech, true);
            setValue('');
            if (textareaRef.current) textareaRef.current.style.height = 'auto';
          }
        };
        recognition.start();
        return;
      } catch (err) {
        console.warn('Failed to start speech recognition, using MediaRecorder fallback:', err);
      }
    }

    startMediaRecorderFallback();
  };

  return (
    <div className="zone-input bg-surface-raised border-t border-border-subtle px-3 sm:px-4 py-2 sm:py-2.5 flex flex-col gap-1.5 sm:gap-2">
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
