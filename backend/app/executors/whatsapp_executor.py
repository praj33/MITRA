import os
import requests
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class WhatsAppExecutor:
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
        self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
        
    def send_message(
        self,
        to_number: str,
        message: str,
        trace_id: str,
        user_id: Optional[str] = None,
        is_system_otp: bool = False
    ) -> Dict[str, Any]:
        """
        Send WhatsApp message with strict security separation:
        1. SYSTEM AUTHENTICATION OTP (is_system_otp=True):
           Uses system Twilio credentials. Never uses user's personal number as sender.
           No false success fallback.
        2. USER-OWNED WHATSAPP MESSAGING (is_system_otp=False):
           Requires authenticated user_id (rejects user_default).
           Isolated from Twilio sandbox.
           Requires Meta WhatsApp Business Platform (slated for future phases).
        """
        # ── 1. SYSTEM AUTHENTICATION OTP GATEWAY ──
        if is_system_otp:
            from_number = self.whatsapp_number
            account_sid = self.account_sid
            auth_token = self.auth_token

            if not account_sid or not auth_token:
                logger.warning("Twilio system credentials not configured for authentication OTP")
                return {
                    "status": "error",
                    "error": "Twilio system credentials not configured for OTP dispatch",
                    "error_code": "TWILIO_CONFIG_MISSING",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "platform": "whatsapp",
                    "channel": "system_otp"
                }

            try:
                # Format phone numbers for Twilio WhatsApp format
                formatted_to = to_number if to_number.startswith("whatsapp:") else f"whatsapp:{to_number}"
                formatted_from = from_number if from_number.startswith("whatsapp:") else f"whatsapp:{from_number}"

                data = {
                    "From": formatted_from,
                    "To": formatted_to,
                    "Body": message
                }
                url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
                response = requests.post(url, data=data, auth=(account_sid, auth_token), timeout=10)

                if response.status_code == 201:
                    result = response.json()
                    return {
                        "status": "success",
                        "message_sid": result.get("sid"),
                        "to": formatted_to,
                        "from": formatted_from,
                        "trace_id": trace_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "platform": "whatsapp",
                        "channel": "system_otp"
                    }
                else:
                    logger.error(f"Twilio system OTP dispatch failed [{response.status_code}]: {response.text}")
                    return {
                        "status": "error",
                        "error": f"Twilio OTP dispatch failed with status {response.status_code}",
                        "error_code": "DISPATCH_FAILED",
                        "trace_id": trace_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "platform": "whatsapp",
                        "channel": "system_otp"
                    }
            except Exception as exc:
                logger.error(f"Twilio system OTP execution failed: {exc}")
                return {
                    "status": "error",
                    "error": str(exc),
                    "error_code": "TWILIO_EXEC_ERROR",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "platform": "whatsapp",
                    "channel": "system_otp"
                }

        # ── 2. USER-OWNED WHATSAPP MESSAGING ──
        # Require authenticated user_id
        if not user_id or not str(user_id).strip() or str(user_id).strip().lower() in ("user_default", "default", "none", "null"):
            return {
                "status": "error",
                "error": "Authentication required: user-owned WhatsApp messaging requires an authenticated user identity.",
                "error_code": "AUTH_REQUIRED",
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat(),
                "platform": "whatsapp"
            }

        # User-owned WhatsApp actions must NEVER execute against system Twilio credentials
        # and must NEVER use a user's personal phone number as a Twilio From number.
        # User-owned messaging requires Meta WhatsApp Business Platform (slated for future phases).
        logger.info(
            f"User-owned WhatsApp messaging rejected for user '{user_id}': "
            "Meta WhatsApp Business Platform integration required."
        )
        return {
            "status": "error",
            "error": "User-owned WhatsApp messaging requires a connected Meta WhatsApp Business account. Twilio is strictly isolated for system authentication OTP.",
            "error_code": "WHATSAPP_BUSINESS_REQUIRED",
            "user_id": str(user_id).strip(),
            "trace_id": trace_id,
            "timestamp": datetime.utcnow().isoformat(),
            "platform": "whatsapp"
        }
    
    def receive_webhook(self, webhook_data: Dict) -> Dict[str, Any]:
        """Handle incoming WhatsApp webhook"""
        return {
            "status": "received",
            "from": webhook_data.get("From"),
            "body": webhook_data.get("Body"),
            "message_sid": webhook_data.get("MessageSid"),
            "timestamp": datetime.utcnow().isoformat(),
            "platform": "whatsapp"
        }