"""Kospel C.MI electric heater HTTP API client."""

from .exceptions import (
    IncompleteRegisterRefreshError,
    KospelConnectionError,
    KospelError,
    KospelWriteError,
    RegisterMissingError,
    RegisterReadError,
    RegisterValueInvalidError,
)
from .kospel.discovery import (
    DeviceDetail,
    KospelDeviceInfo,
    MODEL_NAMES,
    discover_devices,
    probe_device,
)

__all__ = [
    "DeviceDetail",
    "KospelDeviceInfo",
    "KospelError",
    "KospelConnectionError",
    "KospelWriteError",
    "IncompleteRegisterRefreshError",
    "MODEL_NAMES",
    "RegisterMissingError",
    "RegisterReadError",
    "RegisterValueInvalidError",
    "discover_devices",
    "probe_device",
]
