# INTEGRATION GUIDE: MITRA Floating Orb Companion for Artha
## Target: `https://artha.blackholeinfiverse.com`

**Author:** Antigravity (AI Engineering)  
**Date:** September 7, 2026  
**Component:** `<mitra-companion>` (Shadow DOM Encapsulated Web Component)  
**Backend API:** `https://mitra.blackholeinfiverse.com`

---

## 1. Overview

The **MITRA Floating Orb Companion** is a zero-dependency, Shadow DOM-isolated Web Component that attaches a persistent, floating AI assistant to any web application in the BHIV ecosystem.

On **Artha** (`https://artha.blackholeinfiverse.com`), MITRA provides:
* **Floating Avatar Orb**: Anchored at the bottom-right corner (`bottom: 24px, right: 24px`) with drag-and-dock capabilities and state persistence.
* **Artha Financial Context**: Detects `host_app: "artha"` automatically and routes financial queries.
* **💎 Artha Financial Analytics Card**: Formats ledger balances, transaction tables, and financial insights natively inside the chat interface.

---

## 2. Integration Options for Artha

Since Artha is a Vite/React application, there are two simple ways to integrate the companion:

### Option A: Direct HTML Script Embed (Recommended — 2 lines)
Open `index.html` in the Artha repository and insert the following snippet directly before the closing `</body>` tag:

```html
<!-- ============================================================ -->
<!-- BHIV MITRA Floating Orb Companion                             -->
<!-- ============================================================ -->
<mitra-companion 
  stylesheet-path="https://mitra.blackholeinfiverse.com/styles/mitra-companion.css" 
  api-base-url="https://mitra.blackholeinfiverse.com"
  host-app="artha">
</mitra-companion>

<script type="module" src="https://mitra.blackholeinfiverse.com/src/mitra-companion.js"></script>
```

---

### Option B: Local Asset Bundle Inside Artha (Zero External Dependency)
If you prefer not to rely on cross-origin script loading:
1. Copy the `src/` and `styles/` directories from this repo into Artha's `public/` directory (e.g., `public/mitra/src/` and `public/mitra/styles/`).
2. Add to Artha's `index.html`:
```html
<mitra-companion 
  stylesheet-path="/mitra/styles/mitra-companion.css" 
  api-base-url="https://mitra.blackholeinfiverse.com"
  host-app="artha">
</mitra-companion>

<script type="module" src="/mitra/src/mitra-companion.js"></script>
```

---

### Option C: React Lifecycle Hook (in `App.tsx`)
If you prefer to load it dynamically within React:
```tsx
import { useEffect } from 'react';

export function useMitraCompanion() {
  useEffect(() => {
    // 1. Check if custom element already defined
    if (!customElements.get('mitra-companion')) {
      const script = document.createElement('script');
      script.type = 'module';
      script.src = 'https://mitra.blackholeinfiverse.com/src/mitra-companion.js';
      document.body.appendChild(script);
    }

    // 2. Mount element if not present
    if (!document.querySelector('mitra-companion')) {
      const companion = document.createElement('mitra-companion');
      companion.setAttribute('stylesheet-path', 'https://mitra.blackholeinfiverse.com/styles/mitra-companion.css');
      companion.setAttribute('api-base-url', 'https://mitra.blackholeinfiverse.com');
      companion.setAttribute('host-app', 'artha');
      document.body.appendChild(companion);
    }
  }, []);
}
```

---

## 3. Backend CORS Requirement

When running on `https://artha.blackholeinfiverse.com`, the browser sends cross-origin requests to `https://mitra.blackholeinfiverse.com`.

### Requirement:
In the backend's environment variables or `backend/app/main.py`:
```env
CORS_ORIGINS=https://artha.blackholeinfiverse.com,https://mitra.blackholeinfiverse.com,http://localhost:3000
```
This ensures the browser does not block API calls with CORS policy errors.

---

## 4. Financial Capability Payloads

When an Artha user queries financial ledger or balance information:
1. **Query**: `"Show my ledger balance"` or `"View recent transactions"`
2. **Backend Intent**: `artha` / `samruddhi`
3. **Response Card**: The companion displays the **💎 ARTHA FINANCIAL ANALYTICS** card with green accent styling, company provenance tag, and transaction table.

---

## 5. Verification Checklist

- [x] All 16 supporting module files restored to `src/`
- [x] `controlPlane.js` prioritizes explicit `api-base-url` attribute
- [x] `controlPlane.js` detects `host-app="artha"` and `window.location.hostname.includes('artha')`
- [x] Resilient API fallback for Nginx `/api` path stripping
- [x] Dedicated Artha financial analytics card added to `ConversationPanel.js`
- [x] `pages/artha.html` standalone test portal verified in Chrome browser
- [x] Backend CORS origin added for `https://artha.blackholeinfiverse.com` in `main.py`
