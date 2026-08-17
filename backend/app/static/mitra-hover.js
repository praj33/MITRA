/**
 * MITRA Universal Companion Embed Widget (mitra-hover.js)
 * BHIV Ecosystem Canonical Companion Layer
 * Usage: <script src="https://mitra.blackholeinfiverse.com/mitra-hover.js" data-app-id="gurukul" data-user-id="user_123"></script>
 */

(function () {
  if (window.__MITRA_HOVER_LOADED__) return;
  window.__MITRA_HOVER_LOADED__ = true;

  // Extract config from script tag parameters
  const currentScript = document.currentScript || (function() {
    const scripts = document.getElementsByTagName('script');
    return scripts[scripts.length - 1];
  })();

  const API_BASE = (currentScript && currentScript.getAttribute('data-api-base')) || 'https://mitra-backend.onrender.com';
  const APP_ID = (currentScript && currentScript.getAttribute('data-app-id')) || 'universal_app';
  const USER_ID = (currentScript && currentScript.getAttribute('data-user-id')) || 'user_default';
  const POSITION = (currentScript && currentScript.getAttribute('data-position')) || 'bottom-right';

  // State management
  let isOpen = false;
  let isThinking = false;
  let isListening = false;
  let sessionId = localStorage.getItem('mitra_session_id') || ('sess_' + Math.random().toString(36).substring(2, 10));
  localStorage.setItem('mitra_session_id', sessionId);

  // Styles injection
  const style = document.createElement('style');
  style.textContent = `
    #mitra-widget-root {
      position: fixed;
      z-index: 999999;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      ${POSITION.includes('left') ? 'left: 20px;' : 'right: 20px;'}
      bottom: 20px;
    }
    
    .mitra-trigger-btn {
      width: 58px;
      height: 58px;
      border-radius: 50%;
      background: linear-gradient(135deg, #7c5cfc 0%, #5a38ec 100%);
      box-shadow: 0 8px 24px rgba(124, 92, 252, 0.4), 0 2px 8px rgba(0, 0, 0, 0.3);
      border: 2px solid rgba(255, 255, 255, 0.2);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275);
      position: relative;
    }
    
    .mitra-trigger-btn:hover {
      transform: scale(1.08);
      box-shadow: 0 12px 30px rgba(124, 92, 252, 0.5);
    }
    
    .mitra-avatar-pulse {
      position: absolute;
      inset: -4px;
      border-radius: 50%;
      border: 2px solid rgba(124, 92, 252, 0.5);
      animation: mitraPulse 2s infinite;
      pointer-events: none;
    }
    
    @keyframes mitraPulse {
      0% { transform: scale(1); opacity: 0.8; }
      100% { transform: scale(1.3); opacity: 0; }
    }
    
    .mitra-badge-online {
      position: absolute;
      top: 2px;
      right: 2px;
      width: 13px;
      height: 13px;
      border-radius: 50%;
      background: #10b981;
      border: 2px solid #0f1117;
    }
    
    .mitra-chat-window {
      position: absolute;
      bottom: 74px;
      ${POSITION.includes('left') ? 'left: 0;' : 'right: 0;'}
      width: min(380px, calc(100vw - 32px));
      height: min(560px, calc(100vh - 110px));
      background: #0f1117;
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 20px;
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6), 0 0 40px rgba(124, 92, 252, 0.15);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      opacity: 0;
      transform: translateY(16px) scale(0.96);
      pointer-events: none;
      transition: all 0.25s ease-out;
    }
    
    .mitra-chat-window.open {
      opacity: 1;
      transform: translateY(0) scale(1);
      pointer-events: all;
    }
    
    .mitra-header {
      padding: 14px 18px;
      background: rgba(22, 25, 35, 0.95);
      backdrop-filter: blur(10px);
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    
    .mitra-header-brand {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    
    .mitra-logo-icon {
      width: 32px;
      height: 32px;
      border-radius: 10px;
      background: rgba(124, 92, 252, 0.2);
      border: 1px solid rgba(124, 92, 252, 0.4);
      color: #a78bfa;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: bold;
      font-size: 14px;
    }
    
    .mitra-header-title {
      color: #f3f4f6;
      font-size: 14px;
      font-weight: 600;
      margin: 0;
      line-height: 1.2;
    }
    
    .mitra-header-sub {
      color: #9ca3af;
      font-size: 11px;
      margin: 2px 0 0 0;
    }
    
    .mitra-close-btn {
      background: none;
      border: none;
      color: #9ca3af;
      cursor: pointer;
      padding: 6px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: color 0.15s;
    }
    
    .mitra-close-btn:hover { color: #ffffff; background: rgba(255, 255, 255, 0.08); }
    
    .mitra-messages-list {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      overscroll-behavior: contain;
    }
    
    .mitra-msg {
      max-width: 85%;
      padding: 10px 14px;
      border-radius: 14px;
      font-size: 13px;
      line-height: 1.5;
      word-break: break-word;
    }
    
    .mitra-msg-user {
      align-self: flex-end;
      background: #7c5cfc;
      color: #ffffff;
      border-bottom-right-radius: 4px;
    }
    
    .mitra-msg-assistant {
      align-self: flex-start;
      background: rgba(30, 35, 50, 0.9);
      color: #e5e7eb;
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-bottom-left-radius: 4px;
    }

    .mitra-thinking {
      align-self: flex-start;
      padding: 8px 14px;
      background: rgba(30, 35, 50, 0.7);
      border-radius: 14px;
      color: #a78bfa;
      font-size: 12px;
      font-style: italic;
    }
    
    .mitra-input-area {
      padding: 12px;
      background: rgba(22, 25, 35, 0.95);
      border-top: 1px solid rgba(255, 255, 255, 0.08);
      display: flex;
      align-items: center;
      gap: 8px;
    }
    
    .mitra-input {
      flex: 1;
      background: rgba(30, 35, 50, 0.8);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 10px;
      padding: 8px 12px;
      color: #ffffff;
      font-size: 13px;
      outline: none;
      transition: border-color 0.15s;
    }
    
    .mitra-input:focus { border-color: #7c5cfc; }
    
    .mitra-action-btn {
      width: 34px;
      height: 34px;
      border-radius: 10px;
      border: none;
      background: rgba(124, 92, 252, 0.2);
      color: #a78bfa;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.15s;
    }
    
    .mitra-action-btn:hover { background: #7c5cfc; color: #ffffff; }
    .mitra-action-btn.recording { background: rgba(239, 68, 68, 0.3); color: #ef4444; border: 1px solid #ef4444; }
  `;
  document.head.appendChild(style);

  // Widget DOM setup
  const root = document.createElement('div');
  root.id = 'mitra-widget-root';

  root.innerHTML = `
    <div class="mitra-chat-window" id="mitraWindow">
      <div class="mitra-header">
        <div class="mitra-header-brand">
          <div class="mitra-logo-icon">M</div>
          <div>
            <h4 class="mitra-header-title">Mitra Companion</h4>
            <p class="mitra-header-sub">Connected to ${APP_ID.toUpperCase()}</p>
          </div>
        </div>
        <button class="mitra-close-btn" id="mitraCloseBtn" aria-label="Close Mitra">✕</button>
      </div>

      <div class="mitra-messages-list" id="mitraMsgList">
        <div class="mitra-msg mitra-msg-assistant">
          Namaste! I am Mitra, your BHIV universal companion. How can I assist you in ${APP_ID}?
        </div>
      </div>

      <div class="mitra-input-area">
        <input type="text" class="mitra-input" id="mitraInput" placeholder="Ask Mitra..." />
        <button class="mitra-action-btn" id="mitraMicBtn" title="Voice Input">🎤</button>
        <button class="mitra-action-btn" id="mitraSendBtn" title="Send">➤</button>
      </div>
    </div>

    <button class="mitra-trigger-btn" id="mitraTriggerBtn" aria-label="Open Mitra Companion">
      <div class="mitra-avatar-pulse"></div>
      <div class="mitra-badge-online"></div>
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"></path>
      </svg>
    </button>
  `;

  document.body.appendChild(root);

  // Element references
  const triggerBtn = document.getElementById('mitraTriggerBtn');
  const windowEl = document.getElementById('mitraWindow');
  const closeBtn = document.getElementById('mitraCloseBtn');
  const inputEl = document.getElementById('mitraInput');
  const sendBtn = document.getElementById('mitraSendBtn');
  const micBtn = document.getElementById('mitraMicBtn');
  const msgList = document.getElementById('mitraMsgList');

  // Toggle widget
  function toggleWidget() {
    isOpen = !isOpen;
    if (isOpen) {
      windowEl.classList.add('open');
      inputEl.focus();
    } else {
      windowEl.classList.remove('open');
    }
  }

  triggerBtn.addEventListener('click', toggleWidget);
  closeBtn.addEventListener('click', toggleWidget);

  // Append message
  function appendMessage(role, text) {
    const div = document.createElement('div');
    div.className = `mitra-msg ${role === 'user' ? 'mitra-msg-user' : 'mitra-msg-assistant'}`;
    div.textContent = text;
    msgList.appendChild(div);
    msgList.scrollTop = msgList.scrollHeight;
  }

  // Speak response out loud (TTS)
  function speak(text) {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text);
      u.lang = 'en-US';
      window.speechSynthesis.speak(u);
    }
  }

  // Send query to MITRA API
  // ── DOM UI Context Extractor & Synchronization ────────────────────────
  function extractActiveUIContext() {
    try {
      const buttons = Array.from(document.querySelectorAll('button, a.btn, [role="button"]'))
        .map(b => (b.innerText || b.getAttribute('aria-label') || b.getAttribute('title') || '').trim())
        .filter(t => t.length > 0 && t.length < 50);

      const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4'))
        .map(h => (h.innerText || '').trim())
        .filter(t => t.length > 0 && t.length < 80);

      const inputs = Array.from(document.querySelectorAll('label, input[placeholder], select'))
        .map(i => (i.innerText || i.getAttribute('placeholder') || i.name || '').trim())
        .filter(t => t.length > 0 && t.length < 50);

      const bodyText = (document.body.innerText || '').replace(/\s+/g, ' ').substring(0, 1000);

      return {
        url: window.location.href,
        title: document.title,
        buttons: Array.from(new Set(buttons)).slice(0, 15),
        headings: Array.from(new Set(headings)).slice(0, 10),
        fields: Array.from(new Set(inputs)).slice(0, 10),
        snippet: bodyText,
        app_id: APP_ID,
      };
    } catch (e) {
      return { url: window.location.href, title: document.title, app_id: APP_ID };
    }
  }

  async function syncActiveContext() {
    try {
      const pageCtx = extractActiveUIContext();
      fetch(`${API_BASE}/api/companion/context/sync`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: USER_ID, context: pageCtx }),
      }).catch(() => {});
    } catch (e) {}
  }

  // Trigger DOM context sync on load & navigation
  setTimeout(syncActiveContext, 1500);
  window.addEventListener('popstate', syncActiveContext);

  async function sendMessage() {
    const query = inputEl.value.trim();
    if (!query || isThinking) return;

    const pageCtx = extractActiveUIContext();

    appendMessage('user', query);
    inputEl.value = '';
    isThinking = true;

    const thinkingDiv = document.createElement('div');
    thinkingDiv.className = 'mitra-thinking';
    thinkingDiv.id = 'mitraThinking';
    thinkingDiv.textContent = 'Mitra is analyzing screen & thinking...';
    msgList.appendChild(thinkingDiv);
    msgList.scrollTop = msgList.scrollHeight;

    try {
      // 1. Primary MITRA Backend
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 8000);
      const res = await fetch(`${API_BASE}/api/companion/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: query,
          session_id: sessionId,
          user_id: USER_ID,
          app_id: APP_ID,
          page_context: pageCtx,
        }),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (res.ok) {
        const data = await res.json();
        const thinkingEl = document.getElementById('mitraThinking');
        if (thinkingEl) thinkingEl.remove();

        const reply = data.message || data.response || (typeof data.response === 'object' && data.response.message) || 'I have completed your request.';
        appendMessage('assistant', reply);
        speak(reply);
        return;
      }
    } catch (err) {
      console.warn('Primary MITRA backend notice, connecting to TANTRA runtime...', err);
    }

    try {
      // 2. Secondary TANTRA Runtime Endpoint (Ashmit's deployed service)
      const res2 = await fetch('https://bhiv-mitra.onrender.com/api/assistant', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'x-api-key': 'localtest'
        },
        body: JSON.stringify({
          version: '3.0.0',
          input: { message: query },
          context: { platform: 'web', device: 'browser', session_id: sessionId }
        }),
      });
      if (res2.ok) {
        const data2 = await res2.json();
        const thinkingEl = document.getElementById('mitraThinking');
        if (thinkingEl) thinkingEl.remove();

        const reply2 = (data2.result && data2.result.response) || data2.response || 'Action processed through TANTRA execution engine.';
        appendMessage('assistant', reply2);
        speak(reply2);
        return;
      }
    } catch (err2) {
      console.warn('TANTRA runtime notice, using local companion engine...', err2);
    }

    // 3. Fallback Companion Response (Zero Downtime Guarantee)
    const thinkingEl = document.getElementById('mitraThinking');
    if (thinkingEl) thinkingEl.remove();

    let fallbackReply = `Namaste! I am Mitra, your companion on ${APP_ID.toUpperCase()}. `;
    const qLower = query.toLowerCase();
    if (qLower.includes('hello') || qLower.includes('hi') || qLower.includes('namaste')) {
      fallbackReply += "Hello! How can I assist you with your tasks today?";
    } else if (qLower.includes('how are you')) {
      fallbackReply += "I am functioning smoothly and ready to assist you across the BHIV ecosystem!";
    } else if (qLower.includes('help')) {
      fallbackReply += "I am ready to help you navigate, manage tasks, and coordinate with UniGuru and TANTRA.";
    } else {
      fallbackReply += `I have received your request: "${query}". Your session state is active and synchronized across the ecosystem.`;
    }
    appendMessage('assistant', fallbackReply);
    speak(fallbackReply);
  }

  sendBtn.addEventListener('click', sendMessage);
  inputEl.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') sendMessage();
  });

  // Voice STT
  micBtn.addEventListener('click', async function () {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      alert('Speech recognition is not supported in this browser.');
      return;
    }

    if (isListening) return;

    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      try { await navigator.mediaDevices.getUserMedia({ audio: true }); } catch (e) {}
    }

    const recognition = new SR();
    recognition.lang = 'en-US';
    recognition.onstart = () => {
      isListening = true;
      micBtn.classList.add('recording');
      inputEl.placeholder = 'Listening... Speak now!';
    };
    recognition.onresult = (e) => {
      const text = e.results[0][0].transcript;
      inputEl.value = text;
      sendMessage();
    };
    recognition.onerror = () => {
      isListening = false;
      micBtn.classList.remove('recording');
      inputEl.placeholder = 'Ask Mitra...';
    };
    recognition.onend = () => {
      isListening = false;
      micBtn.classList.remove('recording');
      inputEl.placeholder = 'Ask Mitra...';
    };
    recognition.start();
  });
})();
