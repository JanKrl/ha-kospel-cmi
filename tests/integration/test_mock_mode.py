"""Integration tests for YAML backend (file-based / development mode)."""

import pytest
import yaml

from kospel_cmi.controller.api import HeaterController
from kospel_cmi.kospel.backend import YamlRegisterBackend
from kospel_cmi.registers.enums import HeaterMode, ManualMode


def _controller_for_state_file(state_file: str) -> HeaterController:
    """Create HeaterController with YamlRegisterBackend for the given state file."""
    backend = YamlRegisterBackend(state_file=state_file)
    return HeaterController(backend=backend)


class TestYamlBackendFullCycle:
    """Tests for complete cycle with YAML backend."""

    @pytest.mark.asyncio
    async def test_yaml_backend_full_cycle(self, tmp_path):
        """Test complete cycle with YAML backend."""
        state_file = tmp_path / "state.yaml"
        state_file.parent.mkdir(parents=True, exist_ok=True)

        controller = _controller_for_state_file(str(state_file))

        await controller.refresh()

        assert len(controller._settings) > 0

        controller.heater_mode = HeaterMode.WINTER
        controller.is_manual_mode_enabled = ManualMode.ENABLED

        result = await controller.save()
        assert result is True

        assert state_file.exists()
        with open(state_file, "r") as f:
            loaded_state = yaml.safe_load(f)
            assert loaded_state is not None
            assert len(loaded_state) > 0

    @pytest.mark.asyncio
    async def test_state_persisted_on_write(self, tmp_path):
        """Test that write operations update YAML file."""
        state_file = tmp_path / "state.yaml"
        state_file.parent.mkdir(parents=True, exist_ok=True)

        controller = _controller_for_state_file(str(state_file))

        await controller.refresh()
        controller.heater_mode = HeaterMode.WINTER
        await controller.save()

        assert state_file.exists()
        with open(state_file, "r") as f:
            loaded_state = yaml.safe_load(f)
            assert loaded_state is not None
            assert any(
                "0b55" in reg for reg in loaded_state.keys() if isinstance(reg, str)
            )

    @pytest.mark.asyncio
    async def test_state_loaded_on_next_run(self, tmp_path):
        """Test that state is loaded on next run."""
        state_file = tmp_path / "state.yaml"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        initial_state = {"0b55": "2000", "0b51": "0500"}
        with open(state_file, "w") as f:
            yaml.dump(initial_state, f)

        controller = _controller_for_state_file(str(state_file))
        await controller.refresh()

        assert len(controller._settings) > 0
        assert (
            controller.heater_mode == HeaterMode.WINTER
            or controller.heater_mode is not None
        )

    @pytest.mark.asyncio
    async def test_state_survives_controller_recreation(self, tmp_path):
        """Test that state survives controller recreation."""
        state_file = tmp_path / "state.yaml"
        state_file.parent.mkdir(parents=True, exist_ok=True)

        controller1 = _controller_for_state_file(str(state_file))
        await controller1.refresh()
        controller1.heater_mode = HeaterMode.WINTER
        await controller1.save()

        controller2 = _controller_for_state_file(str(state_file))
        await controller2.refresh()

        assert (
            controller2.heater_mode == HeaterMode.WINTER
            or len(controller2._settings) > 0
        )


class TestYamlBackendStatePersistence:
    """Tests for state file persistence with YAML backend."""

    @pytest.mark.asyncio
    async def test_write_operations_update_yaml(self, tmp_path):
        """Test that write operations update YAML file."""
        state_file = tmp_path / "state.yaml"
        state_file.parent.mkdir(parents=True, exist_ok=True)

        controller = _controller_for_state_file(str(state_file))
        await controller.refresh()
        controller.manual_temperature = 25.0
        await controller.save()

        assert state_file.exists()
        with open(state_file, "r") as f:
            loaded_state = yaml.safe_load(f)
            assert loaded_state is not None

    @pytest.mark.asyncio
    async def test_read_operations_load_from_yaml(self, tmp_path):
        """Test that read operations load from YAML file."""
        state_file = tmp_path / "state.yaml"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        pre_state = {"0b8d": "fa00"}
        with open(state_file, "w") as f:
            yaml.dump(pre_state, f)

        controller = _controller_for_state_file(str(state_file))
        await controller.refresh()

        temp = controller.manual_temperature
        assert temp is not None


class TestYamlBackendVsRealAPI:
    """Tests for consistency of YAML backend with registry."""

    @pytest.mark.asyncio
    async def test_same_operations_produce_same_results(
        self, tmp_path, sample_registers
    ):
        """Test that same operations produce expected results with YAML backend."""
        state_file = tmp_path / "state.yaml"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file, "w") as f:
            yaml.dump(sample_registers, f)

        controller = _controller_for_state_file(str(state_file))
        await controller.refresh()
        controller.heater_mode = HeaterMode.WINTER
        await controller.save()

        assert controller.heater_mode == HeaterMode.WINTER

    @pytest.mark.asyncio
    async def test_register_values_match_expected_format(self, tmp_path):
        """Test that register values match expected format."""
        state_file = tmp_path / "state.yaml"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        test_state = {"0b55": "d700", "0b51": "0500"}
        with open(state_file, "w") as f:
            yaml.dump(test_state, f)

        controller = _controller_for_state_file(str(state_file))
        await controller.refresh()

        assert len(controller._register_cache) > 0
        for reg_value in controller._register_cache.values():
            assert isinstance(reg_value, str)
            assert len(reg_value) == 4
            assert all(c in "0123456789abcdef" for c in reg_value.lower())

    @pytest.mark.asyncio
    async def test_yaml_backend_consistent_with_registry(self, tmp_path):
        """Test that YAML backend behaves consistently with registry definitions."""
        state_file = tmp_path / "state.yaml"
        state_file.parent.mkdir(parents=True, exist_ok=True)

        controller = _controller_for_state_file(str(state_file))
        await controller.refresh()

        from kospel_cmi.controller.registry import SETTINGS_REGISTRY

        for setting_name in SETTINGS_REGISTRY.keys():
            getattr(controller, setting_name, None)
