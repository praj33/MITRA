export class Footer {
  constructor(onSend, onOpenCapabilities) {
    this.element = document.createElement('div');
    this.element.className = 'mitra-input-area';

    this.element.innerHTML = `
      <button class="mitra-btn" id="btn-open-launcher" title="Capabilities">
        <svg viewBox="0 0 24 24"><path d="M4 8h4V4H4v4zm6 12h4v-4h-4v4zm-6 0h4v-4H4v4zm0-6h4v-4H4v4zm6 0h4v-4h-4v4zm6-10v4h4V4h-4zm-6 4h4V4h-4v4zm6 6h4v-4h-4v4zm0 6h4v-4h-4v4z"/></svg>
      </button>
      <input type="text" class="mitra-input" id="chat-input" placeholder="Message MITRA or use /capabilities..." />
      <button class="mitra-send" id="btn-send">
        <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
      </button>
    `;

    const input = this.element.querySelector('#chat-input');
    const btnSend = this.element.querySelector('#btn-send');
    const btnOpenLauncher = this.element.querySelector('#btn-open-launcher');

    const triggerSend = () => {
      const text = input.value.trim();
      if (text) {
        if (onSend) onSend(text);
        input.value = '';
      }
    };

    btnSend.addEventListener('click', triggerSend);
    input.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') triggerSend();
    });

    btnOpenLauncher.addEventListener('click', () => {
      if (onOpenCapabilities) onOpenCapabilities();
    });
  }
}
