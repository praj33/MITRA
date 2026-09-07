/**
 * Helper to dynamically render an image or video avatar element.
 * Supports PNG, JPG, GIF, WebP, and MP4/WebM videos.
 */
export function renderAvatarElement(avatarDataUrl, className = 'mitra-avatar-media') {
  if (!avatarDataUrl) return null;
  
  const isVideo = avatarDataUrl.startsWith('data:video/') || 
                  avatarDataUrl.endsWith('.mp4') || 
                  avatarDataUrl.endsWith('.webm');
                  
  if (isVideo) {
    const video = document.createElement('video');
    video.className = className;
    video.src = avatarDataUrl;
    video.autoplay = true;
    video.loop = true;
    video.muted = true;
    video.playsInline = true;
    video.setAttribute('playsinline', '');
    video.style.width = '100%';
    video.style.height = '100%';
    video.style.objectFit = 'cover';
    video.style.borderRadius = '50%';
    video.style.pointerEvents = 'none';
    video.draggable = false;
    return video;
  } else {
    const img = document.createElement('img');
    img.className = className;
    img.src = avatarDataUrl;
    img.style.width = '100%';
    img.style.height = '100%';
    img.style.objectFit = 'cover';
    img.style.borderRadius = '50%';
    img.style.pointerEvents = 'none';
    img.draggable = false;
    return img;
  }
}
