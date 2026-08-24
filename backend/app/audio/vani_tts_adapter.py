"""
Vani TTS Adapter - Integration with Soham's Vani system
Handles text-to-speech conversion using Vani's multilingual capabilities
"""
import os
import json
import requests
import base64
from typing import Optional, Dict, Any
from datetime import datetime

class VaniTTSAdapter:
    """Adapter for Soham's Vani TTS system"""
    
    def __init__(self):
        self.vani_api_base = os.getenv("VANI_API_BASE")
        self.vani_api_key = os.getenv("VANI_API_KEY")
        
        # Validate required environment variables
        if not self.vani_api_base:
            raise ValueError("VANI_API_BASE environment variable is required")
        if not self.vani_api_key:
            raise ValueError("VANI_API_KEY environment variable is required")
        
        self.use_remote_vani = True  # Now always using remote since we have the required vars
        self.cache_dir = os.path.join(os.path.dirname(__file__), "cache")
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def synthesize_speech(self, text: str, language: str = "en", voice_id: str = None, 
                         prosody_settings: Dict[str, Any] = None) -> Optional[bytes]:
        """
        Synthesize speech using Vani TTS
        
        Args:
            text: Text to convert to speech
            language: Target language code
            voice_id: Specific voice identifier
            prosody_settings: Prosody parameters (pitch, speed, etc.)
            
        Returns:
            Audio bytes or None if failed
        """
        if not text or not text.strip():
            return None
            
        # Generate cache key
        cache_key = self._generate_cache_key(text, language, voice_id, prosody_settings)
        cached_audio = self._get_from_cache(cache_key)
        if cached_audio:
            return cached_audio
        
        # Try Vani TTS
        if self.use_remote_vani:
            audio_bytes = self._synthesize_with_vani(text, language, voice_id, prosody_settings)
            if audio_bytes:
                self._save_to_cache(cache_key, audio_bytes)
                return audio_bytes
        
        # Fallback synthesis
        return self._fallback_synthesis(text, language)
    
    def _synthesize_with_vani(self, text: str, language: str, voice_id: str, 
                             prosody_settings: Dict[str, Any]) -> Optional[bytes]:
        """Synthesize using Vani API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.vani_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "text": text,
                "language": language,
                "voice_id": voice_id or self._get_default_voice(language),
                "prosody": prosody_settings or {}
            }
            
            response = requests.post(
                f"{self.vani_api_base}/synthesize",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.content
            else:
                print(f"Vani TTS error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Vani TTS failed: {e}")
            return None
    
    def _get_default_voice(self, language: str) -> str:
        """Get default voice ID for language"""
        voice_mapping = {
            "en": "vani_english_female",
            "es": "vani_spanish_female",
            "fr": "vani_french_female",
            "de": "vani_german_male",
            "hi": "vani_hindi_female",
            "zh": "vani_chinese_male",
            "ja": "vani_japanese_female",
            "pt": "vani_portuguese_male",
            "ru": "vani_russian_male",
            "mr": "vani_marathi_female",
            "ta": "vani_tamil_female",
            "te": "vani_telugu_female",
            "kn": "vani_kannada_female",
            "ml": "vani_malayalam_female"
        }
        return voice_mapping.get(language, "vani_english_female")
    
    def _generate_cache_key(self, text: str, language: str, voice_id: str, 
                           prosody_settings: Dict[str, Any]) -> str:
        """Generate unique cache key"""
        import hashlib
        cache_data = f"{text}_{language}_{voice_id}_{str(prosody_settings)}"
        return hashlib.md5(cache_data.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[bytes]:
        """Retrieve audio from cache"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.mp3")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    return f.read()
            except Exception as e:
                print(f"Cache read error: {e}")
        return None
    
    def _save_to_cache(self, cache_key: str, audio_bytes: bytes):
        """Save audio to cache"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.mp3")
        try:
            with open(cache_file, 'wb') as f:
                f.write(audio_bytes)
        except Exception as e:
            print(f"Cache save error: {e}")
    
    def _fallback_synthesis(self, text: str, language: str) -> bytes:
        """Fallback synthesis method"""
        # Return empty bytes as fallback
        return b""
    
    def get_supported_languages(self) -> list:
        """Get list of supported languages"""
        return [
            "en", "es", "fr", "de", "hi", "zh", "ja", 
            "pt", "ru", "mr", "ta", "te", "kn", "ml"
        ]
    
    def get_available_voices(self, language: str = None) -> Dict[str, list]:
        """Get available voices for languages"""
        voices = {
            "en": ["vani_english_male", "vani_english_female"],
            "es": ["vani_spanish_male", "vani_spanish_female"],
            "fr": ["vani_french_male", "vani_french_female"],
            "de": ["vani_german_male", "vani_german_female"],
            "hi": ["vani_hindi_male", "vani_hindi_female"],
            "zh": ["vani_chinese_male", "vani_chinese_female"],
            "ja": ["vani_japanese_male", "vani_japanese_female"],
            "pt": ["vani_portuguese_male", "vani_portuguese_female"],
            "ru": ["vani_russian_male", "vani_russian_female"],
            "mr": ["vani_marathi_male", "vani_marathi_female"],
            "ta": ["vani_tamil_male", "vani_tamil_female"],
            "te": ["vani_telugu_male", "vani_telugu_female"],
            "kn": ["vani_kannada_male", "vani_kannada_female"],
            "ml": ["vani_malayalam_male", "vani_malayalam_female"]
        }
        
        if language:
            return {language: voices.get(language, [])}
        return voices

# Global instance
vani_tts_adapter = VaniTTSAdapter()

def get_vani_tts_adapter():
    return vani_tts_adapter