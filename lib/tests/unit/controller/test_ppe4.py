"""Unit tests for Ppe4 controller and controller protocols."""

import pytest

from kospel_cmi.controller.base import KospelController, WaterHeaterController
from kospel_cmi.controller.device import EkcoM3
from kospel_cmi.controller.ppe4 import Ppe4
from kospel_cmi.exceptions import (
    IncompleteRegisterRefreshError,
    RegisterMissingError,
)
from kospel_cmi.registers.enums import HeatingStatus


class MockModbusBackend:
    """In-memory mock for ModbusBackend."""

    def __init__(self, registers: dict[int, int] | None = None) -> None:
        self.registers: dict[int, int] = dict(registers or {})
        self.writes: list[dict[int, int]] = []
        self.closed: bool = False

    async def read_registers(self, start_register: int, count: int) -> dict[int, int]:
        return {
            addr: self.registers.get(addr, 0)
            for addr in range(start_register, start_register + count)
        }

    async def write_registers(self, values: dict[int, int]) -> None:
        self.writes.append(dict(values))
        self.registers.update(values)

    async def write_register(self, register: int, value: int) -> None:
        await self.write_registers({register: value})

    async def aclose(self) -> None:
        self.closed = True


class PartialModbusBackend(MockModbusBackend):
    """Returns only explicitly provided registers on read_registers."""

    async def read_registers(self, start_register: int, count: int) -> dict[int, int]:
        return {
            addr: self.registers[addr]
            for addr in range(start_register, start_register + count)
            if addr in self.registers
        }


SAMPLE_PPE4_REGISTERS: dict[int, int] = {
    1134: 185,  # inlet: 18.5 °C
    1135: 415,  # outlet: 41.5 °C
    1136: 220,  # internal: 22.0 °C
    1138: 12000,  # power: 12000 W (12.0 kW)
    1139: 54,  # flow: 5.4 L/min
    1140: 420,  # target: 42.0 °C
    1143: 24000,  # installed power: 24.0 kW
    1144: 18000,  # boiler max power limit: 18.0 kW
    1276: 12345,  # serial suffix
    1388: 550,  # max temperature limit: 55.0 °C
    1390: 1,  # active profile: 1 (Profile 1)
    1391: 480,  # manual setpoint: 48.0 °C
    1392: 380,  # profile 1: 38.0 °C
    1393: 420,  # profile 2: 42.0 °C
    1394: 500,  # profile 3: 50.0 °C
    1448: 0,
    1449: 0,
    1450: 3500,  # energy today lo word (3500 Wh = 3.5 kWh)
    1451: 0,  # energy today hi word
    1576: 0,
    1577: 0,
    1578: 857,  # water today lo word (85.7 L)
    1579: 0,  # water today hi word
}


class TestControllerProtocols:
    """Verify EkcoM3 and Ppe4 satisfy KospelController and WaterHeaterController."""

    def test_ppe4_implements_protocols(self) -> None:
        backend = MockModbusBackend(SAMPLE_PPE4_REGISTERS)
        controller = Ppe4(backend=backend)
        controller.from_registers(SAMPLE_PPE4_REGISTERS)
        assert isinstance(controller, KospelController)
        assert isinstance(controller, WaterHeaterController)
        assert controller.water_heater_writable is True
        assert controller.water_min_temperature == 20.0
        assert controller.water_max_temperature == 55.0

    def test_ekcom3_implements_protocols(self) -> None:
        from tests.unit.controller.test_device import MockRegisterBackend

        controller = EkcoM3(backend=MockRegisterBackend())
        controller.from_registers({"0b4a": "8c01", "0b2f": "8c01"})
        assert isinstance(controller, KospelController)
        assert isinstance(controller, WaterHeaterController)
        assert controller.water_heater_writable is False
        assert controller.water_min_temperature == 30.0
        assert controller.water_max_temperature == 65.0


class TestPpe4PropertiesAndRefresh:
    """Tests for Ppe4 register refresh and property decoding."""

    @pytest.mark.asyncio
    async def test_refresh_populates_all_properties(self) -> None:
        backend = MockModbusBackend(SAMPLE_PPE4_REGISTERS)
        controller = Ppe4(backend=backend, strict_refresh=True)
        await controller.refresh()

        assert controller.inlet_temperature == pytest.approx(18.5)
        assert controller.outlet_temperature == pytest.approx(41.5)
        assert controller.water_current_temperature == pytest.approx(41.5)
        assert controller.internal_temperature == pytest.approx(22.0)
        assert controller.power == pytest.approx(12.0)
        assert controller.dhw_heating_status == HeatingStatus.RUNNING
        assert controller.flow == pytest.approx(5.4)
        assert controller.target_temperature == pytest.approx(42.0)
        assert controller.supply_setpoint == pytest.approx(42.0)
        assert controller.installed_power_kw == pytest.approx(24.0)
        assert controller.boiler_max_power_kw == pytest.approx(18.0)
        assert controller.max_temperature == pytest.approx(55.0)
        assert controller.active_profile == 1
        assert controller.manual_temperature == pytest.approx(48.0)
        assert controller.get_profile_temperature(1) == pytest.approx(38.0)
        assert controller.get_profile_temperature(2) == pytest.approx(42.0)
        assert controller.get_profile_temperature(3) == pytest.approx(50.0)
        assert controller.energy_today_kwh == pytest.approx(3.5)
        assert controller.water_today_liters == pytest.approx(85.7)

    @pytest.mark.asyncio
    async def test_strict_refresh_raises_when_missing_required(self) -> None:
        backend = PartialModbusBackend({1134: 200})
        controller = Ppe4(backend=backend, strict_refresh=True)
        controller.from_registers({1135: 400})
        with pytest.raises(IncompleteRegisterRefreshError):
            await controller.refresh()
        assert controller._registers == {1135: 400}

    def test_unused_markers_return_none(self) -> None:
        controller = Ppe4(backend=MockModbusBackend())
        controller.from_registers({1134: 0xFFFF, 1135: 0xAAAA, 1138: 0})
        assert controller.inlet_temperature is None
        assert controller.outlet_temperature is None
        assert controller.dhw_heating_status == HeatingStatus.IDLE

    def test_32bit_counters_combine_low_and_high_words(self) -> None:
        controller = Ppe4(backend=MockModbusBackend())
        # 1 * 65536 + 4464 = 70000 Wh = 70.0 kWh
        # 1 * 65536 + 4464 = 70000 * 0.1L = 7000.0 L
        controller.from_registers(
            {1450: 4464, 1451: 1, 1578: 4464, 1579: 1}
        )
        assert controller.energy_today_kwh == pytest.approx(70.0)
        assert controller.water_today_liters == pytest.approx(7000.0)

    def test_missing_register_raises_register_missing_error(self) -> None:
        controller = Ppe4(backend=MockModbusBackend())
        with pytest.raises(RegisterMissingError):
            _ = controller.inlet_temperature


class TestPpe4Setters:
    """Tests for Ppe4 write methods."""

    @pytest.mark.asyncio
    async def test_set_manual_heating_writes_mode_and_setpoint_atomically(self) -> None:
        backend = MockModbusBackend(SAMPLE_PPE4_REGISTERS)
        controller = Ppe4(backend=backend)
        controller.from_registers(dict(SAMPLE_PPE4_REGISTERS))

        await controller.set_manual_heating(45.0)
        assert backend.writes == [{1390: 0, 1391: 450}]
        assert controller.active_profile == 0
        assert controller.manual_temperature == pytest.approx(45.0)

    @pytest.mark.asyncio
    async def test_set_active_profile_validates_and_writes(self) -> None:
        backend = MockModbusBackend(SAMPLE_PPE4_REGISTERS)
        controller = Ppe4(backend=backend)
        controller.from_registers(dict(SAMPLE_PPE4_REGISTERS))

        await controller.set_active_profile(2)
        assert backend.writes == [{1390: 2}]
        assert controller.active_profile == 2

        with pytest.raises(ValueError):
            await controller.set_active_profile(4)

    @pytest.mark.asyncio
    async def test_set_profile_temperature_validates_and_writes(self) -> None:
        backend = MockModbusBackend(SAMPLE_PPE4_REGISTERS)
        controller = Ppe4(backend=backend)
        controller.from_registers(dict(SAMPLE_PPE4_REGISTERS))

        await controller.set_profile_temperature(1, 39.5)
        assert backend.writes == [{1392: 395}]
        assert controller.get_profile_temperature(1) == pytest.approx(39.5)

        with pytest.raises(ValueError):
            await controller.set_profile_temperature(0, 40.0)
        with pytest.raises(ValueError):
            controller.get_profile_temperature(4)

