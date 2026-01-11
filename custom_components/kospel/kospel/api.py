"""
Dedicated module for all Kospel heater API interactions.

This module centralizes all HTTP API calls to the heater, making it easier to
implement simulator mode and maintain consistent error handling.
"""

import logging
import aiohttp
from typing import Optional, Dict

from ..registers.utils import reg_to_int, int_to_reg, set_bit
from .simulator import (
    simulator_read_register,
    simulator_read_registers,
    simulator_write_register,
    simulator_write_flag_bit,
    with_simulator,
)

logger = logging.getLogger(__name__)


@with_simulator(simulator_read_register)
async def read_register(
    session: aiohttp.ClientSession,
    api_base_url: str,
    register: str,
    simulation_mode: bool | None = None,
) -> Optional[str]:
    """
    Read a single register from the heater.

    Args:
        session: aiohttp ClientSession
        api_base_url: Base URL for the heater API (e.g., "http://192.168.1.1/api/dev/65")
        register: Register address (e.g., "0b55")

    Returns:
        Hex string value of the register, or None if read failed
    """
    url = f"{api_base_url}/{register}/1"
    logger.debug(f"Reading register {register} from {url}")
    try:
        async with session.get(url, timeout=5) as response:
            response.raise_for_status()
            data = await response.json()
            regs = data.get("regs", {})
            value = regs.get(register)
            if value:
                int_val = reg_to_int(value)
                logger.debug(f"Register {register}: {value} ({int_val})")
            else:
                logger.warning(f"Register {register} not found in response")
            return value
    except (aiohttp.ClientError, aiohttp.ClientResponseError) as e:
        logger.error(f"Error reading register {register}: {e}")
        return None
    except Exception as e:
        logger.error(
            f"Unexpected error reading register {register}: {e}", exc_info=True
        )
        return None


@with_simulator(simulator_read_registers)
async def read_registers(
    session: aiohttp.ClientSession,
    api_base_url: str,
    start_register: str,
    count: int,
    simulation_mode: bool | None = None,
) -> Dict[str, str]:
    """
    Read multiple registers from the heater in a single batch call.

    Args:
        session: aiohttp ClientSession
        api_base_url: Base URL for the heater API
        start_register: Starting register address (e.g., "0b00")
        count: Number of registers to read

    Returns:
        Dictionary mapping register addresses to hex values
    """
    url = f"{api_base_url}/{start_register}/{count}"
    logger.debug(f"Reading {count} registers starting from {start_register} from {url}")
    try:
        async with session.get(url, timeout=5) as response:
            response.raise_for_status()
            data = await response.json()
            regs = data.get("regs", {})
            logger.debug(f"Read {len(regs)} registers from {start_register}")
            return regs
    except (aiohttp.ClientError, aiohttp.ClientResponseError) as e:
        logger.error(f"Error reading registers from {start_register}: {e}")
        return {}
    except Exception as e:
        logger.error(
            f"Unexpected error reading registers from {start_register}: {e}",
            exc_info=True,
        )
        return {}


@with_simulator(simulator_write_register)
async def write_register(
    session: aiohttp.ClientSession,
    api_base_url: str,
    register: str,
    hex_value: str,
    simulation_mode: bool | None = None,
) -> bool:
    """
    Write a value to a single register.

    Args:
        session: aiohttp ClientSession
        api_base_url: Base URL for the heater API
        register: Register address (e.g., "0b55")
        hex_value: Hex string value to write (e.g., "d700")

    Returns:
        True if write succeeded, False otherwise
    """
    url = f"{api_base_url}/{register}"
    int_val = reg_to_int(hex_value)
    logger.debug(f"Writing register {register}: {hex_value} ({int_val}) to {url}")
    try:
        async with session.post(url, json=hex_value, timeout=5) as response:
            response.raise_for_status()
            data = await response.json()
            success = data.get("status") == "0"
            if success:
                logger.debug(f"Successfully wrote register {register}")
            else:
                logger.warning(
                    f"Register {register} write returned non-zero status: {data.get('status')}"
                )
            return success
    except (aiohttp.ClientError, aiohttp.ClientResponseError) as e:
        logger.error(f"Error writing register {register}: {e}")
        return False
    except Exception as e:
        logger.error(
            f"Unexpected error writing register {register}: {e}", exc_info=True
        )
        return False


@with_simulator(simulator_write_flag_bit)
async def write_flag_bit(
    session: aiohttp.ClientSession,
    api_base_url: str,
    register: str,
    bit_index: int,
    state: bool,
    simulation_mode: bool | None = None,
) -> bool:
    """
    Write a single flag bit in a register using read-modify-write pattern.

    Args:
        session: aiohttp ClientSession
        api_base_url: Base URL for the heater API
        register: Register address (e.g., "0b55")
        bit_index: Bit index to modify (0-15)
        state: True to set bit, False to clear bit

    Returns:
        True if write succeeded, False otherwise
    """
    # Read current value
    hex_val = await read_register(session, api_base_url, register, simulation_mode)
    if hex_val is None:
        logger.error(f"Flag bit write failed: Could not read {register}")
        return False

    # Modify the bit
    current_int = reg_to_int(hex_val)
    new_int = set_bit(current_int, bit_index, state)
    old_bit = (current_int >> bit_index) & 1
    new_bit = 1 if state else 0

    logger.debug(
        f"Flag bit write: register {register}, bit {bit_index}: "
        f"{old_bit} → {new_bit} ({hex_val} / {current_int} → {int_to_reg(new_int)} / {new_int})"
    )

    # Only write if value actually changed
    if current_int == new_int:
        logger.debug(
            f"Flag bit {bit_index} in register {register} already in desired state"
        )
        return True

    new_hex = int_to_reg(new_int)
    return await write_register(
        session, api_base_url, register, new_hex, simulation_mode
    )
