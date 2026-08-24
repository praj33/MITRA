"""
TTS Service - Main Text-to-Speech service orchestrator
Coordinates between different TTS engines and provides unified interface
"""
import os
import base64
from typing import Optional, Dict, Any
from datetime import datetime

from .prosody_mapper import get_prosody_mapper

class TTSService:
    """Main TTS service orchestrator"""
    
    def __init__(self):
        self.vani_adapter = None
        self.prosody_mapper = get_prosody_mapper()
        self.default_engine = "local"
        self.supported_engines = ["vani", "openai", "local"]
        
    def synthesize(self, text: str, language: str = "en", voice: str = None, 
                   engine: str = None, prosody_style: str = None,
                   custom_prosody: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Synthesize text to speech with specified parameters
        
        Args:
            text: Text to synthesize
            language: Language code
            voice: Voice identifier
            engine: TTS engine to use
            prosody_style: Predefined prosody style
            custom_prosody: Custom prosody parameters
            
        Returns:
            Dict with audio data and metadata
        """
        if not text or not text.strip():
            return self._error_response("Empty text provided")
        
        engine = engine or self.default_engine
        
        # Validate parameters
        if engine not in self.supported_engines:
            return self._error_response(f"Unsupported engine: {engine}")
        
        if self.vani_adapter and language not in self.vani_adapter.get_supported_languages():
            return self._error_response(f"Unsupported language: {language}")
        
        # Get prosody settings
        prosody_settings = self._get_prosody_settings(prosody_style, custom_prosody, language)
        
        # Synthesize based on engine
        audio_bytes = None

        if engine == "local":
            audio_bytes = self._synthesize_with_local(text, language, voice)

        elif engine == "openai":
            audio_bytes = self._synthesize_with_openai(text, language, voice)

        elif engine == "vani":
            if not self.vani_adapter:
                return self._error_response("Vani adapter not initialized")
            audio_bytes = self.vani_adapter.synthesize_speech(
                text=text,
                language=language,
                voice_id=voice,
                prosody_settings=prosody_settings
            )
        # 🔥 ADD THIS BACK
        if not audio_bytes:
            return self._error_response("Synthesis failed")
        
        # Return successful response
        return {
            "status": "success",
            "audio_base64": base64.b64encode(audio_bytes).decode(),
            "audio_bytes": len(audio_bytes),
            "language": language,
            "engine": engine,
            "voice": voice or "alloy",
            "prosody_style": prosody_style,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _get_prosody_settings(self, prosody_style: str, custom_prosody: Dict[str, Any], 
                             language: str) -> Dict[str, Any]:
        """Get prosody settings based on style or custom parameters"""
        if custom_prosody:
            return custom_prosody
        
        if prosody_style:
            return self.prosody_mapper.get_prosody_for_style(prosody_style, language)
        
        # Default prosody
        return {
            "pitch": "medium",
            "speed": "normal",
            "volume": "medium"
        }
    
    def _synthesize_with_openai(self, text: str, language: str, voice: str) -> Optional[bytes]:
        """Synthesize using OpenAI TTS"""
        try:
            from openai import OpenAI
            openai_key = os.getenv("OPENAI_API_KEY")

            if not openai_key:
                print("OPENAI_API_KEY not set")
                return None

            client = OpenAI(api_key=openai_key)

            # Simple multilingual-safe default voice
            selected_voice = voice if voice else "alloy"

            response = client.audio.speech.create(
                model="tts-1",
                voice=selected_voice,
                input=text
            )

            return response.content

        except Exception as e:
            import traceback
            print("========== OPENAI TTS FULL ERROR ==========")
            print(traceback.format_exc())
            print("===========================================")
            return None

    
    def _synthesize_with_local(self, text: str, language: str, voice: str) -> Optional[bytes]:
        """Local dummy TTS for development/testing"""
        dummy_audio = f"AI_ASSISTANT_AUDIO: {text}".encode("utf-8")
        return dummy_audio
    
    def _error_response(self, error_message: str) -> Dict[str, Any]:
        """Generate error response"""
        return {
            "status": "error",
            "error": error_message,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_available_voices(self, language: str = None, engine: str = None) -> Dict[str, Any]:
        """Get available voices"""
        engine = engine or self.default_engine
        
        if engine == "vani":
            return self.vani_adapter.get_available_voices(language)
        elif engine == "openai":
            return self._get_openai_voices(language)
        else:
            return {}
    
    def _get_openai_voices(self, language: str = None) -> Dict[str, list]:
        """Get OpenAI voices"""
        voices = {
            "en": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        }
        if language:
            return {language: voices.get(language, [])}
        return voices
    
    def get_supported_languages(self, engine: str = None) -> list:
        """Get supported languages"""
        engine = engine or self.default_engine
        
        if engine == "vani":
            return self.vani_adapter.get_supported_languages()
        elif engine == "openai":
            return ["en", "es", "fr", "de", "hi", "zh", "ja", "pt"]
        else:
            return []
    
    def get_prosody_styles(self) -> list:
        """Get available prosody styles"""
        return self.prosody_mapper.get_available_styles()

# Global instance
tts_service = TTSService()

def get_tts_service():
    return tts_service