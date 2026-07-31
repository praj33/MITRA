# backend/app/routers/voice_stt.py — Real Free Whisper Speech-to-Text Endpoint
import os
import tempfile
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

class STTResponse(BaseModel):
    text: str
    language: str = "en"
    confidence: float = 0.95

@router.post("/api/stt", response_model=STTResponse)
@router.post("/voice_stt", response_model=STTResponse)
async def process_voice_stt(file: UploadFile = File(...)):
    """
    Real Speech-to-Text endpoint.
    Uses Groq free Whisper Large v3 Turbo, OpenAI Whisper, or faster-whisper.
    """
    if not file:
        raise HTTPException(status_code=400, detail="No audio file provided")

    content = await file.read()
    if not content or len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty audio file provided")

    # Determine file extension
    ext = ".webm"
    if file.filename and "." in file.filename:
        ext = "." + file.filename.rsplit(".", 1)[-1].lower()
    elif file.content_type:
        if "mp4" in file.content_type:
            ext = ".mp4"
        elif "wav" in file.content_type:
            ext = ".wav"
        elif "ogg" in file.content_type:
            ext = ".ogg"

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        groq_key = os.getenv("GROQ_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")

        # Option A: Groq Free Whisper API (sub-200ms ultra fast)
        if groq_key:
            try:
                from groq import Groq
                client = Groq(api_key=groq_key)
                with open(tmp_path, "rb") as audio_file:
                    transcription = client.audio.transcriptions.create(
                        file=(os.path.basename(tmp_path), audio_file.read()),
                        model="whisper-large-v3-turbo",
                        response_format="text",
                        language="en"
                    )
                text = str(transcription).strip()
                if text:
                    logger.info(f"Groq STT transcribed: {text[:50]}...")
                    return STTResponse(text=text, language="en", confidence=0.98)
            except Exception as e:
                logger.warning(f"Groq STT failed: {e}")

        # Option B: OpenAI Whisper API
        if openai_key:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=openai_key)
                with open(tmp_path, "rb") as audio_file:
                    transcription = client.audio.transcriptions.create(
                        file=audio_file,
                        model="whisper-1"
                    )
                text = (transcription.text or "").strip()
                if text:
                    logger.info(f"OpenAI STT transcribed: {text[:50]}...")
                    return STTResponse(text=text, language="en", confidence=0.98)
            except Exception as e:
                logger.warning(f"OpenAI STT failed: {e}")

        # Option C: Open-Source faster-whisper / local fallback
        try:
            from faster_whisper import WhisperModel
            model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
            segments, _ = model.transcribe(tmp_path, beam_size=5)
            text = " ".join([segment.text for segment in segments]).strip()
            if text:
                return STTResponse(text=text, language="en", confidence=0.95)
        except Exception as e:
            logger.warning(f"faster-whisper local fallback unavailable: {e}")

        return STTResponse(
            text="",
            language="en",
            confidence=0.0
        )
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
