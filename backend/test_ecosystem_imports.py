import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

results = {}

# Voice
try:
    from app.voice.stt_engine import STTService
    from app.voice.voice_session_manager import VoiceSessionManager
    from app.voice.language_auto import LanguageAuto
    from app.voice.telephony_stream import TelephonyStream
    results["voice"] = "OK"
except Exception as e:
    results["voice"] = str(e)

# Audio
try:
    from app.audio.tts_service import TTSService
    results["audio"] = "OK"
except Exception as e:
    results["audio"] = str(e)

# Agents
try:
    from app.agents.base_agent import BaseAgent
    results["agents"] = "OK"
except Exception as e:
    results["agents"] = str(e)

# Governance
try:
    from app.governance.behavior_validator import BehaviorValidator
    results["governance"] = "OK"
except Exception as e:
    results["governance"] = str(e)

# UniGuru
try:
    from app.uniguru.rules.base import RuleContext, RuleResult, RuleAction
    from app.uniguru.rules.forward import ForwardRule
    results["uniguru_rules"] = "OK"
except Exception as e:
    results["uniguru_rules"] = str(e)

# Runtime
try:
    from app.runtime.lifecycle import RuntimeLifecycle
    from app.runtime.store import RuntimeStore
    results["runtime"] = "OK"
except Exception as e:
    results["runtime"] = str(e)

# Executors
try:
    from app.executors.email_executor import EmailExecutor
    results["executors"] = "OK"
except Exception as e:
    results["executors"] = str(e)

# UniGuru capability (upgraded)
try:
    from app.capabilities.uniguru_capability import UniGuruCapability
    cap = UniGuruCapability()
    assert cap.name == "uniguru"
    assert "knowledge" in cap.supported_intents
    results["uniguru_cap"] = "OK"
except Exception as e:
    results["uniguru_cap"] = str(e)

print("=" * 40)
for k, v in results.items():
    status = "OK" if v == "OK" else "WARN"
    print(f"  [{status}] {k}: {v}")
ok = sum(1 for v in results.values() if v == "OK")
print(f"\n  {ok}/{len(results)} modules imported successfully")
print("=" * 40)
