"""Integration tests for water heater related registers (alpha.7)."""

import pytest

from kospel_cmi.controller.device import Ekco_M3


class TestWaterHeaterRegisters:
    """Tests for water_current_temperature and pressure decoding."""

    @pytest.mark.asyncio
    async def test_water_current_temperature_decoded(
        self, heater_controller_with_registers: Ekco_M3
    ) -> None:
        """water_current_temperature is decoded from register 0b4a."""
        controller = heater_controller_with_registers
        assert hasattr(controller, "water_current_temperature")
        # sample_registers has 0b4a: "a401" = 420 = 42.0°C
        assert controller.water_current_temperature == 42.0

    @pytest.mark.asyncio
    async def test_pressure_decoded_from_0b4e(
        self, heater_controller_with_registers: Ekco_M3
    ) -> None:
        """pressure is decoded from register 0b4e (scaled_x100)."""
        controller = heater_controller_with_registers
        assert hasattr(controller, "pressure")
        # sample_registers has 0b4e: "f401" = 500 = 5.00 bar
        assert controller.pressure == 5.0

    @pytest.mark.asyncio
    async def test_cwu_temperatures_decoded(
        self, heater_controller_with_registers: Ekco_M3
    ) -> None:
        """cwu_temperature_economy and cwu_temperature_comfort are decoded."""
        controller = heater_controller_with_registers
        assert controller.cwu_temperature_economy == 40.0
        assert controller.cwu_temperature_comfort == 45.0

    @pytest.mark.asyncio
    async def test_supply_setpoint_decoded(
        self, heater_controller_with_registers: Ekco_M3
    ) -> None:
        """supply_setpoint (CWU) is decoded from register 0b2f."""
        controller = heater_controller_with_registers
        assert controller.supply_setpoint == 45.0

    @pytest.mark.asyncio
    async def test_room_setpoint_decoded(
        self, heater_controller_with_registers: Ekco_M3
    ) -> None:
        """room_setpoint (CO) is decoded from register 0b31."""
        controller = heater_controller_with_registers
        assert controller.room_setpoint == 22.0
