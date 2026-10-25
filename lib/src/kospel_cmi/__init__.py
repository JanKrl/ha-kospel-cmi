"""Kospel electric heater HTTP API client (C.MI and ModBus-over-HTTP)."""

from .controller.base import KospelController, WaterHeaterController
from .controller.device import EkcoM3
from .controller.ppe4 import Ppe4
from .exceptions import (
    IncompleteRegisterRefreshError,
    KospelConnectionError,
    KospelError,
    KospelWriteError,
    RegisterMissingError,
    RegisterReadError,
    RegisterValueInvalidError,
)
from .kospel.backend import (
    CmiBackend,
    HttpCmiBackend,
    HttpModbusBackend,
    HttpRegisterBackend,
    ModbusBackend,
    RegisterBackend,
    YamlCmiBackend,
    YamlModbusBackend,
    YamlRegisterBackend,
)
from .kospel.discovery import (
    MODEL_ID_PPE4,
    MODEL_NAMES,
    DeviceDetail,
    KospelDeviceInfo,
    discover_devices,
    probe_cmi_device,
    probe_device,
    probe_modbus_device,
)

__all__ = [
    "CmiBackend",
    "DeviceDetail",
    "EkcoM3",
    "HttpCmiBackend",
    "HttpModbusBackend",
    "HttpRegisterBackend",
    "IncompleteRegisterRefreshError",
    "KospelConnectionError",
    "KospelController",
    "KospelDeviceInfo",
    "KospelError",
    "KospelWriteError",
    "MODEL_ID_PPE4",
    "MODEL_NAMES",
    "ModbusBackend",
    "Ppe4",
    "RegisterBackend",
    "RegisterMissingError",
    "RegisterReadError",
    "RegisterValueInvalidError",
    "WaterHeaterController",
    "YamlCmiBackend",
    "YamlModbusBackend",
    "YamlRegisterBackend",
    "discover_devices",
    "probe_cmi_device",
    "probe_device",
    "probe_modbus_device",
]
