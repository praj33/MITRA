"""
backend/app/executors/mime_builder.py — Safe RFC 2822 MIME Message Builder & HTML Sanitizer

Implements:
- Header injection / CRLF rejection
- RFC 2822 message construction (plain text, HTML alternative, attachments)
- Unicode header and body encoding
- Email address validation
- Strict HTML content sanitization for inbound/retrieved email bodies
"""
import re
import os
import email
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Any, Optional, Union


# Regex for basic email format validation
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def validate_safe_header_value(name: str, value: str) -> str:
    """
    Validates that a header string contains no carriage returns or newlines (CRLF injection check).
    """
    if not isinstance(value, str):
        value = str(value or "")
    if "\r" in value or "\n" in value:
        raise ValueError(f"Header injection detected: header '{name}' contains carriage return or newline characters.")
    return value.strip()


def validate_email_address(email_str: str) -> str:
    """
    Validates email format and ensures no CRLF or control characters.
    """
    clean = validate_safe_header_value("Email", email_str)
    # Handle 'Name <email@example.com>' format or plain 'email@example.com'
    if "<" in clean and ">" in clean:
        match = re.search(r"<([^>]+)>", clean)
        addr = match.group(1).strip() if match else clean
    else:
        addr = clean

    if not EMAIL_REGEX.match(addr):
        raise ValueError(f"Invalid email address format: '{email_str}'")
    return clean


def sanitize_html_content(raw_html: str) -> str:
    """
    Sanitizes raw HTML to render safely without script execution, iframes, or event handlers.
    Preserves structural text formatting (<p>, <br>, <b>, <i>, <a>, <div>, <span>, lists, tables).
    """
    if not raw_html or not isinstance(raw_html, str):
        return ""

    sanitized = raw_html

    # 1. Remove dangerous script, style, iframe, object, embed, form, meta, link tags and their contents
    dangerous_tags = ["script", "style", "iframe", "object", "embed", "applet", "form", "meta", "link"]
    for tag in dangerous_tags:
        pattern = re.compile(rf"<{tag}\b[^>]*>[\s\S]*?</{tag}>", re.IGNORECASE)
        sanitized = pattern.sub("", sanitized)
        # Also strip self-closing or lone tags
        self_closing = re.compile(rf"<{tag}\b[^>]*\/?>", re.IGNORECASE)
        sanitized = self_closing.sub("", sanitized)

    # 2. Strip inline event handlers (e.g. onclick=..., onload=..., onerror=...)
    event_handler_pattern = re.compile(r"\bon\w+\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+)", re.IGNORECASE)
    sanitized = event_handler_pattern.sub("", sanitized)

    # 3. Strip javascript: and vbscript: URIs from href, src, or action attributes
    dangerous_uri_pattern = re.compile(
        r"""(href|src|action)\s*=\s*(['"])\s*(?:javascript|vbscript|data(?!\s*:\s*image\/)):.*?\2""",
        re.IGNORECASE
    )
    sanitized = dangerous_uri_pattern.sub(r'\1="#"', sanitized)

    return sanitized


def build_safe_rfc2822_message(
    to_email: Union[str, List[str]],
    subject: str,
    text_body: str,
    html_body: Optional[str] = None,
    from_email: Optional[str] = None,
    cc: Optional[Union[str, List[str]]] = None,
    bcc: Optional[Union[str, List[str]]] = None,
    attachments: Optional[List[Dict[str, Any]]] = None,
) -> bytes:
    """
    Constructs a standards-compliant, CRLF-safe RFC 2822 MIME email message.
    Returns bytes representation ready for base64url encoding and API submission.
    """
    # 1. Validate Subject (prevent header injection)
    clean_subject = validate_safe_header_value("Subject", subject or "")

    # 2. Normalize and validate recipient lists
    def _normalize_recipients(recipients: Optional[Union[str, List[str]]]) -> List[str]:
        if not recipients:
            return []
        if isinstance(recipients, str):
            parts = [r.strip() for r in recipients.split(",") if r.strip()]
        else:
            parts = [str(r).strip() for r in recipients if str(r).strip()]
        for r in parts:
            validate_email_address(r)
        return parts

    to_list = _normalize_recipients(to_email)
    if not to_list:
        raise ValueError("At least one valid recipient is required in 'to_email'.")

    cc_list = _normalize_recipients(cc)
    bcc_list = _normalize_recipients(bcc)

    # 3. Build MIME hierarchy
    has_html = bool(html_body and html_body.strip())
    has_attachments = bool(attachments and len(attachments) > 0)

    if has_attachments:
        root_msg = MIMEMultipart("mixed")
        if has_html:
            body_container = MIMEMultipart("alternative")
            body_container.attach(MIMEText(text_body, "plain", "utf-8"))
            body_container.attach(MIMEText(sanitize_html_content(html_body), "html", "utf-8"))
            root_msg.attach(body_container)
        else:
            root_msg.attach(MIMEText(text_body, "plain", "utf-8"))
    elif has_html:
        root_msg = MIMEMultipart("alternative")
        root_msg.attach(MIMEText(text_body, "plain", "utf-8"))
        root_msg.attach(MIMEText(sanitize_html_content(html_body), "html", "utf-8"))
    else:
        root_msg = MIMEText(text_body, "plain", "utf-8")

    # 4. Apply headers safely
    root_msg["Subject"] = Header(clean_subject, "utf-8").encode()
    root_msg["To"] = ", ".join(to_list)

    if from_email:
        clean_from = validate_email_address(from_email)
        root_msg["From"] = clean_from

    if cc_list:
        root_msg["Cc"] = ", ".join(cc_list)

    if bcc_list:
        root_msg["Bcc"] = ", ".join(bcc_list)

    # 5. Attachments packaging
    if has_attachments and attachments:
        for att in attachments:
            raw_filename = att.get("filename") or "attachment.bin"
            # Prevent path traversal
            safe_filename = os.path.basename(raw_filename).strip()
            validate_safe_header_value("Attachment Filename", safe_filename)

            content_bytes = att.get("data")
            if isinstance(content_bytes, str):
                import base64
                try:
                    content_bytes = base64.b64decode(content_bytes)
                except Exception:
                    content_bytes = content_bytes.encode("utf-8")
            elif not isinstance(content_bytes, bytes):
                content_bytes = b""

            # Enforce 25MB attachment limit
            if len(content_bytes) > 25 * 1024 * 1024:
                raise ValueError(f"Attachment '{safe_filename}' exceeds the maximum allowed size of 25MB.")

            mime_type = att.get("mime_type") or "application/octet-stream"
            maintype, _, subtype = mime_type.partition("/")
            part = MIMEBase(maintype or "application", subtype or "octet-stream")
            part.set_payload(content_bytes)
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{safe_filename}"'
            )
            root_msg.attach(part)

    return root_msg.as_bytes()
