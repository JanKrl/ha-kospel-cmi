"""
Common controller protocols and capability interfaces for Kospel devices.
"""

from typing import Optional, Protocol, runtime_checkable


@runtime_checkable
class KospelController(Protocol):
    """Common lifecycle and capability protocol for all Kospel device controllers."""

    @property
    def water_heater_writable(self) -> bool:
        """True if water heater target temperature and operation mode are writable."""
        ...

    async def refresh(self) -> None:
        """Refresh register state from the underlying backend."""
        ...

    async def aclose(self) -> None:
        """Release backend resources (e.g. HTTP session)."""
        ...


@runtime_checkable
class WaterHeaterController(KospelController, Protocol):
    """Protocol for controllers exposing domestic hot water (DHW) state and controls."""

    @property
    def water_current_temperature(self) -> Optional[float]:
        """Current hot water temperature (°C)."""
        ...

    @property
    def supply_setpoint(self) -> Optional[float]:
        """Effective hot water target temperature (°C)."""
        ...

    @property
    def water_min_temperature(self) -> float:
        """Minimum allowed hot water target temperature (°C)."""
        ...

    @property
    def water_max_temperature(self) -> float:
        """Maximum allowed hot water target temperature (°C)."""
        ...
