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

import ipaddress

BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),      # IPv4 loopback
    ipaddress.ip_network("10.0.0.0/8"),       # RFC 1918 private
    ipaddress.ip_network("172.16.0.0/12"),    # RFC 1918 private
    ipaddress.ip_network("192.168.0.0/16"),   # RFC 1918 private
    ipaddress.ip_network("169.254.0.0/16"),   # Link-local / Cloud metadata (includes 169.254.169.254)
    ipaddress.ip_network("100.64.0.0/10"),    # Carrier-grade NAT
    ipaddress.ip_network("0.0.0.0/8"),        # Current network
    ipaddress.ip_network("224.0.0.0/4"),      # Multicast
    ipaddress.ip_network("240.0.0.0/4"),      # Reserved
    ipaddress.ip_network("::1/128"),          # IPv6 loopback
    ipaddress.ip_network("fe80::/10"),        # IPv6 link-local
    ipaddress.ip_network("fc00::/7"),         # IPv6 unique local (private)
    ipaddress.ip_network("::/128"),           # IPv6 unspecified
]

def validate_safe_mail_host(hostname: str) -> str:
    """
    Validate that hostname does not resolve to loopback, private RFC 1918, link-local,
    or cloud metadata IP addresses (SSRF protection).
    Returns the resolved safe IPv4 address for socket connections.
    """
    if not hostname or not isinstance(hostname, str):
        raise ValueError("Invalid mail hostname: hostname is required.")

    clean_host = hostname.strip().lower()

    # Block localhost explicitly
    if clean_host in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
        raise ValueError(f"Connection to '{clean_host}' is blocked (SSRF protection).")

    # Resolve all addresses (both IPv4 and IPv6)
    try:
        addr_info = socket.getaddrinfo(clean_host, None)
    except socket.gaierror as e:
        raise ValueError(f"Failed to resolve mail host '{clean_host}': {e}")
    except Exception as e:
        raise ValueError(f"DNS resolution error for mail host '{clean_host}': {e}")

    if not addr_info:
        raise ValueError(f"No IP addresses resolved for mail host '{clean_host}'.")

    resolved_ipv4 = None

    for item in addr_info:
        ip_str = item[4][0]
        try:
            ip_obj = ipaddress.ip_address(ip_str)
        except ValueError:
            raise ValueError(f"Invalid resolved IP '{ip_str}' for mail host '{clean_host}'.")

        # Check against all blocked networks and properties
        if (
            ip_obj.is_loopback
            or ip_obj.is_private
            or ip_obj.is_link_local
            or ip_obj.is_multicast
            or ip_obj.is_reserved
            or ip_obj.is_unspecified
        ):
            raise ValueError(f"Connection to restricted network address '{ip_str}' is blocked (SSRF protection).")

        for net in BLOCKED_IP_NETWORKS:
            if ip_obj in net:
                raise ValueError(f"Connection to restricted network address '{ip_str}' in '{net}' is blocked (SSRF protection).")

        if isinstance(ip_obj, ipaddress.IPv4Address) and resolved_ipv4 is None:
            resolved_ipv4 = ip_str

    return resolved_ipv4 or addr_info[0][4][0]

def _get_ipv4_host(hostname: str) -> str:
    """Resolve and validate hostname with SSRF protection."""
    return validate_safe_mail_host(hostname)

class EmailExecutor:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com").strip()
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_user = os.getenv("EMAIL_USER", "").strip()
        self.email_password = os.getenv("EMAIL_PASSWORD", "").strip()
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
                    "from": self.email_user or "user_connected_account",
                    "subject": subject,
                    "message": message,
                    "method": method,
                    "status": status,
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                })
            except Exception as e:
                logger.warning(f"Email DB log failed: {e}")

    def send_email_smtp(
        self,
        to_email: str,
        subject: str,
        message: str,
        trace_id: str,
        sender_email: Optional[str] = None,
        sender_pass: Optional[str] = None,
        smtp_server: Optional[str] = None,
        smtp_port: Optional[int] = None
    ) -> Dict[str, Any]:
        """Send email via SMTP with SSRF-safe hostname validation and TLS verification."""
        user = (sender_email or self.email_user or "").strip()
        password = (sender_pass or self.email_password or "").strip()
        host = (smtp_server or self.smtp_server or "").strip()
        port = smtp_port or self.smtp_port or 587

        if not user or not password:
            return {
                "status": "error",
                "error": "SMTP credentials not configured",
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat()
            }

        try:
            target_host = _get_ipv4_host(host)
        except ValueError as ssrf_err:
            logger.warning("SMTP host SSRF rejection for '%s': %s", host, ssrf_err)
            return {
                "status": "error",
                "error": str(ssrf_err),
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat()
            }

        msg = MIMEMultipart()
        msg['From'] = user
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))
        text = msg.as_string()

        import ssl
        ssl_ctx = ssl.create_default_context()

        # 1. Try SSL port 465 if configured or default
        if port == 465:
            try:
                server = smtplib.SMTP_SSL(target_host, 465, context=ssl_ctx, timeout=8)
                server.login(user, password)
                server.sendmail(user, to_email, text)
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
                return {
                    "status": "error",
                    "error": f"SMTP SSL delivery failed: {str(ssl_err)}",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat()
                }

        # 2. Try STARTTLS port 587
        try:
            server = smtplib.SMTP(target_host, port, timeout=8)
            server.ehlo(host)
            server.starttls(context=ssl_ctx)
            server.ehlo(host)
            server.login(user, password)
            server.sendmail(user, to_email, text)
            server.quit()
            logger.info(f"Email sent via SMTP TLS ({port}) to {to_email}")
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
            logger.warning(f"SMTP TLS {port} failed: {tls_err}")
            return {
                "status": "error",
                "error": f"SMTP TLS delivery failed: {str(tls_err)}",
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat()
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

    def send_message(
        self,
        to_email: str,
        subject: str,
        message: str,
        trace_id: str,
        user_id: Optional[str] = None,
        is_system_action: bool = False
    ) -> Dict[str, Any]:
        """
        Send email message.
        - For user-owned actions (is_system_action=False): requires valid user_id and an authorized
          connected account (Google OAuth, Microsoft OAuth, or verified user SMTP).
          NEVER falls back to system credentials or another user's credentials.
        - For system actions (is_system_action=True): uses system SMTP credentials if configured.
        """
        from app.services.connected_account_service import connected_account_service
        from app.services.token_refresh_service import token_refresh_service
        from app.core.encryption import decrypt_secret, is_encrypted

        clean_user_id = str(user_id).strip() if user_id else ""

        # 1. Enforce user ownership for user-directed communication
        if not is_system_action:
            if not clean_user_id or clean_user_id.lower() in ("user_default", "default", "none", "null"):
                logger.warning(
                    "EmailExecutor rejected user action: missing or invalid authenticated user_id '%s'",
                    clean_user_id
                )
                return {
                    "status": "error",
                    "error": "Authentication required: user-owned email actions require a valid authenticated user identity.",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat()
                }

            # 1a. Try Google OAuth
            try:
                oauth_token = token_refresh_service.get_valid_access_token(clean_user_id, "google")
                if oauth_token:
                    res_gmail = self.send_email_gmail_api(oauth_token, to_email, subject, message, trace_id)
                    if res_gmail and res_gmail.get("status") == "success":
                        res_gmail["user_connected_account"] = True
                        return res_gmail
                    elif res_gmail and res_gmail.get("status") == "error":
                        return res_gmail
            except Exception as e:
                logger.warning("Google OAuth dispatch error for %s: %s", clean_user_id, e)

            # 1b. Try Microsoft OAuth
            try:
                ms_token = token_refresh_service.get_valid_access_token(clean_user_id, "microsoft")
                if ms_token:
                    res_outlook = self.send_email_outlook_api(ms_token, to_email, subject, message, trace_id)
                    if res_outlook and res_outlook.get("status") == "success":
                        res_outlook["user_connected_account"] = True
                        return res_outlook
                    elif res_outlook and res_outlook.get("status") == "error":
                        return res_outlook
            except Exception as e:
                logger.warning("Microsoft OAuth dispatch error for %s: %s", clean_user_id, e)

            # 1c. Try canonical connected_account_service app password
            try:
                conn = connected_account_service.get_user_connection(clean_user_id, "gmail", include_decrypted_tokens=True)
                if conn and conn.get("status") == "connected" and conn.get("access_token"):
                    sender_email = conn.get("email") or ""
                    sender_pass = conn.get("access_token")
                    logger.info("Using user '%s' connected personal Gmail (%s) via connected_account_service.", clean_user_id, sender_email)
                    res = self.send_email_smtp(
                        to_email=to_email,
                        subject=subject,
                        message=message,
                        trace_id=trace_id,
                        sender_email=sender_email,
                        sender_pass=sender_pass,
                        smtp_server="smtp.gmail.com",
                        smtp_port=587
                    )
                    res["user_connected_account"] = True
                    return res
            except Exception as exc:
                logger.warning("Connected account app password error for %s: %s", clean_user_id, exc)

            # 1d. Try connected custom SMTP
            try:
                conn_smtp = connected_account_service.get_user_connection(clean_user_id, "smtp", include_decrypted_tokens=True)
                if conn_smtp and conn_smtp.get("status") == "connected" and conn_smtp.get("access_token"):
                    extra = conn_smtp.get("extra_data", {})
                    smtp_server = extra.get("smtp_server") or self.smtp_server
                    smtp_port = int(extra.get("smtp_port") or 587)
                    res = self.send_email_smtp(
                        to_email=to_email,
                        subject=subject,
                        message=message,
                        trace_id=trace_id,
                        sender_email=conn_smtp.get("email"),
                        sender_pass=conn_smtp.get("access_token"),
                        smtp_server=smtp_server,
                        smtp_port=smtp_port
                    )
                    res["user_connected_account"] = True
                    return res
            except Exception as exc:
                logger.warning("Connected custom SMTP error for %s: %s", clean_user_id, exc)

            # 1e. Fallback to legacy user_integrations with decryption
            db = _get_db()
            if db is not None:
                try:
                    user_integration = db["user_integrations"].find_one({"user_id": clean_user_id})
                    if user_integration and "gmail" in user_integration and user_integration["gmail"].get("connected"):
                        user_gmail = user_integration["gmail"]
                        sender_email = user_gmail.get("email") or ""
                        pass_val = user_gmail.get("encrypted_app_password") or user_gmail.get("app_password")
                        sender_pass = decrypt_secret(pass_val) if is_encrypted(pass_val) else pass_val
                        logger.info("Using user '%s' personal Gmail (%s) from user_integrations.", clean_user_id, sender_email)
                        res = self.send_email_smtp(
                            to_email=to_email,
                            subject=subject,
                            message=message,
                            trace_id=trace_id,
                            sender_email=sender_email,
                            sender_pass=sender_pass,
                            smtp_server="smtp.gmail.com",
                            smtp_port=587
                        )
                        res["user_connected_account"] = True
                        return res
                    elif user_integration and "smtp" in user_integration and user_integration["smtp"].get("connected"):
                        user_smtp = user_integration["smtp"]
                        sender_email = user_smtp.get("email") or ""
                        raw_p = user_smtp.get("password") or ""
                        sender_pass = decrypt_secret(raw_p) if is_encrypted(raw_p) else raw_p
                        smtp_server = user_smtp.get("smtp_server") or self.smtp_server
                        smtp_port = int(user_smtp.get("smtp_port") or 587)
                        res = self.send_email_smtp(
                            to_email=to_email,
                            subject=subject,
                            message=message,
                            trace_id=trace_id,
                            sender_email=sender_email,
                            sender_pass=sender_pass,
                            smtp_server=smtp_server,
                            smtp_port=smtp_port
                        )
                        res["user_connected_account"] = True
                        return res
                except Exception as exc:
                    logger.warning("Failed loading user integration for %s: %s", clean_user_id, exc)

            # STRICT NO-FALLBACK RULE: Never fall back to system credentials for user-owned communication
            return {
                "status": "error",
                "error": "No connected email account found for authenticated user. Please connect your Gmail, Microsoft, or SMTP account in Settings.",
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat()
            }

        # 2. System Actions ONLY: Uses system SMTP credentials
        if not self.email_user or not self.email_password:
            return {
                "status": "error",
                "error": "System SMTP credentials not configured in environment.",
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat()
            }

        res = self.send_email_smtp(
            to_email=to_email,
            subject=subject,
            message=message,
            trace_id=trace_id,
            sender_email=self.email_user,
            sender_pass=self.email_password,
            smtp_server=self.smtp_server,
            smtp_port=self.smtp_port
        )
        res["user_connected_account"] = False
        return res