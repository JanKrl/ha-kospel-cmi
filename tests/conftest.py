"""Shared pytest fixtures for kospel-cmi-lib tests."""

import pytest
import aiohttp


@pytest.fixture
def api_base_url() -> str:
    """Base URL for heater API (used by controller/API tests)."""
    return "http://192.168.1.1/api/dev/65"


@pytest.fixture
async def session() -> aiohttp.ClientSession:
    """aiohttp ClientSession for HTTP-dependent tests (use as async fixture)."""
    async with aiohttp.ClientSession() as s:
        yield s
