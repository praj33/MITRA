export class Header {
  constructor(onMinimize, onDock) {
    this.element = document.createElement('div');
    this.element.className = 'mitra-header';

    this.element.innerHTML = `
      <div class="mitra-title">
        <div class="mitra-status-dot"></div>
        MITRA
      </div>
      <div class="mitra-controls">
        <button class="mitra-btn" id="btn-dock" title="Dock">
          <svg viewBox="0 0 24 24"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14zm-7-2h5v-5h-2v3h-3v2z"/></svg>
        </button>
        <button class="mitra-btn" id="btn-minimize" title="Minimize">
          <svg viewBox="0 0 24 24"><path d="M19 13H5v-2h14v2z"/></svg>
        </button>
      </div>
    `;

    this.element.querySelector('#btn-minimize').addEventListener('click', () => {
      if (onMinimize) onMinimize();
    });

    this.element.querySelector('#btn-dock').addEventListener('click', () => {
      if (onDock) onDock();
    });
  }
}
