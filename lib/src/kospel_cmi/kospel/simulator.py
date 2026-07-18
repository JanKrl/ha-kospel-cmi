"""
YAML file-based register read/write. Function module, analogous to api.py (HTTP).

All functions take state_file as the first parameter. No classes; operations
perform load/modify/save on the file.
"""

import logging
from pathlib import Path
from typing import Dict

import aiofiles
import yaml

from ..exceptions import KospelWriteError
from ..registers.utils import int_to_reg_address, reg_address_to_int, reg_to_int

logger = logging.getLogger(__name__)

# Ensure YAML output quotes string keys and values (register hex format)
def _quote_str(dumper: yaml.Dumper, data: str) -> yaml.ScalarNode:
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style='"')


yaml.add_representer(str, _quote_str)


def _resolve_state_file(state_file: str) -> Path:
    """Resolve state_file: absolute as-is, relative under package data/."""
    path = Path(state_file)
    if path.is_absolute():
        return path
    component_dir = Path(__file__).parent.parent
    return (component_dir / "data" / state_file).resolve()


def _str_representer(dumper: yaml.Dumper, data: str) -> yaml.ScalarNode:
    """Quote all strings in YAML output (register hex values and keys)."""
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style='"')


async def _load_registers(state_file: str) -> Dict[str, str]:
    """Load register state from YAML file. Returns empty dict on missing/error."""
    path = _resolve_state_file(state_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        async with aiofiles.open(path, "r") as f:
            content = await f.read()
            return yaml.safe_load(content) or {}
    except Exception as e:
        logger.warning(f"Could not load state from {path}: {e}")
        return {}


async def _save_registers(state_file: str, registers: Dict[str, str]) -> None:
    """Save register state to YAML file."""
    path = _resolve_state_file(state_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        content = yaml.safe_dump(
            registers,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=True,
        )
        async with aiofiles.open(path, "w") as f:
            await f.write(content)
    except Exception as e:
        logger.error("Could not save state to %s: %s", path, e)
        raise KospelWriteError(f"Could not save register state to {path}") from e


async def read_register(state_file: str, register: str) -> str:
    """
    Read a single register from the YAML state file.

    Args:
        state_file: Path to the YAML state file (required).
        register: Register address (e.g. "0b55").

    Returns:
        Hex string value (defaults to "0000" if register not in file).
    """
    registers = await _load_registers(state_file)
    value = registers.get(register, "0000")
    int_val = reg_to_int(value)
    logger.debug(f"[YAML] READ register {register}: {value} ({int_val})")
    return value


async def read_registers(
    state_file: str,
    start_register: str,
    count: int,
) -> Dict[str, str]:
    """
    Read multiple registers from the YAML state file.

    Args:
        state_file: Path to the YAML state file.
        start_register: Starting register address (e.g. "0b00").
        count: Number of registers to read.

    Returns:
        Dictionary mapping register addresses to hex values.
    """
    registers = await _load_registers(state_file)
    start_int = reg_address_to_int(start_register)
    prefix = start_register[:2]
    result: Dict[str, str] = {}
    for i in range(count):
        reg_int = start_int + i
        reg_str = int_to_reg_address(prefix, reg_int)
        result[reg_str] = registers.get(reg_str, "0000")
    end_register = list(result.keys())[-1] if result else start_register
    logger.debug(
        f"[YAML] READ registers {start_register} to {end_register} ({count} registers)"
    )
    return result


async def write_register(
    state_file: str,
    register: str,
    hex_value: str,
) -> None:
    """
    Write a single register to the YAML state file.

    Args:
        state_file: Path to the YAML state file.
        register: Register address (e.g. "0b55").
        hex_value: Hex string value to write.

    Raises:
        KospelWriteError: If the state file could not be written.
    """
    registers = await _load_registers(state_file)
    old_value = registers.get(register, "0000")
    old_int = reg_to_int(old_value)
    new_int = reg_to_int(hex_value)
    registers[register] = hex_value
    await _save_registers(state_file, registers)
    logger.debug(
        f"[YAML] WRITE register {register}: {old_value} → {hex_value} "
        f"({old_int} → {new_int})"
    )
