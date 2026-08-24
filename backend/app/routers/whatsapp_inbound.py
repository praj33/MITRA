"""
WhatsApp Inbound Router (Twilio Sandbox Compatible)

Supports:

* Text messages
* Voice messages
  """

from fastapi import APIRouter, Form
from fastapi.responses import Response
import httpx
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
import base64
import tempfile
import subprocess
import os
try:
    from langdetect import detect
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

from app.core.assistant_orchestrator import handle_assistant_request
from app.voice.stt_engine import get_stt_service

router = APIRouter()

@router.post("/webhooks/whatsapp/form")
async def whatsapp_webhook_form(
    From: str = Form(...),
    Body: str = Form(None),
    MediaContentType0: str = Form(None),
    MediaUrl0: str = Form(None),
):
    print(f"[WhatsApp] From: {From}")
    print(f"[WhatsApp] Body: {Body}")
    print(f"[WhatsApp] Media: {MediaContentType0}")

    stt_service = get_stt_service()

    # =================================================
    # HANDLE VOICE MESSAGE
    # =================================================

    if MediaContentType0 and MediaContentType0.startswith("audio/") and MediaUrl0:

        print("[WhatsApp] Voice message detected")

        try:
            print("Voice media URL:", MediaUrl0)

            import os

            TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
            TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

            async with httpx.AsyncClient(follow_redirects=True) as client:
                media_response = await client.get(
                    MediaUrl0,
                    auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
                )

            audio_bytes = media_response.content
            print("Downloaded audio size:", len(audio_bytes))

            # Save OGG
            with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as f:
                f.write(audio_bytes)
                ogg_path = f.name

            print("Saved OGG:", ogg_path)

            wav_path = ogg_path.replace(".ogg", ".wav")

            # Convert audio
            subprocess.run([
                "ffmpeg",
                "-y",
                "-i", ogg_path,
                "-ac", "1",
                "-ar", "16000",
                wav_path
            ])

            print("Converted WAV:", wav_path)

            # Read WAV
            with open(wav_path, "rb") as f:
                converted_audio = f.read()

            print("WAV size:", len(converted_audio))

            # STT
            stt_result = await stt_service.transcribe(converted_audio)

            print("Transcript:", stt_result.text)
            print("Language:", stt_result.language)

            os.remove(ogg_path)
            os.remove(wav_path)

            class MockInput:
                message = stt_result.text
                summarized_payload = None

            class MockContext:
                platform = "whatsapp"
                device = "mobile"
                session_id = From
                voice_output = False
                target_language = stt_result.language

            class MockRequest:
                input = MockInput()
                context = MockContext()

            result = await handle_assistant_request(MockRequest())
            print("ASSISTANT RAW RESULT:", result)

            response_text = ""

            if isinstance(result, dict):
                response = result.get("response")
                if isinstance(response, dict):
                    response_text = response.get("text")
                elif isinstance(response, str):
                    response_text = response

            if not response_text:
                response_text = "Hello! I am your AI assistant. How can I help you?"

        except Exception as e:
            print("[WhatsApp] Voice processing error:", e)
            response_text = "Sorry, I couldn't understand the voice message."

        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{response_text}</Message>
</Response>
"""

        return Response(content=twiml, media_type="application/xml")

    # =================================================
    # HANDLE TEXT MESSAGE
    # =================================================

    if Body:

        try:

            class MockInput:
                message = Body
                summarized_payload = None

            # Detect language from input text
            detected_language = "en"
            if LANGDETECT_AVAILABLE:
                try:
                    detected_language = detect(Body)
                except Exception as e:
                    print(f"Language detection error: {e}")
            
            class MockContext:
                platform = "whatsapp"
                device = "mobile"
                session_id = From
                voice_output = False
                target_language = detected_language

            class MockRequest:
                input = MockInput()
                context = MockContext()

            result = await handle_assistant_request(MockRequest())
            print("ASSISTANT RAW RESULT:", result)

            response_text = ""

            if isinstance(result, dict):
                response = result.get("response")
                if isinstance(response, dict):
                    response_text = response.get("text")
                elif isinstance(response, str):
                    response_text = response

            if not response_text:
                response_text = "Hello! I am your AI assistant. How can I help you?"

        except Exception as e:
            print("[WhatsApp] Text processing error:", e)
            response_text = "Sorry, something went wrong."

        # Generate voice reply using detected language
        try:
            tts = gTTS(text=response_text, lang=detected_language)
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            tts.save(tmp.name)
            with open(tmp.name, "rb") as f:
                audio_bytes = f.read()
            audio_base64 = base64.b64encode(audio_bytes).decode()
        except Exception as e:
            print("TTS error:", e)

        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{response_text}</Message>
</Response>
"""

        return Response(content=twiml, media_type="application/xml")

    # =================================================
    # DEFAULT
    # =================================================

    return Response(
        content="""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>Unsupported message type.</Message>
</Response>
""",
        media_type="application/xml"
    )
