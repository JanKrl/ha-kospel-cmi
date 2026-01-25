"""
Simulator API implementation for development without actual heater access.

This module provides simulator implementations of API functions that maintain
register state in memory and persist it to a YAML file. It also provides
utilities for enabling and routing to simulation mode.
"""

import os
import inspect
import functools
import yaml
import aiofiles
from pathlib import Path
from typing import Dict, Optional, Callable, Any

import logging
from ..registers.utils import (
    reg_to_int,
    reg_address_to_int,
    set_bit,
    get_bit,
    int_to_reg,
)

logger = logging.getLogger(__name__)


def is_simulation_mode() -> bool:
    """Check if simulation mode is enabled via environment variable."""
    return os.getenv("SIMULATION_MODE", "").lower() in ("1", "true", "yes", "on")


def with_simulator(simulator_func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator that routes function calls to simulator implementation when simulation mode is enabled.

    The decorator automatically extracts the parameters needed by the simulator function
    from the original function call, skipping parameters like `session` and `api_base_url`
    that are only needed for real API calls.

    Args:
        simulator_func: The simulator function to call when simulation mode is enabled.
                       Must have a signature that is a subset of the decorated function's signature.

    Returns:
        Decorated function that routes to simulator or real implementation.

    Example:
        @with_simulator(simulator_read_register)
        async def read_register(session, api_base_url, register):
            # Real implementation
            ...
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        # Get parameter names from simulator function signature
        simulator_sig = inspect.signature(simulator_func)
        simulator_param_names = list(simulator_sig.parameters.keys())

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get parameter names from original function signature
            func_sig = inspect.signature(func)

            # Bind arguments to parameter names
            bound_args = func_sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Check simulation_mode parameter
            sim_mode = bound_args.arguments.get("simulation_mode")
            if sim_mode is None:
                # Fall back to environment variable for backward compatibility
                sim_mode = is_simulation_mode()
            # If sim_mode is explicitly True or False, use that value

            if sim_mode:
                logger.debug(f"Routing {func.__name__} to simulator implementation")
                # Extract only the parameters needed by the simulator function
                simulator_kwargs = {
                    param_name: bound_args.arguments[param_name]
                    for param_name in simulator_param_names
                    if param_name in bound_args.arguments
                }

                return await simulator_func(**simulator_kwargs)
            else:
                return await func(*args, **kwargs)

        return wrapper

    return decorator


class SimulatorRegisterState:
    """Manages simulator register state with file-based persistence."""

    def __init__(self, state_file: Optional[str] = None):
        """
        Initialize simulator register state.

        Args:
            state_file: Path to state file. If None, uses SIMULATION_STATE_FILE
                       env var or defaults to "simulation_state.yaml"
                       If an absolute path is provided, it's used as-is.
                       If a relative path is provided, it's prepended with "data/"
        """
        if state_file is None:
            state_file = os.getenv("SIMULATION_STATE_FILE", "simulation_state.yaml")

        yaml.add_representer(
            str, self._str_presenter
        )  # This ensures that all string keys and register values are quoted.

        # Handle absolute vs relative paths
        state_file_path = Path(state_file)
        if state_file_path.is_absolute():
            self.state_file = state_file_path
        else:
            component_dir_path = Path(__file__).parent.parent
            self.state_file = component_dir_path / "data" / state_file
        self.registers: Dict[str, str] = {}

        # Ensure parent directory exists
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

    async def _load_state(self) -> None:
        """Load register state from file if it exists."""
        try:
            async with aiofiles.open(self.state_file, "r") as f:
                content = await f.read()
                self.registers = yaml.safe_load(content) or {}
        except Exception as e:
            logger.warning(
                f"Could not load simulator state from {self.state_file}: {e}"
            )
            self.registers = {}

    async def _save_state(self) -> None:
        """Save register state to file."""
        try:
            content = yaml.safe_dump(
                self.registers,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=True,
            )
            async with aiofiles.open(self.state_file, "w") as f:
                await f.write(content)

        except Exception as e:
            logger.warning(f"Could not save simulator state to {self.state_file}: {e}")

    async def get_register(self, register: str) -> str:
        """
        Get register value, returning default "0000" if not in state.

        Args:
            register: Register address

        Returns:
            Hex string value (defaults to "0000" if register not in state)
        """
        await self._load_state()
        return self.registers.get(register, "0000")

    async def set_register(self, register: str, value: str) -> None:
        """
        Set register value and save to file.

        Args:
            register: Register address
            value: Hex string value
        """
        self.registers[register] = value
        await self._save_state()

    async def get_all_registers(self) -> Dict[str, str]:
        """Get all registers in state."""
        await self._load_state()
        return self.registers.copy()

    def _str_presenter(self, dumper, data) -> yaml.ScalarNode:
        """
        Custom representer to ensure all string keys and register values are quoted.

        Register values are 4-character hex strings (e.g., "2000", "0800").
        All other strings are also quoted for consistency.

        Args:
            dumper: YAML dumper
            data: String data

        Returns:
            YAML scalar node
        """
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style='"')


# Global simulator state instance
_simulator_state: Optional[SimulatorRegisterState] = None


async def _get_simulator_state() -> SimulatorRegisterState:
    """Get or create the global simulator state instance."""
    global _simulator_state
    if _simulator_state is None:
        _simulator_state = SimulatorRegisterState()
        await _simulator_state._load_state()
    return _simulator_state


async def simulator_read_register(register: str) -> Optional[str]:
    """
    Simulator implementation of read_register.

    Args:
        register: Register address

    Returns:
        Hex string value (defaults to "0000" if register not in state)
    """
    state = await _get_simulator_state()
    value = await state.get_register(register)

    int_val = reg_to_int(value)
    logger.debug(f"[SIMULATOR] READ register {register}: {value} ({int_val})")
    return value


async def simulator_read_registers(start_register: str, count: int) -> Dict[str, str]:
    """
    Simulator implementation of read_registers.

    Args:
        start_register: Starting register address
        count: Number of registers to read

    Returns:
        Dictionary of register addresses to hex values
    """
    state = await _get_simulator_state()

    result = {}
    start_int = reg_address_to_int(start_register)
    prefix = start_register[:2]

    for i in range(count):
        reg_int = start_int + i
        reg_str = f"{prefix}{reg_int:02x}"
        value = await state.get_register(reg_str)
        result[reg_str] = value

    end_register = list(result.keys())[-1] if result else start_register
    logger.debug(
        f"[SIMULATOR] READ registers {start_register} to {end_register} ({count} registers)"
    )
    return result


async def simulator_write_register(register: str, hex_value: str) -> bool:
    """
    Simulator implementation of write_register.

    Args:
        register: Register address
        hex_value: Hex string value to write

    Returns:
        True (always succeeds in simulator mode)
    """
    state = await _get_simulator_state()

    old_value = await state.get_register(register)
    old_int = reg_to_int(old_value)
    new_int = reg_to_int(hex_value)

    await state.set_register(register, hex_value)
    logger.debug(
        f"[SIMULATOR] WRITE register {register}: {old_value} → {hex_value} ({old_int} → {new_int})"
    )
    return True


async def simulator_write_flag_bit(register: str, bit_index: int, state: bool) -> bool:
    """
    Simulator implementation of write_flag_bit.

    Args:
        register: Register address
        bit_index: Bit index to modify
        state: True to set bit, False to clear bit

    Returns:
        True (always succeeds in simulator mode)
    """
    simulator_state = await _get_simulator_state()

    old_value = await simulator_state.get_register(register)
    old_int = reg_to_int(old_value)
    old_bit = get_bit(old_int, bit_index)

    new_int = set_bit(old_int, bit_index, state)
    new_value = int_to_reg(new_int)
    new_bit = get_bit(new_int, bit_index)

    await simulator_state.set_register(register, new_value)
    logger.debug(
        f"[SIMULATOR] BIT_WRITE register {register} bit {bit_index}: "
        f"{old_bit} → {new_bit} ({old_value} → {new_value}, {old_int} → {new_int})"
    )
    return True
