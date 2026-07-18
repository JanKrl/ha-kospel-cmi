"""Kospel HTTP API and discovery."""

from .discovery import (
    MODEL_NAMES,
    DeviceDetail,
    KospelDeviceInfo,
    discover_devices,
    probe_device,
)

__all__ = [
    "DeviceDetail",
    "KospelDeviceInfo",
    "MODEL_NAMES",
    "discover_devices",
    "probe_device",
]
