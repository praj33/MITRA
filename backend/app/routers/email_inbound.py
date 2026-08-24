from fastapi import APIRouter
from pydantic import BaseModel
from app.core.assistant_orchestrator import handle_assistant_request

router = APIRouter()

class InboundEmailPayload(BaseModel):
    from_email: str
    subject: str
    body: str

@router.post("/webhooks/email")
async def email_webhook(payload: InboundEmailPayload):

    class MockInput:
        message = payload.body
        summarized_payload = None

    class MockContext:
        platform = "email"
        device = "server"
        session_id = payload.from_email
        voice_output = False
        target_language = "en"

    class MockRequest:
        input = MockInput()
        context = MockContext()

    return await handle_assistant_request(MockRequest())
