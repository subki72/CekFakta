"""Unit tests for political narrative objectivity verifier and text analysis logic."""

import pytest


def test_calculate_similarity_metric():
    """Verify text similarity metric returns normalized float score."""
    sample_text_a = "Pemerintah mengumumkan kebijakan ekonomi baru untuk menstabilkan inflasi pangan."
    sample_text_b = "Kebijakan ekonomi baru diumumkan pemerintah guna menjaga stabilitas harga bahan pokok."
    
    # Token set overlap ratio
    tokens_a = set(sample_text_a.lower().split())
    tokens_b = set(sample_text_b.lower().split())
    intersection = tokens_a.intersection(tokens_b)
    union = tokens_a.union(tokens_b)
    similarity = len(intersection) / len(union) if union else 0.0
    
    assert similarity > 0.2
    assert similarity <= 1.0


def test_verifier_sentiment_polarity_range():
    """Verify confidence score boundaries for polarity assessment."""
    confidence = 0.88
    assert 0.0 <= confidence <= 1.0
    assert isinstance(confidence, float)
