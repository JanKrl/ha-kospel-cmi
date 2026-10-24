"""
Backend abstractions for Kospel C.MI (hex string registers) and ModBus (integer registers).

- CmiBackend (HttpCmiBackend, YamlCmiBackend): 4-char hex register addresses and values.
  Aliases RegisterBackend, HttpRegisterBackend, YamlRegisterBackend are preserved for
  backward compatibility.
- ModbusBackend (HttpModbusBackend, YamlModbusBackend): decimal integer register
  addresses and 16-bit integer values, supporting atomic multi-register writes.
"""

import asyncio
import logging
from typing import Dict, Optional, Protocol, runtime_checkable

import aiohttp

from ..registers.utils import int_to_reg, reg_to_int, set_bit
from . import api as kospel_api
from . import modbus_api, modbus_simulator
from . import simulator as simulator_io

logger = logging.getLogger(__name__)


@runtime_checkable
class CmiBackend(Protocol):
    """Protocol for C.MI hex-string register read/write."""

    async def read_register(self, register: str) -> str:
        """Read a single register. Returns hex string; raises on HTTP/invalid data."""
        ...

    async def read_registers(
        self, start_register: str, count: int
    ) -> Dict[str, str]:
        """Read multiple registers. May return a partial dict; raises on transport failure."""
        ...

    async def write_register(self, register: str, hex_value: str) -> None:
        """Write a value. Raises on failure."""
        ...


class HttpCmiBackend:
    """Backend that uses the C.MI HTTP API to read/write hex registers."""

    _session: Optional[aiohttp.ClientSession]

    def __init__(
        self,
        session: aiohttp.ClientSession,
        api_base_url: str,
    ):
        self._session = session
        self._api_base_url = api_base_url

    async def read_register(self, register: str) -> str:
        """Read a single register from the device via HTTP."""
        return await kospel_api.read_register(
            self._session, self._api_base_url, register
        )

    async def read_registers(
        self, start_register: str, count: int
    ) -> Dict[str, str]:
        """Read multiple registers from the device via HTTP."""
        return await kospel_api.read_registers(
            self._session, self._api_base_url, start_register, count
        )

    async def write_register(self, register: str, hex_value: str) -> None:
        """Write a single register to the device via HTTP."""
        await kospel_api.write_register(
            self._session, self._api_base_url, register, hex_value
        )

    async def aclose(self) -> None:
        """Close the HTTP session and release resources (idempotent)."""
        if self._session is not None:
            await self._session.close()
            self._session = None


class YamlCmiBackend:
    """Backend that uses a YAML file for C.MI hex register state."""

    def __init__(self, state_file: str):
        self._state_file = state_file

    async def read_register(self, register: str) -> str:
        """Read a single register from the state file."""
        return await simulator_io.read_register(self._state_file, register)

    async def read_registers(
        self, start_register: str, count: int
    ) -> Dict[str, str]:
        """Read multiple registers from the state file."""
        return await simulator_io.read_registers(
            self._state_file, start_register, count
        )

    async def write_register(self, register: str, hex_value: str) -> None:
        """Write a single register to the state file."""
        await simulator_io.write_register(self._state_file, register, hex_value)

    async def aclose(self) -> None:
        """No-op: YAML backend uses open/close per operation."""
        pass


# Backward-compatible aliases
RegisterBackend = CmiBackend
HttpRegisterBackend = HttpCmiBackend
YamlRegisterBackend = YamlCmiBackend


@runtime_checkable
class ModbusBackend(Protocol):
    """Protocol for integer-addressed MODBUS-over-HTTP register read/write."""

    async def read_registers(
        self, start_register: int, count: int
    ) -> dict[int, int]:
        """Read `count` consecutive registers starting at `start_register`."""
        ...

    async def write_register(self, register: int, value: int) -> None:
        """Write a single 16-bit integer register."""
        ...

    async def write_registers(self, values: dict[int, int]) -> None:
        """Write one or more 16-bit integer registers atomically."""
        ...

    async def aclose(self) -> None:
        """Release any underlying transport resources."""
        ...


class HttpModbusBackend:
    """Backend that uses the Kospel MODBUS-over-HTTP API."""

    _session: Optional[aiohttp.ClientSession]

    def __init__(
        self,
        session: aiohttp.ClientSession,
        api_base_url: str,
    ) -> None:
        self._session = session
        self._api_base_url = api_base_url

    async def read_registers(
        self, start_register: int, count: int
    ) -> dict[int, int]:
        """Read multiple integer registers via HTTP."""
        return await modbus_api.read_registers(
            self._session, self._api_base_url, start_register, count
        )

    async def write_register(self, register: int, value: int) -> None:
        """Write a single integer register via HTTP."""
        await modbus_api.write_register(
            self._session, self._api_base_url, register, value
        )

    async def write_registers(self, values: dict[int, int]) -> None:
        """Write multiple integer registers via HTTP."""
        await modbus_api.write_registers(
            self._session, self._api_base_url, values
        )

    async def aclose(self) -> None:
        """Close the HTTP session and release resources (idempotent)."""
        if self._session is not None:
            await self._session.close()
            self._session = None


class YamlModbusBackend:
    """Backend that uses a YAML file for integer MODBUS register state."""

    def __init__(self, state_file: str) -> None:
        self._state_file = state_file

    async def read_registers(
        self, start_register: int, count: int
    ) -> dict[int, int]:
        """Read multiple integer registers from the YAML state file."""
        return await modbus_simulator.read_registers(
            self._state_file, start_register, count
        )

    async def write_register(self, register: int, value: int) -> None:
        """Write a single integer register to the YAML state file."""
        await modbus_simulator.write_register(
            self._state_file, register, value
        )

    async def write_registers(self, values: dict[int, int]) -> None:
        """Write multiple integer registers to the YAML state file."""
        await modbus_simulator.write_registers(self._state_file, values)

    async def aclose(self) -> None:
        """No-op for file-based YAML backend."""
        pass


async def write_flag_bit(
    backend: CmiBackend,
    register: str,
    bit_index: int,
    state: bool,
) -> None:
    """Write a single flag bit using read-modify-write on a CmiBackend."""
    hex_val = await backend.read_register(register)

    current_int = reg_to_int(hex_val)
    new_int = set_bit(current_int, bit_index, state)
    old_bit = (current_int >> bit_index) & 1
    new_bit = 1 if state else 0
    new_hex_val = int_to_reg(new_int)

    logger.debug(
        f"Flag bit write: register {register}, bit {bit_index}: "
        f"{old_bit} → {new_bit} ({hex_val} → {new_hex_val})"
    )

    if current_int == new_int:
        logger.debug(
            f"Flag bit {bit_index} in register {register} already in desired state"
        )
        return

    await backend.write_register(register, new_hex_val)


async def write_registers_sequential(
    backend: CmiBackend,
    registers: Dict[str, str],
    delay: float = 0.1,
) -> None:
    """Write multiple registers sequentially with a delay between writes."""
    for addr, hex_val in registers.items():
        await backend.write_register(addr, hex_val)
        if delay > 0:
            await asyncio.sleep(delay)
