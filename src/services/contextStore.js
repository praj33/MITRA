import { eventBus } from './eventBus.js';

/**
 * ContextStore — localStorage-backed companion state with v5 session support.
 */
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
        const parsed = JSON.parse(stored);
        return {
          history: [],
          dockMode: 'floating',
          replays: [],
          avatar: null,
          position: null,
          sessionId: null,
          userId: null,
          windowState: 'minimized',
          ...parsed
        };
      }
    } catch (e) {
      console.warn('[MITRA] Failed to load context from localStorage', e);
    }
    return {
      history: [],
      dockMode: 'floating',
      replays: [],
      avatar: null,
      position: null,
      sessionId: null,
      userId: null,
      windowState: 'minimized',
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

  // ─── Reset / Clear Methods ──────────────────────────────────────────────────

  clearHistory() {
    this.state.history = [];
    this.saveState();
    eventBus.emit('context.cleared', { type: 'history' });
  }

  resetAll() {
    this.state = {
      history: [],
      dockMode: 'floating',
      replays: [],
      avatar: null,
      position: null,
      sessionId: null,
      userId: null,
    };
    try {
      localStorage.removeItem(this.storageKey);
    } catch (e) {
      // Non-fatal
    }
    eventBus.emit('context.cleared', { type: 'all' });
  }

  // ─── v5 Session & User ID ───────────────────────────────────────────────────

  setSessionId(id) {
    this.state.sessionId = id || null;
    this.saveState();
  }

  getSessionId() {
    return this.state.sessionId || null;
  }

  setUserId(id) {
    this.state.userId = id || null;
    this.saveState();
  }

  getUserId() {
    return this.state.userId
      || localStorage.getItem('mitra_user_id')
      || this._parseUserIdFromToken()
      || null;
  }

  _parseUserIdFromToken() {
    try {
      const token = localStorage.getItem('authToken') || localStorage.getItem('token');
      if (!token) return null;
      const payloadB64 = token.split('.')[1];
      if (!payloadB64) return null;
      const payload = JSON.parse(atob(payloadB64));
      return payload.sub || payload.id || payload.user_id || null;
    } catch {
      return null;
    }
  }

  // ─── History ────────────────────────────────────────────────────────────────

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

  // ─── Replays ────────────────────────────────────────────────────────────────

  addReplay(replayItem) {
    if (!this.state.replays) this.state.replays = [];
    this.state.replays.push(replayItem);
    this.saveState();
    eventBus.emit('replay.generated', replayItem);
  }

  getReplays() {
    return this.state.replays || [];
  }

  // ─── Dock Mode ──────────────────────────────────────────────────────────────

  setDockMode(mode) {
    if (!mode) return;
    const validMode = (mode === 'left' || mode === 'right' || mode === 'floating') ? mode : 'floating';
    this.state.dockMode = validMode;
    this.saveState();
  }

  getDockMode() {
    return this.state.dockMode || 'floating';
  }

  // ─── Avatar ─────────────────────────────────────────────────────────────────

  setAvatar(avatarDataUrl) {
    this.state.avatar = avatarDataUrl;
    this.saveState();
    eventBus.emit('avatar.changed', { avatar: avatarDataUrl });
  }

  getAvatar() {
    return this.state.avatar || null;
  }

  // ─── Window State ────────────────────────────────────────────────────────────

  setWindowState(state) {
    if (!state) return;
    this.state.windowState = state === 'expanded' ? 'expanded' : 'minimized';
    this.saveState();
  }

  getWindowState() {
    return this.state.windowState || 'minimized';
  }

  // ─── Position ───────────────────────────────────────────────────────────────

  setPosition(position) {
    if (!position || position.left == null || position.top == null) return;
    this.state.position = position;
    this.saveState();
    eventBus.emit('position.changed', { position });
  }

  getPosition() {
    return this.state.position || null;
  }
}

export const contextStore = new ContextStore();
