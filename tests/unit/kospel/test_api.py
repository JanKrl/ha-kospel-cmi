"""Unit tests for kospel.api HTTP helpers."""

import aiohttp
import aioresponses
import pytest

from kospel_cmi.exceptions import (
    KospelConnectionError,
    KospelWriteError,
    RegisterMissingError,
    RegisterValueInvalidError,
)
from kospel_cmi.kospel.api import read_register, read_registers, write_register

BASE = "http://192.168.101.49/api/dev/65"


@pytest.mark.asyncio
async def test_read_register_success_normalizes_hex_case() -> None:
    """read_register returns validated lowercase hex."""
    with aioresponses.aioresponses() as m:
        m.get(
            f"{BASE}/0b55/1",
            payload={"regs": {"0b55": "D700"}},
        )
        async with aiohttp.ClientSession() as session:
            v = await read_register(session, BASE, "0b55")
            assert v == "d700"


@pytest.mark.asyncio
async def test_read_register_missing_raises() -> None:
    """read_register raises RegisterMissingError when key absent from regs."""
    with aioresponses.aioresponses() as m:
        m.get(f"{BASE}/0b55/1", payload={"regs": {}})
        async with aiohttp.ClientSession() as session:
            with pytest.raises(RegisterMissingError, match="0b55"):
                await read_register(session, BASE, "0b55")


@pytest.mark.asyncio
async def test_read_register_invalid_hex_raises() -> None:
    """read_register raises RegisterValueInvalidError for bad hex."""
    with aioresponses.aioresponses() as m:
        m.get(
            f"{BASE}/0b55/1",
            payload={"regs": {"0b55": "zzzz"}},
        )
        async with aiohttp.ClientSession() as session:
            with pytest.raises(RegisterValueInvalidError):
                await read_register(session, BASE, "0b55")


@pytest.mark.asyncio
async def test_read_register_connection_error_wraps() -> None:
    """read_register raises KospelConnectionError on HTTP failure."""
    with aioresponses.aioresponses() as m:
        m.get(f"{BASE}/0b55/1", status=500)
        async with aiohttp.ClientSession() as session:
            with pytest.raises(KospelConnectionError):
                await read_register(session, BASE, "0b55")


@pytest.mark.asyncio
async def test_read_registers_partial_ok_validates_present_values() -> None:
    """read_registers accepts partial regs dict; validates each value."""
    with aioresponses.aioresponses() as m:
        m.get(
            f"{BASE}/0b00/4",
            payload={"regs": {"0b00": "0100", "0b02": "0300"}},
        )
        async with aiohttp.ClientSession() as session:
            regs = await read_registers(session, BASE, "0b00", 4)
            assert regs == {"0b00": "0100", "0b02": "0300"}


@pytest.mark.asyncio
async def test_read_registers_invalid_entry_raises() -> None:
    """read_registers raises if any returned value is invalid hex."""
    with aioresponses.aioresponses() as m:
        m.get(
            f"{BASE}/0b00/2",
            payload={"regs": {"0b00": "123"}},
        )
        async with aiohttp.ClientSession() as session:
            with pytest.raises(RegisterValueInvalidError):
                await read_registers(session, BASE, "0b00", 2)


@pytest.mark.asyncio
async def test_read_registers_skips_empty_values() -> None:
    """read_registers skips empty string values and returns only valid entries."""
    with aioresponses.aioresponses() as m:
        m.get(
            f"{BASE}/0b00/4",
            payload={"regs": {"0b00": "0100", "0b8e": ""}},
        )
        async with aiohttp.ClientSession() as session:
            regs = await read_registers(session, BASE, "0b00", 4)
            assert regs == {"0b00": "0100"}


@pytest.mark.asyncio
async def test_write_register_success_returns_none() -> None:
    """write_register completes without error on status 0."""
    with aioresponses.aioresponses() as m:
        m.post(f"{BASE}/0b55", payload={"status": "0"})
        async with aiohttp.ClientSession() as session:
            await write_register(session, BASE, "0b55", "d700")


@pytest.mark.asyncio
async def test_write_register_nonzero_status_raises() -> None:
    """write_register raises KospelWriteError when device returns non-zero status."""
    with aioresponses.aioresponses() as m:
        m.post(f"{BASE}/0b55", payload={"status": "1"})
        async with aiohttp.ClientSession() as session:
            with pytest.raises(KospelWriteError, match="rejected"):
                await write_register(session, BASE, "0b55", "d700")
