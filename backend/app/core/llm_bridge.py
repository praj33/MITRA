import os
import asyncio
import hashlib
import logging
import re
from collections import OrderedDict
from typing import Dict, List, Optional

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


class LocalKnowledgeBase:
    """
    Dynamic knowledge base — uses cached LLM responses.
    No hardcoded topics. All knowledge comes from LLM at runtime.
    """

    def __init__(self):
        self._cache: OrderedDict[str, str] = OrderedDict()
        self._max_cache_size = int(os.getenv("KB_CACHE_MAX_SIZE", "200"))
        self._llm_client = None

    def _get_llm(self):
        """Lazy-init — try Groq first, then any available provider."""
        if self._llm_client is not None:
            return self._llm_client

        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key and AsyncGroq:
            try:
                self._llm_client = ("groq", AsyncGroq(api_key=groq_key), os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"))
                return self._llm_client
            except Exception:
                pass

        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and AsyncOpenAI:
            try:
                self._llm_client = ("openai", AsyncOpenAI(api_key=openai_key), "gpt-3.5-turbo")
                return self._llm_client
            except Exception:
                pass

        self._llm_client = False
        return None

    async def find_response(self, query: str) -> Optional[str]:
        """Find a response dynamically using LLM with caching."""
        cache_key = hashlib.sha256(query.lower().strip().encode()).hexdigest()

        if cache_key in self._cache:
            self._cache.move_to_end(cache_key)
            return self._cache[cache_key]

        llm = self._get_llm()
        if not llm:
            return None

        provider_name, client, model = llm

        prompt = (
            f"You are Mitra, a helpful AI assistant. Answer this question concisely and accurately:\n\n"
            f"{query}\n\n"
            f"Provide a clear, helpful answer:"
        )

        try:
            if provider_name == "groq":
                response = await client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=500,
                )
                output = response.choices[0].message.content
            elif provider_name == "openai":
                response = await client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=500,
                )
                output = response.choices[0].message.content
            else:
                return None

            if output and output.strip():
                self._cache[cache_key] = output
                if len(self._cache) > self._max_cache_size:
                    self._cache.popitem(last=False)
                return output

        except Exception as e:
            logger.warning(f"Knowledge base LLM call failed: {e}")

        return None


# Global knowledge base instance
knowledge_base = LocalKnowledgeBase()


class LLMBridge:
    # Bounded LRU cache to prevent memory leaks
    MAX_CACHE_SIZE = int(os.getenv("LLM_CACHE_MAX_SIZE", "500"))

    def __init__(self):
        openai_key = os.getenv("OPENAI_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY")
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip() or "llama-3.1-8b-instant"
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo").strip() or "gpt-3.5-turbo"
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-pro").strip() or "gemini-pro"
        self.mistral_model = os.getenv("MISTRAL_MODEL", "mistral-medium").strip() or "mistral-medium"

        self.openai_client = AsyncOpenAI(api_key=openai_key) if AsyncOpenAI and openai_key else None
        self.groq_client = AsyncGroq(api_key=groq_key) if AsyncGroq and groq_key else None
        self.google_key = os.getenv("GOOGLE_API_KEY")
        mistral_key = os.getenv("MISTRAL_API_KEY")
        self.mistral_client = MistralClient(api_key=mistral_key) if MistralClient and mistral_key else None

        if genai and self.google_key:
            genai.configure(api_key=self.google_key)

        # Bounded LRU cache (OrderedDict)
        self.cache: OrderedDict[str, str] = OrderedDict()

    async def call_llm(self, model: str, prompt: str) -> str:
        if not prompt or not isinstance(prompt, str):
            raise ValueError("Prompt must be a non-empty string")

        prompt = prompt.strip()
        key = hashlib.sha256(f"{model}:{prompt}".encode()).hexdigest()

        if key in self.cache:
            return self.cache[key]

        try:
            # ----- OPENAI -----
            if model == "chatgpt":
                if not self.openai_client:
                    if AsyncOpenAI is None:
                        raise ImportError("openai package is not installed")
                    raise ValueError("OPENAI_API_KEY is not configured")
                response = await self.openai_client.chat.completions.create(
                    model=self.openai_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                )
                output = response.choices[0].message.content

            # ----- GROQ -----
            elif model == "groq":
                if not self.groq_client:
                    if AsyncGroq is None:
                        raise ImportError("groq package is not installed")
                    raise ValueError("GROQ_API_KEY is not configured")
                response = await self.groq_client.chat.completions.create(
                    model=self.groq_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                )
                output = response.choices[0].message.content

            # ----- GEMINI -----
            elif model == "gemini":
                if not genai:
                    raise ImportError("google-generativeai not installed")
                gemini_model = genai.GenerativeModel(self.gemini_model)
                result = await asyncio.to_thread(
                    gemini_model.generate_content,
                    prompt,
                    generation_config={"temperature": 0},
                )
                output = result.text

            # ----- MISTRAL -----
            elif model == "mistral":
                if not self.mistral_client:
                    raise ImportError("mistralai not installed")
                result = await asyncio.to_thread(
                    self.mistral_client.chat,
                    model=self.mistral_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                )
                output = result.choices[0].message["content"]

            # ----- UNIGURU -----
            elif model == "uniguru":
                # Dynamic knowledge base — delegates to available LLM provider
                user_query_match = re.search(r"User (?:request|question):\s*(.+?)(?:\n|$)", prompt)
                if user_query_match:
                    user_query = user_query_match.group(1).strip()
                else:
                    lines = prompt.strip().split("\n")
                    user_query = lines[-1] if lines else prompt[:200]

                cache_key = hashlib.sha256(f"uniguru:{user_query}".encode()).hexdigest()
                if cache_key in self.cache:
                    output = self.cache[cache_key]
                else:
                    kb_response = await knowledge_base.find_response(user_query)
                    if kb_response:
                        output = kb_response
                    else:
                        output = (
                            f"I can help with that! While I don't have real-time internet access, "
                            f"I can provide information based on my knowledge.\n\n"
                            f"Could you be more specific about what aspect you'd like me to explain?"
                        )

            else:
                raise ValueError(f"Unsupported model: {model}")

        except Exception as e:
            logger.warning("LLM fallback triggered for model %s: %s", model, e)
            output = f"I'm having trouble connecting to my knowledge sources right now. Could you try rephrasing your question?"

        # Cache with LRU eviction
        # Don't cache uniguru responses to ensure fresh knowledge base responses
        if model != "uniguru":
            self.cache[key] = output
            if len(self.cache) > self.MAX_CACHE_SIZE:
                self.cache.popitem(last=False)  # Remove oldest entry

        return output


llm_bridge = LLMBridge()
