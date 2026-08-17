"""
IntentFlow Module — Dynamic NLU Intent Classification Engine
Uses LLM for classification with regex fallback for offline mode.
"""

import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import dateutil.parser as parser


class IntentFlow:
    def __init__(self):
        # Regex patterns used only as offline/fallback when LLM is unavailable
        self._fallback_patterns = {
            'summarize': ['summarize', 'summary', 'summarise', 'tl;dr', 'key points', 'brief'],
            'task': ['create a task', 'add a task', 'make a task', 'new task for', 'assign task to', 'create todo', 'add to my todo'],
            'search': ['search for', 'find me', 'lookup', 'research about', 'look up'],
            'email': ['send email', 'send an email', 'email to', 'compose email', 'send mail to'],
            'calendar': ['add to calendar', 'schedule meeting', 'create event', 'set appointment', 'add meeting'],
            'reminder': ['set reminder', 'remind me to', 'create reminder', 'add reminder', 'alert me to'],
            'telegram': ['send telegram', 'telegram message to'],
            'instagram': ['send instagram', 'instagram message to', 'send dm on instagram'],
            'ems': ['create ems task', 'assign ems task', 'ems assignment'],
            'device': ['send command to device', 'control device', 'device command'],
            'general': [],
        }

        self.entity_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'url': r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            'date': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            'time': r'\b\d{1,2}:\d{2}(?:\s?[APMapm]{2})?\b',
            'duration': r'\b\d+\s*(?:hour|minute|day|week|month)s?\b',
        }

        self._llm_bridge = None

    def _get_llm_bridge(self):
        """Lazy-init LLM bridge to avoid circular imports."""
        if self._llm_bridge is None:
            try:
                from app.core.llm_bridge import llm_bridge
                self._llm_bridge = llm_bridge
            except Exception:
                self._llm_bridge = False
        return self._llm_bridge if self._llm_bridge is not False else None

    def _fallback_classify(self, text: str) -> str:
        """Regex-only fallback classification when LLM is unavailable."""
        text_lower = text.lower()
        for intent, keywords in self._fallback_patterns.items():
            if intent == 'general':
                continue
            for keyword in keywords:
                if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                    return intent
        return 'general'

    async def _llm_classify(self, text: str) -> Optional[str]:
        """Use LLM for dynamic intent classification."""
        llm = self._get_llm_bridge()
        if not llm:
            return None

        prompt = (
            "Classify the user message into ONE of these intents. Return ONLY the intent label:\n"
            "Intents: summarize, task, search, email, calendar, reminder, telegram, instagram, ems, device, general\n\n"
            "Examples:\n"
            "- 'Send an email to john@example.com' -> email\n"
            "- 'Remind me to call mom at 5pm' -> reminder\n"
            "- 'Create a task for the team' -> task\n"
            "- 'What is quantum computing?' -> general\n"
            "- 'Summarize this article' -> summarize\n"
            "- 'Search for Python tutorials' -> search\n"
            "- 'Schedule a meeting tomorrow' -> calendar\n"
            "- 'Send telegram message to @user' -> telegram\n"
            "- 'Send DM on Instagram to @friend' -> instagram\n\n"
            f"User message: {text}\n\n"
            "Intent:"
        )

        try:
            response = await llm.call_llm("uniguru", prompt)
            intent = response.strip().lower()
            valid_intents = set(self._fallback_patterns.keys()) - {'general'}
            if intent in valid_intents:
                return intent
            if intent == 'general' or 'general' in intent:
                return 'general'
            return None
        except Exception:
            return None

    def classify_intent(self, text: str) -> str:
        """Classify using regex fallback (synchronous path)."""
        return self._fallback_classify(text)

    async def classify_intent_async(self, text: str) -> str:
        """Classify using LLM (async) with regex fallback."""
        llm_result = await self._llm_classify(text)
        if llm_result:
            return llm_result
        return self._fallback_classify(text)

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities from text using regex patterns."""
        entities = {}
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                entities[entity_type] = list(set(matches))
        return entities

    def resolve_dates_times(self, text: str) -> Dict[str, Any]:
        """Resolve date/time references to structured format."""
        resolved = {}
        try:
            relative_patterns = {
                'today': datetime.now(),
                'tomorrow': datetime.now() + timedelta(days=1),
                'yesterday': datetime.now() - timedelta(days=1),
                'next week': datetime.now() + timedelta(weeks=1),
                'next month': datetime.now() + timedelta(days=30),
            }
            text_lower = text.lower()
            for rel, date_obj in relative_patterns.items():
                if rel in text_lower:
                    resolved['relative_date'] = rel
                    resolved['resolved_date'] = date_obj.isoformat()
                    break

            date_matches = re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', text)
            if date_matches:
                try:
                    parsed_date = parser.parse(date_matches[0])
                    resolved['absolute_date'] = date_matches[0]
                    resolved['parsed_date'] = parsed_date.isoformat()
                except Exception:
                    pass
        except Exception as e:
            resolved['date_error'] = str(e)

        time_matches = re.findall(r'\b\d{1,2}:\d{2}(?:\s?[APMapm]{2})?\b', text)
        if time_matches:
            resolved['time'] = time_matches[0]
        return resolved

    def extract_context(self, text: str) -> Dict[str, Any]:
        """Extract smart context from text."""
        context = {'urgency': 'normal', 'priority': 'medium', 'sentiment': 'neutral'}
        text_lower = text.lower()

        urgent_keywords = ['urgent', 'asap', 'immediately', 'emergency', 'critical']
        if any(word in text_lower for word in urgent_keywords):
            context['urgency'] = 'high'

        high_priority = ['important', 'priority', 'critical', 'deadline']
        if any(word in text_lower for word in high_priority):
            context['priority'] = 'high'

        positive = ['good', 'great', 'excellent', 'happy', 'thanks']
        negative = ['bad', 'terrible', 'angry', 'frustrated', 'problem']
        if any(word in text_lower for word in positive):
            context['sentiment'] = 'positive'
        elif any(word in text_lower for word in negative):
            context['sentiment'] = 'negative'

        return context

    async def process_text_async(self, text: str) -> Dict[str, Any]:
        """Process text through IntentFlow with LLM-enhanced classification."""
        intent_label = await self.classify_intent_async(text)
        entities = self.extract_entities(text)
        dates_times = self.resolve_dates_times(text)
        context = self.extract_context(text)

        return {
            "intent": intent_label,
            "entities": entities,
            "dates_times": dates_times,
            "context": context,
            "confidence": 0.9,
            "timestamp": datetime.now().isoformat(),
            "version": "intentflow_v2_dynamic",
            "original_text": text,
        }

    def process_text(self, text: str) -> Dict[str, Any]:
        """Process text synchronously using regex fallback."""
        intent_label = self.classify_intent(text)
        entities = self.extract_entities(text)
        dates_times = self.resolve_dates_times(text)
        context = self.extract_context(text)

        return {
            "intent": intent_label,
            "entities": entities,
            "dates_times": dates_times,
            "context": context,
            "confidence": 0.8,
            "timestamp": datetime.now().isoformat(),
            "version": "intentflow_v2_fallback",
            "original_text": text,
        }


# Global instance
intent_flow = IntentFlow()