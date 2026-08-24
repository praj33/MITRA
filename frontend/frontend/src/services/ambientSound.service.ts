/**
 * Web Audio API Ambient Sound Synthesizer
 * Generates procedural relaxation/focus soundscapes without external MP3 assets.
 */

let audioCtx: AudioContext | null = null;
let currentSourceNode: AudioNode | null = null;
let gainNode: GainNode | null = null;
let isPlaying = false;
let currentSoundId: string | null = null;

const getAudioContext = (): AudioContext => {
  if (!audioCtx) {
    const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
    audioCtx = new AudioContextClass();
  }
  if (audioCtx.state === 'suspended') {
    audioCtx.resume();
  }
  return audioCtx;
};

export const AmbientSoundService = {
  play(soundId: string, volume = 0.5) {
    this.stop();
    const ctx = getAudioContext();
    gainNode = ctx.createGain();
    gainNode.gain.setValueAtTime(volume, ctx.currentTime);
    gainNode.connect(ctx.destination);

    const bufferSize = 2 * ctx.sampleRate;
    const noiseBuffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
    const output = noiseBuffer.getChannelData(0);

    if (soundId === 'rain') {
      // Pink noise + lowpass
      let b0 = 0, b1 = 0, b2 = 0, b3 = 0, b4 = 0, b5 = 0, b6 = 0;
      for (let i = 0; i < bufferSize; i++) {
        const white = Math.random() * 2 - 1;
        b0 = 0.99886 * b0 + white * 0.0555179;
        b1 = 0.99332 * b1 + white * 0.0750759;
        b2 = 0.96900 * b2 + white * 0.1538520;
        b3 = 0.86650 * b3 + white * 0.3104856;
        b4 = 0.55000 * b4 + white * 0.5329522;
        b5 = -0.7616 * b5 - white * 0.0168980;
        output[i] = b0 + b1 + b2 + b3 + b4 + b5 + b6 + white * 0.5362;
        output[i] *= 0.11;
        b6 = white * 0.115926;
      }
    } else if (soundId === 'space') {
      // Brown noise (Deep Space)
      let lastOut = 0.0;
      for (let i = 0; i < bufferSize; i++) {
        const white = Math.random() * 2 - 1;
        output[i] = (lastOut + (0.02 * white)) / 1.02;
        lastOut = output[i];
        output[i] *= 3.5;
      }
    } else {
      // Soft White Noise
      for (let i = 0; i < bufferSize; i++) {
        output[i] = (Math.random() * 2 - 1) * 0.15;
      }
    }

    const whiteNoiseNode = ctx.createBufferSource();
    whiteNoiseNode.buffer = noiseBuffer;
    whiteNoiseNode.loop = true;

    // Filter node for extra smoothness
    const filter = ctx.createBiquadFilter();
    filter.type = soundId === 'space' ? 'lowpass' : 'bandpass';
    filter.frequency.value = soundId === 'space' ? 180 : 800;

    whiteNoiseNode.connect(filter);
    filter.connect(gainNode);

    whiteNoiseNode.start();
    currentSourceNode = whiteNoiseNode;
    isPlaying = true;
    currentSoundId = soundId;
  },

  setVolume(volume: number) {
    if (gainNode && audioCtx) {
      gainNode.gain.setValueAtTime(volume, audioCtx.currentTime);
    }
  },

  stop() {
    if (currentSourceNode) {
      try {
        (currentSourceNode as any).stop();
        currentSourceNode.disconnect();
      } catch (e) {}
      currentSourceNode = null;
    }
    isPlaying = false;
    currentSoundId = null;
  },

  isPlaying() {
    return isPlaying;
  },

  getCurrentSound() {
    return currentSoundId;
  }
};
