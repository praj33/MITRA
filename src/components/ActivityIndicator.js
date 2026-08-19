export class ActivityIndicator {
  constructor(eventBus) {
    this.element = document.createElement('div');
    this.element.className = 'mitra-activity-indicator';
    this.element.innerHTML = `
      <div class="indicator-dot"></div>
      <span class="indicator-text">Idle</span>
    `;
    this.textEl = this.element.querySelector('.indicator-text');
    this.dotEl = this.element.querySelector('.indicator-dot');

    if (eventBus) {
      eventBus.on('capability.started', (data) => this.setStatus('Running Capability', 'running'));
      eventBus.on('capability.finished', () => this.setStatus('Completed', 'completed'));
      eventBus.on('capability.failed', () => this.setStatus('Failed', 'failed'));
      eventBus.on('runtime.thinking', () => this.setStatus('Thinking', 'thinking'));
      eventBus.on('runtime.idle', () => this.setStatus('Idle', 'idle'));
    }
  }

  setStatus(text, stateClass) {
    this.textEl.textContent = text;
    this.dotEl.className = `indicator-dot ${stateClass}`;
    
    if (stateClass === 'completed' || stateClass === 'failed') {
      setTimeout(() => this.setStatus('Idle', 'idle'), 3000);
    }
  }
}
