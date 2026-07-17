"""
CLI tool to discover Kospel C.MI devices on the network.

Scans one or more subnets and prints found devices with host, serial, model,
and API URL ready for use with other tools or integrations.
"""

import argparse
import asyncio

import aiohttp

from ..kospel.discovery import KospelDeviceInfo, discover_devices

# Common subnets to try when none specified (typical home/office networks)
DEFAULT_SUBNETS = [
    "192.168.1.0/24",
    "192.168.0.0/24",
    "192.168.101.0/24",
    "10.0.0.0/24",
]


def _format_devices(devices: list[KospelDeviceInfo]) -> str:
    """Format discovered devices for console output.

    When a device's ``devices`` list is empty (e.g. all /info requests failed),
    the model column shows "?" instead of raising IndexError.
    """
    if not devices:
        return "No Kospel C.MI devices found."

    lines = [
        "",
        f"Found {len(devices)} Kospel C.MI device(s):",
        "",
        f"{'Host':<18} {'Serial':<18} {'Model':<12} API URL",
        "-" * 80,
    ]
    for d in devices:
        model = d.devices[0].model_name if d.devices else "?"
        lines.append(f"{d.host:<18} {d.serial_number:<18} {model:<12} {d.api_base_url}")
    lines.append("")
    return "\n".join(lines)


def _parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Discover Kospel C.MI devices on the network. "
        "Scans specified subnet(s) or common defaults if none given."
    )
    parser.add_argument(
        "subnet",
        nargs="*",
        metavar="SUBNET",
        help="Subnet(s) in CIDR notation (e.g. 192.168.101.0/24). "
        "If omitted, scans common defaults: 192.168.1.0/24, 192.168.0.0/24, "
        "192.168.101.0/24, 10.0.0.0/24",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=3.0,
        metavar="SECS",
        help="Per-host probe timeout in seconds (default: 3)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=20,
        metavar="N",
        help="Max concurrent probes per subnet (default: 20)",
    )
    return parser.parse_args()


async def _main_async() -> int:
    """Async main logic. Returns exit code."""
    args = _parse_args()
    subnets = args.subnet if args.subnet else DEFAULT_SUBNETS

    print(f"Scanning {len(subnets)} subnet(s) for Kospel C.MI devices...")
    if not args.subnet:
        print(f"Using defaults: {', '.join(DEFAULT_SUBNETS)}")
    print()

    all_devices: list[KospelDeviceInfo] = []
    seen_hosts: set[str] = set()

    async with aiohttp.ClientSession() as session:
        for subnet in subnets:
            devices = await discover_devices(
                session,
                subnet,
                timeout=args.timeout,
                concurrency_limit=args.concurrency,
            )
            for d in devices:
                if d.host not in seen_hosts:
                    seen_hosts.add(d.host)
                    all_devices.append(d)

    print(_format_devices(all_devices))

    if all_devices:
        print("Use the API URL with other tools, e.g.:")
        print(f"  kospel-scan-registers --url {all_devices[0].api_base_url}")
        return 0
    return 1


def main() -> None:
    """CLI entry point."""
    exit_code = asyncio.run(_main_async())
    raise SystemExit(exit_code)
