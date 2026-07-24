"""
Language Auto - Automatic language detection and handling for voice

Provides:
- Language detection from audio/text
- Language code mapping and normalization
- Multilingual TTS configuration
- Language preference management per user/session
"""

import re
import os
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum

from app.core.logging import get_logger

logger = get_logger(__name__)


class LanguageCode(Enum):
    """Supported language codes (ISO 639-1)"""
    EN = "en"      # English
    ES = "es"      # Spanish
    FR = "fr"      # French
    DE = "de"      # German
    IT = "it"      # Italian
    PT = "pt"      # Portuguese
    NL = "nl"      # Dutch
    RU = "ru"      # Russian
    ZH = "zh"      # Chinese
    JA = "ja"      # Japanese
    KO = "ko"      # Korean
    AR = "ar"      # Arabic
    HI = "hi"      # Hindi
    TH = "th"      # Thai
    VI = "vi"      # Vietnamese
    ID = "id"      # Indonesian
    MS = "ms"      # Malay
    TR = "tr"      # Turkish
    PL = "pl"      # Polish
    SV = "sv"      # Swedish

    @classmethod
    def from_code(cls, code: str) -> Optional["LanguageCode"]:
        """Get LanguageCode from string"""
        code = code.lower().split("-")[0]  # Handle en-US, es-MX, etc.
        try:
            return cls(code)
        except ValueError:
            return None


# Language metadata
LANGUAGE_METADATA = {
    "en": {
        "name": "English",
        "native_name": "English",
        "tts_voices": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
        "tts_engine": "openai",
        "stt_model": "whisper-1",
        "script": "Latin",
        "region": "US"
    },
    "es": {
        "name": "Spanish",
        "native_name": "Español",
        "tts_voices": ["alloy", "echo"],
        "tts_engine": "openai",
        "stt_model": "whisper-1",
        "script": "Latin",
        "region": "ES"
    },
    "fr": {
        "name": "French",
        "native_name": "Français",
        "tts_voices": ["alloy", "echo"],
        "tts_engine": "openai",
        "stt_model": "whisper-1",
        "script": "Latin",
        "region": "FR"
    },
    "de": {
        "name": "German",
        "native_name": "Deutsch",
        "tts_voices": ["alloy", "echo"],
        "tts_engine": "openai",
        "stt_model": "whisper-1",
        "script": "Latin",
        "region": "DE"
    },
    "hi": {
        "name": "Hindi",
        "native_name": "हिन्दी",
        "tts_voices": ["af_sarah", "am_adam"],
        "tts_engine": "vani",
        "stt_model": "whisper-1",
        "script": "Devanagari",
        "region": "IN"
    },
    "zh": {
        "name": "Chinese",
        "native_name": "中文",
        "tts_voices": ["alloy", "echo"],
        "tts_engine": "openai",
        "stt_model": "whisper-1",
        "script": "Chinese",
        "region": "CN"
    },
    "ja": {
        "name": "Japanese",
        "native_name": "日本語",
        "tts_voices": ["alloy", "echo"],
        "tts_engine": "openai",
        "stt_model": "whisper-1",
        "script": "Japanese",
        "region": "JP"
    },
    "ko": {
        "name": "Korean",
        "native_name": "한국어",
        "tts_voices": ["alloy", "echo"],
        "tts_engine": "openai",
        "stt_model": "whisper-1",
        "script": "Korean",
        "region": "KR"
    },
    "pt": {
        "name": "Portuguese",
        "native_name": "Português",
        "tts_voices": ["alloy", "echo"],
        "tts_engine": "openai",
        "stt_model": "whisper-1",
        "script": "Latin",
        "region": "BR"
    },
    "ar": {
        "name": "Arabic",
        "native_name": "العربية",
        "tts_voices": ["alloy"],
        "tts_engine": "openai",
        "stt_model": "whisper-1",
        "script": "Arabic",
        "region": "SA"
    }
}

# Language detection patterns
LANGUAGE_PATTERNS = {
    "en": [
        r'\b(the|a|an|is|are|was|were|have|has|been|being|do|does|did|will|would|could|should|may|might|must|shall|can)\b',
        r'\b(hello|hi|hey|good|thank|please|sorry|yes|no|okay|ok)\b',
        r'\b(what|who|where|when|why|how|which)\b'
    ],
    "es": [
        r'\b(el|la|los|las|un|una|de|que|es|son|está|están|fue|fueron|tengo|tiene|haber|hacer|poder|querer)\b',
        r'\b(hola|gracias|por|favor|sí|no|buenos|días|tardes|noches)\b',
        r'\b(qué|cuál|dónde|cuándo|por qué|cómo)\b'
    ],
    "fr": [
        r'\b(le|la|les|un|une|de|du|des|être|avoir|être|faire|pouvoir|vouloir|devoir|savoir)\b',
        r'\b(bonjour|merci|s\'il|pardon|oui|non|bonne|soir|matin|jour|nuit)\b',
        r'\b(qui|que|quoi|où|quand|pourquoi|comment)\b'
    ],
    "de": [
        r'\b(der|die|das|ein|eine|und|oder|aber|nicht|sein|haben|werden|kann|will|muss|soll)\b',
        r'\b(ja|nein|danke|bitte|hallo|guten|morgen|tag|abend|nacht)\b',
        r'\b(wer|was|wo|wann|warum|wie|welcher)\b'
    ],
    "hi": [
        r'\b(है|हैं|था|थे|हूं|होगा|कर|किया|है|लिए|से|में|का|की|को|ने|बात|कहा)\b',
        r'\b(नमस्ते|धन्यवाद|हां|नहीं|जी|हां|बिल्कुल)\b',
        r'\b(क्या|कौन|कहां|कब|कैसे|क्यों)\b'
    ]
}

# Language detection heuristics based on character sets
SCRIPT_PATTERNS = {
    "ar": re.compile(r'[\u0600-\u06FF]'),
    "hi": re.compile(r'[\u0900-\u097F]'),
    "zh": re.compile(r'[\u4e00-\u9fff]'),
    "ja": re.compile(r'[\u3040-\u309F\u30A0-\u30FF]'),
    "ko": re.compile(r'[\uAC00-\uD7AF]'),
    "ru": re.compile(r'[\u0400-\u04FF]'),
    "th": re.compile(r'[\u0E00-\u0E7F]')
}

# Default fallback
DEFAULT_LANGUAGE = "en"
DEFAULT_TTS_VOICE = "alloy"


@dataclass
class LanguageDetectionResult:
    """Result of language detection"""
    language: str
    confidence: float
    script: Optional[str] = None
    region: Optional[str] = None
    alternatives: Optional[List[Tuple[str, float]]] = None


class LanguageAuto:
    """
    Automatic language detection and handling for voice interactions.
    Supports text-based and audio-based language detection.
    """
    
    def __init__(
        self,
        default_language: str = DEFAULT_LANGUAGE,
        confidence_threshold: float = 0.7,
        enable_adaptive: bool = True
    ):
        self.default_language = default_language
        self.confidence_threshold = confidence_threshold
        self.enable_adaptive = enable_adaptive
        
        # User language preferences cache
        self._user_preferences: Dict[str, Dict[str, Any]] = {}
        
        # Session language tracking
        self._session_languages: Dict[str, str] = {}
        
        logger.info(f"[LanguageAuto] Initialized - default={default_language}")
    
    def detect_from_text(self, text: str) -> LanguageDetectionResult:
        """
        Detect language from text input.
        
        Args:
            text: Input text to analyze
            
        Returns:
            LanguageDetectionResult with detected language and confidence
        """
        if not text or not text.strip():
            return LanguageDetectionResult(
                language=self.default_language,
                confidence=0.0
            )
        
        text_lower = text.lower()
        
        # Check for script-based patterns first
        for script_name, pattern in SCRIPT_PATTERNS.items():
            if pattern.search(text):
                metadata.get(script_name, {})
                return LanguageDetectionResult(
                    language=script_name,
                    confidence=0.95,
                    script=metadata.get("script"),
                    region=metadata.get("region")
                )
        
        # Use pattern matching for Latin-script languages
        language_scores: Dict[str, float] = {}
        
        for lang, patterns in LANGUAGE_PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
                score += matches
            
            if score > 0:
                language_scores[lang] = score
        
        # Normalize scores
        if language_scores:
            max_score = max(language_scores.values())
            if max_score > 0:
                language_scores = {
                    lang: score / max_score
                    for lang, score in language_scores.items()
                }
        
        # Get best match
        if language_scores:
            best_lang = max(language_scores, key=language_scores.get)
            confidence = language_scores[best_lang]
            
            # Get alternatives
            alternatives = [
                (lang, score)
                for lang, score in sorted(
                    language_scores.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:3]
                if lang != best_lang
            ]
            
            metadata = LANGUAGE_METADATA.get(best_lang, {})
            
            return LanguageDetectionResult(
                language=best_lang,
                confidence=confidence,
                script=metadata.get("script"),
                region=metadata.get("region"),
                alternatives=alternatives
            )
        
        # Default fallback
        return LanguageDetectionResult(
            language=self.default_language,
            confidence=0.0
        )
    
    def normalize_language_code(self, code: str) -> str:
        """
        Normalize language code to standard format.
        
        Args:
            code: Language code (e.g., en-US, es_MX, esp)
            
        Returns:
            Normalized ISO 639-1 code
        """
        if not code:
            return self.default_language
        
        # Normalize
        code = code.lower().strip()
        code = code.replace("-", "_").replace("_", "-")
        
        # Extract base language
        base_code = code.split("-")[0]
        
        # Map common variations
        variations = {
            "eng": "en",
            "spa": "es",
            "fra": "fr",
            "fre": "fr",
            "deu": "de",
            "ger": "de",
            "ita": "it",
            "por": "pt",
            "chi": "zh",
            "zho": "zh",
            "jpn": "ja",
            "kor": "ko",
            "hin": "hi",
            "ara": "ar",
            "rus": "ru",
            "tha": "th",
            "vie": "vi",
            "ind": "id",
            "msa": "ms",
            "tur": "tr",
            "pol": "pl",
            "swe": "sv",
            "dut": "nl",
            "nld": "nl"
        }
        
        return variations.get(base_code, base_code)
    
    def get_language_metadata(self, language: str) -> Dict[str, Any]:
        """
        Get metadata for a language.
        
        Args:
            language: Language code
            
        Returns:
            Language metadata dictionary
        """
        normalized = self.normalize_language_code(language)
        return LANGUAGE_METADATA.get(normalized, {
            "name": normalized.title(),
            "native_name": normalized.title(),
            "tts_voices": [DEFAULT_TTS_VOICE],
            "tts_engine": "openai",
            "stt_model": "whisper-1",
            "script": "Latin",
            "region": "US"
        })
    
    def get_tts_config(
        self,
        language: str,
        voice: str = None,
        style: str = None
    ) -> Dict[str, Any]:
        """
        Get TTS configuration for a language.
        
        Args:
            language: Language code
            voice: Preferred voice (optional)
            style: Prosody style (optional)
            
        Returns:
            TTS configuration dictionary
        """
        metadata = self.get_language_metadata(language)
        
        config = {
            "language": language,
            "engine": metadata.get("tts_engine", "openai"),
            "voice": voice or metadata.get("tts_voices", [DEFAULT_TTS_VOICE])[0],
            "available_voices": metadata.get("tts_voices", []),
            "prosody_style": style or "neutral"
        }
        
        return config
    
    def get_stt_config(self, language: str) -> Dict[str, Any]:
        """
        Get STT (Speech-to-Text) configuration.
        
        Args:
            language: Language code
            
        Returns:
            STT configuration dictionary
        """
        metadata = self.get_language_metadata(language)
        
        return {
            "language": language,
            "model": metadata.get("stt_model", "whisper-1"),
            "region": metadata.get("region", "US")
        }
    
    def set_user_preference(
        self,
        user_id: str,
        language: str,
        voice: str = None
    ):
        """
        Set language preference for a user.
        
        Args:
            user_id: User identifier
            language: Preferred language
            voice: Preferred TTS voice
        """
        if user_id not in self._user_preferences:
            self._user_preferences[user_id] = {}
        
        self._user_preferences[user_id]["language"] = self.normalize_language_code(language)
        if voice:
            self._user_preferences[user_id]["voice"] = voice
        
        logger.info(f"[LanguageAuto] User preference set - user={user_id}, lang={language}")
    
    def get_user_preference(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get language preference for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            User preference dictionary or None
        """
        return self._user_preferences.get(user_id)
    
    def set_session_language(
        self,
        session_id: str,
        language: str,
        confidence: float = 1.0
    ):
        """
        Set detected language for a session.
        
        Args:
            session_id: Session identifier
            language: Detected language
            confidence: Detection confidence
        """
        normalized = self.normalize_language_code(language)
        self._session_languages[session_id] = normalized
        
        logger.debug(
            f"[LanguageAuto] Session language set - "
            f"session={session_id}, lang={normalized}, confidence={confidence}"
        )
    
    def get_session_language(self, session_id: str) -> Optional[str]:
        """
        Get detected language for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Language code or None
        """
        return self._session_languages.get(session_id)
    
    def detect_and_configure(
        self,
        text: str = None,
        user_id: str = None,
        session_id: str = None,
        stt_language: str = None,
        requested_language: str = None
    ) -> Dict[str, Any]:
        """
        Detect language and return full configuration.
        
        Priority:
        1. STT-detected language (highest priority)
        2. Detected from transcript text (FastText/Whisper)
        3. User preference
        4. Default language
        
        Args:
            text: Input text (for detection)
            user_id: User ID (for preference lookup)
            session_id: Session ID (for session tracking)
            stt_language: Language detected by STT service
            requested_language: Explicitly requested language (deprecated - use stt_language)
            
        Returns:
            Complete language configuration for LLM and TTS
        """
        # Priority 1: STT-detected language (highest priority)
        if stt_language:
            language = self.normalize_language_code(stt_language)
            source = "stt_detected"
        # Priority 2: Detect from transcript text
        elif text:
            result = self.detect_from_text(text)
            language = result.language
            confidence = result.confidence
            source = f"transcript_detected"
            
            # Update session language if provided
            if session_id and confidence >= self.confidence_threshold:
                self.set_session_language(session_id, language, confidence)
        # Priority 3: User preference
        elif user_id:
            prefs = self.get_user_preference(user_id)
            if prefs and prefs.get("language"):
                language = prefs["language"]
                source = "user_preference"
            else:
                language = None
                source = None
        else:
            language = None
            source = None
        
        # Priority 4: Fallback to default
        if not language:
            language = self.default_language
            source = "default"
        
        # Get configurations for LLM and TTS
        tts_config = self.get_tts_config(language)
        stt_config = self.get_stt_config(language)
        
        # Add user voice preference if available
        if user_id:
            prefs = self.get_user_preference(user_id)
            if prefs and prefs.get("voice"):
                tts_config["voice"] = prefs["voice"]
        
        return {
            "language": language,
            "source": source,
            "tts": tts_config,
            "stt": stt_config,
            "is_multilingual": language in ["en", "es", "fr", "de", "zh", "ja", "ko", "hi"],
            "llm_language": self._get_llm_language(language)  # Language code for LLM
        }
    
    def _get_llm_language(self, language: str) -> str:
        """
        Get language code suitable for LLM prompts.
        Some models work better with full language names.
        
        Args:
            language: ISO language code
            
        Returns:
            Language code/name for LLM
        """
        # Map to language names some models understand better
        llm_language_map = {
            "en": "English",
            "es": "Spanish", 
            "fr": "French",
            "de": "German",
            "hi": "Hindi",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
            "pt": "Portuguese",
            "ar": "Arabic",
            "ru": "Russian",
            "th": "Thai",
            "vi": "Vietnamese",
            "id": "Indonesian",
            "ms": "Malay",
            "it": "Italian",
            "nl": "Dutch",
            "pl": "Polish",
            "tr": "Turkish",
            "sv": "Swedish"
        }
        
        return llm_language_map.get(language, language.title())

    def configure_for_assistant(
        self,
        stt_result: Dict[str, Any] = None,
        text: str = None,
        user_id: str = None,
        session_id: str = None
    ) -> Dict[str, Any]:
        """
        Configure language settings for the assistant pipeline.
        
        This is the main entry point - use this instead of detect_and_configure.
        
        Args:
            stt_result: Result from STT service (may include detected_language)
            text: Input text for fallback detection
            user_id: User ID for preference lookup
            session_id: Session ID for tracking
            
        Returns:
            Dict with 'llm_prompt_language', 'tts_language', 'tts_voice', 'tts_engine'
        """
        # Extract STT-detected language
        stt_language = None
        if stt_result:
            stt_language = stt_result.get("language")
            if not stt_language:
                # Check alternative keys
                stt_language = stt_result.get("detected_language")
                stt_language = stt_language or stt_result.get("lang")
        
        # Get full configuration
        config = self.detect_and_configure(
            text=text,
            user_id=user_id,
            session_id=session_id,
            stt_language=stt_language
        )
        
        # Return simplified config for assistant pipeline
        return {
            "llm_prompt_language": config["llm_language"],
            "target_language": config["language"],  # For TTS
            "tts_language": config["tts"]["language"],
            "tts_voice": config["tts"]["voice"],
            "tts_engine": config["tts"]["engine"],
            "tts_available_voices": config["tts"]["available_voices"],
            "stt_language": config["stt"]["language"],
            "stt_model": config["stt"]["model"],
            "source": config["source"]
        }
    
    def get_supported_languages(self) -> List[Dict[str, Any]]:
        """
        Get list of supported languages with metadata.
        
        Returns:
            List of language metadata dictionaries
        """
        return [
            {
                "code": code,
                "name": meta["name"],
                "native_name": meta["native_name"],
                "tts_available": len(meta.get("tts_voices", [])) > 0,
                "voices": meta.get("tts_voices", []),
                "engine": meta.get("tts_engine")
            }
            for code, meta in LANGUAGE_METADATA.items()
        ]
    
    def is_supported(self, language: str) -> bool:
        """Check if a language is supported"""
        normalized = self.normalize_language_code(language)
        return normalized in LANGUAGE_METADATA


# Global instance
_language_auto_instance: Optional[LanguageAuto] = None


def get_language_auto() -> LanguageAuto:
    """Get or create the global LanguageAuto instance"""
    global _language_auto_instance
    if _language_auto_instance is None:
        _language_auto_instance = LanguageAuto()
    return _language_auto_instance


def create_language_auto(**kwargs) -> LanguageAuto:
    """Create a new LanguageAuto instance"""
    return LanguageAuto(**kwargs)
