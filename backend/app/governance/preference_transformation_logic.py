"""
PREFERENCE-AWARE TRANSFORMATION LOGIC
Day 2: User preference mediation for inbound content
"""

import json
from datetime import datetime, time
from enum import Enum
from typing import Dict, List, Optional, Tuple

class LanguageMode(Enum):
    FORMAL = "formal"
    CASUAL = "casual" 
    MINIMAL = "minimal"
    DETAILED = "detailed"

class NotificationFrequency(Enum):
    IMMEDIATE = "immediate"
    BATCHED_HOURLY = "batched_hourly"
    BATCHED_DAILY = "batched_daily"
    ON_DEMAND = "on_demand"

class EmotionalTone(Enum):
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    PROTECTIVE = "protective"
    TRANSPARENT = "transparent"

class PreferenceMediator:
    def __init__(self):
        self.user_preferences = {}
    
    def load_user_preferences(self, user_id: str) -> Dict:
        """Load user preferences from storage"""
        return self.user_preferences.get(user_id, self._default_preferences())
    
    def _default_preferences(self) -> Dict:
        """Default preference settings"""
        return {
            "language": LanguageMode.CASUAL.value,
            "notification_frequency": NotificationFrequency.IMMEDIATE.value,
            "emotional_tone": EmotionalTone.NEUTRAL.value,
            "time_windows": {
                "work": "09:00-17:00",
                "personal": "17:00-22:00",
                "sleep": "22:00-09:00"
            },
            "priority_contacts": {
                "family": [],
                "work": [],
                "emergency": []
            }
        }
    
    def should_deliver_now(self, user_id: str, source: str, urgency: str) -> Tuple[bool, str]:
        """Determine if content should be delivered immediately"""
        prefs = self.load_user_preferences(user_id)
        current_time = datetime.now().time()
        
        # Emergency always delivers
        if urgency == "critical" or source in prefs["priority_contacts"]["emergency"]:
            return True, "emergency_override"
        
        # Priority contacts bypass time windows
        if self._is_priority_contact(source, prefs):
            return True, "priority_contact"
        
        # Check time windows
        if self._in_sleep_hours(current_time, prefs):
            return False, "sleep_hours"
        
        # Check notification frequency
        if prefs["notification_frequency"] == NotificationFrequency.ON_DEMAND.value:
            return False, "on_demand_mode"
        
        if prefs["notification_frequency"] in [NotificationFrequency.BATCHED_HOURLY.value, NotificationFrequency.BATCHED_DAILY.value]:
            if urgency in ["low", "medium"]:
                return False, "batched_delivery"
        
        return True, "immediate_delivery"
    
    def transform_content(self, content: str, user_id: str, context: Dict) -> Dict:
        """Transform content based on user preferences"""
        prefs = self.load_user_preferences(user_id)
        
        # Apply language transformation
        transformed_content = self._apply_language_mode(content, prefs["language"])
        
        # Apply emotional tone filtering
        transformed_content = self._apply_emotional_tone(transformed_content, prefs["emotional_tone"], context)
        
        # Generate delivery format
        return {
            "message_primary": transformed_content,
            "urgency_level": self._adjust_urgency(context.get("urgency", "medium"), prefs),
            "source_hidden": self._format_source(context.get("source", "unknown"), prefs),
            "suggested_action": self._generate_action(context, prefs),
            "emotional_tone": prefs["emotional_tone"]
        }
    
    def _apply_language_mode(self, content: str, language_mode: str) -> str:
        """Transform content based on language preference"""
        if language_mode == LanguageMode.MINIMAL.value:
            return f"• {content[:50]}..." if len(content) > 50 else f"• {content}"
        
        elif language_mode == LanguageMode.FORMAL.value:
            # Remove casual language, make professional
            formal_content = content.replace("Hey!", "").replace("ASAP", "as soon as possible")
            return f"Communication received: {formal_content}"
        
        elif language_mode == LanguageMode.DETAILED.value:
            return f"Message content: {content}\nContext: Inbound communication requiring review"
        
        else:  # CASUAL
            return content
    
    def _apply_emotional_tone(self, content: str, tone_mode: str, context: Dict) -> str:
        """Filter content based on emotional tone preference"""
        if tone_mode == EmotionalTone.PROTECTIVE.value:
            # Check for emotional manipulation indicators
            manipulation_keywords = ["devastated", "crushing", "heartbroken", "abandoned", "hurt"]
            if any(keyword in content.lower() for keyword in manipulation_keywords):
                return "Message contains concerning language - review when ready"
        
        elif tone_mode == EmotionalTone.NEUTRAL.value:
            # Strip emotional language
            neutral_replacements = {
                "devastated": "concerned",
                "amazing": "notable", 
                "terrible": "problematic",
                "love": "appreciate"
            }
            for emotional, neutral in neutral_replacements.items():
                content = content.replace(emotional, neutral)
        
        elif tone_mode == EmotionalTone.POSITIVE.value:
            # Emphasize constructive aspects
            if context.get("risk_categories"):
                return f"Message received - constructive review recommended"
        
        return content
    
    def _is_priority_contact(self, source: str, prefs: Dict) -> bool:
        """Check if source is in priority contacts"""
        priority_lists = prefs["priority_contacts"]
        for category in priority_lists.values():
            if source in category:
                return True
        return False
    
    def _in_sleep_hours(self, current_time: time, prefs: Dict) -> bool:
        """Check if current time is in sleep hours"""
        sleep_window = prefs["time_windows"]["sleep"]
        start_str, end_str = sleep_window.split("-")
        start_time = time.fromisoformat(start_str)
        end_time = time.fromisoformat(end_str)
        
        # Handle overnight sleep hours (22:00-09:00)
        if start_time > end_time:
            return current_time >= start_time or current_time <= end_time
        else:
            return start_time <= current_time <= end_time
    
    def _adjust_urgency(self, original_urgency: str, prefs: Dict) -> str:
        """Adjust urgency based on user preferences and context"""
        current_time = datetime.now().time()
        
        # Reduce urgency during sleep hours for non-emergency
        if self._in_sleep_hours(current_time, prefs):
            if original_urgency == "high":
                return "medium"
            elif original_urgency == "medium":
                return "low"
        
        return original_urgency
    
    def _format_source(self, source: str, prefs: Dict) -> str:
        """Format source information based on preferences"""
        if self._is_priority_contact(source, prefs):
            # Show more detail for priority contacts
            for category, contacts in prefs["priority_contacts"].items():
                if source in contacts:
                    return f"{category.title()} contact"
        
        # Generic formatting for unknown sources
        if "@" in source:
            return "Email contact"
        elif source.startswith("+"):
            return "Phone contact"
        else:
            return "Unknown contact"
    
    def _generate_action(self, context: Dict, prefs: Dict) -> str:
        """Generate suggested action based on content and preferences"""
        if context.get("risk_categories"):
            return "Review for safety concerns"
        
        if context.get("urgency") == "high":
            return "Response recommended"
        
        if prefs["notification_frequency"] in [NotificationFrequency.BATCHED_HOURLY.value, NotificationFrequency.BATCHED_DAILY.value]:
            return "Included in next digest"
        
        return "No immediate action required"

# Integration with inbound validator
def apply_user_preferences(validator_output: Dict, user_id: str) -> Dict:
    """Apply user preferences to validator output"""
    mediator = PreferenceMediator()
    
    # Check delivery timing
    should_deliver, reason = mediator.should_deliver_now(
        user_id, 
        validator_output.get("source", "unknown"),
        validator_output.get("urgency_level", "medium")
    )
    
    if not should_deliver:
        return {
            "delivery_status": "delayed",
            "delay_reason": reason,
            "scheduled_delivery": "next_batch"
        }
    
    # Transform content based on preferences
    transformed = mediator.transform_content(
        validator_output.get("message_primary", ""),
        user_id,
        validator_output
    )
    
    return {
        "delivery_status": "immediate",
        **transformed
    }

# Example usage
if __name__ == "__main__":
    # Sample user preferences
    mediator = PreferenceMediator()
    mediator.user_preferences["user_123"] = {
        "language": "minimal",
        "notification_frequency": "batched_hourly",
        "emotional_tone": "protective",
        "time_windows": {
            "work": "09:00-17:00",
            "personal": "17:00-22:00",
            "sleep": "22:00-09:00"
        },
        "priority_contacts": {
            "family": ["mom@email.com"],
            "work": ["boss@company.com"],
            "emergency": ["911"]
        }
    }
    
    # Test transformation
    sample_output = {
        "message_primary": "I'm devastated you haven't responded! This is urgent!",
        "urgency_level": "high",
        "source": "unknown@email.com",
        "risk_categories": ["emotional_manipulation"]
    }
    
    result = apply_user_preferences(sample_output, "user_123")
    print(json.dumps(result, indent=2))