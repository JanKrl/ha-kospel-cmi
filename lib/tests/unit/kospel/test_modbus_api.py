"""Unit tests for kospel.modbus_api MODBUS-over-HTTP helpers."""

import aiohttp
import aioresponses
import pytest
from yarl import URL

from kospel_cmi.exceptions import (
    KospelConnectionError,
    KospelWriteError,
)
from kospel_cmi.kospel.modbus_api import (
    read_registers,
    write_register,
    write_registers,
)

BASE = "http://192.168.1.36/api"


@pytest.mark.asyncio
async def test_read_registers_parses_integer_map() -> None:
    """read_registers returns dict[int, int] from valid MODBUS JSON response."""
    with aioresponses.aioresponses() as m:
        m.get(
            f"{BASE}/1134/3",
            body='{"ver":"1.0","status":"OK","status_value":"0","res":{"1134":206,"1135":420,"1136":220}}',
        )
        async with aiohttp.ClientSession() as session:
            regs = await read_registers(session, BASE, 1134, 3)
            assert regs == {1134: 206, 1135: 420, 1136: 220}


@pytest.mark.asyncio
async def test_read_registers_tolerates_malformed_empty_res() -> None:
    """read_registers tolerates firmware's malformed empty payload ('\"res\":}}')."""
    with aioresponses.aioresponses() as m:
        m.get(
            f"{BASE}/1800/10",
            body='{"ver":"1.0","status":"OK","status_value":"0","res":}}',
        )
        async with aiohttp.ClientSession() as session:
            regs = await read_registers(session, BASE, 1800, 10)
            assert regs == {}


@pytest.mark.asyncio
async def test_read_registers_raises_on_error_status() -> None:
    """read_registers raises KospelConnectionError when status != OK."""
    with aioresponses.aioresponses() as m:
        m.get(
            f"{BASE}/1134/999",
            body='{"ver":"1.0","status":"ERROR","status_value":"-14","msg":"Wrong MODBUS register count."}',
        )
        async with aiohttp.ClientSession() as session:
            with pytest.raises(KospelConnectionError):
                await read_registers(session, BASE, 1134, 999)


@pytest.mark.asyncio
async def test_read_registers_raises_on_http_error() -> None:
    """read_registers raises KospelConnectionError on HTTP failure."""
    with aioresponses.aioresponses() as m:
        m.get(f"{BASE}/1134/2", status=500)
        async with aiohttp.ClientSession() as session:
            with pytest.raises(KospelConnectionError):
                await read_registers(session, BASE, 1134, 2)


@pytest.mark.asyncio
async def test_write_registers_sends_compact_json_without_whitespace() -> None:
    """write_registers sends compact JSON (no spaces) to POST /api/write."""
    with aioresponses.aioresponses() as m:
        m.post(
            f"{BASE}/write",
            body='{"ver":"1.0","status":"OK","status_value":"0"}',
        )
        async with aiohttp.ClientSession() as session:
            await write_registers(session, BASE, {1390: 0, 1391: 450})

        calls = m.requests[("POST", URL(f"{BASE}/write"))]
        assert len(calls) == 1
        sent_data = calls[0].kwargs.get("data")
        assert sent_data == '{"1390":0,"1391":450}'
        assert " " not in sent_data


@pytest.mark.asyncio
async def test_write_register_delegates_single_register() -> None:
    """write_register writes a single register via POST /api/write."""
    with aioresponses.aioresponses() as m:
        m.post(
            f"{BASE}/write",
            body='{"ver":"1.0","status":"OK","status_value":"0"}',
        )
        async with aiohttp.ClientSession() as session:
            await write_register(session, BASE, 1393, 450)

        calls = m.requests[("POST", URL(f"{BASE}/write"))]
        assert len(calls) == 1
        assert calls[0].kwargs.get("data") == '{"1393":450}'


@pytest.mark.asyncio
async def test_write_registers_raises_on_error_status() -> None:
    """write_registers raises KospelWriteError when device rejects write."""
    with aioresponses.aioresponses() as m:
        m.post(
            f"{BASE}/write",
            body='{"ver":"1.0","status":"ERROR","status_value":"-10"}',
        )
        async with aiohttp.ClientSession() as session:
            with pytest.raises(KospelWriteError):
                await write_registers(session, BASE, {1391: 450})

