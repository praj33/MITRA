"""
Email Handler Integration Example
To be integrated into AI_ASSISTANT_main/routes/email_handler.py

MANDATORY: SafetyService.validate_inbound() MUST be called FIRST
"""

from fastapi import APIRouter, Request
from datetime import datetime

from services.safety_service import get_safety_service

router = APIRouter()

@router.post("/inbound/email")
async def email_handler(request: Request):
    """
    Email inbound handler with MANDATORY safety-first validation.
    
    Flow: Inbound → SafetyService → Intelligence → Enforcement → Execution
    """
    payload = await request.json()
    
    # ============================================================
    # STEP 1: SAFETY VALIDATION (MANDATORY FIRST CALL)
    # ============================================================
    safety_service = get_safety_service()
    safety_result = safety_service.validate_inbound({
        "content": f"{payload['subject']}\\n\\n{payload['body']}",
        "sender": payload["from"],
        "recipient": payload["to"],
        "platform": "email",
        "timestamp": datetime.now().isoformat() + "Z"
    })
    
    # ============================================================
    # STEP 2: HARD STOP ON DENY
    # ============================================================
    if safety_result["decision"] == "hard_deny":
        return {
            "status": "blocked",
            "reason": "Email blocked due to safety policy",
            "trace_id": safety_result["trace_id"]
        }
    
    # ============================================================
    # STEP 3: REWRITE CONTENT IF NEEDED
    # ============================================================
    if safety_result["decision"] == "soft_rewrite":
        payload["body"] = safety_result["rewritten_content"]
    
    # ============================================================
    # STEP 4: PROCEED TO INTELLIGENCE
    # ============================================================
    intelligence_result = await process_intelligence(payload["body"], safety_result["trace_id"])
    enforcement_result = await apply_enforcement(intelligence_result, safety_result["trace_id"])
    response = await execute_response(enforcement_result, payload["from"], safety_result["trace_id"])
    
    return {"status": "success", "trace_id": safety_result["trace_id"]}


async def process_intelligence(content: str, trace_id: str) -> dict:
    return {"trace_id": trace_id, "response": f"Processed: {content}"}

async def apply_enforcement(intelligence_result: dict, trace_id: str) -> dict:
    return {"trace_id": trace_id, "approved": True}

async def execute_response(enforcement_result: dict, recipient: str, trace_id: str) -> dict:
    return {"trace_id": trace_id, "sent_to": recipient}
