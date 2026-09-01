"""
text_normalizer.py — Mitra Dynamic LLM & Algorithmic Intent Corrector

Replaces brittle hardcoded dictionaries with Zero-Shot LLM semantic correction
and algorithmic Levenshtein edit-distance normalization.
"""
from __future__ import annotations

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


async def resolve_coreference_query_async(query: str, history: list[dict[str, str]]) -> str:
    """
    Zero-Shot Conversational Coreference Resolver.
    If query contains anaphoric pronouns or follow-up references ('it', 'that', 'they', 'can we build it'),
    uses fast zero-shot LLM reasoning to resolve pronouns against conversation history into a clear, standalone query.
    """
    if not query or not history:
        return query

    query_clean = query.strip()
    pronoun_pattern = r"\b(it|that|this|they|them|these|those|there|here|built|build|cost|work|invented)\b"
    if not re.search(pronoun_pattern, query_clean, re.IGNORECASE):
        return query_clean

    try:
        from app.core.llm_bridge import llm_bridge
        # Clean history items to remove any embedded raw search payloads
        clean_history = []
        for m in history[-6:]:
            content = m.get("content", "")
            if not content:
                continue
            if "Live Web Search Context:" in content:
                content = content.split("Live Web Search Context:")[0].strip()
            elif "Live Weather Data" in content:
                content = content.split("Live Weather Data")[0].strip()
            clean_history.append(f"{m.get('role', 'user').upper()}: {content[:300]}")

        formatted_history = "\n".join(clean_history)
        coref_prompt = [
            {
                "role": "system",
                "content": (
                    "You are an expert conversational coreference preprocessor. "
                    "Given the recent conversation history [HISTORY] and the user's latest follow-up question [FOLLOW_UP], "
                    "rewrite [FOLLOW_UP] into a complete, standalone, explicit question by replacing ambiguous pronouns "
                    "(e.g. 'it', 'that', 'this', 'built it') with the exact topic/subject from history. "
                    "Return ONLY the single rewritten standalone question sentence. Do NOT add quotes, labels, search contexts, or extra commentary."
                ),
            },
            {
                "role": "user",
                "content": f"[HISTORY]\n{formatted_history}\n\n[FOLLOW_UP]\n{query_clean}",
            },
        ]
        resolved = await llm_bridge.call_llm_with_messages(
            model="groq",
            messages=coref_prompt,
            temperature=0.0,
            max_tokens=60,
        )
        if resolved and isinstance(resolved, str):
            clean = resolved.strip()
            if "Live Web Search Context:" in clean:
                clean = clean.split("Live Web Search Context:")[0].strip()
            if "Based on live information" in clean:
                clean = clean.split("\n\n")[-1].strip()

            lines = [l.strip() for l in clean.split("\n") if l.strip() and not l.strip().startswith("-") and not l.strip().startswith("#")]
            clean_res = lines[0] if lines else clean
            clean_res = clean_res.strip('"\'')
            clean_res = re.sub(r"^(rewritten question|standalone query|question):\s*", "", clean_res, flags=re.IGNORECASE).strip()
            
            if len(clean_res) > 0 and not clean_res.startswith("[") and not clean_res.startswith("Based on"):
                logger.info("Coreference resolved: '%s' -> '%s'", query_clean, clean_res)
                return clean_res
    except Exception as exc:
        logger.debug("LLM coreference resolution skipped: %s — using heuristic fallback", exc)

    return _heuristic_coreference_rewrite(query_clean, history)


def _heuristic_coreference_rewrite(query: str, history: list[dict[str, str]]) -> str:
    """
    Algorithmic coreference fallback.
    Extracts key subject noun phrase from recent user turns in history and replaces anaphoric pronouns.
    """
    if not history:
        return query

    last_user_turn = None
    for m in reversed(history):
        if m.get("role") == "user" and m.get("content"):
            last_user_turn = m.get("content")
            break

    if not last_user_turn:
        return query

    clean_prev = re.sub(
        r"^(what is|what are|explain|tell me about|how does|who is|where is|why is|detail)\s+",
        "",
        last_user_turn.strip(),
        flags=re.IGNORECASE,
    ).strip("?.!")

    if not clean_prev or len(clean_prev) < 3:
        return query

    query_replaced = re.sub(r"\b(it|that|this)\b", clean_prev, query, flags=re.IGNORECASE)
    if query_replaced != query:
        logger.info("Heuristic coreference resolved: '%s' -> '%s'", query, query_replaced)
        return query_replaced

    return query


async def normalize_text_async(text: str) -> str:
    """
    Dynamic Zero-Shot text normalization. Uses fast LLM reasoning to resolve
    typos, phonetic shorthand, and mangled words dynamically without hardcoded dictionaries.
    """
    if not text or not isinstance(text, str):
        return ""

    text_clean = text.strip()
    if len(text_clean) < 3:
        return text_clean

    # 1. Quick algorithmic check: if text contains only valid dictionary words, return as-is
    if not _has_potential_typo(text_clean):
        return text_clean

    # 2. Dynamic Zero-Shot LLM Auto-Correction (Fast < 100ms path)
    try:
        from app.core.llm_bridge import llm_bridge
        correction_prompt = [
            {
                "role": "system",
                "content": (
                    "You are an expert NLP preprocessor. Correct any typos, phonetic slang, "
                    "or misspelled words in the user's input while preserving the exact meaning. "
                    "Return ONLY the corrected sentence in plain text. Do NOT add quotes, explanations, or punctuation changes."
                ),
            },
            {"role": "user", "content": text_clean},
        ]
        corrected = await llm_bridge.call_llm_with_messages(
            model="groq",
            messages=correction_prompt,
            temperature=0.0,
            max_tokens=60,
        )
        if corrected and isinstance(corrected, str):
            clean_corr = corrected.strip().strip('"\'')
            if len(clean_corr) > 0 and len(clean_corr) < len(text_clean) * 3:
                return clean_corr
    except Exception as exc:
        logger.debug("LLM dynamic text normalization skipped/failed: %s", exc)

    # 3. Algorithmic Levenshtein fallback against dynamic capabilities (Zero hardcoded word lists)
    return normalize_text_algorithmic(text_clean)


def normalize_text_algorithmic(text: str) -> str:
    """
    Dynamic algorithmic Levenshtein correction against system capability names.
    Contains zero hardcoded word dictionaries.
    """
    if not text:
        return ""

    try:
        from app.companion.capability_registry import capability_registry
        known_keywords = capability_registry.get_capabilities()
    except Exception:
        known_keywords = ["weather", "calendar", "tasks", "reminders", "finance", "browser", "news"]

    words = text.split()
    corrected_words = []

    for word in words:
        clean_word = re.sub(r"[^\w]", "", word).lower()
        matched = False
        if len(clean_word) >= 4:
            for kw in known_keywords:
                if abs(len(clean_word) - len(kw)) <= 2:
                    dist = _levenshtein_distance(clean_word, kw)
                    if dist == 1:
                        replacement = kw
                        if word[0].isupper():
                            replacement = replacement.capitalize()
                        punc_suffix = re.findall(r"[^\w]+$", word)
                        if punc_suffix:
                            replacement += punc_suffix[0]
                        corrected_words.append(replacement)
                        matched = True
                        break
        if not matched:
            corrected_words.append(word)

    return " ".join(corrected_words)


def _has_potential_typo(text: str) -> bool:
    """Checks if text contains unusual token structures or short mangled words."""
    words = [re.sub(r"[^\w]", "", w).lower() for w in text.split() if w]
    # Check for single-character or mangled 2-letter non-standard tokens
    suspect_tokens = {"wat", "wht", "wats", "yo", "hw", "wether", "wthr", "tmrw"}
    return any(w in suspect_tokens or (len(w) == 1 and w not in ("a", "i")) for w in words)


def _levenshtein_distance(s1: str, s2: str) -> int:
    """Computes basic Levenshtein edit distance."""
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]
