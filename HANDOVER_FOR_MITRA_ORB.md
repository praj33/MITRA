# HANDOVER DOCUMENT: MITRA Floating Orb Companion
## Developer Integration Guide for Raj Prajapati & Backend Team

**Author:** Ashwini Wadekar  
**Target Collaborator:** Raj Prajapati (Backend Runtime & SETU Integration)  
**Component Name:** `<mitra-companion>` (Floating Orb Universal OS Companion)  
**Repository:** `https://github.com/praj33/MITRA.git`  
**Branches:** `main` & `master1`  
**Date:** September 4, 2026  

---

## 1. Executive Overview

The **MITRA Floating Orb Companion** is a lightweight, zero-dependency, Shadow DOM-encapsulated Web Component designed to embed seamlessly into any web page across the BHIV Ecosystem (**SETU, Artha/Samruddhi, SAMACHAR, UniGuru, and Gurukul**).

It provides:
- A persistent floating avatar orb anchored at the bottom-right corner (`bottom: 24px, right: 24px`).
- Drag-and-drop floating position and left/right side docking modes with `localStorage` state persistence.
- Shadow DOM CSS encapsulation preventing host page styling leakage.
- Real-time ecosystem capability card rendering (**SETU, SAMACHAR, UniGuru, Samruddhi/Artha, Translate**).

---

## 2. Core Floating Orb Architecture & File Map

The floating orb companion consists of the following modular files:

| File Path | Description & Responsibility |
|---|---|
| **[`src/components/MITRAButton.js`](file:///c:/Users/pc/Desktop/BHIV_ASHWINI/Mitra/src/components/MITRAButton.js)** | Renders the floating avatar orb button (`.mitra-orb`), pulsing glow animation (`.mitra-avatar-pulse`), unread badge counter, and click-to-toggle chat window event handlers. |
| **[`src/components/DockController.js`](file:///c:/Users/pc/Desktop/BHIV_ASHWINI/Mitra/src/components/DockController.js)** | Controls floating mode vs. docked left/right modes, boundary calculation, and position persistence in `localStorage`. |
| **[`src/mitra-companion.js`](file:///c:/Users/pc/Desktop/BHIV_ASHWINI/Mitra/src/mitra-companion.js)** | Entry point registering `<mitra-companion>` custom element, mounting Shadow DOM, loading CSS stylesheet, and initializing runtime event listeners. |
| **[`styles/mitra-companion.css`](file:///c:/Users/pc/Desktop/BHIV_ASHWINI/Mitra/styles/mitra-companion.css)** | Complete CSS design system for `#mitra-shell.floating`, orb animations, card layouts, dark theme tokens, and z-index isolation (`999999`). |
| **[`src/services/controlPlane.js`](file:///c:/Users/pc/Desktop/BHIV_ASHWINI/Mitra/src/services/controlPlane.js)** | Frontend control plane managing backend API fetches, host application context extraction (`getHostContext`), capability intercepts, and 40+ language dynamic translation. |
| **[`src/services/RuntimeService.js`](file:///c:/Users/pc/Desktop/BHIV_ASHWINI/Mitra/src/services/RuntimeService.js)** | Handles health pings, reminder polling, and fallback backend connection management. |

---

## 3. How to Embed the Floating Orb in Any Page

To add the MITRA Floating Orb Companion to any HTML page or web application, include the following two tags before `</body>`:

```html
<!-- 1. Web Component Element -->
<mitra-companion 
  stylesheet-path="styles/mitra-companion.css" 
  api-base-url="http://localhost:8001">
</mitra-companion>

<!-- 2. Import Module Script -->
<script type="module" src="src/mitra-companion.js?v=5"></script>
```

> **Note on `api-base-url`**:  
> During local development (`localhost` / `127.0.0.1`), `controlPlane.js` automatically resolves `getApiBaseUrl()` to `http://localhost:8001`. For production deployment on Render, update `api-base-url` to `https://mitra.blackholeinfiverse.com` or your designated backend endpoint.

---

## 4. Backend Endpoints & Payload Formats Connected

### 4.1 Canonical Chat Endpoint
- **URL:** `POST /api/mitra/chat`
- **Request Payload:**
```json
{
  "message": "Check Tea Leaves stock inventory",
  "user_id": "user_default",
  "session_id": "sess_default",
  "context": {
    "host_app": "setu",
    "current_page": "setu.html"
  }
}
```
- **Response Structure:**
```json
{
  "message": "SETU operational query processed for 'Check Tea Leaves stock inventory'",
  "intent": "setu",
  "capability_result": {
    "capability": "setu",
    "status": "success",
    "summary": "Retrieved SETU operational data",
    "data": {
      "source_context": {
        "connected_company_id": "bc_bright_connection_001",
        "connected_company_name": "Bright Connection Ltd"
      },
      "data": {
        "count": 3,
        "products": [
          {"name": "Tea Leaves Premium", "sku": "TEA-001", "price": 250, "stock_quantity": 8},
          {"name": "Organic Coffee Beans", "sku": "COF-002", "price": 450, "stock_quantity": 42},
          {"name": "Darjeeling First Flush", "sku": "TEA-003", "price": 600, "stock_quantity": 15}
        ]
      }
    }
  }
}
```

### 4.2 SETU Gateway Endpoint Wiring
- **URL:** `POST http://localhost:5000/api/mitra/execute` (Configurable via `SETU_NODE_GATEWAY`)
- **Headers:** `X-SETU-API-Key: setu_mitra_secret_key`
- **Envelope Payload:**
```json
{
  "dispatch_id": "disp_1788426000",
  "correlation_id": "trace_1788426000",
  "product_id": "prod_mitra_crm",
  "capability_id": "cap_inventory_read",
  "intent_id": "setu.inventory.lookup",
  "payload": {
    "query": "Check Tea Leaves stock inventory",
    "limit": 10
  }
}
```

### 4.3 Health Diagnostics Endpoint
- **URL:** `GET /api/companion/health`
- **Response:** `{ "status": "healthy", "timestamp": "...", "version": "2.0.0" }`

---

## 5. Ecosystem Capability Cards Supported

The floating orb dynamically renders visual capability cards inside the Shadow DOM:

1. **🔌 SETU OPERATIONAL GATEWAY Card**:  
   Triggered by queries containing `inventory`, `stock`, `tea leaves`, `setu`, or `sku`. Displays stock quantities, SKU codes, prices, and `bc_bright_connection_001` provenance badge.

2. **📰 SAMACHAR NEWS ANALYSIS Card**:  
   Triggered by queries containing `news`, `headlines`, or `samachar`. Displays live article metadata, author (`India Today News Desk`), 95% authenticity rating, and news synthesis.

3. **🎓 UNIGURU KNOWLEDGE Card**:  
   Triggered by educational/academic queries. Displays RAG textbook citations, page numbers, and Kosha lineage hashes.

4. **💎 SAMRUDDHI FINANCIAL Card**:  
   Triggered by balance/portfolio queries. Displays Tally ledger balances and multi-asset trade analytics.

5. **🌐 DYNAMIC 40+ LANGUAGE TRANSLATION Card**:  
   Triggered by queries like `Translate 'How are you?' into French/Spanish/German/Japanese/Marathi/Hindi`. Displays formal translations across 40+ global and Indian languages.

---

## 6. Verification & Sign-Off

- **Automated Hardening Suite:** `python backend/test_production_hardening.py` — **6/6 Tests Passed (100%)**.
- **Browser Compatibility:** Tested and verified on Google Chrome, Edge, and Shadow DOM isolated environments.
- **Git Branch Status:** Merged into `main` and `master1` branches on `https://github.com/praj33/MITRA.git`.

For any questions or further backend gateway enhancements, please reach out to **Ashwini Wadekar**.
