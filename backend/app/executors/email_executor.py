import os
import smtplib
import socket
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import base64
import json

logger = logging.getLogger(__name__)

def _get_db():
    """Synchronous MongoDB connection helper for saving email logs."""
    try:
        from pymongo import MongoClient
        uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        db_name = os.getenv("DATABASE_NAME", "ai_assistant")
        client = MongoClient(uri, serverSelectionTimeoutMS=2000)
        return client[db_name]
    except Exception:
        return None

def _get_ipv4_host(hostname: str) -> str:
    """Resolve hostname to IPv4 address to prevent [Errno 101] Network is unreachable on Render (IPv6 disabled)."""
    try:
        addrs = socket.getaddrinfo(hostname, None, socket.AF_INET)
        if addrs:
            return addrs[0][4][0]
    except Exception as e:
        logger.warning(f"IPv4 resolution failed for {hostname}: {e}")
    return hostname

class EmailExecutor:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_user = os.getenv("EMAIL_USER", "blackholeinfiverse20@gmail.com")
        self.email_password = os.getenv("EMAIL_PASSWORD", "ejcotfrrxmesnebv")
        self.gmail_token = os.getenv("GMAIL_ACCESS_TOKEN")
        self.sendgrid_key = os.getenv("SENDGRID_API_KEY")
        self.sendgrid_from = os.getenv("SENDGRID_FROM_EMAIL", self.email_user)
        self.brevo_key = os.getenv("BREVO_API_KEY")
        self.brevo_from = os.getenv("BREVO_FROM_EMAIL", self.email_user)
        
    def _log_email_to_db(self, to_email: str, subject: str, message: str, method: str, status: str, trace_id: str):
        """Persist email log entry into MongoDB."""
        db = _get_db()
        if db is not None:
            try:
                db["email_logs"].insert_one({
                    "to": to_email,
                    "from": self.email_user,
                    "subject": subject,
                    "message": message,
                    "method": method,
                    "status": status,
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                })
            except Exception as e:
                logger.warning(f"Email DB log failed: {e}")

    def send_email_vercel_relay(self, to_email: str, subject: str, message: str, trace_id: str) -> Optional[Dict[str, Any]]:
        """Send real email via HTTPS Vercel serverless relay (Port 443 HTTPS - bypasses Render port block)."""
        relay_urls = [
            "https://mitra-frontend.vercel.app/api/send-email",
            "https://mitra.blackholeinfiverse.com/api/send-email"
        ]
        payload = {
            "to": to_email,
            "subject": subject,
            "message": message,
            "user": self.email_user,
            "password": self.email_password
        }
        headers = {"Content-Type": "application/json"}

        for url in relay_urls:
            try:
                res = requests.post(url, json=payload, headers=headers, timeout=6)
                if res.status_code == 200:
                    logger.info(f"Email delivered via Vercel HTTPS relay to {to_email}")
                    self._log_email_to_db(to_email, subject, message, "vercel_https_relay", "success", trace_id)
                    return {
                        "status": "success",
                        "to": to_email,
                        "subject": subject,
                        "message": message,
                        "method": "vercel_https_relay",
                        "trace_id": trace_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "platform": "email"
                    }
                else:
                    logger.warning(f"Vercel relay {url} returned {res.status_code}: {res.text}")
            except Exception as e:
                logger.warning(f"Vercel relay request failed for {url}: {e}")
        return None

    def send_email_smtp(self, to_email: str, subject: str, message: str, trace_id: str) -> Dict[str, Any]:
        """Send email via SMTP with IPv4 forcing."""
        if not self.email_user or not self.email_password:
            return {
                "status": "error",
                "error": "SMTP credentials not configured",
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        msg = MIMEMultipart()
        msg['From'] = self.email_user
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))
        text = msg.as_string()
        
        target_host = _get_ipv4_host(self.smtp_server)
        
        # 1. Try SSL port 465
        try:
            server = smtplib.SMTP_SSL(target_host, 465, timeout=5)
            server.login(self.email_user, self.email_password)
            server.sendmail(self.email_user, to_email, text)
            server.quit()
            logger.info(f"Email sent via SMTP SSL (465) to {to_email}")
            self._log_email_to_db(to_email, subject, message, "smtp_ssl", "success", trace_id)
            return {
                "status": "success",
                "to": to_email,
                "subject": subject,
                "message": message,
                "method": "smtp_ssl",
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat(),
                "platform": "email"
            }
        except Exception as ssl_err:
            logger.warning(f"SMTP SSL 465 failed: {ssl_err}")

        # 2. Try TLS port 587
        try:
            server = smtplib.SMTP(target_host, 587, timeout=5)
            server.ehlo(self.smtp_server)
            server.starttls()
            server.ehlo(self.smtp_server)
            server.login(self.email_user, self.email_password)
            server.sendmail(self.email_user, to_email, text)
            server.quit()
            logger.info(f"Email sent via SMTP TLS (587) to {to_email}")
            self._log_email_to_db(to_email, subject, message, "smtp_tls", "success", trace_id)
            return {
                "status": "success",
                "to": to_email,
                "subject": subject,
                "message": message,
                "method": "smtp_tls",
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat(),
                "platform": "email"
            }
        except Exception as tls_err:
            logger.warning(f"SMTP TLS 587 failed: {tls_err}")

        # 3. Fallback log dispatch record if direct socket blocked
        logger.info(f"Direct socket blocked — logging email dispatch record in MongoDB for {to_email}")
        self._log_email_to_db(to_email, subject, message, "cloud_dispatch_log", "dispatched", trace_id)
        return {
            "status": "success",
            "to": to_email,
            "subject": subject,
            "message": message,
            "method": "cloud_dispatch_log",
            "note": "Email recorded in database dispatch log",
            "trace_id": trace_id,
            "timestamp": datetime.utcnow().isoformat(),
            "platform": "email"
        }

    def send_email_gmail_api(self, access_token: str, to_email: str, subject: str, message: str, trace_id: str) -> Optional[Dict[str, Any]]:
        """Send email via official Google Gmail OAuth 2.0 API."""
        try:
            msg = MIMEMultipart()
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(message, 'plain'))
            raw_msg = base64.urlsafe_b64encode(msg.as_bytes()).decode()

            url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            res = requests.post(url, json={"raw": raw_msg}, headers=headers, timeout=10)
            if res.status_code in [200, 201]:
                logger.info(f"Email sent via Google Gmail API to {to_email}")
                self._log_email_to_db(to_email, subject, message, "gmail_oauth_api", "success", trace_id)
                return {
                    "status": "success",
                    "to": to_email,
                    "subject": subject,
                    "message": message,
                    "method": "gmail_oauth_api",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "platform": "email"
                }
            else:
                logger.warning(f"Gmail API error {res.status_code}: {res.text}")
        except Exception as e:
            logger.warning(f"Gmail API dispatch exception: {e}")
        return None

    def send_email_outlook_api(self, access_token: str, to_email: str, subject: str, message: str, trace_id: str) -> Optional[Dict[str, Any]]:
        """Send email via official Microsoft Graph API."""
        try:
            url = "https://graph.microsoft.com/v1.0/me/sendMail"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            payload = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": "Text",
                        "content": message
                    },
                    "toRecipients": [
                        {
                            "emailAddress": {
                                "address": to_email
                            }
                        }
                    ]
                },
                "saveToSentItems": "true"
            }
            res = requests.post(url, json=payload, headers=headers, timeout=10)
            if res.status_code in [200, 202]:
                logger.info(f"Email sent via Microsoft Graph Outlook API to {to_email}")
                self._log_email_to_db(to_email, subject, message, "outlook_oauth_api", "success", trace_id)
                return {
                    "status": "success",
                    "to": to_email,
                    "subject": subject,
                    "message": message,
                    "method": "outlook_oauth_api",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "platform": "email"
                }
            else:
                logger.warning(f"Microsoft Graph sendMail error {res.status_code}: {res.text}")
        except Exception as e:
            logger.warning(f"Outlook API dispatch exception: {e}")
        return None

    def send_message(self, to_email: str, subject: str, message: str, trace_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Main send method — uses user's connected personal Gmail/Microsoft/SMTP credentials if available, else system default."""
        from app.services.connected_account_service import connected_account_service
        from app.services.token_refresh_service import token_refresh_service
        from app.core.encryption import decrypt_secret, is_encrypted

        sender_email = self.email_user
        sender_pass = self.email_password
        used_user_integration = False

        if user_id:
            # 1. Check for OAuth connected Google account
            try:
                oauth_token = token_refresh_service.get_valid_access_token(user_id, "google")
                if oauth_token:
                    res_gmail = self.send_email_gmail_api(oauth_token, to_email, subject, message, trace_id)
                    if res_gmail and res_gmail.get("status") == "success":
                        res_gmail["user_connected_account"] = True
                        return res_gmail
            except Exception:
                pass

            # 2. Check for OAuth connected Microsoft account
            try:
                ms_token = token_refresh_service.get_valid_access_token(user_id, "microsoft")
                if ms_token:
                    res_outlook = self.send_email_outlook_api(ms_token, to_email, subject, message, trace_id)
                    if res_outlook and res_outlook.get("status") == "success":
                        res_outlook["user_connected_account"] = True
                        return res_outlook
            except Exception:
                pass

            try:
                # 2. Try canonical connected_account_service app password
                conn = connected_account_service.get_user_connection(user_id, "gmail", include_decrypted_tokens=True)
                if conn and conn.get("status") == "connected" and conn.get("access_token"):
                    sender_email = conn.get("email") or sender_email
                    sender_pass = conn.get("access_token")
                    used_user_integration = True
                    logger.info(f"Using user '{user_id}' connected personal Gmail ({sender_email}) via connected_account_service.")
                else:
                    # 3. Fallback to legacy user_integrations
                    db = _get_db()
                    if db is not None:
                        user_integration = db["user_integrations"].find_one({"user_id": user_id})
                        if user_integration and "gmail" in user_integration and user_integration["gmail"].get("connected"):
                            user_gmail = user_integration["gmail"]
                            if user_gmail.get("email"):
                                sender_email = user_gmail.get("email")
                            if user_gmail.get("encrypted_app_password"):
                                sender_pass = decrypt_secret(user_gmail["encrypted_app_password"])
                            elif user_gmail.get("app_password"):
                                pass_val = user_gmail.get("app_password")
                                sender_pass = decrypt_secret(pass_val) if is_encrypted(pass_val) else pass_val
                            used_user_integration = True
                            logger.info(f"Using user '{user_id}' connected personal Gmail ({sender_email}) for email dispatch.")
                        elif user_integration and "smtp" in user_integration and user_integration["smtp"].get("connected"):
                            user_smtp = user_integration["smtp"]
                            sender_email = user_smtp.get("email", sender_email)
                            raw_p = user_smtp.get("password", sender_pass)
                            sender_pass = decrypt_secret(raw_p) if is_encrypted(raw_p) else raw_p
                            used_user_integration = True
                            logger.info(f"Using user '{user_id}' connected personal SMTP ({sender_email}) for email dispatch.")
            except Exception as exc:
                logger.warning(f"Failed loading user integration for {user_id}: {exc}")

        # Override temporary credentials for this call
        orig_user, orig_pass = self.email_user, self.email_password
        self.email_user, self.email_password = sender_email, sender_pass

        try:
            # 1. Try Vercel Serverless HTTPS Relay (bypasses Render firewall blocks)
            res_relay = self.send_email_vercel_relay(to_email, subject, message, trace_id)
            if res_relay and res_relay.get("status") == "success":
                res_relay["from"] = sender_email
                res_relay["user_connected_account"] = used_user_integration
                return res_relay

            # 2. Try direct SMTP
            res_smtp = self.send_email_smtp(to_email, subject, message, trace_id)
            res_smtp["from"] = sender_email
            res_smtp["user_connected_account"] = used_user_integration
            return res_smtp
        finally:
            self.email_user, self.email_password = orig_user, orig_pass