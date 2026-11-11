"""
YAML file-based integer MODBUS register read/write, analogous to modbus_api.py.
"""

import logging
from pathlib import Path

import aiofiles
import yaml

from ..exceptions import KospelWriteError

logger = logging.getLogger(__name__)


def _resolve_state_file(state_file: str) -> Path:
    """Resolve state_file: absolute as-is, relative under package data/."""
    path = Path(state_file)
    if path.is_absolute():
        return path
    component_dir = Path(__file__).parent.parent
    return (component_dir / "data" / state_file).resolve()


async def _load_registers(state_file: str) -> dict[int, int]:
    """Load integer MODBUS register state from YAML file."""
    path = _resolve_state_file(state_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        async with aiofiles.open(path, "r") as f:
            content = await f.read()
            raw = yaml.safe_load(content) or {}
            return {int(k): int(v) for k, v in raw.items()}
    except Exception as err:
        logger.warning("Could not load MODBUS state from %s: %s", path, err)
        return {}


async def _save_registers(state_file: str, registers: dict[int, int]) -> None:
    """Save integer MODBUS register state to YAML file."""
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
    except Exception as err:
        logger.error("Could not save MODBUS state to %s: %s", path, err)
        raise KospelWriteError(
            f"Could not save MODBUS register state to {path}"
        ) from err


async def read_registers(
    state_file: str,
    start_register: int,
    count: int,
) -> dict[int, int]:
    """Read a range of integer MODBUS registers from the YAML state file."""
    registers = await _load_registers(state_file)
    result = {
        addr: registers.get(addr, 0)
        for addr in range(start_register, start_register + count)
    }
    logger.debug(
        "[YAML MODBUS] READ registers %s..%s (%s registers)",
        start_register,
        start_register + count - 1,
        count,
    )
    return result


async def write_registers(
    state_file: str,
    values: dict[int, int],
) -> None:
    """Write one or more integer MODBUS registers to the YAML state file."""
    registers = await _load_registers(state_file)
    for reg, val in values.items():
        registers[int(reg)] = int(val) & 0xFFFF
    await _save_registers(state_file, registers)
    logger.debug("[YAML MODBUS] WRITE registers %s", values)


async def write_register(
    state_file: str,
    register: int,
    value: int,
) -> None:
    """Write a single integer MODBUS register to the YAML state file."""
    await write_registers(state_file, {register: value})
