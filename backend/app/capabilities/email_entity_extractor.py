"""
email_entity_extractor.py — Deterministic Entity & Body Extractor for Email Actions
Extracts recipient, subject, and body/content from natural language email requests.

CRITICAL INVARIANT:
The email body/content must NEVER default to the entire raw user command
when a structured or natural message/body/saying is present or can be extracted.
"""
from __future__ import annotations
import re
from typing import Any, Dict, Optional, Tuple

_EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

_DEFAULT_SUBJECT = "Message from Mitra AI"

_COMMAND_PREFIXES = (
    "send an email to",
    "send an email",
    "send email to",
    "send email",
    "email to",
    "email",
    "create a draft email to",
    "create a draft email",
    "create a draft to",
    "create a draft",
    "create draft email to",
    "create draft email",
    "create draft to",
    "create draft",
    "compose a draft to",
    "compose a draft",
    "compose draft",
    "draft an email to",
    "draft an email",
    "draft email to",
    "draft email",
    "save as draft",
    "save a draft",
    "make a draft",
)


def _strip_quotes(text: str) -> str:
    """Safely strip matching surrounding single or double quotes."""
    s = text.strip()
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        if len(s) >= 2:
            return s[1:-1].strip()
    return s


def is_raw_command_text(text: str, raw_message: Optional[str] = None) -> bool:
    """
    Check if a text snippet represents a raw dispatch command rather than an actual body.
    """
    if not text:
        return False
    t_clean = text.strip().lower()
    if raw_message and t_clean == raw_message.strip().lower():
        return True
    for prefix in _COMMAND_PREFIXES:
        if t_clean.startswith(prefix):
            return True
    return False


def extract_email_entities(
    text: str,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Deterministically extract recipient, subject, and content/body from text.

    Returns dict with keys:
        - recipient: str (email address or identifier)
        - subject: str (extracted subject or default)
        - content: str (extracted clean email body, NEVER the raw command)
        - is_extracted: bool (True if explicit body/saying was extracted)
    """
    params = params or {}
    raw_message = (text or "").strip()

    # 1. Recipient Extraction
    recipient = ""
    if params.get("recipient"):
        recipient = str(params["recipient"]).strip()
    elif params.get("to"):
        recipient = str(params["to"]).strip()
    elif params.get("to_addr"):
        recipient = str(params["to_addr"]).strip()
    elif isinstance(params.get("entities"), dict):
        emails = params["entities"].get("email")
        if isinstance(emails, list) and emails:
            recipient = str(emails[0]).strip()

    if not recipient and raw_message:
        match = _EMAIL_REGEX.search(raw_message)
        if match:
            recipient = match.group(0)

    # 2. Extract Subject and Body from params if explicitly provided and not raw command
    param_subject = params.get("subject")
    param_body = params.get("body") or params.get("content")

    # If param_body is already a raw command, discard it to allow deterministic extraction
    if param_body and is_raw_command_text(str(param_body), raw_message):
        param_body = None

    extracted_subject: Optional[str] = str(param_subject).strip() if param_subject else None
    extracted_body: Optional[str] = str(param_body).strip() if param_body else None

    # 3. Deterministic Parsing from text
    if raw_message and (not extracted_subject or not extracted_body):
        subj, body = _parse_subject_and_body(raw_message)
        if not extracted_subject and subj:
            extracted_subject = subj
        if not extracted_body and body:
            extracted_body = body

    # 4. Fallback cleanup: Ensure body is never the raw command
    final_body = (extracted_body or "").strip()
    is_extracted = bool(final_body)

    if final_body and is_raw_command_text(final_body, raw_message):
        # Attempt to strip the command part
        cleaned = _strip_command_prefix(final_body, recipient)
        if cleaned and not is_raw_command_text(cleaned, raw_message):
            final_body = cleaned
        else:
            final_body = ""
            is_extracted = False

    # 5. Fallback subject
    final_subject = (extracted_subject or "").strip()
    if not final_subject:
        final_subject = _DEFAULT_SUBJECT

    return {
        "recipient": recipient,
        "to_addr": recipient,
        "to": recipient,
        "subject": final_subject,
        "content": final_body,
        "body": final_body,
        "is_extracted": is_extracted,
    }


def _parse_subject_and_body(msg: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse subject and body using structured deterministic patterns.
    """
    subj: Optional[str] = None
    body: Optional[str] = None

    # ── Pattern 1: Explicit Quoted Subject AND Quoted Message/Body ───────────
    # e.g. with subject "Meeting tomorrow" and message "Hi Raj, let's meet tomorrow."
    # or with message "Hi Raj, let's meet tomorrow." and subject "Meeting tomorrow"
    subj_q = re.search(
        r'\b(?:with\s+)?subject\s*[:=]?\s*(?:"([^"]+)"|\'([^\']+)\')',
        msg,
        re.IGNORECASE,
    )
    if subj_q:
        subj = (subj_q.group(1) or subj_q.group(2) or "").strip()

    body_q = re.search(
        r'\b(?:and\s+)?(?:with\s+)?(?:the\s+)?(?:message|body|content|text)\s*[:=]?\s*(?:"([^"]+)"|\'([^\']+)\')',
        msg,
        re.IGNORECASE,
    )
    if body_q:
        body = (body_q.group(1) or body_q.group(2) or "").strip()

    if subj and body:
        return subj, body

    # ── Pattern 2: Key-Value / Header style (Subject: ... Body: ...) ──────────
    # e.g. Subject: Meeting tomorrow. Body: Let's meet at 5.
    kv_match = re.search(
        r'\bsubject:\s*([^\n\r.]+?)(?:\s*\.?\s*(?:body|message|content):\s*([\s\S]+))$',
        msg,
        re.IGNORECASE,
    )
    if kv_match:
        s = _strip_quotes(kv_match.group(1).strip())
        b = _strip_quotes(kv_match.group(2).strip())
        return s or subj, b or body

    # ── Pattern 3: Colon after recipient (Email <addr>: <message>) ───────────
    # e.g. Email rajprajapati1729@gmail.com: "Please call me."
    # or Email alice@example.com: Please send me the report.
    colon_match = re.search(
        r'\b(?:email|send\s+(?:an?\s+)?email\s+(?:to\s+)?)\s*[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\s*:\s*(.+)$',
        msg,
        re.IGNORECASE,
    )
    if colon_match:
        extracted = _strip_quotes(colon_match.group(1).strip())
        if extracted and not is_raw_command_text(extracted, msg):
            return subj, extracted

    # ── Pattern 4: about <subject> and say/saying <message> ───────────────────
    # e.g. Email alice@example.com about tomorrow's meeting and say I'll call at 5.
    about_say_match = re.search(
        r'\babout\s+(.+?)\s+(?:and\s+)?(?:saying|say|tell\s+(?:them|him|her))\s+(.+)$',
        msg,
        re.IGNORECASE,
    )
    if about_say_match:
        s = _strip_quotes(about_say_match.group(1).strip())
        b = _strip_quotes(about_say_match.group(2).strip())
        return s or subj, b or body

    # ── Pattern 5: saying / say <message> (Quoted or Unquoted) ───────────────
    # e.g. Send an email to rajprajapati1729@gmail.com saying "Hello Raj"
    # or Send an email to alice@example.com saying Hello Alice
    # or Create a draft email to rajprajapati1729@gmail.com saying "Meet me urgently."
    saying_match = re.search(
        r'\b(?:saying|say|tell\s+(?:them|him|her))\s+(.+)$',
        msg,
        re.IGNORECASE,
    )
    if saying_match:
        b = _strip_quotes(saying_match.group(1).strip())
        if b and not is_raw_command_text(b, msg):
            return subj, b

    # ── Pattern 6: with message / body / content / text <message> ─────────────
    # e.g. Send an email to rajprajapati1729@gmail.com with subject "Meeting" and message "Let's meet at 5 PM."
    # If subject was already found by Pattern 1, look for remaining body:
    msg_clause = re.search(
        r'\b(?:and\s+)?(?:with\s+)?(?:the\s+)?(?:message|body|content|text)\s*[:=]?\s+(.+)$',
        msg,
        re.IGNORECASE,
    )
    if msg_clause:
        b = _strip_quotes(msg_clause.group(1).strip())
        if b and not is_raw_command_text(b, msg):
            return subj, b

    # ── Pattern 7: about <subject> without explicit saying ────────────────────
    if not subj:
        about_match = re.search(
            r'\b(?:about|titled)\s+(?:"([^"]+)"|\'([^\']+)\'|([^.\n\r]+))',
            msg,
            re.IGNORECASE,
        )
        if about_match:
            s_cand = about_match.group(1) or about_match.group(2) or about_match.group(3)
            if s_cand:
                subj = _strip_quotes(s_cand.strip())

    return subj, body


def _strip_command_prefix(text: str, recipient: str = "") -> str:
    """Strip leading command patterns like 'Send an email to <email>' from text."""
    s = text.strip()
    if recipient:
        s = re.sub(
            rf'(?i)^(?:please\s+)?(?:send\s+(?:an?\s+)?email\s+(?:to\s+)?|email\s+(?:to\s+)?|draft\s+(?:an?\s+)?email\s+(?:to\s+)?){re.escape(recipient)}\s*[:,]?\s*',
            '',
            s,
        )
    for p in _COMMAND_PREFIXES:
        if s.lower().startswith(p):
            s = s[len(p):].lstrip(" :,-")
            break
    return _strip_quotes(s.strip())
