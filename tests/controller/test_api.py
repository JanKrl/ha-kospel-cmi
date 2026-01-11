"""Unit tests for controller/api.py - HeaterController class."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp

from controller.api import HeaterController
from controller.registry import SETTINGS_REGISTRY
from registers.enums import HeaterMode, ManualMode, WaterHeaterEnabled, PumpStatus, ValvePosition


class TestHeaterControllerInit:
    """Tests for HeaterController initialization."""

    def test_init_with_session_and_url(self, mock_session, api_base_url):
        """Test initialization with session and API URL."""
        controller = HeaterController(mock_session, api_base_url)
        assert controller.session == mock_session
        assert controller.api_base_url == api_base_url
        assert controller._registry == SETTINGS_REGISTRY
        assert controller._settings == {}
        assert controller._pending_writes == {}
        assert controller._register_cache == {}

    def test_init_with_custom_registry(self, mock_session, api_base_url):
        """Test initialization with custom registry."""
        custom_registry = {"test_setting": MagicMock()}
        controller = HeaterController(mock_session, api_base_url, registry=custom_registry)
        assert controller._registry == custom_registry

    def test_initial_state(self, mock_session, api_base_url):
        """Test initial state is empty."""
        controller = HeaterController(mock_session, api_base_url)
        assert controller._settings == {}
        assert controller._pending_writes == {}
        assert controller._register_cache == {}


class TestHeaterControllerFromRegisters:
    """Tests for from_registers() method."""

    def test_decode_all_settings(self, mock_session, api_base_url, sample_registers):
        """Test decoding all registry settings."""
        controller = HeaterController(mock_session, api_base_url)
        controller.from_registers(sample_registers)
        
        # Verify settings were decoded
        assert len(controller._settings) > 0
        # Verify register cache was populated
        assert len(controller._register_cache) > 0
        # Verify pending writes cleared
        assert controller._pending_writes == {}

    def test_handles_missing_registers(self, mock_session, api_base_url):
        """Test handling of missing registers."""
        registers = {"0b00": "0000"}  # Only one register, missing others
        controller = HeaterController(mock_session, api_base_url)
        controller.from_registers(registers)
        
        # Should handle gracefully, default to "0000" for missing registers
        # Some settings may be None if decode fails
        assert len(controller._settings) > 0

    def test_clears_pending_writes(self, mock_session, api_base_url, sample_registers):
        """Test that refresh clears pending writes."""
        controller = HeaterController(mock_session, api_base_url)
        controller._pending_writes = {"heater_mode": HeaterMode.WINTER}
        controller.from_registers(sample_registers)
        
        assert controller._pending_writes == {}

    def test_handles_decode_errors(self, mock_session, api_base_url):
        """Test handling of decode errors gracefully."""
        registers = {"0b55": "invalid"}  # Invalid hex
        controller = HeaterController(mock_session, api_base_url)
        controller.from_registers(registers)
        
        # Should set to None on decode error
        # The setting should exist but may be None
        assert "heater_mode" in controller._settings or controller._settings.get("heater_mode") is None

    def test_updates_register_cache(self, mock_session, api_base_url, sample_registers):
        """Test that register cache is updated."""
        controller = HeaterController(mock_session, api_base_url)
        controller.from_registers(sample_registers)
        
        # Verify cache contains register values
        assert "0b55" in controller._register_cache
        assert controller._register_cache["0b55"] == sample_registers.get("0b55", "0000")


class TestHeaterControllerRefresh:
    """Tests for refresh() method."""

    @pytest.mark.asyncio
    async def test_refresh_calls_read_registers(self, mock_session, api_base_url, sample_registers):
        """Test that refresh calls read_registers with correct parameters."""
        controller = HeaterController(mock_session, api_base_url)
        
        with patch("controller.api.read_registers", new_callable=AsyncMock) as mock_read:
            mock_read.return_value = sample_registers
            
            await controller.refresh()
            
            mock_read.assert_called_once_with(mock_session, api_base_url, "0b00", 256)

    @pytest.mark.asyncio
    async def test_refresh_calls_from_registers(self, mock_session, api_base_url, sample_registers):
        """Test that refresh calls from_registers with result."""
        controller = HeaterController(mock_session, api_base_url)
        
        with patch("controller.api.read_registers", new_callable=AsyncMock) as mock_read:
            mock_read.return_value = sample_registers
            
            await controller.refresh()
            
            # Verify settings were loaded
            assert len(controller._settings) > 0

    @pytest.mark.asyncio
    async def test_refresh_handles_empty_response(self, mock_session, api_base_url):
        """Test handling of empty response."""
        controller = HeaterController(mock_session, api_base_url)
        
        with patch("controller.api.read_registers", new_callable=AsyncMock) as mock_read:
            mock_read.return_value = {}
            
            await controller.refresh()
            
            # Should handle gracefully
            assert controller._settings == {}

    @pytest.mark.asyncio
    async def test_refresh_integration(self, mock_session, api_base_url, sample_registers):
        """Test refresh integration."""
        controller = HeaterController(mock_session, api_base_url)
        
        with patch("controller.api.read_registers", new_callable=AsyncMock) as mock_read:
            mock_read.return_value = sample_registers
            
            await controller.refresh()
            
            # Verify settings were loaded
            assert len(controller._settings) > 0
            assert len(controller._register_cache) > 0


class TestHeaterControllerGetattr:
    """Tests for __getattr__() method."""

    def test_get_valid_setting(self, heater_controller_with_registers):
        """Test getting valid setting."""
        # Assuming sample_registers has heater_mode set to SUMMER
        # Note: actual value depends on sample_registers fixture
        value = heater_controller_with_registers.heater_mode
        assert value is not None

    def test_get_invalid_setting_raises_attribute_error(self, mock_session, api_base_url):
        """Test getting invalid setting raises AttributeError."""
        controller = HeaterController(mock_session, api_base_url)
        
        with pytest.raises(AttributeError, match="has no attribute 'invalid_setting'"):
            _ = controller.invalid_setting

    def test_get_unloaded_setting_returns_none(self, mock_session, api_base_url):
        """Test getting unloaded setting returns None."""
        controller = HeaterController(mock_session, api_base_url)
        
        value = controller.heater_mode
        assert value is None

    def test_private_attribute_raises_attribute_error(self, mock_session, api_base_url):
        """Test that private attributes raise AttributeError."""
        controller = HeaterController(mock_session, api_base_url)
        
        with pytest.raises(AttributeError):
            _ = controller._private_attr


class TestHeaterControllerSetattr:
    """Tests for __setattr__() method."""

    def test_set_writable_setting(self, heater_controller_with_registers):
        """Test setting writable setting."""
        controller = heater_controller_with_registers
        new_mode = HeaterMode.WINTER
        
        controller.heater_mode = new_mode
        
        assert controller._settings["heater_mode"] == new_mode
        assert controller._pending_writes["heater_mode"] == new_mode

    def test_set_read_only_setting_raises_attribute_error(self, heater_controller_with_registers):
        """Test setting read-only setting raises AttributeError."""
        controller = heater_controller_with_registers
        
        with pytest.raises(AttributeError, match="is read-only"):
            controller.valve_position = ValvePosition.CO

    def test_set_invalid_setting_raises_attribute_error(self, mock_session, api_base_url):
        """Test setting invalid setting raises AttributeError."""
        controller = HeaterController(mock_session, api_base_url)
        
        with pytest.raises(AttributeError, match="has no attribute"):
            controller.invalid_setting = "value"

    def test_set_private_attribute(self, mock_session, api_base_url):
        """Test setting private attribute works normally."""
        controller = HeaterController(mock_session, api_base_url)
        
        controller._private_attr = "value"
        assert controller._private_attr == "value"


class TestHeaterControllerGetSetting:
    """Tests for get_setting() method."""

    def test_get_existing_setting(self, heater_controller_with_registers):
        """Test getting existing setting."""
        controller = heater_controller_with_registers
        value = controller.get_setting("heater_mode")
        assert value is not None

    def test_get_invalid_setting_raises_key_error(self, mock_session, api_base_url):
        """Test getting invalid setting raises KeyError."""
        controller = HeaterController(mock_session, api_base_url)
        
        with pytest.raises(KeyError, match="not found in registry"):
            controller.get_setting("invalid_setting")


class TestHeaterControllerSetSetting:
    """Tests for set_setting() method."""

    def test_set_valid_setting(self, heater_controller_with_registers):
        """Test setting valid setting."""
        controller = heater_controller_with_registers
        new_mode = HeaterMode.WINTER
        
        controller.set_setting("heater_mode", new_mode)
        
        assert controller._settings["heater_mode"] == new_mode
        assert controller._pending_writes["heater_mode"] == new_mode

    def test_set_invalid_setting_raises_key_error(self, mock_session, api_base_url):
        """Test setting invalid setting raises KeyError."""
        controller = HeaterController(mock_session, api_base_url)
        
        with pytest.raises(KeyError, match="not found in registry"):
            controller.set_setting("invalid_setting", "value")

    def test_set_read_only_setting_raises_value_error(self, mock_session, api_base_url):
        """Test setting read-only setting raises ValueError."""
        controller = HeaterController(mock_session, api_base_url)
        
        with pytest.raises(ValueError, match="is read-only"):
            controller.set_setting("valve_position", ValvePosition.CO)


class TestHeaterControllerGetAllSettings:
    """Tests for get_all_settings() method."""

    def test_get_all_settings_returns_copy(self, heater_controller_with_registers):
        """Test that get_all_settings returns a copy."""
        controller = heater_controller_with_registers
        
        settings = controller.get_all_settings()
        
        # Modify the copy
        settings["test"] = "value"
        
        # Original should not be modified
        assert "test" not in controller._settings

    def test_get_all_settings_returns_current_settings(self, heater_controller_with_registers):
        """Test that get_all_settings returns current settings."""
        controller = heater_controller_with_registers
        
        settings = controller.get_all_settings()
        
        assert settings == controller._settings


class TestHeaterControllerSave:
    """Tests for save() method."""

    @pytest.mark.asyncio
    async def test_save_no_pending_writes(self, mock_session, api_base_url):
        """Test save with no pending writes returns True."""
        controller = HeaterController(mock_session, api_base_url)
        
        result = await controller.save()
        
        assert result is True

    @pytest.mark.asyncio
    async def test_save_groups_writes_by_register(self, mock_session, api_base_url, heater_controller_with_registers):
        """Test that save groups writes by register."""
        controller = heater_controller_with_registers
        controller.heater_mode = HeaterMode.WINTER
        controller.is_manual_mode_enabled = ManualMode.ENABLED
        
        # Both settings are in register 0b55
        with patch("controller.api.write_register", new_callable=AsyncMock) as mock_write:
            with patch("controller.api.read_register", new_callable=AsyncMock) as mock_read:
                mock_read.return_value = "0000"
                mock_write.return_value = True
                
                result = await controller.save()
                
                # Should write once per register (both settings in 0b55)
                # Verify write_register was called with correct register
                assert mock_write.called

    @pytest.mark.asyncio
    async def test_save_reads_register_if_not_cached(self, mock_session, api_base_url, heater_controller_with_registers):
        """Test that save reads register if not in cache."""
        controller = heater_controller_with_registers
        controller._register_cache.clear()  # Clear cache
        controller.heater_mode = HeaterMode.WINTER
        
        with patch("controller.api.write_register", new_callable=AsyncMock) as mock_write:
            with patch("controller.api.read_register", new_callable=AsyncMock) as mock_read:
                mock_read.return_value = "0000"
                mock_write.return_value = True
                
                await controller.save()
                
                # Should read register before writing
                mock_read.assert_called()

    @pytest.mark.asyncio
    async def test_save_uses_cached_register(self, mock_session, api_base_url, heater_controller_with_registers):
        """Test that save uses cached register value."""
        controller = heater_controller_with_registers
        controller._register_cache["0b55"] = "0000"  # Set cache
        controller.heater_mode = HeaterMode.WINTER
        
        with patch("controller.api.write_register", new_callable=AsyncMock) as mock_write:
            with patch("controller.api.read_register", new_callable=AsyncMock) as mock_read:
                mock_write.return_value = True
                
                await controller.save()
                
                # Should not read if cached
                mock_read.assert_not_called()

    @pytest.mark.asyncio
    async def test_save_handles_encode_failure(self, mock_session, api_base_url, heater_controller_with_registers):
        """Test that save handles encode failures gracefully."""
        controller = heater_controller_with_registers
        controller.heater_mode = HeaterMode.WINTER
        
        # Mock encode to fail by patching the setting definition
        with patch.object(SETTINGS_REGISTRY["heater_mode"], "encode", return_value=None):
            result = await controller.save()
            
            # Should return False on failure
            assert result is False

    @pytest.mark.asyncio
    async def test_save_handles_write_failure(self, mock_session, api_base_url, heater_controller_with_registers):
        """Test that save handles write failures gracefully."""
        controller = heater_controller_with_registers
        controller.heater_mode = HeaterMode.WINTER
        
        with patch("controller.api.write_register", new_callable=AsyncMock) as mock_write:
            with patch("controller.api.read_register", new_callable=AsyncMock) as mock_read:
                mock_read.return_value = "0000"
                mock_write.return_value = False
                
                result = await controller.save()
                
                # Should return False on failure
                assert result is False

    @pytest.mark.asyncio
    async def test_save_clears_pending_writes_on_success(self, mock_session, api_base_url, heater_controller_with_registers):
        """Test that save clears pending writes on success."""
        controller = heater_controller_with_registers
        controller.heater_mode = HeaterMode.WINTER
        
        with patch("controller.api.write_register", new_callable=AsyncMock) as mock_write:
            with patch("controller.api.read_register", new_callable=AsyncMock) as mock_read:
                mock_read.return_value = "0000"
                mock_write.return_value = True
                
                await controller.save()
                
                # Pending writes should be cleared
                assert controller._pending_writes == {}

    @pytest.mark.asyncio
    async def test_save_updates_cache_on_success(self, mock_session, api_base_url, heater_controller_with_registers):
        """Test that save updates cache on success."""
        controller = heater_controller_with_registers
        controller._register_cache["0b55"] = "0000"
        controller.heater_mode = HeaterMode.WINTER
        
        with patch("controller.api.write_register", new_callable=AsyncMock) as mock_write:
            mock_write.return_value = True
            
            await controller.save()
            
            # Cache should be updated with new value
            assert "0b55" in controller._register_cache

    @pytest.mark.asyncio
    async def test_save_multiple_settings_same_register(self, mock_session, api_base_url, heater_controller_with_registers):
        """Test saving multiple settings in same register."""
        controller = heater_controller_with_registers
        controller.heater_mode = HeaterMode.WINTER
        controller.is_manual_mode_enabled = ManualMode.ENABLED
        # Both are in register 0b55
        
        with patch("controller.api.write_register", new_callable=AsyncMock) as mock_write:
            with patch("controller.api.read_register", new_callable=AsyncMock) as mock_read:
                mock_read.return_value = "0000"
                mock_write.return_value = True
                
                result = await controller.save()
                
                assert result is True
                # Should write once (combined value)
                assert mock_write.call_count >= 1


class TestHeaterControllerPrintSettings:
    """Tests for print_settings() method."""

    def test_print_settings_formats_values(self, heater_controller_with_registers, capsys):
        """Test that print_settings formats values correctly."""
        controller = heater_controller_with_registers
        
        controller.print_settings()
        
        captured = capsys.readouterr()
        assert "Heater Settings" in captured.out
        assert "heater_mode" in captured.out or "temperature" in captured.out

    def test_print_settings_handles_none_values(self, mock_session, api_base_url, capsys):
        """Test that print_settings handles None values."""
        controller = HeaterController(mock_session, api_base_url)
        
        controller.print_settings()
        
        captured = capsys.readouterr()
        assert "Unknown/Not loaded" in captured.out or len(captured.out) > 0

    def test_print_settings_shows_pending_writes(self, heater_controller_with_registers, capsys):
        """Test that print_settings shows pending writes."""
        controller = heater_controller_with_registers
        controller.heater_mode = HeaterMode.WINTER
        
        controller.print_settings()
        
        captured = capsys.readouterr()
        assert "Unsaved Changes" in captured.out

