import { getActiveMitraAvatar, renderAvatarElement, MITRA_CANONICAL_AVATAR_DATA_URL } from '../services/avatarHelper.js';

export class AvatarModal {
  constructor(eventBus, contextStore) {
    this.eventBus = eventBus;
    this.contextStore = contextStore;
    this.element = document.createElement('div');
    this.element.className = 'mitra-avatar-modal-overlay';
    this.element.style.display = 'none';

    this.render();
  }

  render() {
    const activeAvatar = getActiveMitraAvatar(this.contextStore);
    const isCustom = this.contextStore && this.contextStore.getAvatar() && this.contextStore.getAvatar() !== 'default' && this.contextStore.getAvatar().length > 20;

    this.element.innerHTML = `
      <div class="mitra-avatar-modal-card">
        <div class="mitra-avatar-modal-header">
          <div class="mitra-avatar-modal-title">✨ Customize MITRA Avatar</div>
          <button class="mitra-avatar-modal-close" title="Close">✕</button>
        </div>
        
        <div class="mitra-avatar-preview-wrap">
          <div class="mitra-avatar-preview-ring">
            <img src="${activeAvatar}" class="mitra-avatar-preview-img" alt="Current Avatar" />
          </div>
          <div class="mitra-avatar-status-badge">
            ${isCustom ? '🎨 Custom Avatar Active' : '🤖 Official Default Avatar'}
          </div>
        </div>

        <div class="mitra-avatar-modal-actions">
          <button class="mitra-avatar-btn primary btn-upload-avatar">
            <span>📤</span> Upload New Avatar (Photo / GIF)
          </button>
          
          <button class="mitra-avatar-btn secondary btn-reset-avatar">
            <span>🤖</span> Reset to Official Robot Avatar
          </button>
        </div>

        <input type="file" class="mitra-avatar-file-hidden" accept="image/png, image/jpeg, image/gif, image/webp, video/mp4, video/webm" style="display:none;" />
      </div>
    `;

    // Attach event listeners
    const closeBtn = this.element.querySelector('.mitra-avatar-modal-close');
    closeBtn.addEventListener('click', () => this.close());

    this.element.addEventListener('click', (e) => {
      if (e.target === this.element) this.close();
    });

    const fileInput = this.element.querySelector('.mitra-avatar-file-hidden');
    const uploadBtn = this.element.querySelector('.btn-upload-avatar');
    uploadBtn.addEventListener('click', () => {
      fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (evt) => {
          const newAvatar = evt.target.result;
          if (this.contextStore) {
            this.contextStore.setAvatar(newAvatar);
          }
          if (this.eventBus) {
            this.eventBus.emit('avatar.changed', { avatar: newAvatar });
          }
          this.close();
        };
        reader.readAsDataURL(file);
      }
    });

    const resetBtn = this.element.querySelector('.btn-reset-avatar');
    resetBtn.addEventListener('click', () => {
      if (typeof localStorage !== 'undefined') {
        localStorage.removeItem('mitra_avatar_data_url');
        localStorage.removeItem('mitra_avatar_custom');
        localStorage.removeItem('mitra_custom_avatar');
      }
      if (this.contextStore) {
        this.contextStore.setAvatar('default');
      }
      if (this.eventBus) {
        this.eventBus.emit('avatar.changed', { avatar: 'default' });
      }
      this.close();
    });
  }

  open() {
    this.render();
    this.element.style.display = 'flex';
  }

  close() {
    this.element.style.display = 'none';
  }
}
