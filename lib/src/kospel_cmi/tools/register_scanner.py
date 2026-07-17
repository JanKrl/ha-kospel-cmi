"""
Register range scanner for reverse-engineering heater registers.

Scans a range of registers from the device, applies multiple interpretation
parsers to each value, and outputs results in human-readable or YAML format.
"""

import argparse
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, TypedDict

import aiofiles
import yaml

from ..kospel.backend import RegisterBackend
from .cli_common import (
    add_backend_arguments,
    add_scan_arguments,
    backend_context,
)
from ..registers.decoders import decode_scaled_x10, decode_scaled_x100
from ..registers.utils import (
    get_bit,
    int_to_reg_address,
    reg_address_to_int,
    reg_to_int,
)

logger = logging.getLogger(__name__)

FORMAT_VERSION = "1"


class RegisterEntryDict(TypedDict):
    """Single register entry in scan result dict output."""

    hex: str
    raw_int: int
    scaled_x10: Optional[float]
    scaled_x100: Optional[float]
    bits: dict[int, bool]


class _ScanMetaRequired(TypedDict):
    """Required keys for scan metadata."""

    start_register: str
    count: int
    timestamp: str


class ScanMetaDict(_ScanMetaRequired, total=False):
    """Scan metadata with optional hide_empty and registers_shown."""

    hide_empty: bool
    registers_shown: int


class ScanResultDict(TypedDict):
    """Top-level dict structure returned by _result_to_dict."""

    format_version: str
    scan: ScanMetaDict
    registers: dict[str, RegisterEntryDict]


@dataclass
class RegisterInterpretation:
    """Parsed interpretation of a single register value."""

    register: str
    hex: str
    raw_int: int
    scaled_x10: Optional[float]
    scaled_x100: Optional[float]
    bits: dict[int, bool]


@dataclass
class RegisterScanResult:
    """Result of scanning a register range."""

    start_register: str
    count: int
    registers: list[RegisterInterpretation] = field(default_factory=list)


def _interpret_register(register: str, hex_val: str) -> RegisterInterpretation:
    """Apply parsers to a single register value."""
    raw_int = reg_to_int(hex_val)
    scaled_x10 = decode_scaled_x10(hex_val)
    scaled_x100 = decode_scaled_x100(hex_val)
    bits = {i: get_bit(raw_int, i) for i in range(16)}
    return RegisterInterpretation(
        register=register,
        hex=hex_val,
        raw_int=raw_int,
        scaled_x10=scaled_x10,
        scaled_x100=scaled_x100,
        bits=bits,
    )


async def scan_register_range(
    backend: RegisterBackend,
    start_register: str,
    count: int,
) -> RegisterScanResult:
    """
    Scan a range of registers and apply interpretation parsers.

    Args:
        backend: RegisterBackend (HttpRegisterBackend or YamlRegisterBackend).
        start_register: Starting register address (e.g. "0b00").
        count: Number of registers to read.

    Returns:
        RegisterScanResult with raw values and parsed interpretations.
    """
    raw_registers = await backend.read_registers(start_register, count)
    interpretations: list[RegisterInterpretation] = []
    start_int = reg_address_to_int(start_register)
    prefix = start_register[:2]

    for i in range(count):
        reg_int = start_int + i
        reg_str = int_to_reg_address(prefix, reg_int)
        hex_val = raw_registers.get(reg_str, "0000")
        interpretations.append(_interpret_register(reg_str, hex_val))

    return RegisterScanResult(
        start_register=start_register,
        count=count,
        registers=interpretations,
    )


def _is_empty_register(reg: RegisterInterpretation) -> bool:
    """Register is empty when hex is 0000."""
    return reg.hex == "0000"


def format_register_row(reg: RegisterInterpretation, first_col: str) -> str:
    """
    Format a single register row with shared display logic.

    Temperature, pressure, and bits (●/·, reverse bit order, 4-bit grouping)
    are formatted consistently. Caller supplies the first column (e.g. register
    address or label like "old"/"new").

    Args:
        reg: Register interpretation to format.
        first_col: First column content, already padded (e.g. f"{reg.register:<8}"
            or f"  {label:<6}").

    Returns:
        Formatted row string.
    """
    x10_str = f"{reg.scaled_x10:.1f}" if reg.scaled_x10 is not None else "—"
    x100_str = f"{reg.scaled_x100:.2f}" if reg.scaled_x100 is not None else "—"
    # ● = set, · = clear (visually scannable in large tables)
    bits_chars = "".join(
        "\u25CF" if reg.bits[i] else "\u00B7" for i in range(15, -1, -1)
    )
    bits_str = " ".join(bits_chars[i : i + 4] for i in range(0, 16, 4))
    return f"{first_col} {reg.hex:<6} {reg.raw_int:>7} {x10_str:>6} {x100_str:>6}  {bits_str}"


def format_scan_result(
    result: RegisterScanResult,
    *,
    include_empty: bool = False,
) -> str:
    """
    Format scan result as human-readable table.

    Args:
        result: Scan result from scan_register_range.
        include_empty: If False (default), omit registers with hex 0000.

    Returns:
        Formatted string for console output.
    """
    lines: list[str] = []
    end_int = reg_address_to_int(result.start_register) + result.count - 1
    prefix = result.start_register[:2]
    end_register = int_to_reg_address(prefix, end_int)

    if include_empty:
        displayed = result.registers
    else:
        displayed = [r for r in result.registers if not _is_empty_register(r)]

    if len(displayed) < result.count and not include_empty:
        lines.append(
            f"Register Scan: {result.start_register} - {end_register} "
            f"({len(displayed)} of {result.count} registers, empty hidden)"
        )
    else:
        lines.append(
            f"Register Scan: {result.start_register} - {end_register} "
            f"({len(displayed)} registers)"
        )
    lines.append("")

    if not displayed:
        lines.append("(no registers)")
        return "\n".join(lines)

    header = f"{'Register':<8} {'Hex':<6} {'Int':>7} {'×10':>6} {'×100':>6}  Bits"
    separator = (
        "-" * 8
        + " "
        + "-" * 6
        + " "
        + "-" * 7
        + " "
        + "-" * 6
        + " "
        + "-" * 6
        + "  "
        + "-" * 19
    )
    lines.append(header)
    lines.append(separator)

    for reg in displayed:
        row = format_register_row(reg, f"{reg.register:<8}")
        lines.append(row)

    return "\n".join(lines)


def _result_to_dict(
    result: RegisterScanResult,
    *,
    include_empty: bool = False,
) -> ScanResultDict:
    """Convert RegisterScanResult to a dict suitable for YAML serialization."""
    if include_empty:
        displayed = result.registers
    else:
        displayed = [r for r in result.registers if not _is_empty_register(r)]

    registers_dict: dict[str, RegisterEntryDict] = {}
    for reg in displayed:
        reg_data: RegisterEntryDict = {
            "hex": reg.hex,
            "raw_int": reg.raw_int,
            "scaled_x10": reg.scaled_x10,
            "scaled_x100": reg.scaled_x100,
            "bits": dict(sorted(reg.bits.items())),
        }
        registers_dict[reg.register] = reg_data

    scan_meta: ScanMetaDict = {
        "start_register": result.start_register,
        "count": result.count,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    if not include_empty:
        scan_meta["hide_empty"] = True
        scan_meta["registers_shown"] = len(displayed)

    return {
        "format_version": FORMAT_VERSION,
        "scan": scan_meta,
        "registers": registers_dict,
    }


def serialize_scan_result(
    result: RegisterScanResult,
    *,
    include_empty: bool = False,
) -> str:
    """
    Serialize scan result to YAML string.

    Output is human-readable and machine-parseable for future diff tools.

    Args:
        result: Scan result from scan_register_range.
        include_empty: If False (default), omit registers with hex 0000.

    Returns:
        YAML string.
    """
    data = _result_to_dict(result, include_empty=include_empty)
    return yaml.safe_dump(
        data,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )


async def write_scan_result(
    path: Path,
    result: RegisterScanResult,
    *,
    include_empty: bool = False,
) -> None:
    """
    Write scan result to a YAML file.

    Args:
        path: Output file path.
        result: Scan result from scan_register_range.
        include_empty: If False (default), omit registers with hex 0000.
    """
    content = serialize_scan_result(result, include_empty=include_empty)
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(content)


def _parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Scan a range of heater registers for reverse-engineering."
    )
    add_backend_arguments(parser)
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        metavar="FILE",
        help="Write results to file (YAML format)",
    )
    parser.add_argument(
        "--show-empty",
        action="store_true",
        help="Include registers with hex 0000 (default: hide them)",
    )
    add_scan_arguments(parser)
    return parser.parse_args()


async def _main_async() -> int:
    """Async main logic. Returns exit code."""
    args = _parse_args()

    cm = backend_context(args)
    if not cm:
        return 1

    async with cm as backend:
        scan_result = await scan_register_range(
            backend, args.start_register, args.count
        )

        include_empty = args.show_empty
        if args.output:
            out_path = Path(args.output)
            await write_scan_result(out_path, scan_result, include_empty=include_empty)
            print(f"Wrote scan to {out_path}")
        else:
            print(format_scan_result(scan_result, include_empty=include_empty))

    return 0


def main() -> None:
    """CLI entry point."""
    exit_code = asyncio.run(_main_async())
    raise SystemExit(exit_code)
