"""
Dedicated module for HTTP API calls to the Kospel heater.

This module contains only HTTP logic. Register backend abstraction (HTTP vs YAML)
lives in kospel/backend.py; the controller uses a RegisterBackend, not this API
directly.
"""

import json
import logging
from typing import Dict

import aiohttp

from ..exceptions import (
    KospelConnectionError,
    KospelWriteError,
    RegisterMissingError,
    RegisterValueInvalidError,
)
from ..registers.utils import reg_to_int, validate_register_hex

logger = logging.getLogger(__name__)


async def read_register(
    session: aiohttp.ClientSession,
    api_base_url: str,
    register: str,
) -> str:
    """
    Read a single register from the heater.

    Args:
        session: aiohttp ClientSession
        api_base_url: Base URL for the heater API (e.g., "http://192.168.1.1/api/dev/65")
        register: Register address (e.g., "0b55")

    Returns:
        Hex string value of the register.

    Raises:
        KospelConnectionError: On network/HTTP/JSON failure.
        RegisterMissingError: If the response does not contain the register.
        RegisterValueInvalidError: If the value is not valid hex.
    """
    url = f"{api_base_url}/{register}/1"
    logger.debug("Reading register %s from %s", register, url)
    try:
        async with session.get(url, timeout=5) as response:
            response.raise_for_status()
            data = await response.json()
    except aiohttp.ClientError as e:
        raise KospelConnectionError(
            f"HTTP error reading register {register} from {url}"
        ) from e
    except json.JSONDecodeError as e:
        raise KospelConnectionError(
            f"Invalid JSON reading register {register} from {url}"
        ) from e

    if not isinstance(data, dict):
        raise KospelConnectionError(
            f"Unexpected response shape reading register {register}: "
            "expected JSON object"
        )

    regs = data.get("regs", {})
    if not isinstance(regs, dict):
        raise KospelConnectionError(
            f"Unexpected 'regs' field reading register {register}: expected object"
        )

    if register not in regs:
        raise RegisterMissingError(register, detail="not present in device response")

    raw = regs[register]
    try:
        validated = validate_register_hex(str(raw))
    except RegisterValueInvalidError as e:
        raise RegisterValueInvalidError(
            f"Invalid hex for register {register}"
        ) from e

    int_val = reg_to_int(validated)
    logger.debug("Register %s: %s (%s)", register, validated, int_val)
    return validated


async def read_registers(
    session: aiohttp.ClientSession,
    api_base_url: str,
    start_register: str,
    count: int,
) -> Dict[str, str]:
    """
    Read multiple registers from the heater in a single batch call.

    Partial responses are allowed: only keys returned by the device are included.
    Each present value must be valid 4-character hex.

    Args:
        session: aiohttp ClientSession
        api_base_url: Base URL for the heater API
        start_register: Starting register address (e.g., "0b00")
        count: Number of registers to read

    Returns:
        Dictionary mapping register addresses to hex values (subset of requested range).

    Raises:
        KospelConnectionError: On network/HTTP/JSON failure.
        RegisterValueInvalidError: If any returned value is not valid hex.
    """
    url = f"{api_base_url}/{start_register}/{count}"
    logger.debug(
        "Reading %s registers starting from %s from %s", count, start_register, url
    )
    try:
        async with session.get(url, timeout=5) as response:
            response.raise_for_status()
            data = await response.json()
    except aiohttp.ClientError as e:
        raise KospelConnectionError(
            f"HTTP error reading registers from {start_register} at {url}"
        ) from e
    except json.JSONDecodeError as e:
        raise KospelConnectionError(
            f"Invalid JSON reading registers from {start_register} at {url}"
        ) from e

    if not isinstance(data, dict):
        raise KospelConnectionError(
            f"Unexpected response shape reading registers from {start_register}: "
            "expected JSON object"
        )

    regs = data.get("regs", {})
    if not isinstance(regs, dict):
        raise KospelConnectionError(
            "Unexpected 'regs' field in batch read: expected object"
        )

    out: Dict[str, str] = {}
    for reg_addr, raw in regs.items():
        if not isinstance(reg_addr, str):
            raise KospelConnectionError(
                f"Unexpected register key type in batch read: {type(reg_addr).__name__}"
            )
        raw_value = str(raw)
        if raw is None or raw_value.strip() == "":
            logger.debug(
                "Skipping register %s with unparsed batch value %r from %s",
                reg_addr,
                raw,
                start_register,
            )
            continue
        try:
            out[reg_addr] = validate_register_hex(raw_value)
        except RegisterValueInvalidError as e:
            raise RegisterValueInvalidError(
                f"Invalid hex for register {reg_addr} in batch read"
            ) from e

    logger.debug(
        "Read %s registers from %s (partial batch allowed)", len(out), start_register
    )
    return out


async def write_register(
    session: aiohttp.ClientSession,
    api_base_url: str,
    register: str,
    hex_value: str,
) -> None:
    """
    Write a value to a single register.

    Args:
        session: aiohttp ClientSession
        api_base_url: Base URL for the heater API
        register: Register address (e.g., "0b55")
        hex_value: Hex string value to write (e.g., "d700")

    Raises:
        KospelConnectionError: On network/HTTP/JSON failure or unexpected response.
        KospelWriteError: If the device reports a non-success status.
    """
    url = f"{api_base_url}/{register}"
    int_val = reg_to_int(hex_value)
    logger.debug(
        "Writing register %s: %s (%s) to %s", register, hex_value, int_val, url
    )
    try:
        async with session.post(url, json=hex_value, timeout=5) as response:
            response.raise_for_status()
            data = await response.json()
    except aiohttp.ClientError as e:
        raise KospelConnectionError(
            f"HTTP error writing register {register} to {url}"
        ) from e
    except json.JSONDecodeError as e:
        raise KospelConnectionError(
            f"Invalid JSON after write to register {register} at {url}"
        ) from e

    if not isinstance(data, dict):
        raise KospelConnectionError(
            f"Unexpected response shape after write to {register}: expected JSON object"
        )

    status = data.get("status")
    if status == "0":
        logger.debug("Successfully wrote register %s", register)
        return

    logger.warning(
        "Register %s write returned non-zero status: %s", register, status
    )
    raise KospelWriteError(
        f"Device rejected write to register {register}: status={status!r}"
    )
