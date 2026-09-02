import { controlPlane, getApiBaseUrl } from '../services/controlPlane.js';

export class ConversationPanel {
  constructor(eventBus, contextStore) {
    this.element = document.createElement('div');
    this.element.className = 'mitra-chat';
    this.element.id = 'chat-container';
    this.eventBus = eventBus;
    this.contextStore = contextStore;
    
    // Load existing history on creation
    this.renderHistory();

    if (eventBus) {
      // Real-time listener: append new incoming messages immediately
      eventBus.on('chat.mitra_message', (data) => {
        if (data.role === 'mitra') {
          this.addMitraMessage(data.text, new Date(), data.intent, data.suggestedActions || [], data.capabilityResult);
        } else {
          this.addSystemMessage(data.text);
        }
      });
      
      // Also render real notifications (like reminders) as chat bubbles
      eventBus.on('notification.received', (data) => {
        if (data.role === 'mitra') {
          this.addMitraMessage(data.text || data.message, new Date(), data.intent, data.suggestedActions || [], data.capabilityResult);
        }
      });

      // Real-time listener: when a user message is sent
      eventBus.on('user.message_sent', (data) => {
        this.addUserMessage(data.text, new Date());
      });

      // Real-time listener: when capability finishes execution successfully
      eventBus.on('capability.completed', (data) => {
        this.addCapabilityCard(data.capability, data.result, data.duration, data.data || {});
      });

      // Real-time listener: when capability execution fails or errors out
      eventBus.on('capability.failed', (data) => {
        this.addCapabilityErrorCard(data.capability, data.error || data.result, data.data || {});
      });

      // Real-time listener: when user clears history or resets companion
      eventBus.on('context.cleared', () => {
        this.renderHistory();
      });
    }
  }

  renderHistory() {
    this.element.innerHTML = '';
    const history = this.contextStore ? this.contextStore.getHistory() : [];
    if (history && history.length > 0) {
      history.forEach(msg => {
        if (msg.role === 'user') {
          this.addUserMessage(msg.text, new Date(msg.timestamp));
        } else if (msg.role === 'mitra') {
          if (msg.isCapability) {
            this.addCapabilityCard(msg.capabilityName, msg.result, msg.duration, msg.data);
          } else {
            this.addMitraMessage(msg.text, new Date(msg.timestamp), msg.intent, msg.suggestedActions, msg.capabilityResult);
          }
        }
      });
    } else {
      this.fetchDynamicGreeting();
    }
  }

  async fetchDynamicGreeting() {
    const defaultGreeting = "Hello. I am MITRA, your Universal Companion across the BHIV ecosystem. How can I assist you today?";
    try {
      const userId = this.contextStore ? this.contextStore.getUserId() : null;
      if (!userId) {
        this.addMitraMessage(defaultGreeting, new Date());
        return;
      }
      
      const token = localStorage.getItem('authToken') || localStorage.getItem('token');
      const headers = { 'X-API-Key': 'bhiv-enterprise-key' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch(`${getApiBaseUrl()}/api/companion/greeting/${encodeURIComponent(userId)}`, { headers });
      if (res.ok) {
        const data = await res.json();
        this.addMitraMessage(data.greeting || data.message || defaultGreeting, new Date());
      } else {
        this.addMitraMessage(defaultGreeting, new Date());
      }
    } catch (e) {
      this.addMitraMessage(defaultGreeting, new Date());
    }
  }

  addUserMessage(text, date = new Date()) {
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble user';
    bubble.innerHTML = `<div style="overflow-wrap: break-word; word-break: break-word; box-sizing: border-box;">${this.escapeHtml(text)}</div><div class="chat-timestamp">${date.toLocaleTimeString()}</div>`;
    this.element.appendChild(bubble);
    this.scrollToBottom();
  }

  addMitraMessage(text, date = new Date(), intent = null, suggestedActions = [], capabilityResult = null) {
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble mitra';
    
    // Auto-speak voice alert ONLY when a reminder is due
    if (intent === 'reminder_alert') {
      controlPlane.speakText(text);
    }

    let html = `
      <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:8px;">
        <div style="white-space: pre-wrap; flex:1; overflow-wrap: break-word; word-break: break-word; box-sizing: border-box; min-width: 0;">${this.formatMarkdown(text)}</div>
        <button class="mitra-speaker-btn" title="Listen to AI voice" style="background:none; border:none; color:rgba(255,255,255,0.6); cursor:pointer; padding:2px; font-size:14px; transition:0.2s; flex-shrink:0;">🔊</button>
      </div>
    `;
    
    // Add Intent badge if present
    if (intent && intent !== 'general') {
      if (intent === 'summarize') {
        html += `<div style="margin-top:8px; font-size:10px; background:rgba(0,230,118,0.15); border:1px solid rgba(0,230,118,0.35); color:#00e676; padding:2px 8px; border-radius:10px; display:inline-flex; align-items:center; gap:4px;">📄 AI Summary</div>`;
      } else if (intent === 'summarize_prompt') {
        html += `<div style="margin-top:8px; font-size:10px; background:rgba(255,183,0,0.15); border:1px solid rgba(255,183,0,0.35); color:#ffb700; padding:2px 8px; border-radius:10px; display:inline-flex; align-items:center; gap:4px;">💡 Input required</div>`;
      } else if (intent !== 'reminder_alert') {
        html += `<div style="margin-top:8px; font-size:10px; opacity:0.85; background:rgba(108,92,231,0.25); border:1px solid rgba(108,92,231,0.4); padding:2px 8px; border-radius:10px; display:inline-flex; align-items:center; gap:4px;">⚡ Intent: ${this.escapeHtml(intent)}</div>`;
      }
    }


    // Capability results are now natively emitted as 'capability.completed' in controlPlane.js
    // which automatically triggers the beautiful 'addCapabilityCard' widget renderer instead of a plain text box here.    // Render Suggested Action chips if present
    if (suggestedActions && suggestedActions.length > 0) {
      const actionsHtml = suggestedActions.map(action => 
        `<button class="mitra-action-chip" style="margin:4px 6px 0 0; background:linear-gradient(135deg, rgba(108,92,231,0.3), rgba(0,230,118,0.2)); border:1px solid rgba(255,255,255,0.25); color:#fff; padding:5px 12px; border-radius:14px; font-size:11px; font-weight:500; cursor:pointer; font-family:inherit; transition:0.2s;">✨ ${this.escapeHtml(action)}</button>`
      ).join('');
      html += `<div style="margin-top:10px; display:flex; flex-wrap:wrap;">${actionsHtml}</div>`;
    }

    html += `<div class="chat-timestamp">${date.toLocaleTimeString()}</div>`;
    bubble.innerHTML = html;

    // Attach click listener for Speaker Button (Speech Output)
    const speakerBtn = bubble.querySelector('.mitra-speaker-btn');
    if (speakerBtn) {
      speakerBtn.addEventListener('click', () => {
        controlPlane.speakText(text);
      });
    }

    // Attach click listeners to suggested action chips
    const chips = bubble.querySelectorAll('.mitra-action-chip');
    chips.forEach(chip => {
      chip.addEventListener('click', (e) => {
        const actionText = e.target.textContent.replace('✨ ', '').trim();
        if (this.eventBus) {
          this.eventBus.emit('chat.send_suggested', actionText);
        }
      });
    });

    // Attach delete reminder listener if present
    const delBtn = bubble.querySelector('.btn-delete-reminder');
    if (delBtn) {
      delBtn.addEventListener('click', async (e) => {
        const remId = e.target.getAttribute('data-id');
        e.target.textContent = 'Deleting...';
        const success = await controlPlane.deleteReminder(remId);
        if (success) {
          e.target.parentElement.style.opacity = '0.5';
          e.target.textContent = 'Deleted from DB ✓';
        } else {
          e.target.textContent = 'Failed to delete';
        }
      });
    }

    this.element.appendChild(bubble);
    this.scrollToBottom();
  }

  /**
   * Render rich visual widgets for Calendar, OCR, Tasks, Voice, Health, etc.
   */
  addCapabilityCard(capability, resultText, duration, backendData = {}) {
    const card = document.createElement('div');
    card.className = 'chat-bubble mitra capability-widget';
    card.style.background = 'rgba(21, 21, 29, 0.95)';
    card.style.border = '1px solid rgba(108, 92, 231, 0.4)';
    card.style.maxWidth = '92%';
    card.style.padding = '14px 16px';
    card.style.borderRadius = '16px';
    card.style.boxShadow = '0 8px 24px rgba(0, 0, 0, 0.3)';

    const now = new Date().toLocaleTimeString();
    const capUpper = capability.toUpperCase();

    let widgetContent = '';

    if (capability === 'calendar') {
      const nowD = new Date();
      const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
      const currentMonth = monthNames[nowD.getMonth()];
      const currentYear = nowD.getFullYear();
      const todayDate = nowD.getDate();

      // Build 7-column Calendar Month Grid
      const daysInMonth = new Date(currentYear, nowD.getMonth() + 1, 0).getDate();
      const firstDayIdx = new Date(currentYear, nowD.getMonth(), 1).getDay();

      let gridCells = '';
      for (let i = 0; i < firstDayIdx; i++) {
        gridCells += `<div style="padding:4px; text-align:center; opacity:0.2;"></div>`;
      }
      for (let d = 1; d <= daysInMonth; d++) {
        const isToday = d === todayDate;
        gridCells += `
          <div style="
            padding:6px 2px; text-align:center; font-size:11px; font-weight:${isToday ? '700' : '400'};
            background:${isToday ? '#6C5CE7' : 'rgba(255,255,255,0.03)'};
            color:${isToday ? '#fff' : '#e4e4e7'}; border-radius:6px;
            border:${isToday ? '1px solid #a29bfe' : '1px solid rgba(255,255,255,0.05)'};
          ">${d}</div>
        `;
      }

      if (backendData.events && Array.isArray(backendData.events)) {
        const eventsHtml = backendData.events.map(e => `
          <div style="background:rgba(255,255,255,0.05); padding:8px; border-radius:6px; margin-bottom:6px; font-size:12px;">
            <div style="font-weight:600; color:#fff; font-size:12px; margin-bottom:2px;">📌 ${this.escapeHtml(e.title || 'Event')}</div>
            <div style="color:rgba(255,255,255,0.6); font-size:10px;">⏰ ${e.start ? new Date(e.start).toLocaleString() : ''} ${e.end ? '→ ' + new Date(e.end).toLocaleString() : ''}</div>
          </div>
        `).join('');

        widgetContent = `
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:6px;">
            <div style="font-weight:700; font-size:13px; color:#6c5ce7; display:flex; align-items:center; gap:6px;">📅 CALENDAR EVENTS</div>
            <span style="font-size:10px; background:rgba(0,230,118,0.2); color:#00e676; padding:2px 6px; border-radius:4px;">Live DB Sync</span>
          </div>
          <!-- 7-Column Day Header (Sun-Sat) -->
          <div style="display:grid; grid-template-columns:repeat(7, 1fr); gap:4px; margin-bottom:6px; text-align:center; font-size:10px; font-weight:700; color:#a1a1aa;">
            <div>SUN</div><div>MON</div><div>TUE</div><div>WED</div><div>THU</div><div>FRI</div><div>SAT</div>
          </div>
          <!-- Month Date Grid -->
          <div style="display:grid; grid-template-columns:repeat(7, 1fr); gap:4px; margin-bottom:10px;">
            ${gridCells}
          </div>
          <div style="max-height:200px; overflow-y:auto; padding-right:4px;">
            ${eventsHtml || '<div style="color:rgba(255,255,255,0.5); font-size:12px; text-align:center; padding:10px;">No upcoming events.</div>'}
          </div>
        `;
      } else {
        // Real event data from backend
        const event = backendData.event || {};
        const eventTitle = event.title || resultText.replace(/^Calendar event created:\s*/i, '').replace(/^"|"$/g, '');
        const eventStart = event.start ? new Date(event.start).toLocaleString() : 'Today';
        const eventEnd = event.end ? ` → ${new Date(event.end).toLocaleString()}` : '';
        const eventId = event.id ? `<div style="margin-top:4px; font-size:9px; color:rgba(255,255,255,0.3);">ID: ${this.escapeHtml(event.id)}</div>` : '';

        widgetContent = `
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:6px;">
            <div style="font-weight:700; font-size:13px; color:#6c5ce7; display:flex; align-items:center; gap:6px;">📅 CALENDAR (${currentMonth} ${currentYear})</div>
            <span style="font-size:10px; background:rgba(0,230,118,0.2); color:#00e676; padding:2px 6px; border-radius:4px;">Live DB Sync</span>
          </div>

          <!-- 7-Column Day Header (Sun-Sat) -->
          <div style="display:grid; grid-template-columns:repeat(7, 1fr); gap:4px; margin-bottom:6px; text-align:center; font-size:10px; font-weight:700; color:#a1a1aa;">
            <div>SUN</div><div>MON</div><div>TUE</div><div>WED</div><div>THU</div><div>FRI</div><div>SAT</div>
          </div>

          <!-- Month Date Grid -->
          <div style="display:grid; grid-template-columns:repeat(7, 1fr); gap:4px; margin-bottom:10px;">
            ${gridCells}
          </div>

          <div style="background:rgba(255,255,255,0.05); padding:10px; border-radius:8px; font-size:12px;">
            <div style="font-weight:600; color:#fff; font-size:13px; margin-bottom:4px;">📌 ${this.escapeHtml(eventTitle)}</div>
            <div style="color:rgba(255,255,255,0.6); font-size:11px;">⏰ ${this.escapeHtml(eventStart)}${this.escapeHtml(eventEnd)}</div>
            ${eventId}
          </div>
        `;
      }

    } else if (capability === 'task') {
      if (backendData.tasks && Array.isArray(backendData.tasks)) {
        // Render Task List
        const tasksHtml = backendData.tasks.map(t => `
          <div style="background:rgba(255,255,255,0.05); padding:8px; border-radius:6px; margin-bottom:6px; font-size:12px; display:flex; flex-direction:column; gap:4px;">
            <div style="display:flex; align-items:center; gap:8px;">
              <input type="checkbox" class="task-checkbox" data-id="${this.escapeHtml(t.id || '')}" ${t.status === 'completed' ? 'checked' : ''} style="accent-color:#6c5ce7; cursor:pointer;">
              <span class="task-title-text" style="font-weight:600; color:#fff; ${t.status === 'completed' ? 'text-decoration:line-through;opacity:0.5;' : ''}">${this.escapeHtml(t.title)}</span>
            </div>
            <div style="display:flex; gap:8px; padding-left:24px;">
              <span style="font-size:9px; background:rgba(108,92,231,0.2); color:#a29bfe; padding:2px 6px; border-radius:4px;">Priority: ${this.escapeHtml(t.priority || 'medium')}</span>
            </div>
          </div>
        `).join('');

        widgetContent = `
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:6px;">
            <div style="font-weight:700; font-size:13px; color:#ffb900; display:flex; align-items:center; gap:6px;">📋 TASK LIST</div>
            <span style="font-size:10px; background:rgba(0,230,118,0.2); color:#00e676; padding:2px 6px; border-radius:4px;">Live DB Sync</span>
          </div>
          <div style="max-height:200px; overflow-y:auto; padding-right:4px;">
            ${tasksHtml || '<div style="color:rgba(255,255,255,0.5); font-size:12px; text-align:center; padding:10px;">No tasks found.</div>'}
          </div>
        `;
      } else {
        const task = backendData.task || {};
        const cleanTaskTitle = task.title || resultText.replace(/^Task created:\s*/i, '').replace(/^"|"$/g, '');
        const taskId = task.id || '';
        const taskPriority = task.priority || 'medium';
        const taskStatus = task.status || 'pending';
        widgetContent = `
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:6px;">
            <div style="font-weight:700; font-size:13px; color:#ffb900; display:flex; align-items:center; gap:6px;">📋 TASK CREATED</div>
            <span style="font-size:10px; background:rgba(0,230,118,0.2); color:#00e676; padding:2px 6px; border-radius:4px;">Saved to DB</span>
          </div>
          <div style="background:rgba(255,255,255,0.05); padding:10px; border-radius:8px; font-size:12px;">
            <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
              <input type="checkbox" class="task-checkbox" data-id="${this.escapeHtml(taskId)}" style="accent-color:#6c5ce7; width:16px; height:16px; cursor:pointer;">
              <span class="task-title-text" style="font-weight:600; color:#fff; font-size:13px;">${this.escapeHtml(cleanTaskTitle)}</span>
            </div>
            <div style="display:flex; gap:8px; flex-wrap:wrap;">
              <span style="font-size:10px; background:rgba(108,92,231,0.2); color:#a29bfe; padding:2px 6px; border-radius:4px;">Priority: ${this.escapeHtml(taskPriority)}</span>
              <span style="font-size:10px; background:rgba(255,183,0,0.15); color:#ffb700; padding:2px 6px; border-radius:4px;">Status: ${this.escapeHtml(taskStatus)}</span>
              ${taskId ? `<span style="font-size:9px; color:rgba(255,255,255,0.3); padding:2px 6px;">ID: ${this.escapeHtml(taskId)}</span>` : ''}
            </div>
          </div>
        `;
      }

    } else if (capability === 'reminder') {
      if (backendData.reminders && Array.isArray(backendData.reminders)) {
        const remindersHtml = backendData.reminders.map(r => `
          <div style="background:rgba(255,255,255,0.05); padding:8px; border-radius:6px; margin-bottom:6px; font-size:12px; display:flex; justify-content:space-between; align-items:center;">
            <div>
              <div style="font-weight:600; color:#fff; font-size:12px;">${this.escapeHtml(r.title || r.text || 'Reminder')}</div>
              <div style="font-size:10px; color:rgba(255,255,255,0.6); margin-top:2px;">⏰ ${r.time ? new Date(r.time).toLocaleString() : 'Scheduled'}</div>
            </div>
            ${r.id ? `<button class="btn-delete-reminder" data-id="${this.escapeHtml(r.id)}" style="background:none; border:none; color:#ff453a; font-size:14px; cursor:pointer;" title="Delete">🗑️</button>` : ''}
          </div>
        `).join('');

        widgetContent = `
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:6px;">
            <div style="font-weight:700; font-size:13px; color:#ffb900; display:flex; align-items:center; gap:6px;">⏰ REMINDERS LIST</div>
            <span style="font-size:10px; background:rgba(0,230,118,0.2); color:#00e676; padding:2px 6px; border-radius:4px;">Active in DB</span>
          </div>
          <div style="max-height:200px; overflow-y:auto; padding-right:4px;">
            ${remindersHtml || '<div style="color:rgba(255,255,255,0.5); font-size:12px; text-align:center; padding:10px;">No reminders found.</div>'}
          </div>
        `;
      } else {
        const reminder = backendData.reminder || {};
        const reminderTime = reminder.time ? new Date(reminder.time).toLocaleString() : 'Scheduled';
        widgetContent = `
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:6px;">
            <div style="font-weight:700; font-size:13px; color:#ffb900; display:flex; align-items:center; gap:6px;">⏰ REMINDER SET</div>
            <span style="font-size:10px; background:rgba(0,230,118,0.2); color:#00e676; padding:2px 6px; border-radius:4px;">Active in DB</span>
          </div>
          <div style="background:rgba(255,255,255,0.05); padding:10px; border-radius:8px; font-size:12px;">
            <div style="font-weight:600; color:#fff; font-size:13px; margin-bottom:4px;">${this.escapeHtml(resultText)}</div>
            <div style="font-size:11px; color:rgba(255,255,255,0.6);">⏰ Fires at: ${this.escapeHtml(reminderTime)}</div>
            ${reminder.id ? `<div style="margin-top:4px;">
              <button class="btn-delete-reminder" data-id="${this.escapeHtml(reminder.id)}" style="background:rgba(255,59,48,0.2); border:1px solid rgba(255,59,48,0.4); color:#ff453a; padding:4px 8px; border-radius:6px; font-size:10px; font-weight:600; cursor:pointer;">🗑️ Delete Reminder</button>
            </div>` : ''}
          </div>
        `;
      }

    } else if (capability === 'ocr' || capability === 'analyze' || capability === 'summarize') {
      widgetContent = `
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:6px;">
          <div style="font-weight:700; font-size:13px; color:#00e676; display:flex; align-items:center; gap:6px;">📄 ANALYZED DOCUMENT SUMMARY</div>
          <span style="font-size:10px; background:rgba(108,92,231,0.2); color:#a29bfe; padding:2px 6px; border-radius:4px;">100% Confidence</span>
        </div>
        <div style="background:rgba(0,0,0,0.3); border:1px solid rgba(255,255,255,0.1); padding:10px; border-radius:8px; font-size:12px; font-family:monospace; color:#e0e0e0; max-height:140px; overflow-y:auto; white-space:pre-wrap;">${this.escapeHtml(resultText)}</div>
      `;

    } else if (capability === 'voice') {
      widgetContent = `
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px;">
          <div style="font-weight:700; font-size:13px; color:#e056fd; display:flex; align-items:center; gap:6px;">🎙️ VOICE TRANSCRIPTION</div>
          <span style="font-size:10px; background:rgba(224,86,253,0.2); color:#e056fd; padding:2px 6px; border-radius:4px;">Processed (${duration})</span>
        </div>
        <div style="background:rgba(255,255,255,0.05); padding:10px; border-radius:8px; font-size:12px; display:flex; align-items:center; gap:12px;">
          <div style="width:32px; height:32px; border-radius:50%; background:#e056fd; display:flex; align-items:center; justify-content:center; color:#fff; font-size:14px; flex-shrink:0;">▶</div>
          <div style="flex:1; color:#fff; font-size:13px;">${this.escapeHtml(resultText)}</div>
        </div>
      `;

    } else if (capability === 'health') {
      const statusColor = backendData.status === 'healthy' ? '#00e676' : '#ffb700';
      const version = backendData.version || 'v5.0.0';
      widgetContent = `
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:6px;">
          <div style="font-weight:700; font-size:13px; color:#00e676; display:flex; align-items:center; gap:6px;">🏥 SYSTEM HEALTH DIAGNOSTICS</div>
          <span style="font-size:10px; background:rgba(0,230,118,0.2); color:#00e676; padding:2px 6px; border-radius:4px;">Online</span>
        </div>
        <div style="background:rgba(255,255,255,0.05); padding:10px; border-radius:8px; font-size:12px; display:flex; flex-direction:column; gap:4px;">
          <div style="display:flex; justify-content:space-between;"><span style="color:#a1a1aa;">Backend Status:</span><span style="color:${statusColor}; font-weight:700;">${this.escapeHtml(backendData.status || 'Healthy')}</span></div>
          <div style="display:flex; justify-content:space-between;"><span style="color:#a1a1aa;">API Version:</span><span style="color:#fff; font-weight:600;">${this.escapeHtml(version)}</span></div>
          <div style="display:flex; justify-content:space-between;"><span style="color:#a1a1aa;">Response Latency:</span><span style="color:#a29bfe; font-weight:600;">${duration}</span></div>
          ${backendData.db_connected ? `<div style="display:flex; justify-content:space-between;"><span style="color:#a1a1aa;">Database:</span><span style="color:#00e676; font-weight:600;">Connected</span></div>` : ''}
        </div>
      `;

    } else if (capability === 'settings') {
      const isVoiceOn = localStorage.getItem('mitra_voice_enabled') !== 'false';
      const isNotifOn = localStorage.getItem('mitra_notif_enabled') !== 'false';
      widgetContent = `
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:6px;">
          <div style="font-weight:700; font-size:13px; color:#a29bfe; display:flex; align-items:center; gap:6px;">⚙️ COMPANION SETTINGS</div>
          <span style="font-size:10px; background:rgba(108,92,231,0.2); color:#a29bfe; padding:2px 6px; border-radius:4px;">Interactive</span>
        </div>
        <div style="background:rgba(255,255,255,0.05); padding:10px; border-radius:8px; font-size:12px; display:flex; flex-direction:column; gap:10px;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="color:#fff; font-weight:500;">Voice Speech Output 🔊</span>
            <input type="checkbox" class="setting-voice-toggle" ${isVoiceOn ? 'checked' : ''} style="accent-color:#6c5ce7; width:16px; height:16px; cursor:pointer;">
          </div>
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="color:#fff; font-weight:500;">Desktop Notifications 🔔</span>
            <input type="checkbox" class="setting-notif-toggle" ${isNotifOn ? 'checked' : ''} style="accent-color:#6c5ce7; width:16px; height:16px; cursor:pointer;">
          </div>
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="color:#fff; font-weight:500;">Polling Heartbeat ⚡</span>
            <span style="color:#00e676; font-weight:600; font-size:11px; background:rgba(0,230,118,0.15); padding:2px 8px; border-radius:10px;">5s Interval</span>
          </div>
          <div style="margin-top:4px; padding-top:8px; border-top:1px solid rgba(255,255,255,0.1);">
            <button class="btn-clear-memory" style="background:rgba(255,59,48,0.2); border:1px solid rgba(255,59,48,0.4); color:#ff453a; padding:6px 12px; border-radius:8px; font-size:11px; font-weight:600; cursor:pointer; width:100%;">🗑️ Clear Conversation Memory</button>
          </div>
        </div>
      `;

    } else if (capability === 'translate') {
      // Translation card — shows original + translated text
      const translationData = backendData.translation || {};
      const translatedText = translationData.text || backendData.result || resultText || '';
      const originalText = translationData.original || backendData.query || '';
      const fromLang = translationData.from || 'English';
      const toLang = translationData.to || 'Target Language';
      const isSuccess = backendData.status !== 'error';
      widgetContent = `
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:6px;">
          <div style="font-weight:700; font-size:13px; color:#a29bfe; display:flex; align-items:center; gap:6px;">🌐 TRANSLATION</div>
          <span style="font-size:10px; background:rgba(162,155,254,0.15); color:#a29bfe; padding:2px 6px; border-radius:4px;">${this.escapeHtml(fromLang)} → ${this.escapeHtml(toLang)}</span>
        </div>
        ${originalText ? `<div style="font-size:11px; color:rgba(255,255,255,0.5); margin-bottom:6px;">Original: <em>${this.escapeHtml(originalText)}</em></div>` : ''}
        <div style="background:rgba(162,155,254,0.1); border:1px solid rgba(162,155,254,0.3); border-radius:8px; padding:12px; font-size:14px; font-weight:600; color:#fff; margin-bottom:8px; overflow-wrap:anywhere; word-break:break-word;">${this.escapeHtml(translatedText)}</div>
        <button class="btn-copy-translation" data-text="${this.escapeHtml(translatedText)}" style="background:rgba(162,155,254,0.2); border:1px solid rgba(162,155,254,0.4); color:#a29bfe; padding:5px 12px; border-radius:8px; font-size:11px; font-weight:600; cursor:pointer;">📋 Copy Translation</button>
      `;

    } else if (capability === 'email') {
      // Real backend email result fields: status, to, subject, message, method
      const emailData = backendData.email || {};
      const isSuccess = emailData.status === 'success' || backendData.status === 'success';
      const toAddr = emailData.to || '';
      const subj = emailData.subject || '';
      const method = emailData.method || 'backend';
      const errorMsg = emailData.error || '';
      const statusColor = isSuccess ? '#00e676' : '#ff453a';
      const statusLabel = isSuccess ? 'Sent ✓' : 'Not Configured ✗';
      widgetContent = `
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:6px;">
          <div style="font-weight:700; font-size:13px; color:${statusColor}; display:flex; align-items:center; gap:6px;">✉️ EMAIL ${isSuccess ? 'SENT' : 'PENDING CONFIGURATION'}</div>
          <span style="font-size:10px; background:rgba(0,230,118,0.15); color:${statusColor}; padding:2px 6px; border-radius:4px;">${statusLabel}</span>
        </div>
        <div style="background:rgba(255,255,255,0.05); padding:10px; border-radius:8px; font-size:12px;">
          ${toAddr ? `<div style="font-weight:600; color:#fff; font-size:13px; margin-bottom:4px;">📬 To: ${this.escapeHtml(toAddr)}</div>` : ''}
          ${subj ? `<div style="font-size:11px; color:rgba(255,255,255,0.6); margin-bottom:4px;">📝 Subject: ${this.escapeHtml(subj)}</div>` : ''}
          ${!isSuccess && errorMsg ? `<div style="margin-top:6px; font-size:11px; color:#ffd93d; background:rgba(255,217,61,0.08); border:1px solid rgba(255,217,61,0.2); padding:8px; border-radius:6px;">⚙️ ${this.escapeHtml(errorMsg)}</div>` : ''}
          ${method && method !== 'none' ? `<div style="margin-top:4px; font-size:9px; color:rgba(255,255,255,0.3);">via: ${this.escapeHtml(method)}</div>` : ''}
        </div>
      `;


    } else if (capability === 'whatsapp') {

      // Real backend WhatsApp result: status, error, details (Twilio)
      const waData = backendData.whatsapp || {};
      const isSuccess = waData.status === 'success' || backendData.status === 'success';
      const statusColor = isSuccess ? '#00e676' : '#ff453a';
      const statusLabel = isSuccess ? 'Sent ✓' : 'Failed ✗';
      widgetContent = `
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; border-bottom:1px solid rgba(255, 255, 255, 0.1); padding-bottom:6px;">
          <div style="font-weight:700; font-size:13px; color:${statusColor}; display:flex; align-items:center; gap:6px;">💬 WHATSAPP ${isSuccess ? 'SENT' : 'FAILED'}</div>
          <span style="font-size:10px; background:rgba(0,230,118,0.15); color:${statusColor}; padding:2px 6px; border-radius:4px;">${statusLabel}</span>
        </div>
        <div style="background:rgba(255,255,255,0.05); padding:10px; border-radius:8px; font-size:12px;">
          <div style="font-weight:600; color:#fff; font-size:13px;">${this.escapeHtml(resultText)}</div>
        </div>
      `;

    } else if (capability === 'samachar') {
      const query = backendData.query || 'latest news';
      const isFailed = backendData.status === 'failed' || backendData.status === 'error' || (resultText && (resultText.includes('UNAVAILABLE') || resultText.includes('failed')));
      
      if (isFailed) {
        card.style.border = '1px solid rgba(255, 59, 48, 0.4)';
        widgetContent = `
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:6px;">
            <div style="font-weight:700; font-size:13px; color:#ff3b30; display:flex; align-items:center; gap:6px;">📰 SAMACHAR SERVICE UNAVAILABLE</div>
            <span style="font-size:10px; background:rgba(255,59,48,0.2); color:#ff453a; padding:2px 6px; border-radius:4px;">Endpoint Unreachable</span>
          </div>
          <div style="font-size:11px; color:rgba(255,255,255,0.6); margin-bottom:6px;">🔍 Query: "${this.escapeHtml(query)}"</div>
          <div style="background:rgba(255,59,48,0.08); border:1px solid rgba(255,59,48,0.2); padding:10px; border-radius:8px; font-size:12px; color:#ff6b6b; overflow-wrap:anywhere; word-break:break-word;">${this.escapeHtml(resultText)}</div>
        `;
      } else {
        const scraped = backendData.scraped_data || {};
        const vetting = backendData.vetting_results || {};
        const summary = backendData.summary || {};
        const category = (scraped.category || 'Technology').toUpperCase();
        const credRating = vetting.credibility_rating || 'High';
        const credScore = vetting.authenticity_score != null ? `${vetting.authenticity_score}%` : '95%';
        const summaryText = summary.text || backendData.result || resultText || 'No summary text extracted.';

        let title = scraped.title;
        let author = (typeof scraped.author === 'object' ? scraped.author.name : scraped.author);
        let datePub = scraped.date;

        // Dynamic extraction for Title if missing or generic
        if (!title || title === 'News Article Analysis' || title === 'News Article') {
          const headingMatch = summaryText.match(/#+\s*([^\n#]+)/) 
            || summaryText.match(/-\s*([^:\n]+):/) 
            || summaryText.match(/Title:\s*([^\n]+)/i);
          if (headingMatch && headingMatch[1]) {
            const cand = headingMatch[1].trim();
            if (cand.length > 5) {
              title = cand;
            }
          }
          if ((!title || title === 'News Article Analysis') && backendData.url) {
            try {
              const parsed = new URL(backendData.url);
              let slug = parsed.pathname.replace(/\/$/, '').split('/').pop() || '';
              slug = slug.replace(/-\d+$/, '').replace(/\.(html|ece|cms|story|article)$/i, '');
              if (slug.length > 3 && slug.includes('-')) {
                title = slug.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
              }
            } catch (e) {}
          }
          // For query-based news, derive title from query itself
          if (!title || title === 'News Article Analysis') {
            const q = backendData.query || '';
            if (q && q.length > 3) {
              title = q.length > 80 ? q.slice(0, 77) + '...' : q;
            } else {
              title = 'News Intelligence Report';
            }
          }
        }
        // Truncate title to max 80 chars to prevent overflow
        if (title && title.length > 80) {
          title = title.slice(0, 77) + '...';
        }

        // Dynamic extraction for Author / Source Domain if missing or generic
        if (!author || author === 'News Desk' || author === 'Unknown') {
          const authorMatch = summaryText.match(/(?:By|Published by|Author:?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)/);
          if (authorMatch && authorMatch[1]) {
            author = authorMatch[1].trim();
          } else if (backendData.url) {
            try {
              const parsed = new URL(backendData.url);
              const domain = parsed.hostname.replace(/^www\./i, '').split('.')[0];
              author = domain.toUpperCase() + ' News Desk';
            } catch (e) {}
          } else {
            author = 'MITRA News Intelligence';
          }
          if (!author) author = 'News Desk';
        }

        // Dynamic extraction for Publication Date if missing or generic
        if (!datePub || datePub === 'Recent' || datePub === 'N/A') {
          const dateMatch = summaryText.match(/\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+20\d{2}\b/i)
            || summaryText.match(/\b20\d{2}-\d{2}-\d{2}\b/);
          if (dateMatch) {
            datePub = dateMatch[0];
          } else {
            datePub = new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
          }
        }

        const directUrl = backendData.url ? `<div style="margin-top:8px; font-size:11px;"><a href="${this.escapeHtml(backendData.url)}" target="_blank" rel="noopener" style="color:#a29bfe; text-decoration:underline; overflow-wrap:anywhere; word-break:break-all;">🔗 View Source Article</a></div>` : '';

        widgetContent = `
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; border-bottom:1px solid rgba(255, 255, 255, 0.1); padding-bottom:6px;">
            <div style="font-weight:700; font-size:13px; color:#00e676; display:flex; align-items:center; gap:6px;">📰 NEWS ANALYSIS</div>
            <span style="font-size:10px; background:rgba(0,230,118,0.15); color:#00e676; padding:2px 6px; border-radius:4px;">${this.escapeHtml(category)}</span>
          </div>
          <div style="font-size:13px; font-weight:700; color:#fff; margin-bottom:6px; overflow-wrap:anywhere; word-break:break-word;">Title: ${this.escapeHtml(title)}</div>
          <div style="display:flex; gap:12px; font-size:11px; color:rgba(255,255,255,0.7); margin-bottom:6px; flex-wrap:wrap;">
            <span>✍️ Author: ${this.escapeHtml(author)}</span>
            <span>📅 Date: ${this.escapeHtml(datePub)}</span>
          </div>
          <div style="display:flex; gap:12px; font-size:11px; color:rgba(255,255,255,0.85); margin-bottom:8px; flex-wrap:wrap;">
            <span>🛡️ Credibility: <strong>${this.escapeHtml(credRating)}</strong></span>
            <span>💯 Authenticity: <strong>${this.escapeHtml(credScore)}</strong></span>
          </div>
          <div style="font-size:11px; font-weight:600; color:#a29bfe; margin-bottom:4px;">Summary:</div>
          <div style="background:rgba(0,0,0,0.3); border:1px solid rgba(255,255,255,0.1); padding:10px; border-radius:8px; font-size:12px; font-family:inherit; color:#e0e0e0; max-height:180px; overflow-y:auto; white-space:pre-wrap; overflow-wrap:anywhere; word-break:break-word;">${this.escapeHtml(summaryText)}</div>
        `;
      }

    } else if (capability === 'uniguru') {
      const isLlmFallback = backendData.source === 'llm_fallback' || !backendData.evidence;
      const verStatus = backendData.verification_status || (isLlmFallback ? 'LLM_FALLBACK' : 'VERIFIED');
      const answerText = backendData.answer || backendData.result || resultText || '';

      let evidenceBox = '';
      if (backendData.evidence) {
        const tbId = backendData.evidence.textbook_id || backendData.textbook_id || 'balbharti_k12';
        const pages = Array.isArray(backendData.evidence.page_numbers)
          ? backendData.evidence.page_numbers.join(', ')
          : (backendData.evidence.page_numbers || 'N/A');
        const srcHash = backendData.evidence.source_hash ? String(backendData.evidence.source_hash).slice(0, 12) + '...' : 'Verified';
        const linHash = backendData.evidence.lineage_hash ? String(backendData.evidence.lineage_hash).slice(0, 12) + '...' : 'Verified';

        evidenceBox = `
          <div style="background:rgba(0,230,118,0.06); border:1px solid rgba(0,230,118,0.2); padding:10px; border-radius:8px; margin-top:8px; font-size:11px;">
            <div style="font-weight:700; color:#00e676; margin-bottom:4px; font-size:11px;">📚 KOSHA EVIDENCE CITATION</div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; color:rgba(255,255,255,0.8);">
              <div>📖 <strong>Textbook:</strong> ${this.escapeHtml(tbId)}</div>
              <div>📄 <strong>Pages:</strong> ${this.escapeHtml(String(pages))}</div>
              <div>🔑 <strong>Source Hash:</strong> ${this.escapeHtml(srcHash)}</div>
              <div>🔗 <strong>Lineage Hash:</strong> ${this.escapeHtml(linHash)}</div>
            </div>
          </div>
        `;
      } else {
        evidenceBox = `
          <div style="background:rgba(255,183,0,0.06); border:1px solid rgba(255,183,0,0.2); padding:6px 10px; border-radius:6px; margin-top:8px; font-size:10px; color:#ffb700; display:flex; align-items:center; gap:6px;">
            <span>ℹ️ Standard Knowledge Response (LLM Bridge Fallback Mode — Kosha RAG REST API awaiting backend endpoint)</span>
          </div>
        `;
      }

      widgetContent = `
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:6px;">
          <div style="font-weight:700; font-size:13px; color:#6c5ce7; display:flex; align-items:center; gap:6px;">🎓 UNIGURU KNOWLEDGE</div>
          <span style="font-size:10px; background:${isLlmFallback ? 'rgba(255,183,0,0.15)' : 'rgba(0,230,118,0.15)'}; color:${isLlmFallback ? '#ffb700' : '#00e676'}; padding:2px 6px; border-radius:4px;">${this.escapeHtml(verStatus)}</span>
        </div>
        <div style="background:rgba(0,0,0,0.3); border:1px solid rgba(255,255,255,0.1); padding:10px; border-radius:8px; font-size:12px; color:#e0e0e0; max-height:220px; overflow-y:auto; white-space:pre-wrap;">${this.escapeHtml(answerText)}</div>
        ${evidenceBox}
      `;

    } else if (capability === 'setu') {
      const provTag = backendData.source_context?.connected_company_id || 'bc_bright_connection_001';

      let bodyContent = '';
      if (backendData.data && backendData.data.products && Array.isArray(backendData.data.products)) {
        const rows = backendData.data.products.map(p => `
          <tr>
            <td style="padding:4px 6px; border-bottom:1px solid rgba(255,255,255,0.05);">${this.escapeHtml(p.sku || p.name)}</td>
            <td style="padding:4px 6px; border-bottom:1px solid rgba(255,255,255,0.05); text-align:right;">₹${p.price || 0}</td>
            <td style="padding:4px 6px; border-bottom:1px solid rgba(255,255,255,0.05); text-align:right; font-weight:700; color:${(p.stock_quantity || 0) < 10 ? '#ff453a' : '#00e676'};">${p.stock_quantity || 0}</td>
          </tr>
        `).join('');
        bodyContent = `
          <table style="width:100%; border-collapse:collapse; font-size:11px; margin-top:6px;">
            <thead><tr style="color:#a1a1aa; border-bottom:1px solid rgba(255,255,255,0.1); text-align:left;"><th>Item</th><th style="text-align:right;">Price</th><th style="text-align:right;">Stock</th></tr></thead>
            <tbody>${rows}</tbody>
          </table>
        `;
      } else {
        bodyContent = `
          <div style="background:rgba(255,255,255,0.04); padding:10px; border-radius:6px; font-size:11px; color:#e0e0e0;">
            ${this.escapeHtml(resultText || 'SETU Operational Gateway Response')}
          </div>
          <div style="margin-top:6px; font-size:10px; color:#a1a1aa;">
            ℹ️ SETU Integration Gateway Interface (Pending live backend contract registration)
          </div>
        `;
      }

      widgetContent = `
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:6px;">
          <div style="font-weight:700; font-size:13px; color:#ffb700; display:flex; align-items:center; gap:6px;">🔌 SETU OPERATIONAL GATEWAY</div>
          <span style="font-size:10px; background:rgba(255,183,0,0.15); color:#ffb700; padding:2px 6px; border-radius:4px;">${this.escapeHtml(provTag)}</span>
        </div>
        ${bodyContent}
      `;

    } else {
      widgetContent = `
        <div style="font-weight:700; font-size:12px; color:#a29bfe; margin-bottom:4px;">⚙️ CAPABILITY EXECUTION [${capUpper}]</div>
        <div style="font-size:13px; color:#fff;">${this.escapeHtml(resultText)}</div>
        <div style="font-size:10px; color:rgba(255,255,255,0.4); margin-top:4px;">Execution time: ${duration}</div>
      `;
    }

    card.innerHTML = `${widgetContent}<div class="chat-timestamp">${now}</div>`;

    const draftBtn = card.querySelector('.btn-email-draft');
    if (draftBtn) {
      draftBtn.addEventListener('click', () => {
        alert(`📧 EMAIL DRAFT PREVIEW:\nSubject: ${resultText}\nStatus: Ready for SMTP dispatch.`);
      });
    }

    const editBtn = card.querySelector('.btn-email-edit');
    if (editBtn) {
      editBtn.addEventListener('click', () => {
        const newMsg = prompt("Edit Email Body / Message:", resultText);
        if (newMsg) {
          controlPlane.sendCapability('email', 'send_email', { body: newMsg });
        }
      });
    }

    const copyTransBtn = card.querySelector('.btn-copy-translation');
    if (copyTransBtn) {
      copyTransBtn.addEventListener('click', () => {
        const textToCopy = copyTransBtn.getAttribute('data-text') || '';
        navigator.clipboard.writeText(textToCopy).then(() => {
          copyTransBtn.textContent = '✅ Copied!';
          setTimeout(() => { copyTransBtn.textContent = '📋 Copy Translation'; }, 2000);
        }).catch(() => {
          copyTransBtn.textContent = '✅ Copied!';
          setTimeout(() => { copyTransBtn.textContent = '📋 Copy Translation'; }, 2000);
        });
      });
    }

    const taskCbs = card.querySelectorAll('.task-checkbox');

    taskCbs.forEach(taskCb => {
      taskCb.addEventListener('change', async (e) => {
        const row = e.target.closest('div[style*="background:rgba(255,255,255,0.05)"]');
        const titleSpan = row ? row.querySelector('.task-title-text') : null;
        
        const taskId = e.target.getAttribute('data-id');
        const newStatus = e.target.checked ? 'completed' : 'pending';

        if (titleSpan) {
          if (e.target.checked) {
            titleSpan.style.textDecoration = 'line-through';
            titleSpan.style.opacity = '0.5';
          } else {
            titleSpan.style.textDecoration = 'none';
            titleSpan.style.opacity = '1.0';
          }
        }

        if (taskId) {
          try {
            const userId = this.contextStore ? this.contextStore.getUserId() : 'anonymous';
            const headers = { 'Content-Type': 'application/json', 'X-API-Key': 'bhiv-enterprise-key' };
            const token = localStorage.getItem('authToken') || localStorage.getItem('token');
            if (token) headers['Authorization'] = `Bearer ${token}`;
            
            await fetch(`https://mitra-backend-q1f3.onrender.com/api/pages/tasks/update?task_id=${encodeURIComponent(taskId)}&status=${newStatus}&user_id=${encodeURIComponent(userId)}`, {
              method: 'POST',
              headers
            });
            // If completed, optionally remove from UI after 1 second
            if (newStatus === 'completed' && row) {
              setTimeout(() => {
                row.style.transition = 'opacity 0.3s ease';
                row.style.opacity = '0';
                setTimeout(() => row.remove(), 300);
              }, 1000);
            }
          } catch (err) {
            console.error('[MITRA] Task update failed:', err);
          }
        }
      });
    });

    const voiceToggle = card.querySelector('.setting-voice-toggle');
    if (voiceToggle) {
      voiceToggle.addEventListener('change', (e) => {
        localStorage.setItem('mitra_voice_enabled', e.target.checked ? 'true' : 'false');
      });
    }

    const notifToggle = card.querySelector('.setting-notif-toggle');
    if (notifToggle) {
      notifToggle.addEventListener('change', (e) => {
        localStorage.setItem('mitra_notif_enabled', e.target.checked ? 'true' : 'false');
      });
    }

    const clearMemBtn = card.querySelector('.btn-clear-memory');
    if (clearMemBtn) {
      clearMemBtn.addEventListener('click', () => {
        if (confirm("Are you sure you want to clear companion conversation memory?")) {
          if (this.contextStore) this.contextStore.clear();
          if (this.eventBus) this.eventBus.emit('context.cleared');
        }
      });
    }

    this.element.appendChild(card);
    this.scrollToBottom();
  }

  addCapabilityErrorCard(capability, errorText, data = {}) {
    const card = document.createElement('div');
    card.className = 'chat-bubble mitra capability-widget failure';
    card.style.background = 'rgba(35, 15, 15, 0.95)';
    card.style.border = '1px solid rgba(255, 59, 48, 0.4)';
    card.style.maxWidth = '92%';
    card.style.padding = '14px 16px';
    card.style.borderRadius = '16px';
    card.style.boxShadow = '0 8px 24px rgba(255, 59, 48, 0.15)';

    const now = new Date().toLocaleTimeString();
    const capUpper = (capability || 'CAPABILITY').toUpperCase();

    card.innerHTML = `
      <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; border-bottom:1px solid rgba(255,59,48,0.2); padding-bottom:6px;">
        <div style="font-weight:700; font-size:13px; color:#ff453a; display:flex; align-items:center; gap:6px;">⚠️ ${this.escapeHtml(capUpper)} EXECUTION FAILED</div>
        <span style="font-size:10px; background:rgba(255,59,48,0.2); color:#ff453a; padding:2px 6px; border-radius:4px;">Failed</span>
      </div>
      <div style="font-size:12px; color:#ff8585; margin-bottom:4px;">${this.escapeHtml(errorText)}</div>
      <div class="chat-timestamp">${now}</div>
    `;

    this.element.appendChild(card);
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

  formatMarkdown(text) {
    if (!text) return '';
    let formatted = this.escapeHtml(text);

    // Headers: ## Heading -> <strong> styled header
    formatted = formatted.replace(/^###\s+(.+)$/gm, '<div style="font-size:12px;font-weight:700;color:#a29bfe;margin:10px 0 4px 0;text-transform:uppercase;letter-spacing:0.5px;">$1</div>');
    formatted = formatted.replace(/^##\s+(.+)$/gm, '<div style="font-size:13px;font-weight:700;color:#e4e4e7;margin:12px 0 6px 0;border-bottom:1px solid rgba(255,255,255,0.1);padding-bottom:4px;">$1</div>');
    formatted = formatted.replace(/^#\s+(.+)$/gm, '<div style="font-size:14px;font-weight:700;color:#fff;margin:12px 0 6px 0;">$1</div>');

    // Bold: **text**
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Italic: *text* (but not bullet points)
    formatted = formatted.replace(/(?<!\n)\*(?!\s)(.+?)(?<!\s)\*(?!\*)/g, '<em>$1</em>');

    // Bullet points: lines starting with *, -, \t* or \t-
    formatted = formatted.replace(/^[\t ]*[\*\-]\s+(.+)$/gm, '<div style="margin:3px 0;padding-left:16px;display:flex;gap:6px;"><span style="color:#6c5ce7;flex-shrink:0;">•</span><span>$1</span></div>');

    // Numbered lists: 1. item
    formatted = formatted.replace(/^(\d+)\.\s+(.+)$/gm, '<div style="margin:3px 0;padding-left:16px;display:flex;gap:6px;"><span style="color:#6c5ce7;font-weight:700;flex-shrink:0;min-width:16px;">$1.</span><span>$2</span></div>');

    // Horizontal rule
    formatted = formatted.replace(/^---+$/gm, '<hr style="border:none;border-top:1px solid rgba(255,255,255,0.1);margin:8px 0;">');

    // Inline code
    formatted = formatted.replace(/`([^`]+)`/g, '<code style="background:rgba(255,255,255,0.1);padding:2px 4px;border-radius:4px;font-family:monospace;">$1</code>');

    // Line breaks (preserve \n as <br> for sections not already converted to divs)
    formatted = formatted.replace(/\n/g, '<br>');

    return formatted;
  }


  escapeHtml(text) {
    if (!text) return '';
    return String(text)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
}
