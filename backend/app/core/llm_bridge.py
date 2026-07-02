import os
import asyncio
import hashlib
import logging

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

logger = logging.getLogger(__name__)


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
        self.uniguru_key = os.getenv("UNIGURU_API_KEY", "uniguru_secret_123")

        if genai and self.google_key:
            genai.configure(api_key=self.google_key)

        self.cache = {}

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
        if cache_key in self.cache:
            return self.cache[cache_key]
        output = await self._dispatch(model, messages, temperature, max_tokens)
        self.cache[cache_key] = output
        return output

    async def _dispatch(self, model: str, messages: list, temperature: float, max_tokens: int) -> str:
        try:
            if model in ("groq", "llama"):
                return await self._call_groq(messages, temperature, max_tokens)
            if model in ("chatgpt", "openai", "gpt"):
                return await self._call_openai(messages, temperature, max_tokens)
            if model == "gemini":
                return await self._call_gemini(messages, temperature)
            if model == "mistral":
                return await self._call_mistral(messages, temperature)
            if model == "uniguru":
                return await self._call_uniguru(messages)
            raise ValueError(f"Unsupported model: {model}")
        except Exception as exc:
            logger.warning("LLM dispatch failed model=%s: %s — trying fallback chain", model, exc)
            return await self._fallback_chain(messages, temperature, max_tokens, failed=model)

    async def _fallback_chain(
        self, messages: list, temperature: float, max_tokens: int, failed: str
    ) -> str:
        # Try all available providers in order (excluding the one that already failed)
        for provider in ("groq", "openai", "gemini", "uniguru"):
            if provider == failed:
                continue
            try:
                if provider == "groq":
                    return await self._call_groq(messages, temperature, max_tokens)
                if provider == "openai":
                    return await self._call_openai(messages, temperature, max_tokens)
                if provider == "gemini":
                    return await self._call_gemini(messages, temperature)
                if provider == "uniguru":
                    return await self._call_uniguru(messages)
            except Exception as exc:
                logger.warning("Fallback provider=%s failed: %s", provider, exc)
        # Final rule-based fallback — always gives a useful reply
        return self._rule_based_response(messages)

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
        """Live UniGuru v2 API — POST /new_query with X-API-Key."""
        import httpx
        query = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
        )
        if not query:
            return "Please ask a question."
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                self.uniguru_url,
                json={"query": query},
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": self.uniguru_key,
                    "Authorization": f"Bearer {self.uniguru_key}",
                },
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

    def _rule_based_response(self, messages: list) -> str:
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

        # Time/date
        if re.search(r"\b(time|date|today|what day|what time)\b", user_msg):
            from datetime import datetime
            now = datetime.now()
            return f"It's currently **{now.strftime('%A, %d %B %Y')}** and the time is **{now.strftime('%I:%M %p')}**."

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

        # Generic thoughtful reply
        return (
            "I understand you're asking about that. I'm working on getting you a full answer "
            "— my knowledge service is warming up. Could you ask again in just a moment, "
            "or try rephrasing? I'm here and listening."
        )


llm_bridge = LLMBridge()
