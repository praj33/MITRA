export function applyTheme(themeName) {
  const root = document.documentElement;
  if (themeName === 'Emerald') {
    root.style.setProperty('--mitra-accent', '#00e676');
    root.style.setProperty('--mitra-bg', 'rgba(10, 25, 19, 0.92)');
    document.body.style.background = '#06140E';
  } else if (themeName === 'Violet') {
    root.style.setProperty('--mitra-accent', '#e056fd');
    root.style.setProperty('--mitra-bg', 'rgba(20, 10, 26, 0.92)');
    document.body.style.background = '#0F0614';
  } else if (themeName === 'Light') {
    root.style.setProperty('--mitra-accent', '#6c5ce7');
    root.style.setProperty('--mitra-bg', 'rgba(255, 255, 255, 0.95)');
    root.style.setProperty('--mitra-text', '#18181b');
    document.body.style.background = '#F4F4F5';
  } else {
    // Midnight (Default)
    root.style.setProperty('--mitra-accent', '#6c5ce7');
    root.style.setProperty('--mitra-bg', 'rgba(20, 20, 24, 0.85)');
    root.style.setProperty('--mitra-text', '#ffffff');
    document.body.style.background = '#0B0B0E';
  }
}

// Apply stored theme on script load
applyTheme(localStorage.getItem('mitra_theme') || 'Midnight');

export class SettingsModal {
  constructor() {
    this.element = document.createElement('div');
    this.element.className = 'mitra-settings-modal-overlay';
    this.element.style.cssText = `
      display: none;
      position: fixed;
      top: 0; left: 0; width: 100vw; height: 100vh;
      background: rgba(0, 0, 0, 0.7);
      backdrop-filter: blur(6px);
      z-index: 99999;
      align-items: center; justify-content: center;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    `;

    this.render();
  }

  render() {
    const activeTheme = localStorage.getItem('mitra_theme') || 'Midnight';
    const userName = localStorage.getItem('mitra_user_name') || 'User';

    this.element.innerHTML = `
      <div class="mitra-settings-modal" style="
        width: 460px; max-width: 90vw; background: #15151D;
        border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 16px;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6); color: #fff;
        padding: 24px; display: flex; flex-direction: column; gap: 20px;
        position: relative;
      ">
        <!-- Modal Header -->
        <div style="display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid rgba(255,255,255,0.08); padding-bottom:12px;">
          <div style="font-size:18px; font-weight:700;">Settings</div>
          <button id="btn-close-settings" style="background:none; border:none; color:rgba(255,255,255,0.6); font-size:20px; cursor:pointer;">✕</button>
        </div>

        <!-- 1. APPEARANCE -->
        <div>
          <div style="font-size:11px; font-weight:700; color:rgba(255,255,255,0.5); letter-spacing:0.5px; margin-bottom:10px;">⚙️ APPEARANCE</div>
          <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:8px;">
            <button class="theme-opt ${activeTheme === 'Midnight' ? 'active' : ''}" data-theme="Midnight" style="background:${activeTheme === 'Midnight' ? '#6C5CE7' : 'rgba(255,255,255,0.05)'}; border:1px solid rgba(255,255,255,0.1); color:#fff; padding:8px; border-radius:8px; font-size:12px; cursor:pointer;">🌙 Midnight</button>
            <button class="theme-opt ${activeTheme === 'Emerald' ? 'active' : ''}" data-theme="Emerald" style="background:${activeTheme === 'Emerald' ? '#00e676' : 'rgba(255,255,255,0.05)'}; border:1px solid rgba(255,255,255,0.1); color:#fff; padding:8px; border-radius:8px; font-size:12px; cursor:pointer;">❇️ Emerald</button>
            <button class="theme-opt ${activeTheme === 'Violet' ? 'active' : ''}" data-theme="Violet" style="background:${activeTheme === 'Violet' ? '#e056fd' : 'rgba(255,255,255,0.05)'}; border:1px solid rgba(255,255,255,0.1); color:#fff; padding:8px; border-radius:8px; font-size:12px; cursor:pointer;">🔮 Violet</button>
            <button class="theme-opt ${activeTheme === 'Light' ? 'active' : ''}" data-theme="Light" style="background:${activeTheme === 'Light' ? '#ffb900' : 'rgba(255,255,255,0.05)'}; border:1px solid rgba(255,255,255,0.1); color:#fff; padding:8px; border-radius:8px; font-size:12px; cursor:pointer;">☀️ Light</button>
            <button class="theme-opt ${activeTheme === 'System' ? 'active' : ''}" data-theme="System" style="background:${activeTheme === 'System' ? '#a29bfe' : 'rgba(255,255,255,0.05)'}; border:1px solid rgba(255,255,255,0.1); color:#fff; padding:8px; border-radius:8px; font-size:12px; cursor:pointer;">💻 System</button>
          </div>
        </div>

        <!-- 2. PROFILE -->
        <div>
          <div style="font-size:11px; font-weight:700; color:rgba(255,255,255,0.5); letter-spacing:0.5px; margin-bottom:8px;">👤 PROFILE</div>
          <div style="display:flex; gap:8px;">
            <input type="text" id="input-display-name" value="${userName}" style="flex:1; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.15); color:#fff; padding:8px 12px; border-radius:8px; font-size:13px;" />
            <button id="btn-save-profile" style="background:#6C5CE7; border:none; color:#fff; padding:8px 16px; border-radius:8px; font-size:12px; font-weight:600; cursor:pointer;">✓ Save</button>
          </div>
        </div>

        <!-- 3. CONNECTION -->
        <div>
          <div style="font-size:11px; font-weight:700; color:rgba(255,255,255,0.5); letter-spacing:0.5px; margin-bottom:6px;">🗝️ CONNECTION</div>
          <div style="background:rgba(0,0,0,0.3); border:1px solid rgba(255,255,255,0.08); padding:10px 12px; border-radius:8px; font-size:12px; display:flex; flex-direction:column; gap:4px;">
            <div style="color:rgba(255,255,255,0.5); font-size:10px;">API Endpoint</div>
            <div style="color:#a29bfe; font-family:monospace; font-size:11px;">https://mitra-backend-q1f3.onrender.com</div>
            <div style="display:flex; align-items:center; gap:6px; margin-top:4px;">
              <span style="width:8px; height:8px; border-radius:50%; background:#00e676; display:inline-block;"></span>
              <span style="color:#00e676; font-size:11px; font-weight:600;">Connected</span>
            </div>
          </div>
        </div>

        <!-- 4. ABOUT -->
        <div>
          <div style="font-size:11px; font-weight:700; color:rgba(255,255,255,0.5); letter-spacing:0.5px; margin-bottom:6px;">ℹ️ ABOUT</div>
          <div style="font-size:12px; color:rgba(255,255,255,0.7);">
            <strong>Mitra v5.0.0</strong> — Universal AI Companion<br/>
            <span style="font-size:11px; color:rgba(255,255,255,0.4);">11 capabilities: Email · Calendar · WhatsApp · Tasks · Reminders...</span>
          </div>
        </div>

        <!-- Modal Footer Actions -->
        <div style="display:flex; justify-content:flex-end; gap:10px; border-top:1px solid rgba(255,255,255,0.08); padding-top:14px;">
          <button id="btn-cancel-settings" style="background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.1); color:#fff; padding:8px 16px; border-radius:8px; font-size:12px; cursor:pointer;">Cancel</button>
          <button id="btn-save-settings" style="background:#6C5CE7; border:none; color:#fff; padding:8px 20px; border-radius:8px; font-size:12px; font-weight:600; cursor:pointer;">Save Changes</button>
        </div>
      </div>
    `;

    this.element.querySelector('#btn-close-settings').addEventListener('click', () => this.close());
    this.element.querySelector('#btn-cancel-settings').addEventListener('click', () => this.close());
    this.element.querySelector('#btn-save-settings').addEventListener('click', () => this.close());

    this.element.querySelector('#btn-save-profile').addEventListener('click', () => {
      const val = this.element.querySelector('#input-display-name').value.trim();
      if (val) {
        localStorage.setItem('mitra_user_name', val);
        alert(`Display name saved: ${val}`);
      }
    });

    const themeOpts = this.element.querySelectorAll('.theme-opt');
    themeOpts.forEach(btn => {
      btn.addEventListener('click', (e) => {
        const theme = e.target.getAttribute('data-theme');
        localStorage.setItem('mitra_theme', theme);
        applyTheme(theme);
        themeOpts.forEach(b => b.style.background = 'rgba(255,255,255,0.05)');
        e.target.style.background = '#6C5CE7';
      });
    });
  }

  open() {
    this.element.style.display = 'flex';
  }

  close() {
    this.element.style.display = 'none';
  }
}
