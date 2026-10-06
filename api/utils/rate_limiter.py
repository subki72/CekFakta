"""
Rate limiter — 3 requests per minute per IP address (BR13).

Uses in-memory storage (dictionary) which resets on serverless cold start.
This is acceptable for Vercel serverless because:
- Each function instance has its own memory
- Cold starts naturally reset the counter
- For 30 concurrent users, this provides sufficient protection
"""

import hashlib
import os
import time
from collections import defaultdict

from fastapi import Request


class RateLimitExceeded(Exception):
    """Raised when a client exceeds the rate limit."""


# In-memory store: { ip_address: [timestamp1, timestamp2, ...] }
_request_log: dict[str, list[float]] = defaultdict(list)

# Configuration (SR4.1: 50 requests per hour)
MAX_REQUESTS = 50
WINDOW_SECONDS = 3600


def get_client_ip(request: Request) -> str:
    """Extract client IP securely prioritizing trusted reverse proxy headers."""
    vercel_ip = request.headers.get("x-vercel-forwarded-for")
    if vercel_ip:
        return vercel_ip.split(",")[0].strip()

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()

    if request.client and request.client.host:
        return request.client.host

    return "unknown"


def check_rate_limit(request: Request) -> None:
    """
    Check if the client IP has exceeded the rate limit.

    Raises RateLimitExceeded if the limit is exceeded.
    """
    client_ip = get_client_ip(request)

    now = time.time()
    window_start = now - WINDOW_SECONDS

    # Clean up old entries outside the window and delete empty keys to prevent memory leak
    if client_ip in _request_log:
        active_timestamps = [ts for ts in _request_log[client_ip] if ts > window_start]
        if active_timestamps:
            _request_log[client_ip] = active_timestamps
        else:
            del _request_log[client_ip]

    # Check if limit exceeded
    if len(_request_log.get(client_ip, [])) >= MAX_REQUESTS:
        raise RateLimitExceeded()

    # Record this request
    _request_log[client_ip].append(now)


def get_client_ip_hash(request: Request) -> str:
    """
    Get a hashed version of the client IP with secret salt for storage (privacy).
    """
    client_ip = get_client_ip(request)
    salt = os.getenv("IP_HASH_SALT", "factguard_default_salt")
    return hashlib.sha256(f"{client_ip}:{salt}".encode()).hexdigest()[:24]

