"""
Prosody Mapper - Handles prosody (intonation, rhythm, stress) mapping for different styles
Manages emotional and contextual speech patterns
"""
import os
import json
from typing import Dict, Any, List
from datetime import datetime

class ProsodyMapper:
    """Maps prosody styles to specific parameters"""
    
    def __init__(self):
        self.mappings_file = os.path.join(os.path.dirname(__file__), "data", "prosody_mappings.json")
        self.prosody_mappings = self._load_mappings()
        self.default_styles = ["neutral", "happy", "sad", "angry", "excited", "calm", "urgent"]
    
    def _load_mappings(self) -> Dict[str, Any]:
        """Load prosody mappings from file"""
        try:
            if os.path.exists(self.mappings_file):
                with open(self.mappings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Return default mappings
                return self._get_default_mappings()
        except Exception as e:
            print(f"Error loading prosody mappings: {e}")
            return self._get_default_mappings()
    
    def _get_default_mappings(self) -> Dict[str, Any]:
        """Get default prosody mappings"""
        return {
            "neutral": {
                "pitch": "medium",
                "speed": "normal",
                "volume": "medium",
                "emphasis": "balanced"
            },
            "happy": {
                "pitch": "high",
                "speed": "fast",
                "volume": "medium",
                "emphasis": "light"
            },
            "sad": {
                "pitch": "low",
                "speed": "slow",
                "volume": "low",
                "emphasis": "heavy"
            },
            "angry": {
                "pitch": "high",
                "speed": "fast",
                "volume": "high",
                "emphasis": "strong"
            },
            "excited": {
                "pitch": "high",
                "speed": "fast",
                "volume": "high",
                "emphasis": "dynamic"
            },
            "calm": {
                "pitch": "medium",
                "speed": "slow",
                "volume": "low",
                "emphasis": "gentle"
            },
            "urgent": {
                "pitch": "high",
                "speed": "fast",
                "volume": "high",
                "emphasis": "intense"
            }
        }
    
    def get_prosody_for_style(self, style: str, language: str = "en") -> Dict[str, Any]:
        """Get prosody parameters for a specific style and language"""
        # Get base style mapping
        base_mapping = self.prosody_mappings.get(style, self.prosody_mappings["neutral"])
        
        # Apply language-specific adjustments
        language_adjustments = self._get_language_adjustments(language)
        
        # Combine base mapping with language adjustments
        final_mapping = base_mapping.copy()
        for key, value in language_adjustments.items():
            if key in final_mapping:
                final_mapping[key] = value
        
        return final_mapping
    
    def _get_language_adjustments(self, language: str) -> Dict[str, Any]:
        """Get language-specific prosody adjustments"""
        adjustments = {
            "en": {
                "speed": "normal",
                "pitch": "medium"
            },
            "es": {
                "speed": "fast",
                "pitch": "medium"
            },
            "fr": {
                "speed": "slow",
                "pitch": "medium"
            },
            "de": {
                "speed": "normal",
                "pitch": "low"
            },
            "hi": {
                "speed": "normal",
                "pitch": "medium"
            },
            "zh": {
                "speed": "slow",
                "pitch": "medium"
            },
            "ja": {
                "speed": "slow",
                "pitch": "high"
            },
            "pt": {
                "speed": "fast",
                "pitch": "medium"
            }
        }
        
        return adjustments.get(language, adjustments["en"])
    
    def get_available_styles(self) -> List[str]:
        """Get list of available prosody styles"""
        return list(self.prosody_mappings.keys())
    
    def add_style_mapping(self, style_name: str, mapping: Dict[str, Any]) -> bool:
        """Add a new prosody style mapping"""
        try:
            self.prosody_mappings[style_name] = mapping
            self._save_mappings()
            return True
        except Exception as e:
            print(f"Error adding style mapping: {e}")
            return False
    
    def update_style_mapping(self, style_name: str, mapping: Dict[str, Any]) -> bool:
        """Update existing prosody style mapping"""
        if style_name in self.prosody_mappings:
            try:
                self.prosody_mappings[style_name].update(mapping)
                self._save_mappings()
                return True
            except Exception as e:
                print(f"Error updating style mapping: {e}")
                return False
        return False
    
    def remove_style_mapping(self, style_name: str) -> bool:
        """Remove a prosody style mapping"""
        if style_name in self.prosody_mappings and style_name not in self.default_styles:
            try:
                del self.prosody_mappings[style_name]
                self._save_mappings()
                return True
            except Exception as e:
                print(f"Error removing style mapping: {e}")
                return False
        return False
    
    def _save_mappings(self):
        """Save prosody mappings to file"""
        try:
            os.makedirs(os.path.dirname(self.mappings_file), exist_ok=True)
            with open(self.mappings_file, 'w', encoding='utf-8') as f:
                json.dump(self.prosody_mappings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving prosody mappings: {e}")
    
    def get_style_description(self, style_name: str) -> str:
        """Get description of a prosody style"""
        descriptions = {
            "neutral": "Balanced, conversational tone",
            "happy": "Bright, cheerful delivery",
            "sad": "Melancholic, subdued tone",
            "angry": "Intense, forceful delivery",
            "excited": "Energetic, enthusiastic speech",
            "calm": "Relaxed, soothing tone",
            "urgent": "Pressing, hurried delivery"
        }
        return descriptions.get(style_name, "Custom style")
    
    def validate_prosody_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate prosody parameters"""
        valid_parameters = ["pitch", "speed", "volume", "emphasis"]
        valid_values = {
            "pitch": ["low", "medium", "high"],
            "speed": ["slow", "normal", "fast"],
            "volume": ["low", "medium", "high"],
            "emphasis": ["light", "balanced", "heavy", "gentle", "strong", "dynamic", "intense"]
        }
        
        for key, value in parameters.items():
            if key not in valid_parameters:
                return False
            if key in valid_values and value not in valid_values[key]:
                return False
        
        return True

# Global instance
prosody_mapper = ProsodyMapper()

def get_prosody_mapper():
    return prosody_mapper