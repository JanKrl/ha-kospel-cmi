"""
Register backend abstraction: Protocol and implementations (HTTP, YAML).

The controller depends only on RegisterBackend. Transport is chosen at construction:
HttpRegisterBackend(session, api_base_url) or YamlRegisterBackend(state_file).
Both delegate to function modules (api.py and simulator.py). write_flag_bit is
a standalone function that takes a backend as first argument (not a method on
the backend) so there is a single implementation for all backends.

Protocol is used so that any object with read_register/read_registers/write_register
can be passed; alternatives (e.g. NamedTuple of callables) would require the caller
to build closures for session/state_file. Protocol keeps "connection" state
inside the backend object and the interface explicit.
"""

import logging
from typing import Dict, Optional, Protocol, runtime_checkable

import aiohttp

from ..registers.utils import int_to_reg, reg_to_int, set_bit
from . import api as kospel_api
from . import simulator as simulator_io

logger = logging.getLogger(__name__)


@runtime_checkable
class RegisterBackend(Protocol):
    """Protocol for register read/write. No session, URL, or mode in method args."""

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


class HttpRegisterBackend:
    """Backend that uses HTTP API to read/write registers."""

    _session: Optional[aiohttp.ClientSession]

    def __init__(
        self,
        session: aiohttp.ClientSession,
        api_base_url: str,
    ):
        """
        Initialize HTTP backend.

        Args:
            session: aiohttp ClientSession for API calls
            api_base_url: Base URL for the heater API (e.g. "http://192.168.1.1/api/dev/65")
        """
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
        """Close the HTTP session and release resources.

        Safe to call multiple times (idempotent). After closing, the backend
        must not be used for further read/write operations.
        """
        if self._session is not None:
            await self._session.close()
            self._session = None


class YamlRegisterBackend:
    """Backend that uses YAML file for register state. Delegates to simulator module."""

    def __init__(self, state_file: str):
        """
        Initialize YAML backend.

        Args:
            state_file: Path to the YAML state file (required; no env var).
        """
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
        """No-op: YAML backend uses open/close per operation, no persistent resources."""
        pass


async def write_flag_bit(
    backend: RegisterBackend,
    register: str,
    bit_index: int,
    state: bool,
) -> None:
    """
    Write a single flag bit using read-modify-write.

    Takes backend as first argument (not a method on backend); single implementation
    for HTTP and YAML backends.

    Args:
        backend: Any RegisterBackend (HTTP or YAML).
        register: Register address (e.g. "0b55").
        bit_index: Bit index to modify (0-15).
        state: True to set bit, False to clear bit.

    Raises:
        Same as backend.read_register / backend.write_register on failure.
    """
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
