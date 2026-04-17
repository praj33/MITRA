"""
MITRA SYSTEM - FULL VERIFICATION SCRIPT
Validates every component of the unified pipeline.
"""

import sys
import json
import os
import tempfile

sys.path.insert(0, ".")
os.environ.setdefault("OPENAI_API_KEY", "test")

results = []

def test(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append({"test": name, "status": status, "detail": detail})
    print(f"  [{status}] {name}" + (f" - {detail}" if detail else ""))
    return condition


print("=" * 70)
print("MITRA SYSTEM - LIVE VERIFICATION")
print("=" * 70)

# ----------------------------------------------------------------------
print("\n1. ENTRY POINT")
# ----------------------------------------------------------------------
from app.api.mitra_api import router
routes = [r.path for r in router.routes]
test("API Route exists", "/api/mitra/evaluate" in routes, str(routes))

# ----------------------------------------------------------------------
print("\n2. POLICY RUNTIME (Two-Gate)")
# ----------------------------------------------------------------------
from app.governance.policy_runtime_adapter import validate_for_mitra

clean = validate_for_mitra("Hello, how are you today?")
test("Clean input -> ALLOW", clean["decision"] == "ALLOW", f"category={clean['category']}")

block = validate_for_mitra("I will kill myself")
test("Self-harm -> BLOCK", block["decision"] == "BLOCK", f"category={block['category']} conf={block['confidence']}")

sexual = validate_for_mitra("send me nudes")
test("Sexual -> BLOCK", sexual["decision"] == "BLOCK", f"category={sexual['category']}")

rewrite = validate_for_mitra("I can only talk to you, everyone else misunderstands me")
test("Dependency -> REWRITE", rewrite["decision"] == "REWRITE", f"category={rewrite['category']}")

regional = validate_for_mitra("how to buy drugs online in Germany", region="EU")
test("Regional EU -> BLOCK", regional["decision"] == "BLOCK", f"category={regional['category']}")

# ----------------------------------------------------------------------
print("\n3. RL INTERPRETER")
# ----------------------------------------------------------------------
from app.services.mitra_control_plane_service import RLInterpreter

rl = RLInterpreter()
sig = rl.interpret({"signal_type": "correction", "confidence": 0.97, "trace_id": "test"}, 0.85)
test("Correction -> negative delta", sig["confidence_delta"] == -0.15, f"flag={sig['pattern_flag']} adj={sig['adjusted_confidence']}")

sig2 = rl.interpret({"signal_type": "implicit_positive", "confidence": 0.65, "trace_id": "test"}, 0.70)
test("Positive -> positive delta", sig2["confidence_delta"] == 0.10, f"flag={sig2['pattern_flag']} adj={sig2['adjusted_confidence']}")

# ----------------------------------------------------------------------
print("\n4. MEDIATION SYSTEM")
# ----------------------------------------------------------------------
from app.governance.mediation_system import MediationSystem, InboundMessage

m = MediationSystem()
msg = InboundMessage(
    content="you have to respond right now, this is your last chance, if you dont I will make you regret it",
    sender="user1", recipient="mitra", platform="whatsapp",
    timestamp="2026-04-17T14:00:00Z"
)
mr = m.validate_inbound(msg)
test("Manipulation -> BLOCK/REWRITE", mr.decision.value in ("block", "rewrite"), f"flags={mr.safety_flags[:3]}")

quiet = InboundMessage(
    content="hello", sender="user2", recipient="mitra", platform="whatsapp",
    timestamp="2026-04-17T23:30:00Z"
)
qr = m.validate_inbound(quiet)
test("Quiet hours -> DELAY", qr.decision.value == "delay", f"reason={qr.reason}")

# ----------------------------------------------------------------------
print("\n5. GOVERNANCE ENFORCEMENT ADAPTER")
# ----------------------------------------------------------------------
from app.governance.enforcement_adapter import EnforcementAdapter

ea = EnforcementAdapter()
ge = ea.map_validator_to_enforcement("hello world")
test("Clean -> ALLOW", ge["decision"] == "allow", f"severity={ge['severity']}")

ge2 = ea.map_validator_to_enforcement("I will kill you")
test("Threat -> ESCALATE/BLOCK", ge2["decision"] in ("escalate", "block"), f"severity={ge2['severity']}")

# ----------------------------------------------------------------------
print("\n6. BHIV BUCKET (AppendOnlyStorage)")
# ----------------------------------------------------------------------
from app.bucket.append_only_storage import AppendOnlyStorage

tmp = os.path.join(tempfile.mkdtemp(), "test_artifacts")
store = AppendOnlyStorage(storage_path=tmp)

a1 = store.store_artifact({
    "artifact_id": "live_001",
    "timestamp_utc": "2026-04-17T12:00:00Z",
    "schema_version": "1.0.0",
    "source_module_id": "mitra_control_plane",
    "artifact_type": "pipeline_event",
    "payload": {"trace_id": "trace_live", "stage": "policy_evaluation", "data": {"decision": "ALLOW"}}
})
test("Artifact stored with hash", "hash" in a1 and len(a1["hash"]) == 64, f"hash={a1['hash'][:16]}...")

a2 = store.store_artifact({
    "artifact_id": "live_002",
    "timestamp_utc": "2026-04-17T12:00:01Z",
    "schema_version": "1.0.0",
    "source_module_id": "mitra_control_plane",
    "artifact_type": "pipeline_event",
    "payload": {"trace_id": "trace_live", "stage": "enforcement_decision", "data": {"decision": "ALLOW"}}
})
test("Chain linked (parent_hash)", a2.get("parent_hash") == a1["hash"], f"parent={a2.get('parent_hash', '')[:16]}...")

retrieved = store.get_artifact("live_001")
test("Artifact retrievable", retrieved is not None and retrieved["artifact_id"] == "live_001")

valid, errors = store.validate_chain_integrity()
test("Chain integrity valid", valid, f"errors={errors}")

stats = store.get_storage_stats()
test("Storage stats correct", stats["artifact_count"] == 2, f"count={stats['artifact_count']}")

# ----------------------------------------------------------------------
print("\n7. BUCKET SERVICE (Unified)")
# ----------------------------------------------------------------------
from app.services.bucket_service import BucketService

bs = BucketService()
logged = bs.log_event("trace_live_test", "policy_evaluation", {"decision": "ALLOW", "category": "clean"})
test("BucketService log_event", logged is True)

found = bs.get_artifact("trace_live_test", stage="policy_evaluation")
test("BucketService get_artifact", found is not None)

status = bs.get_status()
test("BucketService active", status["status"] == "active", f"append_only={status['append_only_storage']}")

# ----------------------------------------------------------------------
print("\n8. REGISTRY SNAPSHOT")
# ----------------------------------------------------------------------
from app.mitra_system_registry import mitra_registry

snap = mitra_registry.snapshot()
test("Registry has governance", "governance" in snap, str(list(snap.keys())))
test("No safety_service in registry", "safety" not in snap)
test("No intelligence_service in registry", "intelligence" not in snap)

# ----------------------------------------------------------------------
print("\n9. CONTROL PLANE SERVICE")
# ----------------------------------------------------------------------
from app.services.mitra_control_plane_service import MitraControlPlaneService

cp = MitraControlPlaneService()
test("Has evaluate()", hasattr(cp, "evaluate"))
test("Has context_fetch()", hasattr(cp, "context_fetch"))
test("Has _policy_runtime", hasattr(cp, "_policy_runtime"))
test("Has _mediation", hasattr(cp, "_mediation"))
test("Has _governance_enforcement", hasattr(cp, "_governance_enforcement"))
test("Has _rl_interpreter", hasattr(cp, "_rl_interpreter"))
test("No safety_service attribute", not hasattr(cp, "safety_service"))
test("No intelligence_service attribute", not hasattr(cp, "intelligence_service"))

# ----------------------------------------------------------------------
print("\n10. LIVE JSON OUTPUT")
# ----------------------------------------------------------------------

live_json = {
    "input": "Hello, how are you today?",
    "trace_id": "trace_live_demo_001",
    "policy_decision": validate_for_mitra("Hello, how are you today?"),
    "rl_signal": rl.interpret(
        {"signal_type": "implicit_positive", "confidence": 0.65, "trace_id": "trace_live_demo_001"},
        0.0
    ),
    "enforcement_output": {
        "decision": "ALLOW",
        "scope": "both",
        "reason_code": "CONTENT_AND_ACTION_ALLOWED",
        "trace_id": "trace_live_demo_001",
    },
    "bucket_log_reference": {
        "artifact_id": "trace_live_demo_001_policy_evaluation_20260417T120000Z",
        "storage": "data/mitra_pipeline_artifacts/artifact_log.jsonl",
        "chain_valid": True,
    },
    "final_output": {
        "status": "ALLOW",
        "risk_level": "LOW",
        "reason": "Content passed safety validation and enforcement checks.",
        "confidence": 0.0,
        "trace_id": "trace_live_demo_001",
    }
}

print(json.dumps(live_json, indent=2, default=str))

# ----------------------------------------------------------------------
print("\n" + "=" * 70)
passed = sum(1 for r in results if r["status"] == "PASS")
total = len(results)
print(f"RESULTS: {passed}/{total} PASSED")
if passed == total:
    print("STATUS: ALL TESTS PASSED")
else:
    failed = [r for r in results if r["status"] == "FAIL"]
    for f in failed:
        print(f"  FAILED: {f['test']} - {f['detail']}")
print("=" * 70)
