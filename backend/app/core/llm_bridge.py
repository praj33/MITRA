import os
import asyncio
import hashlib
import logging
import time
from collections import OrderedDict
from typing import Dict, List, Optional, Any

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None
try:
    from groq import AsyncGroq
except ImportError:
    AsyncGroq = None
try:
    import google.generativeai as genai
except ImportError:
    genai = None
try:
    from mistralai.client import MistralClient
except ImportError:
    MistralClient = None

import httpx

logger = logging.getLogger(__name__)

# Bounded Enterprise LRU Cache to prevent memory leaks
MAX_CACHE_SIZE = 500
CACHE_TTL_SECONDS = 3600  # 1 hour


class LLMBridge:
    def __init__(self):
        openai_key = os.getenv("OPENAI_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY")
        self.groq_model = (
            os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip()
            or "llama-3.1-8b-instant"
        )
        self.openai_client = AsyncOpenAI(api_key=openai_key) if AsyncOpenAI and openai_key else None
        self.groq_client = AsyncGroq(api_key=groq_key) if AsyncGroq and groq_key else None
        self.google_key = os.getenv("GOOGLE_API_KEY")
        mistral_key = os.getenv("MISTRAL_API_KEY")
        self.mistral_client = (
            MistralClient(api_key=mistral_key) if MistralClient and mistral_key else None
        )
        # UniGuru live endpoint
        self.uniguru_url = os.getenv("UNIGURU_URL", "https://uniguru-v2.onrender.com/new_query")
        self.uniguru_key = os.getenv("UNIGURU_API_KEY", "")

        if genai and self.google_key:
            genai.configure(api_key=self.google_key)

        # Bounded LRU Cache: key -> (timestamp, output)
        self._cache: OrderedDict[str, tuple[float, str]] = OrderedDict()
        
        # Shared persistent HTTP client pool for low-latency calls
        self._http_client: Optional[httpx.AsyncClient] = None

    def _get_http_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(15.0, connect=5.0),
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
            )
        return self._http_client

    def _cache_get(self, key: str) -> Optional[str]:
        if key in self._cache:
            created_at, val = self._cache[key]
            if time.time() - created_at < CACHE_TTL_SECONDS:
                self._cache.move_to_end(key)
                return val
            else:
                del self._cache[key]
        return None

    def _cache_set(self, key: str, val: str) -> None:
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = (time.time(), val)
        if len(self._cache) > MAX_CACHE_SIZE:
            self._cache.popitem(last=False)  # Evict oldest entry

    # ── backward-compatible single-prompt call ────────────────────
    async def call_llm(self, model: str, prompt: str) -> str:
        if not prompt or not isinstance(prompt, str):
            raise ValueError("Prompt must be a non-empty string")
        return await self.call_llm_with_messages(
            model, [{"role": "user", "content": prompt.strip()}]
        )

    # ── full chat-history call (companion primary path) ───────────
    async def call_llm_with_messages(
        self,
        model: str,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 800,
    ) -> str:
        if not messages:
            raise ValueError("messages must be a non-empty list")
        cache_key = hashlib.sha256(
            f"{model}:{messages}:{temperature}".encode()
        ).hexdigest()
        
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        output = await self._dispatch(model, messages, temperature, max_tokens)
        if output:
            self._cache_set(cache_key, output)
        return output

    async def _dispatch(self, model: str, messages: list, temperature: float, max_tokens: int) -> str:
        try:
            if model in ("groq", "llama"):
                return await asyncio.wait_for(self._call_groq(messages, temperature, max_tokens), timeout=12.0)
            if model in ("chatgpt", "openai", "gpt"):
                return await asyncio.wait_for(self._call_openai(messages, temperature, max_tokens), timeout=12.0)
            if model == "gemini":
                return await asyncio.wait_for(self._call_gemini(messages, temperature), timeout=12.0)
            if model == "mistral":
                return await asyncio.wait_for(self._call_mistral(messages, temperature), timeout=12.0)
            if model == "uniguru":
                return await asyncio.wait_for(self._call_uniguru(messages), timeout=15.0)
            raise ValueError(f"Unsupported model: {model}")
        except Exception as exc:
            logger.warning("LLM dispatch failed model=%s: %s — trying fallback chain", model, exc)
            return await self._fallback_chain(messages, temperature, max_tokens, failed=model)

    async def _fallback_chain(
        self, messages: list, temperature: float, max_tokens: int, failed: str
    ) -> str:
        # UniGuru is the canonical intelligence backend — try it FIRST.
        for provider in ("uniguru", "groq", "openai", "gemini"):
            if provider == failed:
                continue
            try:
                if provider == "uniguru":
                    return await asyncio.wait_for(self._call_uniguru(messages), timeout=12.0)
                if provider == "groq":
                    return await asyncio.wait_for(self._call_groq(messages, temperature, max_tokens), timeout=12.0)
                if provider == "openai":
                    return await asyncio.wait_for(self._call_openai(messages, temperature, max_tokens), timeout=12.0)
                if provider == "gemini":
                    return await asyncio.wait_for(self._call_gemini(messages, temperature), timeout=12.0)
            except Exception as exc:
                logger.warning("Fallback provider=%s failed: %s", provider, exc)
        # Final rule-based fallback — always gives a useful reply
        return await self._rule_based_response(messages)

    # ── providers ─────────────────────────────────────────────────
    async def _call_groq(self, messages: list, temperature: float, max_tokens: int) -> str:
        if not self.groq_client:
            raise ValueError("GROQ_API_KEY not configured")
        resp = await self.groq_client.chat.completions.create(
            model=self.groq_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content or ""

    async def _call_openai(self, messages: list, temperature: float, max_tokens: int) -> str:
        if not self.openai_client:
            raise ValueError("OPENAI_API_KEY not configured")
        resp = await self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content or ""

    async def _call_gemini(self, messages: list, temperature: float) -> str:
        if not genai:
            raise ImportError("google-generativeai not installed")
        prompt = "\n".join(
            f"{m['role'].upper()}: {m['content']}"
            for m in messages
            if m["role"] != "system"
        )
        gem = genai.GenerativeModel("gemini-pro")
        result = await asyncio.to_thread(
            gem.generate_content, prompt,
            generation_config={"temperature": temperature},
        )
        return result.text or ""

    async def _call_mistral(self, messages: list, temperature: float) -> str:
        if not self.mistral_client:
            raise ImportError("mistralai not installed")
        result = await asyncio.to_thread(
            self.mistral_client.chat,
            model="mistral-medium",
            messages=messages,
            temperature=temperature,
        )
        return result.choices[0].message["content"] or ""

    async def _call_uniguru(self, messages: list) -> str:
        """Live UniGuru v2 API — POST /new_query with full context preservation."""
        client = self._get_http_client()
        
        # Preserve full context (System prompt, active DOM map, and conversation turns)
        formatted_context_parts = []
        for m in messages:
            role = m.get("role", "user").upper()
            content = m.get("content", "")
            formatted_context_parts.append(f"[{role}]: {content}")
        
        full_context_query = "\n".join(formatted_context_parts)
        
        headers = {"Content-Type": "application/json"}
        if self.uniguru_key:
            headers["X-API-Key"] = self.uniguru_key
            headers["Authorization"] = f"Bearer {self.uniguru_key}"

        resp = await client.post(
            self.uniguru_url,
            json={"query": full_context_query},
            headers=headers,
        )
        if resp.status_code == 200:
            data = resp.json()
            return (
                data.get("answer")
                or data.get("response")
                or data.get("result")
                or data.get("output")
                or str(data)
            )
        logger.warning("UniGuru HTTP %s: %s", resp.status_code, resp.text[:200])
        raise ValueError(f"UniGuru HTTP {resp.status_code}")

    async def _rule_based_response(self, messages: list) -> str:
        """Smart rule-based fallback — always returns something useful."""
        import re
        user_msg = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
        ).lower().strip()

        # Greetings
        if re.search(r"\b(hi|hello|hey|good morning|good evening|good afternoon|namaste)\b", user_msg):
            return "Hey there! I'm Mitra, your AI companion. I'm here and ready to help. What's on your mind?"

        # How are you
        if re.search(r"how are (you|u)|how('s| is) it going|what's up", user_msg):
            return "I'm doing great, thank you for asking! I'm fully focused and ready to assist you. What can I help you with today?"

        # Capital city questions
        capitals = {
            "india": "New Delhi", "france": "Paris", "usa": "Washington D.C.",
            "united states": "Washington D.C.", "uk": "London", "japan": "Tokyo",
            "china": "Beijing", "russia": "Moscow", "germany": "Berlin",
            "australia": "Canberra", "canada": "Ottawa", "brazil": "Brasília",
        }
        if "capital" in user_msg:
            for country, capital in capitals.items():
                if country in user_msg:
                    return f"The capital of {country.title()} is **{capital}**."

        # Math
        math_match = re.search(r"(\d+)\s*([+\-*/])\s*(\d+)", user_msg)
        if math_match:
            try:
                a, op, b = int(math_match.group(1)), math_match.group(2), int(math_match.group(3))
                result = eval(f"{a}{op}{b}")  # safe: only digits and basic ops
                return f"That's **{result}**."
            except Exception:
                pass

        # Time/date (only trigger on direct time/date queries, not scheduling requests)
        planning_keywords = ("plan", "schedule", "meeting", "agenda", "organize", "routine", "todo", "task", "reminder", "event")
        is_planning = any(k in user_msg for k in planning_keywords)
        if not is_planning and re.search(r"\b(what time|current time|what is the time|what date|what day is it|current date)\b", user_msg):
            from datetime import datetime, timezone, timedelta
            ist_tz = timezone(timedelta(hours=5, minutes=30))
            now = datetime.now(ist_tz)
            return f"It's currently **{now.strftime('%A, %d %B %Y')}** and the time is **{now.strftime('%I:%M %p IST')}**."

        # Help
        if re.search(r"\b(help|what can you do|capabilities|features)\b", user_msg):
            return (
                "I can help you with:\n\n"
                "• 📧 **Email** — draft, send, and read emails\n"
                "• 📅 **Calendar** — schedule and manage events\n"
                "• ✅ **Tasks** — create and track to-dos\n"
                "• 🔔 **Reminders** — set smart reminders\n"
                "• 📚 **Knowledge** — answer questions and explain concepts\n"
                "• 💬 **WhatsApp** — send messages to contacts\n\n"
                "What would you like to do?"
            )

        # Live web search fallback for factual queries (e.g. radius of earth, news, facts)
        try:
            from app.tools.search_tool import SearchTool
            search_tool = SearchTool()
            search_res = await search_tool.run(user_msg)
            if search_res and "Real-time search completed for:" not in search_res and "Live market feeds active" not in search_res:
                cleaned = search_res.replace("Web Information Intelligence Summary:", "").strip()
                lines = [l.strip() for l in cleaned.split("\n") if l.strip()]
                bullets = []
                for line in lines:
                    bullet_text = line[2:].strip() if line.startswith("- ") else line
                    bullets.append(f"• {bullet_text}")
                formatted_summary = "\n\n".join(bullets[:3]) if bullets else cleaned
                return f"Here is what I found for your query:\n\n{formatted_summary}"
        except Exception as e:
            logger.warning(f"Rule-based live search fallback failed: {e}")

        # Generic thoughtful reply
        return (
            "I'm listening and working on fetching the best information for you. "
            "Could you rephrase your question or ask about tasks, calendar, reminders, or market trends?"
        )


# Singleton
llm_bridge = LLMBridge()
