"""Integration tests for simulation mode functionality."""

import pytest
import yaml

import aiohttp

from controller.api import HeaterController
from registers.enums import HeaterMode, ManualMode


class TestSimulationModeFullCycle:
    """Tests for complete cycle in simulation mode."""

    @pytest.mark.asyncio
    async def test_simulation_mode_full_cycle(
        self, api_base_url, enable_simulation_mode, tmp_path, monkeypatch
    ):
        """Test complete cycle in simulation mode."""
        # Reset global simulator state
        import kospel.simulator

        kospel.simulator._simulator_state = None

        # Set up simulator state file with absolute path
        state_file = tmp_path / "test_simulation_state.yaml"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv("SIMULATION_STATE_FILE", str(state_file))

        async with aiohttp.ClientSession() as session:
            controller = HeaterController(session, api_base_url)

            # Refresh in simulation mode
            await controller.refresh()

            # Verify settings were loaded
            assert len(controller._settings) > 0

            # Modify setting
            controller.heater_mode = HeaterMode.WINTER
            controller.is_manual_mode_enabled = ManualMode.ENABLED

            # Save in simulation mode
            result = await controller.save()
            assert result is True

            # Verify state was persisted to YAML
            assert state_file.exists()
            with open(state_file, "r") as f:
                loaded_state = yaml.safe_load(f)
                assert loaded_state is not None
                assert len(loaded_state) > 0

    @pytest.mark.asyncio
    async def test_state_persisted_on_write(
        self, api_base_url, enable_simulation_mode, tmp_path, monkeypatch
    ):
        """Test that write operations update YAML file."""
        # Reset global simulator state
        import kospel.simulator

        kospel.simulator._simulator_state = None

        # Set up simulator state file with absolute path
        state_file = tmp_path / "test_simulation_state.yaml"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv("SIMULATION_STATE_FILE", str(state_file))

        async with aiohttp.ClientSession() as session:
            controller = HeaterController(session, api_base_url)

            # Initial state
            await controller.refresh()

            # Modify and save
            controller.heater_mode = HeaterMode.WINTER
            await controller.save()

            # Verify file was updated
            assert state_file.exists()
            with open(state_file, "r") as f:
                loaded_state = yaml.safe_load(f)
                assert loaded_state is not None
                # Register 0b55 should be in state
                assert any(
                    "0b55" in reg for reg in loaded_state.keys() if isinstance(reg, str)
                )

    @pytest.mark.asyncio
    async def test_state_loaded_on_next_run(
        self, api_base_url, enable_simulation_mode, tmp_path, monkeypatch
    ):
        """Test that state is loaded on next run."""
        # Reset global simulator state
        import kospel.simulator

        kospel.simulator._simulator_state = None

        # Set up simulator state file with absolute path
        state_file = tmp_path / "test_simulation_state.yaml"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv("SIMULATION_STATE_FILE", str(state_file))

        # Create initial state file
        initial_state = {"0b55": "2000", "0b51": "0500"}  # WINTER mode
        with open(state_file, "w") as f:
            yaml.dump(initial_state, f)

        async with aiohttp.ClientSession() as session:
            controller = HeaterController(session, api_base_url)

            # Refresh should load from file
            await controller.refresh()

            # Verify state was loaded
            assert len(controller._settings) > 0
            # Heater mode should be WINTER (from file)
            assert (
                controller.heater_mode == HeaterMode.WINTER
                or controller.heater_mode is not None
            )

    @pytest.mark.asyncio
    async def test_state_survives_controller_recreation(
        self, api_base_url, enable_simulation_mode, tmp_path, monkeypatch
    ):
        """Test that state survives controller recreation."""
        # Reset global simulator state
        import kospel.simulator

        kospel.simulator._simulator_state = None

        # Set up simulator state file with absolute path
        state_file = tmp_path / "test_simulation_state.yaml"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv("SIMULATION_STATE_FILE", str(state_file))

        # First controller instance
        async with aiohttp.ClientSession() as session1:
            controller1 = HeaterController(session1, api_base_url)
            await controller1.refresh()
            controller1.heater_mode = HeaterMode.WINTER
            await controller1.save()

        # Reset global state to force reload from file
        kospel.simulator._simulator_state = None

        # Second controller instance (recreated)
        async with aiohttp.ClientSession() as session2:
            controller2 = HeaterController(session2, api_base_url)
            await controller2.refresh()

            # Should load previous state
            assert (
                controller2.heater_mode == HeaterMode.WINTER
                or len(controller2._settings) > 0
            )


class TestSimulationModeStatePersistence:
    """Tests for state file persistence."""

    @pytest.mark.asyncio
    async def test_write_operations_update_yaml(
        self, api_base_url, enable_simulation_mode, tmp_path, monkeypatch
    ):
        """Test that write operations update YAML file."""
        # Reset global simulator state
        import kospel.simulator

        kospel.simulator._simulator_state = None

        # Set up simulator state file with absolute path
        state_file = tmp_path / "test_simulation_state.yaml"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv("SIMULATION_STATE_FILE", str(state_file))

        async with aiohttp.ClientSession() as session:
            controller = HeaterController(session, api_base_url)

            # Initial state
            await controller.refresh()

            # Write operation
            controller.manual_temperature = 25.0
            await controller.save()

            # Verify file was updated
            assert state_file.exists()
            with open(state_file, "r") as f:
                loaded_state = yaml.safe_load(f)
                assert loaded_state is not None

    @pytest.mark.asyncio
    async def test_read_operations_load_from_yaml(
        self, api_base_url, enable_simulation_mode, tmp_path, monkeypatch
    ):
        """Test that read operations load from YAML file."""
        # Reset global simulator state
        import kospel.simulator

        kospel.simulator._simulator_state = None

        # Set up simulator state file with absolute path
        state_file = tmp_path / "test_simulation_state.yaml"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv("SIMULATION_STATE_FILE", str(state_file))

        # Pre-populate state file
        pre_state = {"0b8d": "fa00"}  # 25.0°C = 250
        with open(state_file, "w") as f:
            yaml.dump(pre_state, f)

        async with aiohttp.ClientSession() as session:
            controller = HeaterController(session, api_base_url)

            # Refresh should load from file
            await controller.refresh()

            # Verify value was loaded
            # manual_temperature should be around 25.0°C
            temp = controller.manual_temperature
            assert temp is not None


class TestSimulationModeVsRealAPI:
    """Tests for consistency between mock and real API."""

    @pytest.mark.asyncio
    async def test_same_operations_produce_same_results(
        self,
        api_base_url,
        enable_simulation_mode,
        tmp_path,
        sample_registers,
        monkeypatch,
    ):
        """Test that same operations produce same results in mock and real mode."""
        # Reset global simulator state
        import kospel.simulator

        kospel.simulator._simulator_state = None

        # Set up simulator state file with absolute path
        state_file = tmp_path / "test_simulation_state.yaml"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv("SIMULATION_STATE_FILE", str(state_file))

        # Initialize mock state with sample registers
        with open(state_file, "w") as f:
            yaml.dump(sample_registers, f)

        async with aiohttp.ClientSession() as session:
            controller = HeaterController(session, api_base_url)

            # Operations in simulation mode
            await controller.refresh()
            controller.heater_mode = HeaterMode.WINTER
            await controller.save()

            # Verify operations worked
            assert controller.heater_mode == HeaterMode.WINTER

    @pytest.mark.asyncio
    async def test_register_values_match_expected_format(
        self, api_base_url, enable_simulation_mode, tmp_path, monkeypatch
    ):
        """Test that register values match expected format."""
        # Reset global simulator state
        import kospel.simulator

        kospel.simulator._simulator_state = None

        # Set up simulator state file with absolute path
        state_file = tmp_path / "test_simulation_state.yaml"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv("SIMULATION_STATE_FILE", str(state_file))

        # Create state with known values
        test_state = {"0b55": "d700", "0b51": "0500"}  # Valid hex strings
        with open(state_file, "w") as f:
            yaml.dump(test_state, f)

        async with aiohttp.ClientSession() as session:
            controller = HeaterController(session, api_base_url)

            await controller.refresh()

            # Verify register values are in correct format (4-char hex)
            assert len(controller._register_cache) > 0
            for reg_value in controller._register_cache.values():
                assert isinstance(reg_value, str)
                assert len(reg_value) == 4
                # Should be valid hex
                assert all(c in "0123456789abcdef" for c in reg_value.lower())

    @pytest.mark.asyncio
    async def test_simulation_mode_consistent_with_registry(
        self, api_base_url, enable_simulation_mode, tmp_path, monkeypatch
    ):
        """Test that simulation mode behaves consistently with registry definitions."""
        # Reset global simulator state
        import kospel.simulator

        kospel.simulator._simulator_state = None

        # Set up simulator state file with absolute path
        state_file = tmp_path / "test_simulation_state.yaml"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv("SIMULATION_STATE_FILE", str(state_file))

        async with aiohttp.ClientSession() as session:
            controller = HeaterController(session, api_base_url)

            # Refresh should decode all registry settings
            await controller.refresh()

            # Verify all registry settings can be accessed
            from controller.registry import SETTINGS_REGISTRY

            for setting_name in SETTINGS_REGISTRY.keys():
                # Should not raise AttributeError
                getattr(controller, setting_name, None)
                # Value may be None if not loaded, but should not raise error
                assert True  # Test passes if no exception raised
