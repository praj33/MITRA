"""
Voice Module - Telephony and Voice Session Management
"""

from .telephony_stream import TelephonyStream, get_telephony_stream
from .voice_session_manager import VoiceSessionManager, get_voice_session_manager
from .language_auto import LanguageAuto, get_language_auto
from .failure_handler import get_failure_handler
from .telephony_executor import TelephonyExecutor, get_telephony_executor
from .stt_engine import get_stt_service

__all__ = [
    "TelephonyStream",
    "get_telephony_stream",
    "VoiceSessionManager",
    "get_voice_session_manager",
    "LanguageAuto",
    "get_language_auto",
    "get_failure_handler",
    "TelephonyExecutor",
    "get_telephony_executor",
    "get_stt_service"
]
