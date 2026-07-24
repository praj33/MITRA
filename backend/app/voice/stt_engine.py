"""
STT Engine — Speech-to-Text using OpenAI Whisper (lazy-loaded)
Whisper model is loaded only when first transcription is requested.
"""
import tempfile
import os
from datetime import datetime

# Lazy-loaded model
_model = None

def _get_model():
    global _model
    if _model is None:
        import whisper
        _model = whisper.load_model("base")
    return _model


class STTResult:
    def __init__(self, text, language):
        self.text = text
        self.language = language
        self.timestamp = datetime.utcnow().isoformat()


class STTService:
    async def transcribe(self, audio_bytes: bytes):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        model = _get_model()
        result = model.transcribe(tmp_path)

        os.remove(tmp_path)

        return STTResult(
            text=result["text"],
            language=result["language"]
        )


_stt_instance = None

def get_stt_service():
    global _stt_instance
    if _stt_instance is None:
        _stt_instance = STTService()
    return _stt_instance
