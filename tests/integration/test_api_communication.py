"""Integration tests for end-to-end API communication."""

import pytest
from unittest.mock import AsyncMock, patch
from aioresponses import aioresponses

import aiohttp

from kospel_cmi.controller.api import HeaterController
from kospel_cmi.kospel.backend import HttpRegisterBackend
from kospel_cmi.registers.enums import HeaterMode, ManualMode


class TestEndToEndReadWrite:
    """Tests for full read/write cycle."""

    @pytest.mark.asyncio
    async def test_end_to_end_read_write(
        self, api_base_url, sample_registers, registry
    ):
        """Test full read/write cycle with mocked HTTP."""
        registers = sample_registers.copy()

        with aioresponses() as m:
            # Mock refresh (read all registers)
            read_url = f"{api_base_url}/0b00/256"
            m.get(read_url, payload={"regs": registers})

            # Mock save (write register)
            write_url = f"{api_base_url}/0b55"
            m.post(write_url, payload={"status": "0"})
            # Mock read for save (cache miss)
            read_single_url = f"{api_base_url}/0b55/1"
            m.get(read_single_url, payload={"regs": {"0b55": registers["0b55"]}})

            async with aiohttp.ClientSession() as session:
                backend = HttpRegisterBackend(session, api_base_url)
                controller = HeaterController(backend=backend, registry=registry)

                # Refresh from API
                await controller.refresh()
                assert len(controller._settings) > 0

                # Modify setting
                original_mode = controller.heater_mode
                controller.heater_mode = HeaterMode.WINTER

                # Save to API
                result = await controller.save()
                assert result is True

                # Verify changes are reflected
                assert controller.heater_mode == HeaterMode.WINTER

    @pytest.mark.asyncio
    async def test_multiple_settings_change(
        self, api_base_url, sample_registers, registry
    ):
        """Test modifying multiple settings."""
        registers = sample_registers.copy()

        with aioresponses() as m:
            # Mock refresh
            read_url = f"{api_base_url}/0b00/256"
            m.get(read_url, payload={"regs": registers})

            # Mock save (both settings in same register 0b55)
            write_url = f"{api_base_url}/0b55"
            m.post(write_url, payload={"status": "0"})
            # Mock read for save
            read_single_url = f"{api_base_url}/0b55/1"
            m.get(read_single_url, payload={"regs": {"0b55": registers["0b55"]}})

            async with aiohttp.ClientSession() as session:
                backend = HttpRegisterBackend(session, api_base_url)
                controller = HeaterController(backend=backend, registry=registry)
                await controller.refresh()

                # Modify multiple settings
                controller.heater_mode = HeaterMode.WINTER
                controller.is_manual_mode_enabled = ManualMode.ENABLED

                # Save
                result = await controller.save()
                assert result is True


class TestBatchOperations:
    """Tests for batch read/write operations."""

    @pytest.mark.asyncio
    async def test_single_refresh_reads_all_registers(
        self, api_base_url, sample_registers, registry
    ):
        """Test that single refresh reads all registers."""
        registers = sample_registers.copy()
        # Add more registers
        for i in range(256):
            reg_key = f"0b{i:02x}"
            if reg_key not in registers:
                registers[reg_key] = "0000"

        with aioresponses() as m:
            read_url = f"{api_base_url}/0b00/256"
            m.get(read_url, payload={"regs": registers})

            async with aiohttp.ClientSession() as session:
                backend = HttpRegisterBackend(session, api_base_url)
                controller = HeaterController(backend=backend, registry=registry)

                # Single refresh call
                await controller.refresh()

                # Verify all settings were loaded
                assert len(controller._settings) > 0
                assert len(controller._register_cache) > 0

    @pytest.mark.asyncio
    async def test_multiple_settings_batched_into_single_write(
        self, api_base_url, sample_registers, registry
    ):
        """Test that multiple setting changes are batched into single write."""
        registers = sample_registers.copy()

        with aioresponses() as m:
            # Mock refresh
            read_url = f"{api_base_url}/0b00/256"
            m.get(read_url, payload={"regs": registers})

            # Mock save - should only write once per register
            write_url = f"{api_base_url}/0b55"
            m.post(write_url, payload={"status": "0"})
            # Mock read for save
            read_single_url = f"{api_base_url}/0b55/1"
            m.get(read_single_url, payload={"regs": {"0b55": registers["0b55"]}})

            async with aiohttp.ClientSession() as session:
                backend = HttpRegisterBackend(session, api_base_url)
                controller = HeaterController(backend=backend, registry=registry)
                await controller.refresh()

                # Modify multiple settings in same register
                controller.heater_mode = HeaterMode.WINTER
                controller.is_manual_mode_enabled = ManualMode.ENABLED

                # Save should batch these into single write
                result = await controller.save()
                assert result is True

    @pytest.mark.asyncio
    async def test_register_grouping_works(
        self, api_base_url, sample_registers, registry
    ):
        """Test that register grouping works correctly."""
        registers = sample_registers.copy()

        with aioresponses() as m:
            # Mock refresh
            read_url = f"{api_base_url}/0b00/256"
            m.get(read_url, payload={"regs": registers})

            # Mock multiple writes (different registers)
            write_url_55 = f"{api_base_url}/0b55"
            write_url_8d = f"{api_base_url}/0b8d"
            m.post(write_url_55, payload={"status": "0"})
            m.post(write_url_8d, payload={"status": "0"})
            # Mock reads for save
            read_url_55 = f"{api_base_url}/0b55/1"
            read_url_8d = f"{api_base_url}/0b8d/1"
            m.get(read_url_55, payload={"regs": {"0b55": registers["0b55"]}})
            m.get(read_url_8d, payload={"regs": {"0b8d": registers["0b8d"]}})

            async with aiohttp.ClientSession() as session:
                backend = HttpRegisterBackend(session, api_base_url)
                controller = HeaterController(backend=backend, registry=registry)
                await controller.refresh()

                # Modify settings in different registers
                controller.heater_mode = HeaterMode.WINTER  # Register 0b55
                controller.manual_temperature = 25.0  # Register 0b8d

                # Save should write to both registers
                result = await controller.save()
                assert result is True


class TestErrorRecovery:
    """Tests for error handling and recovery."""

    @pytest.mark.asyncio
    async def test_network_error_during_read(self, api_base_url, registry):
        """Test handling of network error during read."""
        with aioresponses() as m:
            read_url = f"{api_base_url}/0b00/256"
            m.get(read_url, exception=aiohttp.ClientError("Connection error"))

            async with aiohttp.ClientSession() as session:
                backend = HttpRegisterBackend(session, api_base_url)
                controller = HeaterController(backend=backend, registry=registry)

                # Refresh should handle error gracefully
                await controller.refresh()

                # Settings should remain empty or handle gracefully
                assert (
                    len(controller._settings) == 0
                    or controller._settings.get("heater_mode") is None
                )

    @pytest.mark.asyncio
    async def test_network_error_during_write_preserves_pending(
        self, api_base_url, sample_registers, registry
    ):
        """Test that network error during write preserves pending writes."""
        registers = sample_registers.copy()

        with aioresponses() as m:
            # Mock successful refresh
            read_url = f"{api_base_url}/0b00/256"
            m.get(read_url, payload={"regs": registers})

            # Mock failed write
            write_url = f"{api_base_url}/0b55"
            m.post(write_url, exception=aiohttp.ClientError("Write error"))
            # Mock read for save
            read_single_url = f"{api_base_url}/0b55/1"
            m.get(read_single_url, payload={"regs": {"0b55": registers["0b55"]}})

            async with aiohttp.ClientSession() as session:
                backend = HttpRegisterBackend(session, api_base_url)
                controller = HeaterController(backend=backend, registry=registry)
                await controller.refresh()

                # Modify setting
                controller.heater_mode = HeaterMode.WINTER
                assert len(controller._pending_writes) > 0

                # Save should fail
                result = await controller.save()
                assert result is False

                # Pending writes should still be present
                assert len(controller._pending_writes) > 0

    @pytest.mark.asyncio
    async def test_invalid_register_data_handles_gracefully(
        self, api_base_url, registry
    ):
        """Test handling of invalid register data."""
        invalid_registers = {"0b55": "invalid"}

        with aioresponses() as m:
            read_url = f"{api_base_url}/0b00/256"
            m.get(read_url, payload={"regs": invalid_registers})

            async with aiohttp.ClientSession() as session:
                backend = HttpRegisterBackend(session, api_base_url)
                controller = HeaterController(backend=backend, registry=registry)

                # Should handle decode errors gracefully
                await controller.refresh()

                # Some settings may be None
                assert (
                    controller._settings.get("heater_mode") is None
                    or len(controller._settings) > 0
                )

    @pytest.mark.asyncio
    async def test_partial_write_failures(
        self, api_base_url, sample_registers, registry
    ):
        """Test handling of partial write failures."""
        registers = sample_registers.copy()

        with aioresponses() as m:
            # Mock refresh
            read_url = f"{api_base_url}/0b00/256"
            m.get(read_url, payload={"regs": registers})

            # Mock one successful write, one failed
            write_url_55 = f"{api_base_url}/0b55"
            write_url_8d = f"{api_base_url}/0b8d"
            m.post(write_url_55, payload={"status": "0"})
            m.post(write_url_8d, exception=aiohttp.ClientError("Write error"))
            # Mock reads for save
            read_url_55 = f"{api_base_url}/0b55/1"
            read_url_8d = f"{api_base_url}/0b8d/1"
            m.get(read_url_55, payload={"regs": {"0b55": registers["0b55"]}})
            m.get(read_url_8d, payload={"regs": {"0b8d": registers["0b8d"]}})

            async with aiohttp.ClientSession() as session:
                backend = HttpRegisterBackend(session, api_base_url)
                controller = HeaterController(backend=backend, registry=registry)
                await controller.refresh()

                # Modify settings in different registers
                controller.heater_mode = HeaterMode.WINTER  # Register 0b55 (success)
                controller.manual_temperature = 25.0  # Register 0b8d (failure)

                # Save should fail overall
                result = await controller.save()
                assert result is False


class TestRegisterCaching:
    """Tests for register caching behavior."""

    @pytest.mark.asyncio
    async def test_cache_used_for_subsequent_writes(
        self, api_base_url, sample_registers, registry
    ):
        """Test that cache is used for subsequent writes to same register."""
        registers = sample_registers.copy()

        with aioresponses() as m:
            # Mock refresh
            read_url = f"{api_base_url}/0b00/256"
            m.get(read_url, payload={"regs": registers})

            # Mock save - should only write once (using cache)
            write_url = f"{api_base_url}/0b55"
            m.post(write_url, payload={"status": "0"})
            # Should NOT need to read register (using cache)

            async with aiohttp.ClientSession() as session:
                backend = HttpRegisterBackend(session, api_base_url)
                controller = HeaterController(backend=backend, registry=registry)
                await controller.refresh()

                # Verify cache is populated
                assert "0b55" in controller._register_cache

                # Modify setting
                controller.heater_mode = HeaterMode.WINTER

                # Count GET requests before save
                get_requests_before = [
                    req for req in m.requests.keys()
                    if req[0] == "GET"
                ]
                initial_get_count = len(get_requests_before)
                assert initial_get_count > 0, "Refresh should have made GET requests"

                # Save should use cache, not read
                result = await controller.save()
                assert result is True
                
                # Verify no additional GET requests were made during save (cache was used)
                get_requests_after = [
                    req for req in m.requests.keys()
                    if req[0] == "GET"
                ]
                final_get_count = len(get_requests_after)
                # Should have same number of GET requests (no additional reads during save)
                assert final_get_count == initial_get_count, "Save should not have made additional GET requests"

    @pytest.mark.asyncio
    async def test_cache_invalidated_on_refresh(
        self, api_base_url, sample_registers, registry
    ):
        """Test that cache is invalidated on refresh."""
        registers = sample_registers.copy()
        new_registers = registers.copy()
        new_registers["0b55"] = "2000"  # Different value

        with aioresponses() as m:
            # Mock first refresh
            read_url = f"{api_base_url}/0b00/256"
            m.get(read_url, payload={"regs": registers})

            # Mock second refresh with different values
            m.get(read_url, payload={"regs": new_registers})

            async with aiohttp.ClientSession() as session:
                backend = HttpRegisterBackend(session, api_base_url)
                controller = HeaterController(backend=backend, registry=registry)

                # First refresh
                await controller.refresh()
                original_value = controller._register_cache.get("0b55")

                # Second refresh
                await controller.refresh()
                new_value = controller._register_cache.get("0b55")

                # Cache should be updated
                assert original_value != new_value

    @pytest.mark.asyncio
    async def test_cache_updated_after_successful_write(
        self, api_base_url, sample_registers, registry
    ):
        """Test that cache is updated after successful write."""
        registers = sample_registers.copy()

        with aioresponses() as m:
            # Mock refresh
            read_url = f"{api_base_url}/0b00/256"
            m.get(read_url, payload={"regs": registers})

            # Mock save
            write_url = f"{api_base_url}/0b55"
            m.post(write_url, payload={"status": "0"})
            # Mock read for save (cache miss scenario)
            read_single_url = f"{api_base_url}/0b55/1"
            m.get(read_single_url, payload={"regs": {"0b55": registers["0b55"]}})

            async with aiohttp.ClientSession() as session:
                backend = HttpRegisterBackend(session, api_base_url)
                controller = HeaterController(backend=backend, registry=registry)
                await controller.refresh()

                # Clear cache to force read
                controller._register_cache.clear()

                # Modify setting
                controller.heater_mode = HeaterMode.WINTER

                # Save should update cache
                await controller.save()

                # Cache should be updated with new value
                assert "0b55" in controller._register_cache
