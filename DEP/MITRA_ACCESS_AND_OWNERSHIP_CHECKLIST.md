# MITRA â€” Access, Infrastructure, and Ownership Checklist

> **Document Type:** Operational Access Control & Security Transfer Artifact
> **Source of Truth:** Infrastructure Providers, Cloud Portals, GitHub Organization Permissions
> **Repository:** `https://github.com/praj33/MITRA.git`
> **Target Technical Owner:** Ashwini Wadekar
> **Target Product Owner:** Riddhi
> **Status:** **TRANSFERRED / PROTOCOL ESTABLISHED** *(Reviewed and acknowledged during the completed in-person handover)*

---

> [!IMPORTANT]
> **CREDENTIAL SECURITY POLICY:**
> Do NOT store raw passwords, SSH private keys, API keys, OAuth client secrets, or database connection strings in this document or in any repository commit.
> **Credential transfer must occur through the approved secure organizational mechanism** (e.g., 1Password, Bitwarden, HashiCorp Vault, or encrypted GPG transfer).

---

## 1. Comprehensive Access Transfer Matrix

| System / Resource | Resource Description & URL | Recommended Owner | Access Verified? | Verification Date | Transfer / Auth Method | Operational Notes |
|---|---|---|---|---|---|---|
| **GitHub Repository** | `https://github.com/praj33/MITRA.git` | Ashwini Wadekar | **PENDING** | `[Pending]` | GitHub Admin Invite | Grant Maintainer/Admin access; configure branch protection on `main`. |
| **Production Cloud VM** | Remote Ubuntu 22.04 LTS VM hosting Docker | Ashwini Wadekar | **PENDING** | `[Pending]` | SSH Key Pair Exchange | Add Ashwini's public SSH key to `~/.ssh/authorized_keys`; verify `sudo` permissions. |
| **Docker Hub Registry** | `bhiv/mitra-backend`, `bhiv/mitra-frontend` | Ashwini Wadekar | **PENDING** | `[Pending]` | Docker Hub Org Invite | Ensure push/pull permissions to `bhiv` organization repository. |
| **Production Domain / DNS** | `mitra.blackholeinfiverse.com` (Cloudflare / Registrar) | Ashwini Wadekar | **PENDING** | `[Pending]` | DNS Console Role | Ensure access to DNS A-records pointing to the production VM IP. |
| **Google Cloud Console** | Project hosting OAuth 2.0 Client credentials | Ashwini Wadekar | **PENDING** | `[Pending]` | GCP IAM Owner / Editor | Grant access to manage OAuth consent screen, scopes, and test users. |
| **MongoDB Atlas** | Dedicated / Serverless cluster (`DATABASE_NAME=ai_assistant`) | Ashwini Wadekar | **PENDING** | `[Pending]` | Atlas Org User Invite | Grant Project Data Access and Network Access IP whitelist permissions. |
| **GitHub Actions Secrets** | Repository Secrets (`VM_PASSWORD`, `MONGODB_URI`, etc.) | Ashwini Wadekar | **PENDING** | `[Pending]` | GitHub Settings Access | Verify visibility and ability to rotate repository action secrets. |
| **OpenAI Developer Portal** | API Key organization management | Ashwini Wadekar | **PENDING** | `[Pending]` | OpenAI Org Invite | Verify billing quota and API key issuance authority. |
| **Tavily Search Portal** | News and web search intelligence API key | Ashwini Wadekar | **PENDING** | `[Pending]` | Tavily Account Invite | Verify monthly credit quota for Samachar capability queries. |
| **Meta for Developers** | WhatsApp Business Cloud API App & System Users | Ashwini Wadekar | **PENDING** | `[Pending]` | Meta Business Admin | Grant access to WhatsApp App configuration, webhooks, and phone number IDs. |
| **Microsoft Azure Portal** | App Registrations for Microsoft 365 OAuth | Ashwini Wadekar | **PENDING** | `[Pending]` | Azure AD Contributor | Grant access to configure redirect URIs and Graph API permissions. |
| **Sentry / APM Monitoring** | Error tracking and exception monitoring | Ashwini Wadekar | **PENDING** | `[Pending]` | Sentry Org Invite | Verify alerts and project DSN configuration. |
| **Figma / UX Assets** | Design system tokens, wireframes, component library | Riddhi | **PENDING** | `[Pending]` | Figma Team Editor | Grant edit access to MITRA design workspace and UI components. |

---

## 2. Infrastructure Ownership Transition Verification

### Step-by-Step Verification Protocol for Ashwini
1. [ ] Log in to GitHub and verify write/admin permissions on `https://github.com/praj33/MITRA`.
2. [ ] Test SSH access to the production VM using your individual key:
   ```bash
   ssh -p <VM_PORT> <ASHWINI_USER>@<VM_IP>
   ```
3. [ ] Verify Docker permissions on VM:
   ```bash
   docker ps
   docker compose version
   ```
4. [ ] Access the MongoDB Atlas web console and verify ability to view the `ai_assistant` database and collections (`users`, `pending_actions`, `audit_collection`, `companion_memories`).
5. [ ] Access Google Cloud Console and inspect the OAuth Consent Screen configuration for the `blackholeinfiverse.com` project.
6. [ ] Confirm access to the secure credential vault (1Password / Bitwarden) where production `.env` backups are stored.

---

## 3. Receiving Owners Confirmation

```
================================================================================
ACCESS PROTOCOL STATUS: TRANSFERRED & ACKNOWLEDGED
================================================================================

Technical Owner:
Name: Ashwini Wadekar
Status: Access matrix, credentials handling protocol, and infrastructure roles reviewed and acknowledged.
Confirmation: Acknowledged during completed in-person walkthrough.

Product Owner:
Name: Riddhi
Status: Product assets, UX guidelines, and design access channels reviewed and acknowledged.
Confirmation: Acknowledged during completed in-person walkthrough.

Transferor:
Name: Raj Prajapati
Status: Infrastructure and repository access provisioning established.
Confirmation: Completed during in-person walkthrough.
================================================================================
```
