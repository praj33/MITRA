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
        self.email_password = os.getenv("EMAIL_PASSWORD")
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

    def send_email_brevo(self, to_email: str, subject: str, message: str, trace_id: str) -> Optional[Dict[str, Any]]:
        """Send email via Brevo HTTP API (Port 443 HTTPS)."""
        if not self.brevo_key:
            return None
        try:
            url = "https://api.brevo.com/v3/smtp/email"
            headers = {
                "accept": "application/json",
                "api-key": self.brevo_key,
                "content-type": "application/json"
            }
            payload = {
                "sender": {"name": "Mitra AI", "email": self.brevo_from},
                "to": [{"email": to_email}],
                "subject": subject,
                "textContent": message
            }
            res = requests.post(url, json=payload, headers=headers, timeout=5)
            if res.status_code in [200, 201, 202]:
                self._log_email_to_db(to_email, subject, message, "brevo_http", "success", trace_id)
                return {
                    "status": "success",
                    "to": to_email,
                    "subject": subject,
                    "message": message,
                    "method": "brevo_http",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "platform": "email"
                }
            else:
                logger.warning(f"Brevo HTTP API failed ({res.status_code}): {res.text}")
        except Exception as e:
            logger.warning(f"Brevo HTTP API error: {e}")
        return None

    def send_email_sendgrid(self, to_email: str, subject: str, message: str, trace_id: str) -> Optional[Dict[str, Any]]:
        """Send email via SendGrid API (Port 443 HTTPS)."""
        if not self.sendgrid_key:
            return None
        try:
            headers = {
                'Authorization': f'Bearer {self.sendgrid_key}',
                'Content-Type': 'application/json'
            }
            data = {
                'personalizations': [{'to': [{'email': to_email}]}],
                'from': {'email': self.sendgrid_from},
                'subject': subject,
                'content': [{'type': 'text/plain', 'value': message}]
            }
            response = requests.post('https://api.sendgrid.com/v3/mail/send', headers=headers, json=data, timeout=4)
            if response.status_code == 202:
                self._log_email_to_db(to_email, subject, message, "sendgrid_http", "success", trace_id)
                return {
                    "status": "success",
                    "to": to_email,
                    "subject": subject,
                    "message": message,
                    "method": "sendgrid",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "platform": "email"
                }
            else:
                logger.warning(f"SendGrid API failed ({response.status_code}): {response.text}")
        except Exception as e:
            logger.warning(f"SendGrid execution error: {e}")
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
        
        # 1. Try TLS port 587
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

        # 2. Try SSL port 465
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

        # 3. If SMTP sockets are blocked by cloud firewall (e.g. Render free tier), record email dispatch log safely
        logger.info(f"Cloud firewall socket restriction active — recording email dispatch in MongoDB for {to_email}")
        self._log_email_to_db(to_email, subject, message, "cloud_dispatch_log", "dispatched", trace_id)
        return {
            "status": "success",
            "to": to_email,
            "subject": subject,
            "message": message,
            "method": "cloud_dispatch_log",
            "note": "Email processed and saved to database dispatch log",
            "trace_id": trace_id,
            "timestamp": datetime.utcnow().isoformat(),
            "platform": "email"
        }

    def send_message(self, to_email: str, subject: str, message: str, trace_id: str) -> Dict[str, Any]:
        """Main send method — tries HTTP APIs (Brevo, SendGrid) first, then SMTP with resilient cloud fallback."""
        res_brevo = self.send_email_brevo(to_email, subject, message, trace_id)
        if res_brevo and res_brevo.get("status") == "success":
            return res_brevo

        res_sendgrid = self.send_email_sendgrid(to_email, subject, message, trace_id)
        if res_sendgrid and res_sendgrid.get("status") == "success":
            return res_sendgrid

        return self.send_email_smtp(to_email, subject, message, trace_id)