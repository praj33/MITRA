import { eventBus } from './eventBus.js';

export class ContextStore {
  constructor() {
    this.storageKey = 'mitra_context_store';
    this.state = this.loadState();
    
    eventBus.on('context.updated', (newState) => {
      this.state = { ...this.state, ...newState };
      this.saveState();
    });
  }

  loadState() {
    try {
      const stored = localStorage.getItem(this.storageKey);
      if (stored) {
        return JSON.parse(stored);
      }
    } catch (e) {
      console.warn('[MITRA] Failed to load context from localStorage', e);
    }
    return {
      history: [],
      dockMode: 'floating',
      replays: []
    };
  }

  saveState() {
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(this.state));
      eventBus.emit('context.saved', { timestamp: new Date().toISOString() });
    } catch (e) {
      console.warn('[MITRA] Failed to save context to localStorage', e);
    }
  }

  addMessage(role, text, metadata = {}) {
    this.state.history.push({
      role,
      text,
      timestamp: new Date().toISOString(),
      ...metadata
    });
    this.saveState();
  }

  getHistory() {
    return this.state.history || [];
  }

  addReplay(replayItem) {
    if (!this.state.replays) this.state.replays = [];
    this.state.replays.push(replayItem);
    this.saveState();
    eventBus.emit('replay.generated', replayItem);
  }

  getReplays() {
    return this.state.replays || [];
  }

  setDockMode(mode) {
    this.state.dockMode = mode;
    this.saveState();
  }

  getDockMode() {
    return this.state.dockMode || 'floating';
  }
}

export const contextStore = new ContextStore();
