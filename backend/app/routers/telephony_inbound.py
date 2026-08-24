"""
Telephony Inbound Router
Voice → STT → Assistant → TTS
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from starlette.responses import Response
from pydantic import BaseModel
import json
import base64
import subprocess
import tempfile
import os

from gtts import gTTS

from app.core.assistant_orchestrator import handle_assistant_request
from app.voice.stt_engine import get_stt_service

router = APIRouter()


class InboundCallPayload(BaseModel):
    caller: str
    transcript: str


def generate_twilio_stream_response(ws_url: str) -> str:

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
<Start>
<Stream url="{ws_url}" />
</Start>
<Say>Hello. Connecting you to the AI assistant.</Say>
<Pause length="60"/>
</Response>
"""


@router.post("/webhooks/call")
async def call_webhook(CallSid: str = None, From: str = None, To: str = None):

    print(f"[Telephony] Incoming call: {CallSid}")

    ws_url = "wss://subauricular-kenogenetically-frieda.ngrok-free.dev/telephony/stream"

    return Response(
        content=generate_twilio_stream_response(ws_url),
        media_type="application/xml"
    )


@router.websocket("/telephony/stream")
async def telephony_stream_websocket(
        websocket: WebSocket,
        call_sid: str = Query(None),
        caller: str = Query(None)
):

    session_id = call_sid or caller or "unknown"

    await websocket.accept()

    print(f"[WS] Connected: {session_id}")

    stt_service = get_stt_service()

    audio_buffer = b""

    try:

        while True:

            message = await websocket.receive_text()
            data = json.loads(message)

            event = data.get("event")

            if event == "media":

                media = data.get("media", {})
                payload = media.get("payload")

                if payload:

                    chunk = base64.b64decode(payload)
                    audio_buffer += chunk

                    if len(audio_buffer) > 16000:

                        with tempfile.NamedTemporaryFile(delete=False, suffix=".raw") as raw_file:

                            raw_file.write(audio_buffer)
                            raw_path = raw_file.name

                        wav_path = raw_path.replace(".raw", ".wav")

                        subprocess.run([
                            "ffmpeg",
                            "-f", "mulaw",
                            "-ar", "8000",
                            "-i", raw_path,
                            "-ar", "16000",
                            "-ac", "1",
                            wav_path
                        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                        with open(wav_path, "rb") as f:
                            audio_bytes = f.read()

                        stt_result = await stt_service.transcribe(audio_bytes)

                        transcript = stt_result.text
                        language = stt_result.language.split("-")[0]

                        print("User:", transcript)

                        try:

                            class MockInput:
                                message = transcript
                                summarized_payload = None

                            class MockContext:
                                platform = "telephony"
                                device = "phone"
                                session_id = session_id
                                voice_output = True
                                target_language = language

                            class MockRequest:
                                input = MockInput()
                                context = MockContext()

                            result = await handle_assistant_request(MockRequest())

                            if isinstance(result, dict):
                                response_text = result.get("response", "")
                            else:
                                response_text = str(result)

                        except Exception as e:

                            print("Assistant error:", e)
                            response_text = "Sorry, something went wrong."

                        print("Assistant:", response_text)

                        try:

                            tts = gTTS(text=response_text, lang=language)

                            tts_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")

                            tts.save(tts_file.name)

                            print("Generated voice:", tts_file.name)

                        except Exception as e:

                            print("TTS error:", e)

                        os.remove(raw_path)
                        os.remove(wav_path)

                        audio_buffer = b""

    except WebSocketDisconnect:

        print("[WS] disconnected")

    finally:

        print(f"[WS] Session ended: {session_id}")