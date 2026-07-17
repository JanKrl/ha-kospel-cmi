"""
Shared CLI argument parsing and backend creation for register scanner tools.

Used by register_scanner and live_scanner to avoid duplication of
--url/--yaml validation, backend instantiation, and cleanup logic.
"""

import argparse
import sys
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import aiohttp

from ..kospel.backend import (
    HttpRegisterBackend,
    RegisterBackend,
    YamlRegisterBackend,
)


def add_backend_arguments(parser: argparse.ArgumentParser) -> None:
    """
    Add --url and --yaml arguments to the parser.

    Args:
        parser: ArgumentParser to add arguments to.
    """
    parser.add_argument(
        "--url",
        type=str,
        help="HTTP mode: base URL (e.g. http://192.168.1.1/api/dev/65)",
    )
    parser.add_argument(
        "--yaml",
        dest="yaml_path",
        type=str,
        metavar="PATH",
        help="YAML mode: path to state file (for offline/dev)",
    )


def add_scan_arguments(parser: argparse.ArgumentParser) -> None:
    """
    Add start_register and count positional arguments to the parser.

    Args:
        parser: ArgumentParser to add arguments to.
    """
    parser.add_argument(
        "start_register",
        nargs="?",
        default="0b00",
        help="Starting register address (default: 0b00)",
    )
    parser.add_argument(
        "count",
        nargs="?",
        type=int,
        default=256,
        help="Number of registers to read (default: 256)",
    )


def _validate_backend_args(args: argparse.Namespace) -> bool:
    """Validate url/yaml args. Print error to stderr and return False on failure."""
    if args.url and args.yaml_path:
        print("Error: Use either --url or --yaml, not both.", file=sys.stderr)
        return False
    if not args.url and not args.yaml_path:
        print(
            "Error: Specify --url for HTTP mode or --yaml for YAML (offline) mode.",
            file=sys.stderr,
        )
        return False
    return True


@asynccontextmanager
async def _http_backend_context(args: argparse.Namespace) -> AsyncIterator[RegisterBackend]:
    """Async context manager for HTTP backend. Uses async with for ClientSession."""
    async with aiohttp.ClientSession() as session:
        assert args.url is not None  # validated by backend_context
        yield HttpRegisterBackend(session, args.url)


@asynccontextmanager
async def _yaml_backend_context(args: argparse.Namespace) -> AsyncIterator[RegisterBackend]:
    """Async context manager for YAML backend. No session to manage."""
    yaml_path = Path(args.yaml_path)
    if not yaml_path.is_absolute():
        yaml_path = Path.cwd() / yaml_path
    yield YamlRegisterBackend(str(yaml_path.resolve()))


def backend_context(
    args: argparse.Namespace,
) -> AbstractAsyncContextManager[RegisterBackend] | None:
    """
    Validate url/yaml args and return async context manager yielding backend.

    Args:
        args: Parsed arguments with url and yaml_path attributes.

    Returns:
        Async context manager on success. Use: async with backend_context(args) as backend.
        None on validation failure (error printed to stderr).

    Note:
        HTTP backend cleanup is handled by ClientSession context exit.
        YamlRegisterBackend has a no-op aclose; backend_context does not call it.
    """
    if not _validate_backend_args(args):
        return None

    if args.yaml_path:
        return _yaml_backend_context(args)
    return _http_backend_context(args)
