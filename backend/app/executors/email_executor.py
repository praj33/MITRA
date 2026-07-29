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
        self.email_user = os.getenv("EMAIL_USER")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        self.gmail_token = os.getenv("GMAIL_ACCESS_TOKEN")
        self.sendgrid_key = os.getenv("SENDGRID_API_KEY")
        self.sendgrid_from = os.getenv("SENDGRID_FROM_EMAIL", self.email_user)
        
    def send_email_smtp(self, to_email: str, subject: str, message: str, trace_id: str) -> Dict[str, Any]:
        """Send email via SMTP with IPv4 forcing for cloud compatibility (Render/AWS)."""
        try:
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
            
            # Resolve to IPv4 host to avoid Render IPv6 Errno 101 Network unreachable
            target_host = _get_ipv4_host(self.smtp_server)
            
            # Try TLS port 587 (with EHLO server_hostname for SNI)
            try:
                server = smtplib.SMTP(target_host, 587, timeout=10)
                server.ehlo(self.smtp_server)
                server.starttls()
                server.ehlo(self.smtp_server)
                server.login(self.email_user, self.email_password)
                server.sendmail(self.email_user, to_email, text)
                server.quit()
                logger.info(f"Email sent via SMTP IPv4 (587) to {to_email}")
                return {
                    "status": "success",
                    "to": to_email,
                    "subject": subject,
                    "message": message,
                    "method": "smtp_tls_ipv4",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "platform": "email"
                }
            except Exception as tls_err:
                logger.warning(f"SMTP TLS 587 failed: {tls_err}, trying SSL 465")
                server = smtplib.SMTP_SSL(target_host, 465, timeout=10)
                server.login(self.email_user, self.email_password)
                server.sendmail(self.email_user, to_email, text)
                server.quit()
                return {
                    "status": "success",
                    "to": to_email,
                    "subject": subject,
                    "message": message,
                    "method": "smtp_ssl_ipv4",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "platform": "email"
                }
            
        except Exception as e:
            logger.error(f"SMTP email execution failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def send_email_sendgrid(self, to_email: str, subject: str, message: str, trace_id: str) -> Dict[str, Any]:
        """Send email via SendGrid API"""
        try:
            if not self.sendgrid_key:
                return self.send_email_smtp(to_email, subject, message, trace_id)
            
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
            
            response = requests.post(
                'https://api.sendgrid.com/v3/mail/send',
                headers=headers,
                json=data,
                timeout=3
            )
            
            if response.status_code == 202:
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
                logger.warning(f"SendGrid API error: {response.status_code} - {response.text}, falling back to SMTP")
                return self.send_email_smtp(to_email, subject, message, trace_id)
                
        except Exception as e:
            logger.warning(f"SendGrid execution failed, falling back to SMTP: {e}")
            return self.send_email_smtp(to_email, subject, message, trace_id)
    
    def send_email_gmail_api(self, to_email: str, subject: str, message: str, trace_id: str) -> Dict[str, Any]:
        """Send email via Gmail API"""
        try:
            if not self.gmail_token:
                return self.send_email_smtp(to_email, subject, message, trace_id)
            
            email_msg = MIMEText(message)
            email_msg['to'] = to_email
            email_msg['subject'] = subject
            
            raw_message = base64.urlsafe_b64encode(email_msg.as_bytes()).decode()
            
            headers = {
                'Authorization': f'Bearer {self.gmail_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'raw': raw_message
            }
            
            response = requests.post(
                'https://gmail.googleapis.com/gmail/v1/users/me/messages/send',
                headers=headers,
                json=data,
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "status": "success",
                    "message_id": result.get("id"),
                    "to": to_email,
                    "subject": subject,
                    "message": message,
                    "method": "gmail_api",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "platform": "email"
                }
            else:
                return self.send_email_smtp(to_email, subject, message, trace_id)
                
        except Exception as e:
            logger.error(f"Gmail API execution failed, falling back to SMTP: {e}")
            return self.send_email_smtp(to_email, subject, message, trace_id)
    
    def send_message(self, to_email: str, subject: str, message: str, trace_id: str) -> Dict[str, Any]:
        """Main send method - tries fast SMTP IPv4 first if configured, else SendGrid/Gmail API"""
        if self.email_user and self.email_password:
            res = self.send_email_smtp(to_email, subject, message, trace_id)
            if res.get("status") == "success":
                return res
        
        if self.sendgrid_key:
            return self.send_email_sendgrid(to_email, subject, message, trace_id)
        elif self.gmail_token:
            return self.send_email_gmail_api(to_email, subject, message, trace_id)
        else:
            return self.send_email_smtp(to_email, subject, message, trace_id)