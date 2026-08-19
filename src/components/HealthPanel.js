export class HealthPanel {
  constructor(eventBus) {
    this.element = document.createElement('div');
    this.element.className = 'mitra-health-panel';
    this.element.style.display = 'none';

    this.element.innerHTML = `
      <div class="health-header">Runtime Health</div>
      <div class="health-stats">
        <div class="stat-row">
          <span>Status</span>
          <span id="health-status" class="status-indicator yellow">Connecting</span>
        </div>
        <div class="stat-row">
          <span>Latency</span>
          <span id="health-latency">-- ms</span>
        </div>
        <div class="stat-row">
          <span>Version</span>
          <span>v1.2.0-beta</span>
        </div>
        <div class="stat-row">
          <span>Last Sync</span>
          <span id="health-sync">Never</span>
        </div>
      </div>
    `;

    this.statusEl = this.element.querySelector('#health-status');
    this.latencyEl = this.element.querySelector('#health-latency');
    this.syncEl = this.element.querySelector('#health-sync');

    if (eventBus) {
      eventBus.on('health.changed', (data) => {
        this.updateHealth(data);
      });
    }
  }

  updateHealth(data) {
    if (data.status) {
      this.statusEl.className = `status-indicator ${data.status}`;
      this.statusEl.textContent = data.status.charAt(0).toUpperCase() + data.status.slice(1);
    }
    if (data.latency) this.latencyEl.textContent = data.latency;
    
    const now = new Date();
    this.syncEl.textContent = now.toLocaleTimeString();
  }

  toggle() {
    if (this.element.style.display === 'none') {
      this.element.style.display = 'block';
    } else {
      this.element.style.display = 'none';
    }
  }
}
