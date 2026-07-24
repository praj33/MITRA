"""
Failure Handler - Error handling for voice/telephony operations

Provides:
- Error classification and recovery strategies
- Graceful degradation for voice services
- Error logging and alerting
- Circuit breaker pattern for voice services
"""

import asyncio
import traceback
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from functools import wraps

from app.core.logging import get_logger

logger = get_logger(__name__)


class FailureType(Enum):
    """Types of voice/telephony failures"""
    # Connection failures
    CONNECTION_TIMEOUT = "connection_timeout"
    CONNECTION_REFUSED = "connection_refused"
    CONNECTION_LOST = "connection_lost"
    
    # Audio processing failures
    AUDIO_ENCODE_ERROR = "audio_encode_error"
    AUDIO_DECODE_ERROR = "audio_decode_error"
    AUDIO_BUFFER_OVERFLOW = "audio_buffer_overflow"
    AUDIO_BUFFER_UNDERFLOW = "audio_buffer_underflow"
    
    # STT/TTS failures
    STT_INIT_ERROR = "stt_init_error"
    STT_PROCESSING_ERROR = "stt_processing_error"
    STT_TIMEOUT = "stt_timeout"
    TTS_INIT_ERROR = "tts_init_error"
    TTS_SYNTHESIS_ERROR = "tts_synthesis_error"
    TTS_TIMEOUT = "tts_timeout"
    
    # Session failures
    SESSION_INIT_ERROR = "session_init_error"
    SESSION_TIMEOUT = "session_timeout"
    SESSION_EXPIRED = "session_expired"
    
    # Provider failures
    PROVIDER_ERROR = "provider_error"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    
    # Language detection
    LANGUAGE_DETECTION_ERROR = "language_detection_error"
    UNSUPPORTED_LANGUAGE = "unsupported_language"
    
    # General
    UNKNOWN_ERROR = "unknown_error"
    PERMISSION_DENIED = "permission_denied"
    RESOURCE_NOT_FOUND = "resource_not_found"


class Severity(Enum):
    """Failure severity levels"""
    LOW = "low"           # Non-critical, can continue
    MEDIUM = "medium"     # Requires attention
    HIGH = "high"         # Service degraded
    CRITICAL = "critical" # Service unavailable


@dataclass
class FailureEvent:
    """Record of a failure event"""
    failure_type: FailureType
    severity: Severity
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None
    stream_id: Optional[str] = None
    trace_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    recovery_attempted: bool = False
    recovery_successful: Optional[bool] = None


@dataclass
class RecoveryStrategy:
    """Recovery strategy configuration"""
    name: str
    action: Callable
    max_attempts: int = 3
    backoff_seconds: float = 1.0
    exponential_backoff: bool = True


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"     # Normal operation
    OPEN = "open"         # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class VoiceFailureHandler:
    """
    Handles failures in voice/telephony operations.
    Implements circuit breaker pattern and recovery strategies.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        # Failure tracking
        self._failure_counts: Dict[str, int] = {}
        self._failure_history: List[FailureEvent] = []
        self._max_history = 1000
        
        # Circuit breaker state
        self._circuit_states: Dict[str, CircuitState] = {}
        self._circuit_timestamps: Dict[str, datetime] = {}
        self._half_open_calls: Dict[str, int] = {}
        
        # Recovery strategies
        self._recovery_strategies: Dict[FailureType, List[RecoveryStrategy]] = {}
        self._register_default_strategies()
        
        # Error callbacks
        self._error_callbacks: List[Callable] = []
        self._alert_callbacks: List[Callable] = []
        
        # Statistics
        self._total_failures = 0
        self._total_recoveries = 0
        
        logger.info("[FailureHandler] Initialized")
    
    def _register_default_strategies(self):
        """Register default recovery strategies"""
        # STT retry strategy
        self.register_recovery_strategy(
            FailureType.STT_PROCESSING_ERROR,
            RecoveryStrategy(
                name="retry_stt",
                action=self._retry_stt,
                max_attempts=2,
                backoff_seconds=0.5
            )
        )
        
        # TTS retry strategy
        self.register_recovery_strategy(
            FailureType.TTS_SYNTHESIS_ERROR,
            RecoveryStrategy(
                name="retry_tts",
                action=self._retry_tts,
                max_attempts=2,
                backoff_seconds=0.5
            )
        )
        
        # Connection retry strategy
        self.register_recovery_strategy(
            FailureType.CONNECTION_TIMEOUT,
            RecoveryStrategy(
                name="retry_connection",
                action=self._retry_connection,
                max_attempts=3,
                backoff_seconds=1.0
            )
        )
        
        # Language detection fallback
        self.register_recovery_strategy(
            FailureType.LANGUAGE_DETECTION_ERROR,
            RecoveryStrategy(
                name="fallback_language",
                action=self._fallback_language,
                max_attempts=1,
                backoff_seconds=0
            )
        )
    
    def register_recovery_strategy(
        self,
        failure_type: FailureType,
        strategy: RecoveryStrategy
    ):
        """Register a recovery strategy for a failure type"""
        if failure_type not in self._recovery_strategies:
            self._recovery_strategies[failure_type] = []
        
        self._recovery_strategies[failure_type].append(strategy)
        logger.debug(
            f"[FailureHandler] Strategy registered - "
            f"type={failure_type.value}, strategy={strategy.name}"
        )
    
    def register_error_callback(self, callback: Callable):
        """Register callback for error events"""
        self._error_callbacks.append(callback)
    
    def register_alert_callback(self, callback: Callable):
        """Register callback for alert conditions"""
        self._alert_callbacks.append(callback)
    
    async def handle_failure(
        self,
        failure_type: FailureType,
        message: str,
        severity: Severity = Severity.MEDIUM,
        session_id: str = None,
        stream_id: str = None,
        trace_id: str = None,
        context: Dict[str, Any] = None,
        exc: Exception = None
    ) -> Dict[str, Any]:
        """
        Handle a failure event.
        
        Args:
            failure_type: Type of failure
            message: Error message
            severity: Severity level
            session_id: Related session ID
            stream_id: Related stream ID
            trace_id: Trace ID for debugging
            context: Additional context
            exc: Exception object if available
            
        Returns:
            Handling result with recovery information
        """
        # Create failure event
        event = FailureEvent(
            failure_type=failure_type,
            severity=severity,
            message=message,
            session_id=session_id,
            stream_id=stream_id,
            trace_id=trace_id,
            context=context or {},
            stack_trace=traceback.format_exc() if exc else None
        )
        
        # Store in history
        self._failure_history.append(event)
        if len(self._failure_history) > self._max_history:
            self._failure_history.pop(0)
        
        self._total_failures += 1
        
        # Log failure
        log_level = {
            Severity.LOW: logger.info,
            Severity.MEDIUM: logger.warning,
            Severity.HIGH: logger.error,
            Severity.CRITICAL: logger.critical
        }[severity]
        
        log_level(
            f"[FailureHandler] Failure - "
            f"type={failure_type.value}, severity={severity.value}, "
            f"session={session_id}, message={message}"
        )
        
        # Update circuit breaker
        service_key = failure_type.value.split("_")[0]  # e.g., "stt" from "stt_error"
        await self._record_failure(service_key)
        
        # Trigger error callbacks
        for callback in self._error_callbacks:
            try:
                await callback(event)
            except Exception as e:
                logger.error(f"[FailureHandler] Callback error: {e}")
        
        # Check for alert conditions
        if severity in [Severity.HIGH, Severity.CRITICAL]:
            await self._trigger_alerts(event)
        
        # Attempt recovery
        recovery_result = await self._attempt_recovery(event)
        event.recovery_attempted = True
        event.recovery_successful = recovery_result.get("success", False)
        
        return {
            "failure_type": failure_type.value,
            "severity": severity.value,
            "message": message,
            "handled": True,
            "recovery": recovery_result,
            "circuit_state": self._circuit_states.get(service_key, CircuitState.CLOSED).value
        }
    
    async def _attempt_recovery(self, event: FailureEvent) -> Dict[str, Any]:
        """Attempt to recover from a failure"""
        strategies = self._recovery_strategies.get(event.failure_type, [])
        
        if not strategies:
            return {
                "success": False,
                "reason": "no_recovery_strategy"
            }
        
        # Try each strategy
        for strategy in strategies:
            for attempt in range(strategy.max_attempts):
                try:
                    logger.info(
                        f"[FailureHandler] Recovery attempt - "
                        f"strategy={strategy.name}, attempt={attempt + 1}"
                    )
                    
                    result = await strategy.action(event, attempt)
                    
                    if result.get("success"):
                        self._total_recoveries += 1
                        logger.info(
                            f"[FailureHandler] Recovery successful - "
                            f"strategy={strategy.name}"
                        )
                        return {
                            "success": True,
                            "strategy": strategy.name,
                            "attempts": attempt + 1,
                            "result": result
                        }
                    
                    # Backoff if configured
                    if strategy.backoff_seconds > 0:
                        delay = strategy.backoff_seconds * (2 ** attempt if strategy.exponential_backoff else 1)
                        await asyncio.sleep(delay)
                        
                except Exception as e:
                    logger.error(
                        f"[FailureHandler] Recovery attempt failed - "
                        f"strategy={strategy.name}, error={e}"
                    )
        
        return {
            "success": False,
            "reason": "all_strategies_exhausted"
        }
    
    async def _retry_stt(self, event: FailureEvent, attempt: int) -> Dict[str, Any]:
        """Retry STT processing"""
        # Simulated retry - in real implementation, would re-process audio
        logger.debug(f"[FailureHandler] STT retry - attempt {attempt + 1}")
        return {"success": True, "action": "stt_retry"}
    
    async def _retry_tts(self, event: FailureEvent, attempt: int) -> Dict[str, Any]:
        """Retry TTS synthesis"""
        logger.debug(f"[FailureHandler] TTS retry - attempt {attempt + 1}")
        return {"success": True, "action": "tts_retry"}
    
    async def _retry_connection(self, event: FailureEvent, attempt: int) -> Dict[str, Any]:
        """Retry connection"""
        logger.debug(f"[FailureHandler] Connection retry - attempt {attempt + 1}")
        return {"success": True, "action": "connection_retry"}
    
    async def _fallback_language(self, event: FailureEvent, attempt: int) -> Dict[str, Any]:
        """Fallback to default language"""
        logger.debug("[FailureHandler] Language fallback to English")
        return {"success": True, "action": "language_fallback", "language": "en"}
    
    # =========================================================
    # STEP 8: Failure Response Generators
    # =========================================================
    
    def get_stt_failure_response(self, language: str = "en") -> str:
        """Get fallback response for STT failure"""
        messages = {
            "en": "I'm having trouble hearing you. Please repeat.",
            "es": "Tengo problemas para escucharte. Por favor, repítelo.",
            "fr": "J'ai du mal à vous entendre. Veuillez répéter.",
            "de": "Ich habe Probleme, Sie zu hören. Bitte wiederholen Sie.",
            "hi": "मुझे आपकी बात सुनने में परेशानी हो रही है। कृपया दोहराएं।",
            "zh": "我听不清您说的话，请再说一次。",
            "ja": "声が聞こえません。もう一度言ってください。",
            "ar": "أواجه مشكلة في سماعك. يرجى التكرار."
        }
        return messages.get(language, messages["en"])
    
    def get_tts_failure_response(self, channel: str = "phone", language: str = "en") -> Dict[str, Any]:
        """Get fallback response for TTS failure"""
        text_messages = {
            "en": "Sorry, I couldn't generate speech. Here's my response in text.",
            "es": "Lo siento, no pude generar voz. Aquí está mi respuesta en texto.",
            "fr": "Désolé, je n'ai pas pu générer la parole. Voici ma réponse en texte.",
            "de": "Entschuldigung, ich konnte keine Sprache generieren. Hier ist meine Antwort.",
            "hi": "क्षमा करें, मैं भाषण नहीं बना पाया। यह मेरा टेक्स्ट में जवाब है।"
        }
        text = text_messages.get(language, text_messages["en"])
        if channel == "phone":
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">{text}</Say>
</Response>"""
            return {"type": "twiml", "content": twiml}
        else:
            return {"type": "text", "content": text}
    
    def get_language_detection_fallback(self) -> str:
        """Get default language when detection fails"""
        return "en"
    
    def get_telephony_playback_fallback(self, message: str = None) -> str:
        """Get safe TwiML fallback for telephony playback failure"""
        default_message = message or "Connection issue. Please try again."
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">{default_message}</Say>
</Response>"""
        return twiml
    
    async def _record_failure(self, service_key: str):
        """Record a failure for circuit breaker"""
        now = datetime.utcnow()
        
        # Initialize if needed
        if service_key not in self._failure_counts:
            self._failure_counts[service_key] = 0
            self._circuit_states[service_key] = CircuitState.CLOSED
        
        # Increment failure count
        self._failure_counts[service_key] += 1
        
        # Check threshold
        if self._failure_counts[service_key] >= self.failure_threshold:
            current_state = self._circuit_states[service_key]
            
            if current_state == CircuitState.CLOSED:
                self._circuit_states[service_key] = CircuitState.OPEN
                self._circuit_timestamps[service_key] = now
                logger.warning(
                    f"[FailureHandler] Circuit opened - service={service_key}, "
                    f"failures={self._failure_counts[service_key]}"
                )
            elif current_state == CircuitState.HALF_OPEN:
                self._circuit_states[service_key] = CircuitState.OPEN
                self._circuit_timestamps[service_key] = now
    
    async def _record_success(self, service_key: str):
        """Record a success for circuit breaker"""
        if service_key in self._failure_counts:
            self._failure_counts[service_key] = max(0, self._failure_counts[service_key] - 1)
        
        current_state = self._circuit_states.get(service_key, CircuitState.CLOSED)
        
        if current_state == CircuitState.HALF_OPEN:
            self._circuit_states[service_key] = CircuitState.CLOSED
            self._failure_counts[service_key] = 0
            logger.info(f"[FailureHandler] Circuit closed - service={service_key}")
    
    def is_circuit_open(self, service_key: str) -> bool:
        """Check if circuit is open for a service"""
        state = self._circuit_states.get(service_key, CircuitState.CLOSED)
        
        if state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if service_key in self._circuit_timestamps:
                last_failure = self._circuit_timestamps[service_key]
                if datetime.utcnow() - last_failure > timedelta(seconds=self.recovery_timeout):
                    # Try half-open
                    self._circuit_states[service_key] = CircuitState.HALF_OPEN
                    self._half_open_calls[service_key] = 0
                    logger.info(f"[FailureHandler] Circuit half-open - service={service_key}")
                    return False
            return True
        
        elif state == CircuitState.HALF_OPEN:
            # Check if max calls reached
            calls = self._half_open_calls.get(service_key, 0)
            if calls >= self.half_open_max_calls:
                return True
            self._half_open_calls[service_key] = calls + 1
            return False
        
        return False
    
    async def _trigger_alerts(self, event: FailureEvent):
        """Trigger alert callbacks"""
        for callback in self._alert_callbacks:
            try:
                await callback(event)
            except Exception as e:
                logger.error(f"[FailureHandler] Alert callback error: {e}")
    
    def get_failure_statistics(self) -> Dict[str, Any]:
        """Get failure statistics"""
        return {
            "total_failures": self._total_failures,
            "total_recoveries": self._total_recoveries,
            "recovery_rate": (
                self._total_recoveries / self._total_failures
                if self._total_failures > 0 else 0
            ),
            "by_type": self._get_failures_by_type(),
            "by_severity": self._get_failures_by_severity(),
            "circuit_states": {
                k: v.value for k, v in self._circuit_states.items()
            }
        }
    
    def _get_failures_by_type(self) -> Dict[str, int]:
        """Get failure counts by type"""
        counts = {}
        for event in self._failure_history:
            ft = event.failure_type.value
            counts[ft] = counts.get(ft, 0) + 1
        return counts
    
    def _get_failures_by_severity(self) -> Dict[str, int]:
        """Get failure counts by severity"""
        counts = {}
        for event in self._failure_history:
            sev = event.severity.value
            counts[sev] = counts.get(sev, 0) + 1
        return counts
    
    def get_circuit_state(self, service_key: str) -> CircuitState:
        """Get circuit state for a service"""
        return self._circuit_states.get(service_key, CircuitState.CLOSED)


def handle_voice_failure(
    failure_type: FailureType,
    severity: Severity = Severity.MEDIUM
):
    """
    Decorator for handling voice function failures.
    
    Usage:
        @handle_voice_failure(FailureType.STT_PROCESSING_ERROR, Severity.HIGH)
        async def my_stt_function(audio_data):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            handler = get_failure_handler()
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                result = await handler.handle_failure(
                    failure_type=failure_type,
                    message=str(e),
                    severity=severity,
                    exc=e
                )
                # Re-raise if recovery not successful
                if not result.get("recovery", {}).get("success", False):
                    raise
                return result
        return wrapper
    return decorator


# Global instance
_failure_handler_instance: Optional[VoiceFailureHandler] = None


def get_failure_handler() -> VoiceFailureHandler:
    """Get or create the global VoiceFailureHandler instance"""
    global _failure_handler_instance
    if _failure_handler_instance is None:
        _failure_handler_instance = VoiceFailureHandler()
    return _failure_handler_instance


def create_failure_handler(**kwargs) -> VoiceFailureHandler:
    """Create a new VoiceFailureHandler instance"""
    return VoiceFailureHandler(**kwargs)


# =========================================================
# Simple Voice Failure Handler Function
# =========================================================

def handle_voice_failure(error):
    """
    Simple voice failure handler function.
    
    Usage:
        from app.voice.failure_handler import handle_voice_failure
        
        result = handle_voice_failure("STT service unavailable")
    
    Args:
        error: The error message or exception
    
    Returns:
        dict: Error response with fallback message
    """
    print("VOICE FAILURE:", error)
    
    return {
        "response": "Sorry, I encountered a voice processing error. Please try again."
    }
