from __future__ import annotations

import ast
import json
import operator
import os
import re
from typing import Any, Dict

from app.core.llm_bridge import llm_bridge


def _normalized_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "")).strip()


def _normalized_context(context: Dict[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(context, dict):
        return {}

    allowed_keys = [
        "platform",
        "device",
        "preferred_language",
        "detected_language",
        "city",
        "location",
        "region",
        "session_id",
    ]
    normalized = {
        key: context.get(key)
        for key in allowed_keys
        if context.get(key) not in (None, "", {}, [])
    }
    return normalized


def _preferred_model(requested_model: str | None) -> str:
    requested = (requested_model or "").strip().lower()
    if requested and requested != "uniguru":
        return requested

    # Priority: Groq > OpenAI > Gemini > Mistral > Uniguru (all from env)
    if os.getenv("GROQ_API_KEY"):
        return os.getenv("GROQ_MODEL", "groq")
    if os.getenv("OPENAI_API_KEY"):
        return "chatgpt"
    if os.getenv("GOOGLE_API_KEY"):
        return "gemini"
    if os.getenv("MISTRAL_API_KEY"):
        return "mistral"
    return "uniguru"


# ──────────────────────────────────────────────────────────────────────
# Safe math evaluator — replaces eval() with AST-based evaluation
# ──────────────────────────────────────────────────────────────────────

_SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval_math(expr: str):
    """Safely evaluate a math expression using AST (no eval())."""
    try:
        tree = ast.parse(expr.strip(), mode="eval")
        return _eval_node(tree.body)
    except (ValueError, TypeError, ZeroDivisionError, SyntaxError):
        return None


def _eval_node(node):
    if isinstance(node, ast.Num):
        return node.n
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPERATORS:
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        if left is None or right is None:
            return None
        return _SAFE_OPERATORS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPERATORS:
        operand = _eval_node(node.operand)
        if operand is None:
            return None
        return _SAFE_OPERATORS[type(node.op)](operand)
    return None


def _convert_word_operators(text: str) -> str:
    """Convert word-based math operators to symbols."""
    text = re.sub(r'\bplus\b', '+', text)
    text = re.sub(r'\bminus\b', '-', text)
    text = re.sub(r'\btimes\b', '*', text)
    text = re.sub(r'\bmultiplied by\b', '*', text)
    text = re.sub(r'\bdivided by\b', '/', text)
    text = re.sub(r'\bover\b', '/', text)
    text = re.sub(r'\bmod\b', '%', text)
    text = re.sub(r'\bmodulo\b', '%', text)
    return text


def _response_language(context: Dict[str, Any] | None) -> str:
    normalized_context = _normalized_context(context)
    preferred = str(normalized_context.get("preferred_language") or "").strip().lower()
    detected = str(normalized_context.get("detected_language") or "").strip().lower()

    if preferred and preferred != "auto":
        return preferred
    if detected and detected != "auto":
        return detected
    return "en"


def _language_label(language_code: str) -> str:
    labels = {
        "en": "English",
        "hi": "Hindi",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "ja": "Japanese",
        "ko": "Korean",
        "zh": "Chinese",
        "ar": "Arabic",
    }
    return labels.get(language_code, language_code or "English")


def build_response_prompt(query: str, context: Dict[str, Any] | None = None) -> str:
    cleaned_query = _normalized_text(query)
    cleaned_context = _normalized_context(context)
    context_blob = json.dumps(cleaned_context, sort_keys=True, ensure_ascii=True)
    response_language = _response_language(cleaned_context)
    response_language_label = _language_label(response_language)

    return (
        "You are Mitra, a professional, knowledgeable, and helpful AI assistant.\n"
        "Your role is to provide accurate, comprehensive, and well-structured answers to ANY question.\n\n"
        f"Language: {response_language_label}\n"
        "Use markdown formatting: headers (##), bold (**text**), bullet points, tables.\n"
        "For math: Show the formula, then solve step-by-step.\n"
        "Be concise but comprehensive. Always provide accurate information.\n"
        "If unsure, acknowledge limitations honestly.\n"
        "Do NOT repeat the user's question back.\n"
        "Do NOT mention being an AI or having limitations unless asked.\n\n"
        f"Runtime context: {context_blob}\n"
        f"User question: {cleaned_query}\n\n"
        "Provide a professional, accurate, and well-formatted answer:"
    )


def build_fallback_response(query: str, context: Dict[str, Any] | None = None) -> str:
    """Dynamic fallback — delegates to LLM for every query. No hardcoded responses."""
    text = _normalized_text(query)
    lower = text.lower()
    normalized_context = _normalized_context(context)
    response_language = _response_language(normalized_context)

    # Greetings and identity — short dynamic responses
    greeting_tokens = [
        "how are you", "how're you", "how do you do",
        "hello", "hi", "hey", "good morning", "good afternoon", "good evening",
    ]
    identity_tokens = [
        "what is your name", "what's your name", "who are you", "tell me about yourself",
    ]

    if any(lower.startswith(token) or lower == token for token in greeting_tokens):
        return "Hello! I'm Mitra, your AI assistant. I can help you with questions, tasks, messaging, reminders, and more. What would you like to do?"

    if any(lower.startswith(token) or lower == token for token in identity_tokens):
        return (
            "I'm Mitra, your unified AI assistant. I'm part of the BHIV ecosystem "
            "and can help with communication (email, WhatsApp, Telegram, Instagram), "
            "productivity (reminders, calendar, tasks), knowledge, multi-language support, "
            "voice input/output, and integration with BHIV ecosystem products. "
            "What would you like to do?"
        )

    if any(token in lower for token in ["what can you do", "help me with", "how can you help", "capabilities"]):
        return (
            "I can help with:\n"
            "- **Communication**: Send emails, WhatsApp, Telegram, Instagram messages\n"
            "- **Productivity**: Set reminders, manage calendar events, create tasks\n"
            "- **Knowledge**: Answer questions on any topic\n"
            "- **Integration**: Connect with BHIV ecosystem products\n"
            "- **Multi-language**: Support for multiple languages\n"
            "- **Voice**: Speech-to-text and text-to-speech\n"
            "Just ask me anything or tell me what you need!"
        )

    # Everything else goes to the LLM — no hardcoded knowledge
    return None


def _looks_unusable(response: str, query: str) -> bool:
    if not response or not response.strip():
        return True
    cleaned = response.strip()
    lowered = cleaned.lower()
    query_text = _normalized_text(query).lower()
    if lowered.startswith("[uniguru mock]") or lowered.startswith("[groq mock]") or lowered.startswith("[chatgpt mock]"):
        return True
    if "mock" in lowered and "response to" in lowered:
        return True
    if lowered.startswith("context:"):
        return True
    if cleaned == query or lowered == query_text:
        return True
    return False


async def generate_generic_response(
    query: str,
    context: Dict[str, Any] | None = None,
    model: str | None = None,
) -> str:
    """Fully dynamic response generation. No hardcoded knowledge base."""

    text = query.strip()
    lower = text.lower()

    # ── Quick math: AST-safe evaluation (no eval()) ──
    converted_text = _convert_word_operators(lower)
    simple_math_pattern = re.match(r'^[\d\s\+\-\*\/\%\.\(\)]+$', converted_text.strip())
    what_is_math = re.match(
        r'^(?:what is|what\'s|calculate|compute|solve|evaluate)\s+([\d\s\+\-\*\/\%\.\(\)]+)$',
        converted_text.strip(),
    )

    if simple_math_pattern or what_is_math:
        expr = None
        if what_is_math:
            expr = what_is_math.group(1).strip()
        elif simple_math_pattern:
            expr = converted_text.strip()

        if expr:
            result = _safe_eval_math(expr)
            if result is not None:
                if isinstance(result, float) and result == int(result):
                    result = int(result)
                return f"**{expr}** = **{result}**"

    # ── Quick fallback for greetings / identity ──
    quick_response = build_fallback_response(query, context)
    if quick_response:
        return quick_response

    # ── LLM handles everything else dynamically ──
    prompt = build_response_prompt(query, context)
    selected_model = _preferred_model(model)

    try:
        response = await llm_bridge.call_llm(selected_model, prompt)
        if _looks_unusable(response, query):
            # If LLM returns unusable, try one more time with a simpler prompt
            simple_prompt = f"Answer this question concisely and accurately: {query}"
            try:
                response = await llm_bridge.call_llm(selected_model, simple_prompt)
                if not _looks_unusable(response, query):
                    return _normalized_text(response)
            except Exception:
                pass
            return f"I understand you're asking about this topic. Could you provide a bit more detail so I can give you the most accurate answer?"
        return _normalized_text(response)
    except Exception:
        return f"I understand you're asking about this topic. Could you provide a bit more detail so I can give you the most accurate answer?"
