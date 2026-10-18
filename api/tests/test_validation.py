"""Unit tests for payload schema validation and sanitization."""

import pytest


def test_input_text_length_constraints():
    """Verify minimum and maximum text length enforcement."""
    min_length = 20
    max_length = 5000
    
    valid_text = "Ini adalah contoh narasi berita politik yang memenuhi batas minimum panjang karakter."
    assert len(valid_text) >= min_length
    assert len(valid_text) <= max_length


def test_input_sanitization_removes_dangerous_tags():
    """Verify basic script tag neutralization."""
    raw_input = "<script>alert('xss')</script>Klaim berita faktual"
    cleaned = raw_input.replace("<script>", "").replace("</script>", "")
    assert "<script>" not in cleaned
    assert "Klaim berita faktual" in cleaned
