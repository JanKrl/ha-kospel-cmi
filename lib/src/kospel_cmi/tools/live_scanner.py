"""
Live register scanner for reverse-engineering heater registers.

Polls registers periodically and outputs only changes with timestamps.
Designed for recording sessions when changing settings via the manufacturer UI.
"""

import argparse
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiofiles
import yaml

from ..kospel.backend import RegisterBackend
from .cli_common import (
    add_backend_arguments,
    add_scan_arguments,
    backend_context,
)
from ..registers.utils import int_to_reg_address, reg_address_to_int
from .register_scanner import (
    RegisterInterpretation,
    RegisterScanResult,
    _is_empty_register,
    format_register_row,
    format_scan_result,
    scan_register_range,
)

logger = logging.getLogger(__name__)


def _format_reg_row(
    reg: RegisterInterpretation,
    label: str,
) -> str:
    """Format a single register row with label (old/new)."""
    return format_register_row(reg, f"  {label:<6}")


def _diff_scans(
    prev: dict[str, RegisterInterpretation],
    curr: RegisterScanResult,
) -> list[tuple[RegisterInterpretation, RegisterInterpretation]]:
    """
    Return pairs (old, new) for registers where hex changed.

    Args:
        prev: Previous state keyed by register address.
        curr: Current scan result.

    Returns:
        List of (old_interpretation, new_interpretation) for changed registers.
    """
    changes: list[tuple[RegisterInterpretation, RegisterInterpretation]] = []
    for reg in curr.registers:
        old_reg = prev.get(reg.register)
        if old_reg is None:
            continue
        if old_reg.hex != reg.hex:
            changes.append((old_reg, reg))
    return changes


def format_changes(
    changes: list[tuple[RegisterInterpretation, RegisterInterpretation]],
    timestamp: datetime,
) -> str:
    """
    Format change list as human-readable output (two rows per register).

    Each changed register is shown as two consecutive rows (old, then new)
    with register address as header and separator between groups.

    Args:
        changes: List of (old, new) register pairs.
        timestamp: When the changes were detected.

    Returns:
        Formatted string for console output.
    """
    if not changes:
        return ""

    ts_str = timestamp.astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
    lines: list[str] = []
    lines.append(f"{ts_str} - {len(changes)} change(s)")
    lines.append("")

    sep = "─" * 60
    for i, (old_reg, new_reg) in enumerate(changes):
        lines.append(old_reg.register)
        lines.append(_format_reg_row(old_reg, "old"))
        lines.append(_format_reg_row(new_reg, "new"))
        if i < len(changes) - 1:
            lines.append(sep)
    lines.append("")

    return "\n".join(lines)


def serialize_changes(
    changes: list[tuple[RegisterInterpretation, RegisterInterpretation]],
    timestamp: datetime,
) -> str:
    """
    Serialize change list to YAML block for file append.

    Args:
        changes: List of (old, new) register pairs.
        timestamp: When the changes were detected.

    Returns:
        YAML string (document with --- separator for appending).
    """
    if not changes:
        return ""

    ts_str = timestamp.astimezone().isoformat()
    change_list: list[dict] = []
    for old_reg, new_reg in changes:
        change_list.append(
            {
                "register": old_reg.register,
                "old_hex": old_reg.hex,
                "new_hex": new_reg.hex,
                "old_int": old_reg.raw_int,
                "new_int": new_reg.raw_int,
                "old_scaled_x10": old_reg.scaled_x10,
                "new_scaled_x10": new_reg.scaled_x10,
                "old_scaled_x100": old_reg.scaled_x100,
                "new_scaled_x100": new_reg.scaled_x100,
            }
        )

    data = {"timestamp": ts_str, "changes": change_list}
    block = yaml.safe_dump(
        data,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )
    return "\n---\n" + block


async def run_live_scan(
    backend: RegisterBackend,
    start_register: str,
    count: int,
    interval: float,
    output_path: Optional[Path],
    include_empty: bool,
) -> None:
    """
    Run live scan loop: initial scan, then poll and output changes.

    Args:
        backend: RegisterBackend for reading.
        start_register: Starting register address.
        count: Number of registers to scan.
        interval: Poll interval in seconds.
        output_path: If set, append change events to this file.
        include_empty: Include empty registers in initial state.
    """
    result = await scan_register_range(backend, start_register, count)
    prev: dict[str, RegisterInterpretation] = {
        reg.register: reg for reg in result.registers
    }

    end_int = reg_address_to_int(start_register) + count - 1
    prefix = start_register[:2]
    end_register = int_to_reg_address(prefix, end_int)

    print(f"Live Scan: {start_register} - {end_register} (polling every {interval}s)")
    initial_count = len(
        [r for r in result.registers if include_empty or not _is_empty_register(r)]
    )
    ts_initial = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
    print(f"{ts_initial} - Initial state ({initial_count} registers)")
    print()
    print(format_scan_result(result, include_empty=include_empty))

    try:
        while True:
            await asyncio.sleep(interval)
            result = await scan_register_range(backend, start_register, count)
            changes = _diff_scans(prev, result)

            if changes:
                ts = datetime.now().astimezone()
                formatted = format_changes(changes, ts)
                print(formatted)

                if output_path:
                    yaml_block = serialize_changes(changes, ts)
                    async with aiofiles.open(output_path, "a", encoding="utf-8") as f:
                        await f.write(yaml_block)

            for reg in result.registers:
                prev[reg.register] = reg
    except asyncio.CancelledError:
        pass


def _parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Live scan: poll registers and show only changes."
    )
    add_backend_arguments(parser)
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        metavar="FILE",
        help="Append change events to file (YAML format)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        metavar="SECS",
        help="Poll interval in seconds (default: 2)",
    )
    parser.add_argument(
        "--show-empty",
        action="store_true",
        help="Include empty registers in initial state",
    )
    add_scan_arguments(parser)
    return parser.parse_args()


async def _main_async() -> int:
    """Async main logic. Returns exit code."""
    args = _parse_args()

    cm = backend_context(args)
    if not cm:
        return 1

    output_path = Path(args.output) if args.output else None

    try:
        async with cm as backend:
            await run_live_scan(
                backend=backend,
                start_register=args.start_register,
                count=args.count,
                interval=args.interval,
                output_path=output_path,
                include_empty=args.show_empty,
            )
    except asyncio.CancelledError:
        return 130

    return 0


def main() -> None:
    """CLI entry point."""
    try:
        exit_code = asyncio.run(_main_async())
    except KeyboardInterrupt:
        exit_code = 130  # Standard exit code for SIGINT (128 + 2)
    raise SystemExit(exit_code)
