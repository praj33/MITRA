export class CapabilityLauncher {
  constructor(onClose, onCapabilitySelected) {
    this.element = document.createElement('div');
    this.element.className = 'mitra-launcher';
    this.element.id = 'launcher';

    const capabilities = [
      { id: 'analyze', name: 'Analyze' },
      { id: 'ocr', name: 'OCR' },
      { id: 'translate', name: 'Translate' },
      { id: 'summarize', name: 'Summarize' },
      { id: 'image', name: 'Image' },
      { id: 'pdf', name: 'PDF' },
      { id: 'replay', name: 'Replay' },
      { id: 'health', name: 'Health' },
      { id: 'settings', name: 'Settings' }
    ];

    const gridHtml = capabilities.map(cap => `
      <div class="capability-card" data-capability="${cap.id}">
        <div class="capability-icon">
          <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/></svg>
        </div>
        <div class="capability-title">${cap.name}</div>
      </div>
    `).join('');

    this.element.innerHTML = `
      <div class="launcher-header">
        Capabilities
        <button class="mitra-btn" id="btn-close-launcher">
          <svg viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
        </button>
      </div>
      <div class="launcher-grid">
        ${gridHtml}
      </div>
    `;

    this.element.querySelector('#btn-close-launcher').addEventListener('click', () => {
      this.close();
      if (onClose) onClose();
    });

    const caps = this.element.querySelectorAll('.capability-card');
    caps.forEach(card => {
      card.addEventListener('click', (e) => {
        const capability = e.currentTarget.getAttribute('data-capability');
        if (onCapabilitySelected) onCapabilitySelected(capability);
        this.close();
      });
    });
  }

  open() {
    this.element.classList.add('active');
  }

  close() {
    this.element.classList.remove('active');
  }
}
