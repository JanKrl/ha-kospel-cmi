"""
HTTP API functions for Kospel MODBUS-over-HTTP devices (e.g. PPE.4).

The built-in Wi-Fi module exposes a decimal-addressed MODBUS-over-HTTP API:
- GET  {api_base_url}/{start}/{count} -> {"ver":"1.0","status":"OK","res":{"1140":420,...}}
- POST {api_base_url}/write           -> compact JSON {"1390":0,"1391":450}
"""

import json
import logging
import re
from typing import Any

import aiohttp

from ..exceptions import KospelConnectionError, KospelWriteError

logger = logging.getLogger(__name__)

# The firmware emits malformed JSON for empty reads: `...,"res":}}`.
_RES_RE = re.compile(r'"res"\s*:\s*(\{.*\})\s*\}\s*$')
_STATUS_RE = re.compile(r'"status"\s*:\s*"([^"]*)"')


def parse_modbus_read_response(text: str) -> dict[int, int]:
    """Parse a MODBUS-over-HTTP register read response into {address: value}.

    Tolerates the firmware's malformed empty payload (`"res":}}`) so reverse
    engineering and register scanning tools can query unmapped address ranges.

    Raises:
        KospelConnectionError: If status is not OK or payload is malformed.
    """
    status = _STATUS_RE.search(text)
    if not status or status.group(1) != "OK":
        raise KospelConnectionError(
            f"Device returned non-OK status for MODBUS read: {text.strip()}"
        )

    match = _RES_RE.search(text.strip())
    if not match:
        return {}
    try:
        raw: dict[str, Any] = json.loads(match.group(1))
    except json.JSONDecodeError as err:
        raise KospelConnectionError(f"Invalid MODBUS res payload: {err}") from err

    try:
        return {int(k): int(v) for k, v in raw.items()}
    except (ValueError, TypeError) as err:
        raise KospelConnectionError(
            f"Non-integer key or value in MODBUS res payload: {err}"
        ) from err


async def read_registers(
    session: aiohttp.ClientSession,
    api_base_url: str,
    start_register: int,
    count: int,
) -> dict[int, int]:
    """Read `count` consecutive 16-bit registers starting at `start_register`."""
    base = api_base_url.rstrip("/")
    url = f"{base}/{start_register}/{count}"
    logger.debug(
        "Reading %s MODBUS registers starting from %s at %s",
        count,
        start_register,
        url,
    )
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
            response.raise_for_status()
            text = await response.text()
    except aiohttp.ClientError as err:
        raise KospelConnectionError(
            f"HTTP error reading MODBUS registers from {start_register} at {url}"
        ) from err

    return parse_modbus_read_response(text)


async def write_registers(
    session: aiohttp.ClientSession,
    api_base_url: str,
    values: dict[int, int],
) -> None:
    """Write one or more 16-bit MODBUS registers via POST /api/write.

    The firmware rejects any whitespace in the JSON body (status_value -10),
    so `separators=(",", ":")` is required.
    """
    base = api_base_url.rstrip("/")
    url = f"{base}/write"
    body = {str(addr): int(value) & 0xFFFF for addr, value in values.items()}
    payload = json.dumps(body, separators=(",", ":"))
    logger.debug("Writing MODBUS registers %s to %s", payload, url)
    try:
        async with session.post(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=5),
        ) as response:
            response.raise_for_status()
            text = await response.text()
    except aiohttp.ClientError as err:
        raise KospelConnectionError(
            f"HTTP error writing MODBUS registers to {url}"
        ) from err

    status = _STATUS_RE.search(text)
    if status and status.group(1) == "OK":
        logger.debug("Successfully wrote MODBUS registers %s", body)
        return

    raise KospelWriteError(
        f"Device rejected MODBUS write to {url}: {text.strip()}"
    )


async def write_register(
    session: aiohttp.ClientSession,
    api_base_url: str,
    register: int,
    value: int,
) -> None:
    """Write a single 16-bit MODBUS register."""
    await write_registers(session, api_base_url, {register: value})
