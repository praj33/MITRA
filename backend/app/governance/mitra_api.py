"""
mitra_api.py — Mitra Safety Evaluation API

Endpoint: POST /api/mitra/evaluate

Accepts structured input, runs through the full pipeline:
  input → validation → classification → enforcement → output

Returns structured decision with trace_id.
"""

from http.server import BaseHTTPRequestHandler
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from runtime_pipeline import run_pipeline


# ---------------------------------------------------------------------------
# Step 6 — Output mapping
# ---------------------------------------------------------------------------

def _map_status(final_decision: str, stages: list) -> str:
    """Map pipeline decision → ALLOW / FLAG / BLOCK"""
    if final_decision == "BLOCK":
        return "BLOCK"
    # REWRITE at safety stage = FLAG
    safety = next((s for s in stages if s["stage"] == "safety_validator"), None)
    if safety and safety["output"].get("decision") == "REWRITE":
        return "FLAG"
    if final_decision == "DELAY":
        return "FLAG"
    return "ALLOW"


def _map_risk(status: str, stages: list) -> str:
    """Map status + enforcement → LOW / MEDIUM / HIGH"""
    if status == "BLOCK":
        return "HIGH"
    enf = next((s for s in stages if s["stage"] == "enforcement_decision"), None)
    if enf:
        severity = enf["output"].get("severity", "low")
        if severity in ("high", "critical"):
            return "HIGH"
        if severity == "medium":
            return "MEDIUM"
    if status == "FLAG":
        return "MEDIUM"
    return "LOW"


def _map_reason(result: dict, stages: list) -> str:
    """Build a clear reason string from pipeline stage outputs"""
    safety = next((s for s in stages if s["stage"] == "safety_validator"), None)
    if safety:
        out = safety["output"]
        if out.get("decision") in ("BLOCK", "REWRITE"):
            return out.get("reason", "Safety rule matched")
    enf = next((s for s in stages if s["stage"] == "enforcement_decision"), None)
    if enf and enf["output"].get("decision") in ("block", "escalate"):
        return "Enforcement rejected response"
    orch = next((s for s in stages if s["stage"] == "orchestration"), None)
    if orch:
        decision = orch["output"].get("decision", "")
        if decision == "block":
            return orch["output"].get("reason", "Mediation blocked message")
        if decision == "delay":
            return orch["output"].get("reason", "Message delayed")
    return "Content passed all safety checks"


def _map_confidence(result: dict, stages: list) -> float:
    """Return confidence as 0.0–1.0 from enforcement or safety stage"""
    enf = next((s for s in stages if s["stage"] == "enforcement_decision"), None)
    if enf:
        raw = enf["output"].get("confidence", 0.95)
        return round(float(raw), 2)
    safety = next((s for s in stages if s["stage"] == "safety_validator"), None)
    if safety:
        raw = safety["output"].get("confidence", 0.0)
        # policy engine returns 0–100, normalize to 0–1
        if isinstance(raw, (int, float)) and raw > 1.0:
            return round(raw / 100.0, 2)
        return round(float(raw), 2)
    return 0.0


class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        # Step 7 — Error handling: parse body
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length))
        except Exception:
            self._respond(400, {"error": "Request body must be valid JSON"})
            return

        # Step 7 — Error handling: missing event
        if "event" not in payload:
            self._respond(400, {"error": "'event' field is required"})
            return

        event = payload["event"]
        title      = event.get("title", "")
        content    = event.get("content", "")
        category   = event.get("category", "")
        confidence = event.get("confidence", None)

        user_input = f"{title} {content}".strip() if title else content

        # Step 7 — Error handling: empty content
        if not user_input:
            self._respond(400, {"error": "'event.content' is required"})
            return

        # Step 5 — Pass into Mitra pipeline, no logic changes
        try:
            result = run_pipeline(
                user_input=user_input,
                user_id=payload.get("user_id", "anonymous"),
                platform=payload.get("platform", "api"),
                region=payload.get("region", None),
            )
        except Exception as e:
            # Step 7 — Error handling: pipeline failure
            self._respond(500, {"error": f"Pipeline failure: {str(e)}"})
            return

        # Step 6 — Map to standardized output
        stages = result["stages"]
        status     = _map_status(result["final_decision"], stages)
        risk_level = _map_risk(status, stages)
        reason     = _map_reason(result, stages)
        conf       = _map_confidence(result, stages)

        self._respond(200, {
            "status":     status,
            "risk_level": risk_level,
            "reason":     reason,
            "confidence": conf,
        })

    def _respond(self, code: int, body: dict):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self._cors()
        self.end_headers()
        self.wfile.write(data)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, format, *args):
        pass
