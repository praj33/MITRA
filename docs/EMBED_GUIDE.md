# MITRA Universal Companion — Integration & Embed Guide 🚀

> **Canonical Companion Layer — BHIV Ecosystem**  
> *One continuous companion across all BHIV applications.*

---

## 1. Quick Integration (1-Line HTML Embed)

Add the following `<script>` tag to the HTML `<head>` or before `</body>` of any BHIV application (**Gurukul**, **Samruddhi**, **SETU**, Prana, etc.):

```html
<!-- MITRA Universal Companion Embed -->
<script 
  src="https://mitra.blackholeinfiverse.com/mitra-hover.js"
  data-app-id="gurukul"
  data-user-id="user_123"
  data-position="bottom-right"
  async>
</script>
```

---

## 2. Targeted VM-Hosted Ecosystem Applications

- **Gurukul**: `https://gurukul.blackholeinfiverse.com`
- **Samruddhi**: `https://samruddhi.blackholeinfiverse.com`
- **TANTRA Governed Runtime (Ashmit)**: `https://bhiv-mitra.onrender.com`
- **MITRA Companion Backend**: `https://mitra-backend.onrender.com`
- **MITRA CDN & App**: `https://mitra.blackholeinfiverse.com`


---

## 2. Configuration Options (`data-*` Attributes)

| Attribute | Type | Default | Description |
|---|---|---|---|
| `data-app-id` | `string` | `"universal_app"` | Identifier of the host application (e.g. `gurukul`, `samruddhi`, `setu`, `prana`). |
| `data-user-id` | `string` | `"user_default"` | Unique identifier of the logged-in user for session continuity. |
| `data-position` | `string` | `"bottom-right"` | Screen placement: `"bottom-right"` or `"bottom-left"`. |
| `data-api-base` | `string` | `"https://mitra-backend.onrender.com"` | Base URL for MITRA API services. |

---

## 3. Features Included Out-of-the-Box
* **Floating Glassmorphic Bubble Widget**: Animated avatar button at screen corner.
* **Cross-Product Session Continuity**: Automatically preserves session history in `localStorage` across BHIV products.
* **Speech-to-Text (STT)**: Microphone button for hands-free voice commands.
* **Text-to-Speech (TTS)**: Spoken voice responses out loud.
* **UniGuru Intelligence Engine**: Evaluates responses using governance rules (Safety, Authority, Delegation, Emotional).

---

## 4. API Endpoints Used by Embed Widget
- `POST /api/companion/chat`: Main conversation endpoint.
- `GET /api/companion/greeting/{user_id}`: Timezone-aware IST greetings.
- `GET /api/companion/capabilities`: Available tools & execution capabilities.

---

**Maintained by**: Raj Prajapati & BHIV Core Team  
**Repository**: `https://github.com/praj33/MITRA.git`
