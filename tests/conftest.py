"""Shared fixtures for Nativ SDK tests."""

import httpx
import pytest

from nativ import Nativ, AsyncNativ


API_KEY = "nativ_test_00000000000000000000000000000000"
BASE_URL = "https://api.test.usenativ.com"


@pytest.fixture
def client(httpx_mock):
    """Pre-configured sync Nativ client pointing at mock transport."""
    return Nativ(api_key=API_KEY, base_url=BASE_URL)


@pytest.fixture
def async_client(httpx_mock):
    """Pre-configured async Nativ client pointing at mock transport."""
    return AsyncNativ(api_key=API_KEY, base_url=BASE_URL)
