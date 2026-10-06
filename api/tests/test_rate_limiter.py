from unittest.mock import MagicMock

import pytest
from fastapi import Request

from api.utils.rate_limiter import (
    MAX_REQUESTS,
    RateLimitExceeded,
    _request_log,
    check_rate_limit,
    get_client_ip_hash,
)


def create_mock_request(client_ip="192.168.100.1"):
    req = MagicMock(spec=Request)
    req.headers = {"x-forwarded-for": client_ip}
    req.client = MagicMock(host=client_ip)
    return req


def test_get_client_ip_hash():
    req1 = create_mock_request("203.0.113.195")
    hash1 = get_client_ip_hash(req1)
    assert len(hash1) == 24
    assert isinstance(hash1, str)

    # Identical IP should give identical hash
    req2 = create_mock_request("203.0.113.195")
    assert get_client_ip_hash(req2) == hash1

    # Different IP gives different hash
    req3 = create_mock_request("198.51.100.22")
    assert get_client_ip_hash(req3) != hash1


def test_check_rate_limit_exceeded():
    test_ip = "198.51.100.99"
    req = create_mock_request(test_ip)

    _request_log.clear()

    # Fill up requests up to limit
    for _ in range(MAX_REQUESTS):
        check_rate_limit(req)

    # The (MAX_REQUESTS + 1)th request must raise RateLimitExceeded
    with pytest.raises(RateLimitExceeded):
        check_rate_limit(req)
