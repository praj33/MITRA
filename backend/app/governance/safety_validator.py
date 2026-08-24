from http.server import BaseHTTPRequestHandler
import json
import time
import hashlib
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            # Route to appropriate validation function
            if self.path == '/api/validateInbound':
                response = self.validate_inbound(request_data)
            elif self.path == '/api/validateAction':
                response = self.validate_action(request_data)
            else:
                self.send_response(404)
                self.end_headers()
                return
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    
    def validate_inbound(self, request_data):
        """Validate inbound messages - returns ALLOW|BLOCK|REWRITE"""
        content = request_data.get('content', '')
        user_id = request_data.get('user_id', 'unknown')
        
        # Generate trace ID
        trace_id = f"inbound_{abs(hash(content + user_id + str(time.time())))}"[:16]
        
        content_lower = content.lower()
        
        # BLOCK scenarios - severe content
        if any(word in content_lower for word in ['kill myself', 'suicide', 'end it all', 'want to die']):
            return {
                "decision": "BLOCK",
                "risk_category": "self_harm",
                "confidence": 95.0,
                "trace_id": trace_id,
                "reason": "Self-harm content detected",
                "safe_alternative": "Crisis support resources are available. Please contact 988 for immediate help.",
                "timestamp": datetime.now().isoformat() + "Z"
            }
        
        if any(word in content_lower for word in ['hack', 'illegal', 'bomb', 'weapon', 'drugs']):
            return {
                "decision": "BLOCK", 
                "risk_category": "illegal_content",
                "confidence": 90.0,
                "trace_id": trace_id,
                "reason": "Illegal content detected",
                "safe_alternative": "I can't help with that request.",
                "timestamp": datetime.now().isoformat() + "Z"
            }
        
        # REWRITE scenarios - moderate issues
        if any(phrase in content_lower for phrase in ['you have to', 'you must', 'if you don\'t', 'last chance']):
            return {
                "decision": "REWRITE",
                "risk_category": "manipulation",
                "confidence": 75.0,
                "trace_id": trace_id,
                "reason": "Emotional manipulation detected",
                "safe_alternative": "Message received requesting communication response.",
                "original_content": content,
                "timestamp": datetime.now().isoformat() + "Z"
            }
        
        if any(word in content_lower for word in ['lonely', 'alone', 'nobody cares', 'no friends']):
            return {
                "decision": "REWRITE",
                "risk_category": "emotional_dependency", 
                "confidence": 70.0,
                "trace_id": trace_id,
                "reason": "Emotional dependency patterns detected",
                "safe_alternative": "I understand you're feeling isolated. Community support resources may be helpful.",
                "original_content": content,
                "timestamp": datetime.now().isoformat() + "Z"
            }
        
        # ALLOW scenarios - safe content
        return {
            "decision": "ALLOW",
            "risk_category": "clean",
            "confidence": 0.0,
            "trace_id": trace_id,
            "reason": "Content is safe",
            "timestamp": datetime.now().isoformat() + "Z"
        }
    
    def validate_action(self, request_data):
        """Validate outbound actions - returns ALLOW|BLOCK|REWRITE"""
        content = request_data.get('content', '')
        action_type = request_data.get('action_type', 'message')
        recipient = request_data.get('recipient', 'unknown')
        
        # Generate trace ID
        trace_id = f"action_{abs(hash(content + action_type + str(time.time())))}"[:16]
        
        content_lower = content.lower()
        
        # BLOCK scenarios - unsafe outbound actions
        if any(word in content_lower for word in ['threat', 'hurt you', 'make you pay', 'regret']):
            return {
                "decision": "BLOCK",
                "risk_category": "threatening_content",
                "confidence": 95.0,
                "trace_id": trace_id,
                "reason": "Threatening content in outbound action",
                "blocked_action": action_type,
                "timestamp": datetime.now().isoformat() + "Z"
            }
        
        if any(word in content_lower for word in ['personal info', 'address', 'phone number', 'ssn']):
            return {
                "decision": "BLOCK",
                "risk_category": "privacy_violation",
                "confidence": 90.0,
                "trace_id": trace_id,
                "reason": "Privacy violation in outbound action",
                "blocked_action": action_type,
                "timestamp": datetime.now().isoformat() + "Z"
            }
        
        # REWRITE scenarios - needs modification
        if any(phrase in content_lower for phrase in ['you should', 'you need to', 'you must', 'urgent']):
            safe_content = content.replace('you should', 'you might consider')
            safe_content = safe_content.replace('you need to', 'you could')
            safe_content = safe_content.replace('you must', 'please consider')
            safe_content = safe_content.replace('urgent', 'important')
            
            return {
                "decision": "REWRITE",
                "risk_category": "pushy_language",
                "confidence": 70.0,
                "trace_id": trace_id,
                "reason": "Pushy language detected in outbound action",
                "original_content": content,
                "rewritten_content": safe_content,
                "action_type": action_type,
                "timestamp": datetime.now().isoformat() + "Z"
            }
        
        if 'immediately' in content_lower or 'right now' in content_lower:
            safe_content = content.replace('immediately', 'when convenient')
            safe_content = safe_content.replace('right now', 'at your convenience')
            
            return {
                "decision": "REWRITE",
                "risk_category": "urgency_pressure",
                "confidence": 65.0,
                "trace_id": trace_id,
                "reason": "Urgency pressure detected in outbound action",
                "original_content": content,
                "rewritten_content": safe_content,
                "action_type": action_type,
                "timestamp": datetime.now().isoformat() + "Z"
            }
        
        # ALLOW scenarios - safe actions
        return {
            "decision": "ALLOW",
            "risk_category": "clean",
            "confidence": 0.0,
            "trace_id": trace_id,
            "reason": "Action is safe to execute",
            "action_type": action_type,
            "timestamp": datetime.now().isoformat() + "Z"
        }