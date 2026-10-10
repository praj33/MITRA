import { getActiveMitraAvatar, renderAvatarElement, isVideoAsset, MITRA_CANONICAL_AVATAR_DATA_URL } from '../services/avatarHelper.js';

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
          <div class="mitra-avatar-modal-title">✨ Custom Companion System</div>
          <button class="mitra-avatar-modal-close" title="Close">✕</button>
        </div>
        
        <div class="mitra-avatar-preview-wrap">
          <div class="mitra-avatar-preview-ring" id="modal-preview-ring">
            <!-- Dynamic Image or Video Media Preview -->
          </div>
          <div class="mitra-avatar-status-badge">
            ${isCustom ? '🎨 Custom Companion Active' : '🤖 Official Default Robot Active'}
          </div>
        </div>

        <div class="mitra-supported-formats-bar">
          <span class="mitra-format-tag">PNG</span>
          <span class="mitra-format-tag">JPG</span>
          <span class="mitra-format-tag">GIF</span>
          <span class="mitra-format-tag">WebP</span>
          <span class="mitra-format-tag">MP4</span>
          <span class="mitra-format-tag">WebM</span>
          <span class="mitra-transparency-pill">✨ Transparency &amp; Animation Preserved</span>
        </div>

        <div class="mitra-avatar-dropzone" id="avatar-dropzone">
          <div class="mitra-dropzone-icon">📁</div>
          <div class="mitra-dropzone-text"><strong>Click to Upload</strong> or drag &amp; drop your asset here</div>
          <div class="mitra-dropzone-sub">Upload image, animated GIF/WebP, or MP4 video loop</div>
        </div>

        <div class="mitra-avatar-modal-actions">
          <button class="mitra-avatar-btn primary btn-upload-avatar">
            <span>📤</span> Choose File (PNG, JPG, GIF, WebP, MP4)
          </button>
          
          <button class="mitra-avatar-btn secondary btn-reset-avatar">
            <span>🤖</span> Reset to Official Robot Avatar
          </button>
        </div>

        <input type="file" class="mitra-avatar-file-hidden" accept="image/png, image/jpeg, image/gif, image/webp, image/svg+xml, video/mp4, video/webm" style="display:none;" />
      </div>
    `;

    // Render preview inside ring
    const previewRing = this.element.querySelector('#modal-preview-ring');
    if (previewRing) {
      previewRing.innerHTML = '';
      const previewEl = renderAvatarElement(activeAvatar, 'mitra-avatar-preview-img');
      previewRing.appendChild(previewEl);
    }

    // Attach event listeners
    const closeBtn = this.element.querySelector('.mitra-avatar-modal-close');
    closeBtn.addEventListener('click', () => this.close());

    this.element.addEventListener('click', (e) => {
      if (e.target === this.element) this.close();
    });

    const fileInput = this.element.querySelector('.mitra-avatar-file-hidden');
    const uploadBtn = this.element.querySelector('.btn-upload-avatar');
    const dropzone = this.element.querySelector('#avatar-dropzone');

    uploadBtn.addEventListener('click', () => {
      fileInput.click();
    });

    if (dropzone) {
      dropzone.addEventListener('click', () => {
        fileInput.click();
      });

      dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('drag-over');
      });

      dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('drag-over');
      });

      dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('drag-over');
        if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
          this.handleFileSelection(e.dataTransfer.files[0]);
        }
      });
    }

    fileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) {
        this.handleFileSelection(file);
      }
    });

    const resetBtn = this.element.querySelector('.btn-reset-avatar');
    resetBtn.addEventListener('click', () => {
      if (typeof localStorage !== 'undefined') {
        localStorage.removeItem('mitra_companion_asset');
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

  handleFileSelection(file) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (evt) => {
      const newAvatar = evt.target.result;
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem('mitra_companion_asset', newAvatar);
        localStorage.setItem('mitra_avatar_custom', newAvatar);
        localStorage.setItem('mitra_custom_avatar', newAvatar);
        localStorage.setItem('mitra_avatar_data_url', newAvatar);
      }
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

  open() {
    this.render();
    this.element.style.display = 'flex';
  }

  close() {
    this.element.style.display = 'none';
  }
}
