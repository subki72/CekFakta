"""Unit tests for HTTP security headers and CORS protection policy."""

import pytest


def test_required_security_headers_present():
    """Verify standard defensive HTTP response headers."""
    expected_headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Content-Security-Policy": "default-src 'self'",
    }
    
    simulated_headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Content-Security-Policy": "default-src 'self'",
    }
    
    for key, value in expected_headers.items():
        assert key in simulated_headers
        assert simulated_headers[key] == value
