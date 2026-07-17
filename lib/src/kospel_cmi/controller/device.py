"""
Device-specific class for Kospel C.MI Standard heater.

Explicit API: each setting is a property (read) or async setter method (write).
Writes happen immediately; no save() or batching.
"""

import logging
from typing import Any, ClassVar, Optional

from ..exceptions import (
    IncompleteRegisterRefreshError,
    RegisterMissingError,
)
from ..kospel.backend import RegisterBackend
from ..registers.decoders import (
    decode_heater_mode,
    decode_map,
    decode_raw_int,
    decode_scaled_x10,
    decode_scaled_x100,
)
from ..registers.encoders import (
    encode_heater_mode,
    encode_map,
    encode_raw_int,
    encode_scaled_x10,
)
from ..registers.enums import (
    ROOM_MODE_MANUAL,
    CwuMode,
    HeaterMode,
    HeatingCircuitActive,
    HeatingStatus,
    ValvePosition,
    WaterHeaterEnabled,
)
from ..registers.utils import int_to_reg_address


logger = logging.getLogger(__name__)

# Decoders for bit-flag settings (register + bit_index)
_decode_water_heater_enabled = decode_map(
    WaterHeaterEnabled.ENABLED, WaterHeaterEnabled.DISABLED
)
_decode_co_heating_active = decode_map(
    HeatingCircuitActive.ACTIVE, HeatingCircuitActive.INACTIVE
)
_decode_cwu_heating_active = decode_map(
    HeatingCircuitActive.ACTIVE, HeatingCircuitActive.INACTIVE
)
_decode_valve_position = decode_map(ValvePosition.CO, ValvePosition.DHW)

_encode_water_heater_enabled = encode_map(
    WaterHeaterEnabled.ENABLED, WaterHeaterEnabled.DISABLED
)

_EKCOM3_READ_REGISTERS: frozenset[str] = frozenset(
    {
        "0b2f",
        "0b30",
        "0b31",
        "0b32",
        "0b34",
        "0b35",
        "0b46",
        "0b48",
        "0b49",
        "0b4a",
        "0b4b",
        "0b4c",
        "0b4e",
        "0b4f",
        "0b51",
        "0b52",
        "0b55",
        "0b62",
        "0b66",
        "0b67",
        "0b68",
        "0b69",
        "0b6a",
        "0b6b",
        "0b6c",
        "0b6d",
        "0b6e",
        "0b6f",
        "0b70",
        "0b74",
        "0b8a",
        "0b8d",
    }
)


class EkcoM3:
    """Kospel Ekco M3 heater. Explicit API for all settings and sensors."""

    REQUIRED_REGISTERS: ClassVar[frozenset[str]] = _EKCOM3_READ_REGISTERS

    def __init__(
        self,
        backend: RegisterBackend,
        *,
        strict_refresh: bool = False,
    ) -> None:
        """Initialize with a register backend.

        Args:
            backend: Backend used for register read/write.
            strict_refresh: If True, ``refresh()`` requires every address in
                ``REQUIRED_REGISTERS`` in the batch response; otherwise it raises
                ``IncompleteRegisterRefreshError`` and leaves the cache unchanged.
        """
        self._backend = backend
        self._strict_refresh = strict_refresh
        self._registers: dict[str, str] = {}

    def _get_register(self, register: str) -> str:
        """Get register value from cache.

        Raises:
            RegisterMissingError: If the register was not in cache after load.
        """
        if register not in self._registers:
            raise RegisterMissingError(
                register,
                detail=(
                    "not in cache; call refresh() or load via from_registers()"
                ),
            )
        return self._registers[register]

    async def refresh(self) -> None:
        """Load registers from backend (batch read).

        Partial maps are stored as returned. On failure, the previous cache is left
        unchanged. With ``strict_refresh=True``,
        if the batch map omits any address in ``REQUIRED_REGISTERS``, raises
        ``IncompleteRegisterRefreshError`` and does not update the cache.

        Raises:
            IncompleteRegisterRefreshError: If ``strict_refresh`` is True and the
                batch response is missing required addresses.
            Exceptions from ``RegisterBackend.read_registers`` (transport errors or
                invalid hex from the device).
        """
        logger.info("Refreshing heater settings from backend")
        regs = await self._backend.read_registers("0b00", 256)
        if self._strict_refresh:
            present = frozenset(regs.keys())
            required = type(self).REQUIRED_REGISTERS
            if not required <= present:
                raise IncompleteRegisterRefreshError(
                    missing_registers=frozenset(required - present)
                )
        self._registers = regs
        logger.info("Heater settings refreshed successfully")

    def from_registers(self, registers: dict[str, str]) -> None:
        """Load pre-fetched register data. May be partial; missing keys fail on read."""
        self._registers = registers

    async def aclose(self) -> None:
        """Release backend resources (e.g. HTTP session). Idempotent."""
        aclose = getattr(self._backend, "aclose", None)
        if aclose is not None:
            await aclose()

    async def __aenter__(self) -> "EkcoM3":
        """Enter async context. Returns self."""
        return self

    async def __aexit__(self, *args: object) -> None:
        """Exit async context. Releases resources via aclose()."""
        await self.aclose()

    # --- Read-only properties ---

    @property
    def heater_mode(self) -> Optional[HeaterMode]:
        """Current heater mode (OFF, SUMMER, WINTER, PARTY, VACATION, MANUAL)."""
        return decode_heater_mode(self._get_register("0b55"))

    @property
    def room_mode(self) -> Optional[int]:
        """Room mode register (0b32). 64 = MANUAL when heater_mode=MANUAL."""
        return decode_raw_int(self._get_register("0b32"))

    @property
    def cwu_mode(self) -> Optional[int]:
        """CWU mode: 0=economy, 1=anti-freeze, 2=comfort."""
        return decode_raw_int(self._get_register("0b30"))

    @property
    def is_water_heater_enabled(self) -> Optional[WaterHeaterEnabled]:
        """Water heater enabled (bit 4 of 0b55)."""
        return _decode_water_heater_enabled(self._get_register("0b55"), 4)

    @property
    def is_co_heating_active(self) -> Optional[HeatingCircuitActive]:
        """CO heating circuit active (bit 7 of 0b51)."""
        return _decode_co_heating_active(self._get_register("0b51"), 7)

    @property
    def is_cwu_heating_active(self) -> Optional[HeatingCircuitActive]:
        """CWU heating circuit active (bit 8 of 0b51)."""
        return _decode_cwu_heating_active(self._get_register("0b51"), 8)

    @property
    def valve_position(self) -> Optional[ValvePosition]:
        """Valve position (bit 2 of 0b51)."""
        return _decode_valve_position(self._get_register("0b51"), 2)

    @property
    def manual_temperature(self) -> Optional[float]:
        """Manual temperature target (0b8d), °C."""
        return decode_scaled_x10(self._get_register("0b8d"))

    @property
    def room_temperature_economy(self) -> Optional[float]:
        """Room temperature economy setpoint (0b68), °C."""
        return decode_scaled_x10(self._get_register("0b68"))

    @property
    def room_temperature_comfort(self) -> Optional[float]:
        """Room temperature comfort setpoint (0b6a), °C."""
        return decode_scaled_x10(self._get_register("0b6a"))

    @property
    def room_temperature_comfort_plus(self) -> Optional[float]:
        """Room temperature comfort+ setpoint (0b6b), °C."""
        return decode_scaled_x10(self._get_register("0b6b"))

    @property
    def room_temperature_comfort_minus(self) -> Optional[float]:
        """Room temperature comfort- setpoint (0b69), °C."""
        return decode_scaled_x10(self._get_register("0b69"))

    @property
    def cwu_temperature_economy(self) -> Optional[float]:
        """CWU economy temperature (0b66), °C."""
        return decode_scaled_x10(self._get_register("0b66"))

    @property
    def cwu_temperature_comfort(self) -> Optional[float]:
        """CWU comfort temperature (0b67), °C."""
        return decode_scaled_x10(self._get_register("0b67"))

    @property
    def pressure(self) -> Optional[float]:
        """System pressure (0b4e), bar."""
        return decode_scaled_x100(self._get_register("0b4e"))

    @property
    def water_current_temperature(self) -> Optional[float]:
        """Current water temperature (0b4a), °C."""
        return decode_scaled_x10(self._get_register("0b4a"))

    @property
    def inlet_temperature(self) -> Optional[float]:
        """Inlet temperature (0b48), °C."""
        return decode_scaled_x10(self._get_register("0b48"))

    @property
    def outlet_temperature(self) -> Optional[float]:
        """Outlet temperature (0b49), °C."""
        return decode_scaled_x10(self._get_register("0b49"))

    @property
    def outside_temperature(self) -> Optional[float]:
        """Outside temperature (0b4c), °C."""
        return decode_scaled_x10(self._get_register("0b4c"))

    @property
    def outside_temperature_off(self) -> Optional[float]:
        """Outside temperature off threshold (0b74), °C."""
        return decode_scaled_x10(self._get_register("0b74"))

    @property
    def supply_setpoint(self) -> Optional[float]:
        """Supply setpoint (0b2f), °C."""
        return decode_scaled_x10(self._get_register("0b2f"))

    @property
    def room_setpoint(self) -> Optional[float]:
        """Room setpoint (0b31), °C."""
        return decode_scaled_x10(self._get_register("0b31"))

    @property
    def power(self) -> Optional[float]:
        """Current power (0b46), kW."""
        return decode_scaled_x10(self._get_register("0b46"))

    @property
    def boiler_max_power_index(self) -> Optional[int]:
        """Max boiler power step index (0b62). Use ``set_boiler_max_power_index``."""
        return decode_raw_int(self._get_register("0b62"))

    @property
    def available_boiler_max_power_settings(self) -> list[float]:
        """Available max power settings (kW) dynamically queried from the heater."""
        try:
            count = decode_raw_int(self._get_register("0b35"))
        except RegisterMissingError:
            return []
        
        if not count:
            return []
            
        options = []
        for i in range(count):
            reg_addr = int_to_reg_address("0b", 0x36 + i)
            try:
                val = decode_scaled_x10(self._get_register(reg_addr))
                if val is not None:
                    options.append(val)
            except RegisterMissingError:
                continue
                
        return options

    @property
    def boiler_max_power_kw(self) -> Optional[float]:
        """Max boiler power limit (0b34), kW. Firmware updates after index write."""
        return decode_scaled_x10(self._get_register("0b34"))

    @property
    def flow(self) -> Optional[float]:
        """Flow (0b4f)."""
        return decode_scaled_x10(self._get_register("0b4f"))

    @property
    def error_code(self) -> Optional[int]:
        """Error code (0b52)."""
        return decode_raw_int(self._get_register("0b52"))

    @property
    def work_mode(self) -> Optional[int]:
        """Work mode (0b8a)."""
        return decode_raw_int(self._get_register("0b8a"))

    @property
    def room_temperature(self) -> Optional[float]:
        """Current room temperature (0b4b), °C."""
        return decode_scaled_x10(self._get_register("0b4b"))

    @property
    def party_vacation_end_minute(self) -> Optional[int]:
        """Party/vacation end minute (0b6c)."""
        return decode_raw_int(self._get_register("0b6c"))

    @property
    def party_vacation_end_hour(self) -> Optional[int]:
        """Party/vacation end hour (0b6d)."""
        return decode_raw_int(self._get_register("0b6d"))

    @property
    def party_vacation_end_day(self) -> Optional[int]:
        """Party/vacation end day (0b6e)."""
        return decode_raw_int(self._get_register("0b6e"))

    @property
    def party_vacation_end_month(self) -> Optional[int]:
        """Party/vacation end month (0b6f)."""
        return decode_raw_int(self._get_register("0b6f"))

    @property
    def party_vacation_end_year(self) -> Optional[int]:
        """Party/vacation end year (0b70)."""
        return decode_raw_int(self._get_register("0b70"))

    # --- Computed properties ---

    @property
    def co_heating_status(self) -> HeatingStatus:
        """CO heating status from heater_mode, is_co_heating_active, power."""
        heater_mode = self.heater_mode
        co_active = self.is_co_heating_active
        power_val = self.power

        if heater_mode != HeaterMode.WINTER:
            return HeatingStatus.DISABLED

        if co_active != HeatingCircuitActive.ACTIVE:
            return HeatingStatus.IDLE

        if power_val is not None and power_val > 0:
            return HeatingStatus.RUNNING
        return HeatingStatus.IDLE

    @property
    def cwu_heating_status(self) -> HeatingStatus:
        """CWU heating status from mode, water heater, CWU active, and power."""
        heater_mode = self.heater_mode
        water_enabled = self.is_water_heater_enabled
        cwu_active = self.is_cwu_heating_active
        power_val = self.power

        if heater_mode == HeaterMode.SUMMER:
            return (
                HeatingStatus.RUNNING
                if cwu_active == HeatingCircuitActive.ACTIVE
                else HeatingStatus.IDLE
            )

        if heater_mode != HeaterMode.WINTER:
            return HeatingStatus.DISABLED

        if water_enabled != WaterHeaterEnabled.ENABLED:
            return HeatingStatus.DISABLED

        if cwu_active != HeatingCircuitActive.ACTIVE:
            return HeatingStatus.IDLE

        if power_val is not None and power_val > 0:
            return HeatingStatus.RUNNING
        return HeatingStatus.IDLE

    # --- Async setters (write immediately) ---

    async def set_heater_mode(self, value: HeaterMode) -> None:
        """Set heater mode. Writes 0b55. If MANUAL, also sets room_mode=64 (0b32)."""
        current = self._get_register("0b55")
        new_hex = encode_heater_mode(value, current_hex=current)
        if new_hex is None:
            raise ValueError("Failed to encode heater_mode")

        await self._backend.write_register("0b55", new_hex)
        self._registers["0b55"] = new_hex
        if value == HeaterMode.MANUAL:
            await self.set_room_mode(ROOM_MODE_MANUAL)

    async def set_room_mode(self, value: int) -> None:
        """Set room mode (0b32)."""
        hex_val = encode_raw_int(value, None)
        if hex_val is None:
            raise ValueError("Failed to encode room_mode")

        await self._backend.write_register("0b32", hex_val)
        self._registers["0b32"] = hex_val

    async def set_cwu_mode(self, value: int) -> None:
        """Set CWU mode (0b30). 0=economy, 1=anti-freeze, 2=comfort."""
        hex_val = encode_raw_int(value, None)
        if hex_val is None:
            raise ValueError("Failed to encode cwu_mode")

        await self._backend.write_register("0b30", hex_val)
        self._registers["0b30"] = hex_val

    async def set_boiler_max_power_index(
        self, value: int
    ) -> None:
        """Set max boiler power step index (0b62)."""
        idx = int(value)
        
        available = self.available_boiler_max_power_settings
        if available and not (0 <= idx < len(available)):
            raise ValueError(
                f"boiler_max_power_index {idx} is out of bounds for available settings {available}"
            )

        hex_val = encode_raw_int(idx, None)
        if hex_val is None:
            raise ValueError("Failed to encode boiler_max_power_index")

        await self._backend.write_register("0b62", hex_val)
        self._registers["0b62"] = hex_val

    async def set_is_water_heater_enabled(self, value: WaterHeaterEnabled) -> None:
        """Set water heater enabled (bit 4 of 0b55)."""
        current = self._get_register("0b55")
        new_hex = _encode_water_heater_enabled(value, 4, current)

        if new_hex is None:
            raise ValueError("Failed to encode is_water_heater_enabled")

        await self._backend.write_register("0b55", new_hex)
        self._registers["0b55"] = new_hex

    async def set_manual_temperature(self, value: float) -> None:
        """Set manual temperature target (0b8d), °C."""
        hex_val = encode_scaled_x10(value, None)
        if hex_val is None:
            raise ValueError("Failed to encode manual_temperature")

        await self._backend.write_register("0b8d", hex_val)
        self._registers["0b8d"] = hex_val

    async def set_outside_temperature_off(self, value: float) -> None:
        """Set outside temperature off threshold (0b74), °C."""
        await self._set_scaled_x10("0b74", value)

    async def set_room_temperature_economy(self, value: float) -> None:
        """Set room temperature economy (0b68), °C."""
        await self._set_scaled_x10("0b68", value)

    async def set_room_temperature_comfort(self, value: float) -> None:
        """Set room temperature comfort (0b6a), °C."""
        await self._set_scaled_x10("0b6a", value)

    async def set_room_temperature_comfort_plus(self, value: float) -> None:
        """Set room temperature comfort+ (0b6b), °C."""
        await self._set_scaled_x10("0b6b", value)

    async def set_room_temperature_comfort_minus(self, value: float) -> None:
        """Set room temperature comfort- (0b69), °C."""
        await self._set_scaled_x10("0b69", value)

    async def set_cwu_temperature_economy(self, value: float) -> None:
        """Set CWU economy temperature (0b66), °C."""
        await self._set_scaled_x10("0b66", value)

    async def set_cwu_temperature_comfort(self, value: float) -> None:
        """Set CWU comfort temperature (0b67), °C."""
        await self._set_scaled_x10("0b67", value)

    async def set_party_vacation_end_minute(self, value: int) -> None:
        """Set party/vacation end minute (0b6c)."""
        await self._set_raw_int("0b6c", value)

    async def set_party_vacation_end_hour(self, value: int) -> None:
        """Set party/vacation end hour (0b6d)."""
        await self._set_raw_int("0b6d", value)

    async def set_party_vacation_end_day(self, value: int) -> None:
        """Set party/vacation end day (0b6e)."""
        await self._set_raw_int("0b6e", value)

    async def set_party_vacation_end_month(self, value: int) -> None:
        """Set party/vacation end month (0b6f)."""
        await self._set_raw_int("0b6f", value)

    async def set_party_vacation_end_year(self, value: int) -> None:
        """Set party/vacation end year (0b70)."""
        await self._set_raw_int("0b70", value)

    async def _set_scaled_x10(self, register: str, value: float) -> None:
        """Helper: write scaled_x10 value to register."""
        hex_val = encode_scaled_x10(value, None)
        if hex_val is None:
            raise ValueError(f"Failed to encode scaled_x10 for {register}")

        await self._backend.write_register(register, hex_val)
        self._registers[register] = hex_val

    async def _set_raw_int(self, register: str, value: int) -> None:
        """Helper: write raw int to register."""
        hex_val = encode_raw_int(value, None)
        if hex_val is None:
            raise ValueError(f"Failed to encode raw_int for {register}")

        await self._backend.write_register(register, hex_val)
        self._registers[register] = hex_val

    # --- Helper methods ---

    async def set_manual_heating(self, temperature: float) -> None:
        """Set MANUAL mode and target temperature. Writes 0b55, 0b32, 0b8d."""
        await self.set_heater_mode(HeaterMode.MANUAL)
        await self.set_manual_temperature(temperature)

    async def set_water_mode(self, mode: CwuMode) -> None:
        """Set CWU water mode (which temperature source is active)."""
        if not isinstance(mode, CwuMode):
            raise TypeError(f"mode must be CwuMode, got {type(mode).__name__}")
        await self.set_cwu_mode(mode.value)

    async def set_water_comfort_temperature(self, temperature: float) -> None:
        """Set CWU comfort temperature (0b67), °C."""
        await self.set_cwu_temperature_comfort(temperature)

    async def set_water_economy_temperature(self, temperature: float) -> None:
        """Set CWU economy temperature (0b66), °C."""
        await self.set_cwu_temperature_economy(temperature)

    # --- Convenience methods for HA integration ---

    def get_setting(self, name: str) -> Any:
        """Get a setting by name. For compatibility with getattr.

        Returns Any because setting types vary (HeaterMode, float, int, etc.).
        Prefer direct property access (e.g. controller.heater_mode) for type safety.
        """
        return getattr(self, name, None)
