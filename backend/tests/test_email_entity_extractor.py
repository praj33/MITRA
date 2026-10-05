"""
test_email_entity_extractor.py — Regression and unit tests for deterministic email entity extraction.
Validates extraction of recipient, subject, and content, ensuring raw commands are NEVER used as email body.
"""
import pytest
from app.capabilities.email_entity_extractor import extract_email_entities, is_raw_command_text


def test_extraction_case_a():
    """A. Send an email to rajprajapati1729@gmail.com saying "Hello Raj" """
    text = 'Send an email to rajprajapati1729@gmail.com saying "Hello Raj"'
    res = extract_email_entities(text)
    assert res["recipient"] == "rajprajapati1729@gmail.com"
    assert res["content"] == "Hello Raj"
    assert res["content"] != text


def test_extraction_case_b():
    """B. Send an email to rajprajapati1729@gmail.com with subject "Meeting tomorrow" and message "Hi Raj, let's meet tomorrow." """
    text = 'Send an email to rajprajapati1729@gmail.com with subject "Meeting tomorrow" and message "Hi Raj, let\'s meet tomorrow."'
    res = extract_email_entities(text)
    assert res["recipient"] == "rajprajapati1729@gmail.com"
    assert res["subject"] == "Meeting tomorrow"
    assert res["content"] == "Hi Raj, let's meet tomorrow."
    assert res["content"] != text


def test_extraction_case_b_full_production_problem():
    """Production problem case with contractions and multiple sentences."""
    text = 'Send an email to rajprajapati1729@gmail.com with subject "Meeting tomorrow" and message "Hi Raj, let\'s meet tomorrow. Please let me know what time works for you."'
    res = extract_email_entities(text)
    assert res["recipient"] == "rajprajapati1729@gmail.com"
    assert res["subject"] == "Meeting tomorrow"
    assert res["content"] == "Hi Raj, let's meet tomorrow. Please let me know what time works for you."
    assert res["content"] != text


def test_extraction_case_c():
    """C. Email rajprajapati1729@gmail.com: "Please call me." """
    text = 'Email rajprajapati1729@gmail.com: "Please call me."'
    res = extract_email_entities(text)
    assert res["recipient"] == "rajprajapati1729@gmail.com"
    assert res["content"] == "Please call me."
    assert res["content"] != text


def test_extraction_case_d():
    """D. Send an email to rajprajapati1729@gmail.com with subject "Meeting" and body "Let's meet at 5 PM." """
    text = 'Send an email to rajprajapati1729@gmail.com with subject "Meeting" and body "Let\'s meet at 5 PM."'
    res = extract_email_entities(text)
    assert res["recipient"] == "rajprajapati1729@gmail.com"
    assert res["subject"] == "Meeting"
    assert res["content"] == "Let's meet at 5 PM."
    assert res["content"] != text


def test_extraction_unquoted_saying():
    """Send an email to alice@example.com saying Hello Alice"""
    text = 'Send an email to alice@example.com saying Hello Alice'
    res = extract_email_entities(text)
    assert res["recipient"] == "alice@example.com"
    assert res["content"] == "Hello Alice"
    assert res["content"] != text


def test_extraction_colon_unquoted():
    """Email alice@example.com: Please send me the report."""
    text = 'Email alice@example.com: Please send me the report.'
    res = extract_email_entities(text)
    assert res["recipient"] == "alice@example.com"
    assert res["content"] == "Please send me the report."
    assert res["content"] != text


def test_extraction_tagged_subject_body():
    """Send an email to alice@example.com. Subject: Meeting tomorrow. Body: Let's meet at 5."""
    text = "Send an email to alice@example.com. Subject: Meeting tomorrow. Body: Let's meet at 5."
    res = extract_email_entities(text)
    assert res["recipient"] == "alice@example.com"
    assert res["subject"] == "Meeting tomorrow"
    assert res["content"] == "Let's meet at 5."
    assert res["content"] != text


def test_extraction_about_and_say():
    """Email alice@example.com about tomorrow's meeting and say I'll call at 5."""
    text = "Email alice@example.com about tomorrow's meeting and say I'll call at 5."
    res = extract_email_entities(text)
    assert res["recipient"] == "alice@example.com"
    assert res["subject"] == "tomorrow's meeting"
    assert res["content"] == "I'll call at 5."
    assert res["content"] != text


def test_extraction_draft_case():
    """Create a draft email to rajprajapati1729@gmail.com saying "Meet me urgently." """
    text = 'Create a draft email to rajprajapati1729@gmail.com saying "Meet me urgently."'
    res = extract_email_entities(text)
    assert res["recipient"] == "rajprajapati1729@gmail.com"
    assert res["content"] == "Meet me urgently."
    assert res["content"] != text


def test_e_invariant_content_never_raw_command():
    """E. Verify canonical content is never equal to the complete raw command."""
    commands = [
        'Send an email to test@example.com saying "Hello"',
        'Send an email to test@example.com with subject "Subj" and message "Body"',
        'Create a draft email to test@example.com saying "Draft body"',
        'Email test@example.com: "Help"',
    ]
    for cmd in commands:
        res = extract_email_entities(cmd)
        assert res["content"] != cmd
        assert not is_raw_command_text(res["content"], cmd)
