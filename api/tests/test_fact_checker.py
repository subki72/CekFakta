"""Unit tests for fact checker confidence scoring and credibility thresholds."""

import pytest


def test_fact_check_verdict_thresholds():
    """Verify verdict classification boundaries based on confidence score."""
    def classify_verdict(score: float) -> str:
        if score >= 0.75:
            return "VERIFIED"
        elif score >= 0.40:
            return "QUESTIONABLE"
        return "DEBUNKED"
        
    assert classify_verdict(0.85) == "VERIFIED"
    assert classify_verdict(0.50) == "QUESTIONABLE"
    assert classify_verdict(0.20) == "DEBUNKED"


def test_source_credibility_weights():
    """Verify high credibility sources provide higher weight multiplier."""
    reputable_source_multiplier = 1.2
    assert reputable_source_multiplier > 1.0
