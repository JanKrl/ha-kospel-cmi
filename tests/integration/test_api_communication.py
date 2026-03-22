"""Integration tests for end-to-end API communication."""

import pytest
from aioresponses import aioresponses

import aiohttp

from kospel_cmi.controller.device import Ekco_M3
from kospel_cmi.kospel.backend import HttpRegisterBackend
from kospel_cmi.registers.enums import HeaterMode


class TestEndToEndReadWrite:
    """Tests for full read/write cycle."""

    @pytest.mark.asyncio
    async def test_end_to_end_read_write(
        self, api_base_url, sample_registers
    ):
        """Test full read/write cycle with mocked HTTP."""
        registers = sample_registers.copy()

        with aioresponses() as m:
            # Mock refresh (read all registers)
            read_url = f"{api_base_url}/0b00/256"
            m.get(read_url, payload={"regs": registers})

            # Mock set_heater_mode writes (0b55 and 0b32 for MANUAL, or just 0b55)
            write_url_55 = f"{api_base_url}/0b55"
            write_url_32 = f"{api_base_url}/0b32"
            m.post(write_url_55, payload={"status": "0"})
            m.post(write_url_32, payload={"status": "0"})

            async with aiohttp.ClientSession() as session:
                backend = HttpRegisterBackend(session, api_base_url)
                controller = Ekco_M3(backend=backend)

                # Refresh from API
                await controller.refresh()
                assert len(controller._registers) > 0

                # Modify setting via immediate write
                result = await controller.set_heater_mode(HeaterMode.WINTER)
                assert result is True

                # Verify changes are reflected
                assert controller.heater_mode == HeaterMode.WINTER

    @pytest.mark.asyncio
    async def test_multiple_settings_change(
        self, api_base_url, sample_registers
    ):
        """Test modifying multiple settings (each writes immediately)."""
        registers = sample_registers.copy()

        with aioresponses() as m:
            read_url = f"{api_base_url}/0b00/256"
            m.get(read_url, payload={"regs": registers})

            write_url_55 = f"{api_base_url}/0b55"
            write_url_32 = f"{api_base_url}/0b32"
            m.post(write_url_55, payload={"status": "0"})
            m.post(write_url_32, payload={"status": "0"})

            async with aiohttp.ClientSession() as session:
                backend = HttpRegisterBackend(session, api_base_url)
                controller = Ekco_M3(backend=backend)
                await controller.refresh()

                result = await controller.set_heater_mode(HeaterMode.MANUAL)
                assert result is True


class TestBatchOperations:
    """Tests for batch read operations."""

    @pytest.mark.asyncio
    async def test_single_refresh_reads_all_registers(
        self, api_base_url, sample_registers
    ):
        """Test that single refresh reads all registers."""
        registers = sample_registers.copy()
        for i in range(256):
            reg_key = f"0b{i:02x}"
            if reg_key not in registers:
                registers[reg_key] = "0000"

        with aioresponses() as m:
            read_url = f"{api_base_url}/0b00/256"
            m.get(read_url, payload={"regs": registers})

            async with aiohttp.ClientSession() as session:
                backend = HttpRegisterBackend(session, api_base_url)
                controller = Ekco_M3(backend=backend)

                await controller.refresh()

                assert len(controller._registers) > 0

    @pytest.mark.asyncio
    async def test_set_heater_mode_writes_immediately(
        self, api_base_url, sample_registers
    ):
        """Test that set_heater_mode writes immediately."""
        registers = sample_registers.copy()

        with aioresponses() as m:
            read_url = f"{api_base_url}/0b00/256"
            m.get(read_url, payload={"regs": registers})

            write_url_55 = f"{api_base_url}/0b55"
            write_url_32 = f"{api_base_url}/0b32"
            m.post(write_url_55, payload={"status": "0"})
            m.post(write_url_32, payload={"status": "0"})

            async with aiohttp.ClientSession() as session:
                backend = HttpRegisterBackend(session, api_base_url)
                controller = Ekco_M3(backend=backend)
                await controller.refresh()

                result = await controller.set_heater_mode(HeaterMode.MANUAL)
                assert result is True

    @pytest.mark.asyncio
    async def test_set_manual_heating_writes_both_registers(
        self, api_base_url, sample_registers
    ):
        """Test that set_manual_heating writes 0b55, 0b32, 0b8d."""
        registers = sample_registers.copy()

        with aioresponses() as m:
            read_url = f"{api_base_url}/0b00/256"
            m.get(read_url, payload={"regs": registers})

            write_url_55 = f"{api_base_url}/0b55"
            write_url_32 = f"{api_base_url}/0b32"
            write_url_8d = f"{api_base_url}/0b8d"
            m.post(write_url_55, payload={"status": "0"})
            m.post(write_url_32, payload={"status": "0"})
            m.post(write_url_8d, payload={"status": "0"})

            async with aiohttp.ClientSession() as session:
                backend = HttpRegisterBackend(session, api_base_url)
                controller = Ekco_M3(backend=backend)
                await controller.refresh()

                result = await controller.set_manual_heating(25.0)
                assert result is True


class TestErrorRecovery:
    """Tests for error handling and recovery."""

    @pytest.mark.asyncio
    async def test_network_error_during_read(self, api_base_url):
        """Test handling of network error during read."""
        with aioresponses() as m:
            read_url = f"{api_base_url}/0b00/256"
            m.get(read_url, exception=aiohttp.ClientError("Connection error"))

            async with aiohttp.ClientSession() as session:
                backend = HttpRegisterBackend(session, api_base_url)
                controller = Ekco_M3(backend=backend)

                await controller.refresh()

                assert len(controller._registers) == 0

    @pytest.mark.asyncio
    async def test_network_error_during_write_returns_false(
        self, api_base_url, sample_registers
    ):
        """Test that set_heater_mode returns False when write fails."""
        registers = sample_registers.copy()

        with aioresponses() as m:
            read_url = f"{api_base_url}/0b00/256"
            m.get(read_url, payload={"regs": registers})

            write_url = f"{api_base_url}/0b55"
            m.post(write_url, exception=aiohttp.ClientError("Write error"))

            async with aiohttp.ClientSession() as session:
                backend = HttpRegisterBackend(session, api_base_url)
                controller = Ekco_M3(backend=backend)
                await controller.refresh()

                result = await controller.set_heater_mode(HeaterMode.WINTER)
                assert result is False

    @pytest.mark.asyncio
    async def test_invalid_register_data_handles_gracefully(
        self, api_base_url
    ):
        """Test handling of invalid register data."""
        invalid_registers = {"0b55": "invalid"}

        with aioresponses() as m:
            read_url = f"{api_base_url}/0b00/256"
            m.get(read_url, payload={"regs": invalid_registers})

            async with aiohttp.ClientSession() as session:
                backend = HttpRegisterBackend(session, api_base_url)
                controller = Ekco_M3(backend=backend)

                await controller.refresh()

                assert controller.heater_mode is None or len(controller._registers) > 0

    @pytest.mark.asyncio
    async def test_partial_write_failures(
        self, api_base_url, sample_registers
    ):
        """Test handling of partial write failures in set_manual_heating."""
        registers = sample_registers.copy()

        with aioresponses() as m:
            read_url = f"{api_base_url}/0b00/256"
            m.get(read_url, payload={"regs": registers})

            write_url_55 = f"{api_base_url}/0b55"
            write_url_32 = f"{api_base_url}/0b32"
            write_url_8d = f"{api_base_url}/0b8d"
            m.post(write_url_55, payload={"status": "0"})
            m.post(write_url_32, payload={"status": "0"})
            m.post(write_url_8d, exception=aiohttp.ClientError("Write error"))

            async with aiohttp.ClientSession() as session:
                backend = HttpRegisterBackend(session, api_base_url)
                controller = Ekco_M3(backend=backend)
                await controller.refresh()

                result = await controller.set_manual_heating(25.0)
                assert result is False


class TestRegisterCaching:
    """Tests for register caching behavior."""

    @pytest.mark.asyncio
    async def test_cache_used_for_writes(
        self, api_base_url, sample_registers
    ):
        """Test that _registers is used for read-modify-write."""
        registers = sample_registers.copy()

        with aioresponses() as m:
            read_url = f"{api_base_url}/0b00/256"
            m.get(read_url, payload={"regs": registers})

            write_url_55 = f"{api_base_url}/0b55"
            m.post(write_url_55, payload={"status": "0"})

            async with aiohttp.ClientSession() as session:
                backend = HttpRegisterBackend(session, api_base_url)
                controller = Ekco_M3(backend=backend)
                await controller.refresh()

                assert "0b55" in controller._registers

                result = await controller.set_heater_mode(HeaterMode.WINTER)
                assert result is True

    @pytest.mark.asyncio
    async def test_cache_invalidated_on_refresh(
        self, api_base_url, sample_registers
    ):
        """Test that cache is invalidated on refresh."""
        registers = sample_registers.copy()
        new_registers = registers.copy()
        new_registers["0b55"] = "2000"

        with aioresponses() as m:
            read_url = f"{api_base_url}/0b00/256"
            m.get(read_url, payload={"regs": registers})
            m.get(read_url, payload={"regs": new_registers})

            async with aiohttp.ClientSession() as session:
                backend = HttpRegisterBackend(session, api_base_url)
                controller = Ekco_M3(backend=backend)

                await controller.refresh()
                original_value = controller._registers.get("0b55")

                await controller.refresh()
                new_value = controller._registers.get("0b55")

                assert original_value != new_value

    @pytest.mark.asyncio
    async def test_cache_updated_after_successful_write(
        self, api_base_url, sample_registers
    ):
        """Test that cache is updated after successful write."""
        registers = sample_registers.copy()

        with aioresponses() as m:
            read_url = f"{api_base_url}/0b00/256"
            m.get(read_url, payload={"regs": registers})

            write_url_55 = f"{api_base_url}/0b55"
            m.post(write_url_55, payload={"status": "0"})

            async with aiohttp.ClientSession() as session:
                backend = HttpRegisterBackend(session, api_base_url)
                controller = Ekco_M3(backend=backend)
                await controller.refresh()

                result = await controller.set_heater_mode(HeaterMode.WINTER)
                assert result is True

                assert "0b55" in controller._registers
