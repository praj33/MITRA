"""
WhatsApp Webhook Integration Example
To be integrated into AI_ASSISTANT_main/routes/whatsapp_webhook.py

MANDATORY: MediationSystem.validate_inbound() MUST be called FIRST (before SafetyService)
"""

from fastapi import APIRouter, Request, HTTPException
from datetime import datetime
import json

# Import SafetyService (adjust path based on your project structure)
from services.safety_service import get_safety_service
# Mediation system import
from mediation_system import InboundMessage, validate_inbound_message, MediationDecision

router = APIRouter()

@router.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """
    WhatsApp webhook handler with MANDATORY safety-first validation.
    
    Flow: Inbound → SafetyService → Intelligence → Enforcement → Execution
    """
    try:
        # Parse WhatsApp payload
        payload = await request.json()
        
        # Extract message content
        message_data = extract_whatsapp_message(payload)
        
        # ============================================================
        # STEP 1: SAFETY VALIDATION (MANDATORY FIRST CALL)
        # ============================================================
        safety_service = get_safety_service()
        safety_result = safety_service.validate_inbound({
            "content": message_data["content"],
            "sender": message_data["from"],
            "recipient": "assistant",
            "platform": "whatsapp",
            "timestamp": datetime.now().isoformat() + "Z",
            "language": message_data.get("language", "en")
        })
        
        # Log safety decision
        log_safety_decision(safety_result)
        
        # ============================================================
        # STEP 2: HARD STOP ON DENY
        # ============================================================
        if safety_result["decision"] == "hard_deny":
            return {
                "status": "blocked",
                "reason": "Message blocked due to safety policy",
                "trace_id": safety_result["trace_id"]
            }
        
        # ============================================================
        # STEP 3: REWRITE CONTENT IF NEEDED
        # ============================================================
        if safety_result["decision"] == "soft_rewrite":
            message_data["content"] = safety_result["rewritten_content"]
        
        # ============================================================
        # STEP 4: PROCEED TO INTELLIGENCE (ONLY AFTER SAFETY APPROVAL)
        # ============================================================
        intelligence_result = await process_intelligence(
            message_data["content"],
            safety_result["trace_id"]
        )
        
        # ============================================================
        # STEP 5: ENFORCEMENT
        # ============================================================
        enforcement_result = await apply_enforcement(
            intelligence_result,
            safety_result["trace_id"]
        )
        
        # ============================================================
        # STEP 6: EXECUTION
        # ============================================================
        response = await execute_response(
            enforcement_result,
            message_data["from"],
            safety_result["trace_id"]
        )
        
        return {
            "status": "success",
            "trace_id": safety_result["trace_id"],
            "response": response
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def extract_whatsapp_message(payload: dict) -> dict:
    """Extract message from WhatsApp webhook payload"""
    try:
        entry = payload["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        message = value["messages"][0]
        
        return {
            "from": message["from"],
            "content": message["text"]["body"],
            "message_id": message["id"],
            "timestamp": message["timestamp"],
            "language": "en"  # TODO: Detect language
        }
    except (KeyError, IndexError) as e:
        raise HTTPException(status_code=400, detail="Invalid WhatsApp payload")


async def process_intelligence(content: str, trace_id: str) -> dict:
    """
    Process content through intelligence layer.
    ONLY called after mediation and safety approval.
    """
    # TODO: Implement intelligence processing
    return {"trace_id": trace_id, "response": f"Processed: {content}"}


async def apply_enforcement(intelligence_result: dict, trace_id: str) -> dict:
    """Apply enforcement rules"""
    # TODO: Implement enforcement logic
    return {
        "trace_id": trace_id,
        "approved": True,
        "result": intelligence_result
    }


async def execute_response(enforcement_result: dict, recipient: str, trace_id: str) -> dict:
    """Execute final response"""
    # TODO: Implement response execution
    return {
        "trace_id": trace_id,
        "sent_to": recipient,
        "status": "delivered"
    }


def log_safety_decision(safety_result: dict):
    """Log safety decision to bucket/database"""
    # TODO: Implement bucket logging
    print(f"[SAFETY] {safety_result['trace_id']}: {safety_result['decision']} - {safety_result['reason']}")
