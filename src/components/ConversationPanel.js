export class ConversationPanel {
  constructor(eventBus, contextStore) {
    this.element = document.createElement('div');
    this.element.className = 'mitra-chat';
    this.element.id = 'chat-container';
    
    // Load existing history
    const history = contextStore.getHistory();
    if (history && history.length > 0) {
      history.forEach(msg => {
        if (msg.role === 'user') this.addUserMessage(msg.text, new Date(msg.timestamp));
        else if (msg.role === 'mitra') this.addMitraMessage(msg.text, new Date(msg.timestamp));
      });
    } else {
      this.addMitraMessage("Hello. I am MITRA, your Universal Companion across the BHIV ecosystem. How can I assist you today?", new Date());
    }

    if (eventBus) {
      eventBus.on('notification.received', (data) => {
        if (data.role === 'mitra') {
          this.addMitraMessage(data.text, new Date());
        } else {
          this.addSystemMessage(data.text);
        }
      });
      eventBus.on('capability.finished', (data) => {
        this.addSystemMessage(`<i>Capability ${data.capability} completed</i>`);
      });
    }
  }

  addUserMessage(text, date = new Date()) {
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble user';
    bubble.innerHTML = `${text}<div class="chat-timestamp">${date.toLocaleTimeString()}</div>`;
    this.element.appendChild(bubble);
    this.scrollToBottom();
  }

  addMitraMessage(text, date = new Date()) {
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble mitra';
    bubble.innerHTML = `${text}<div class="chat-timestamp">${date.toLocaleTimeString()}</div>`;
    this.element.appendChild(bubble);
    this.scrollToBottom();
  }

  addSystemMessage(html) {
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble user';
    bubble.style.opacity = '0.7';
    bubble.style.fontSize = '12px';
    bubble.innerHTML = html;
    this.element.appendChild(bubble);
    this.scrollToBottom();
  }

  scrollToBottom() {
    this.element.scrollTop = this.element.scrollHeight;
  }
}
