import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

results = {}

# ─── CRITICAL SERVICES ───
try:
    from app.services.safety_service import SafetyService
    svc = SafetyService()
    assert svc.get_status()["status"] == "active"
    results["safety_service"] = "OK"
except Exception as e:
    results["safety_service"] = str(e)

try:
    from app.services.intelligence_service import IntelligenceService
    svc = IntelligenceService()
    assert svc.get_status()["status"] == "active"
    results["intelligence_service"] = "OK"
except Exception as e:
    results["intelligence_service"] = str(e)

try:
    from app.services.enforcement_service import EnforcementService
    svc = EnforcementService()
    assert svc.get_status()["status"] == "active"
    results["enforcement_service"] = "OK"
except Exception as e:
    results["enforcement_service"] = str(e)

try:
    from app.services.execution_service import ExecutionService
    results["execution_service"] = "OK"
except Exception as e:
    results["execution_service"] = str(e)

try:
    from app.services.bucket_service import BucketService
    results["bucket_service"] = "OK"
except Exception as e:
    results["bucket_service"] = str(e)

# ─── EXTERNAL LAYER ───
try:
    from app.external.safety.behavior_validator import validate_behavior
    results["ext_safety"] = "OK"
except Exception as e:
    results["ext_safety"] = str(e)

try:
    from app.external.enforcement.enforcement_engine import enforce
    results["ext_enforcement_engine"] = "OK"
except Exception as e:
    results["ext_enforcement_engine"] = str(e)

try:
    from app.external.enforcement.simple_engine import EnforcementEngine as SE
    results["ext_simple_engine"] = "OK"
except Exception as e:
    results["ext_simple_engine"] = str(e)

try:
    from app.external.intelligence.intelligence_service import IntelligenceCore
    results["ext_intelligence"] = "OK"
except Exception as e:
    results["ext_intelligence"] = str(e)

try:
    from app.external.bucket.database.mongo_db import MongoDBClient
    results["ext_bucket_mongo"] = "OK"
except Exception as e:
    results["ext_bucket_mongo"] = str(e)

try:
    from app.external.bucket.middleware.audit_middleware import AuditMiddleware
    results["ext_audit_middleware"] = "OK"
except Exception as e:
    results["ext_audit_middleware"] = str(e)

try:
    from app.external.bucket.utils.threat_validator import BucketThreatModel
    results["ext_threat_validator"] = "OK"
except Exception as e:
    results["ext_threat_validator"] = str(e)

# ─── VOICE ───
try:
    from app.voice.stt_engine import STTService
    from app.voice.voice_session_manager import VoiceSessionManager
    from app.voice.language_auto import LanguageAuto
    from app.voice.telephony_stream import TelephonyStream
    from app.voice.telephony_executor import TelephonyExecutor
    from app.voice.voice_trace import VoiceTraceLogger
    from app.voice.failure_handler import VoiceFailureHandler
    results["voice_full"] = "OK"
except Exception as e:
    results["voice_full"] = str(e)

try:
    from app.audio.tts_service import TTSService
    results["audio_tts"] = "OK"
except Exception as e:
    results["audio_tts"] = str(e)

# ─── EXECUTORS ───
try:
    from app.executors.email_executor import EmailExecutor
    results["email_executor"] = "OK"
except Exception as e:
    results["email_executor"] = str(e)

try:
    from app.executors.whatsapp_executor import WhatsAppExecutor
    results["whatsapp_executor"] = "OK"
except Exception as e:
    results["whatsapp_executor"] = str(e)

try:
    from app.executors.instagram_executor import InstagramExecutor
    results["instagram_executor"] = "OK"
except Exception as e:
    results["instagram_executor"] = str(e)

# ─── GOVERNANCE ───
try:
    from app.governance.behavior_validator import BehaviorValidator
    results["gov_behavior"] = "OK"
except Exception as e:
    results["gov_behavior"] = str(e)

try:
    from app.governance.enforcement_adapter import EnforcementAdapter
    results["gov_enforcement"] = "OK"
except Exception as e:
    results["gov_enforcement"] = str(e)

try:
    from app.governance.enforcement_execution_system import EnforcementExecutionSystem
    results["gov_exec_system"] = "OK"
except Exception as e:
    results["gov_exec_system"] = str(e)

try:
    from app.governance.inbound_behavior_validator import InboundBehaviorValidator
    results["gov_inbound"] = "OK"
except Exception as e:
    results["gov_inbound"] = str(e)

# ─── UNIGURU ───
try:
    from app.uniguru.rules.base import RuleContext, RuleResult, RuleAction
    from app.uniguru.rules.forward import ForwardRule
    from app.capabilities.uniguru_capability import UniGuruCapability
    results["uniguru"] = "OK"
except Exception as e:
    results["uniguru"] = str(e)

# ─── RUNTIME ───
try:
    from app.runtime.constants import RuntimeState, DispatchStatus
    from app.runtime.store import RuntimeStore
    from app.runtime.lifecycle import RuntimeLifecycle
    results["runtime"] = "OK"
except Exception as e:
    results["runtime"] = str(e)

# ─── AGENTS + TOOLS ───
try:
    from app.agents.base_agent import BaseAgent
    results["agents"] = "OK"
except Exception as e:
    results["agents"] = str(e)

try:
    from app.tools.calculator_tool import CalculatorTool
    results["tools"] = "OK"
except Exception as e:
    results["tools"] = str(e)

# ─── PRINT RESULTS ───
print("=" * 55)
print("  MITRA v5.0.0 — Deep Ecosystem Import Audit")
print("=" * 55)
ok = 0
fail = 0
for k, v in results.items():
    status = "OK" if v == "OK" else "FAIL"
    if v == "OK":
        ok += 1
    else:
        fail += 1
    indicator = "  [OK]  " if v == "OK" else "  [FAIL]"
    detail = "" if v == "OK" else f" — {v}"
    print(f"{indicator} {k}{detail}")

print(f"\n  {ok}/{ok+fail} passed, {fail} failed")
print("=" * 55)
