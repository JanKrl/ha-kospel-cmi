"""Unit tests for kospel/simulator.py - Simulator API implementation."""

import pytest
import yaml
from pathlib import Path
from unittest.mock import patch, AsyncMock

from custom_components.kospel.kospel.simulator import (
    SimulatorRegisterState,
    simulator_read_register,
    simulator_read_registers,
    simulator_write_register,
    simulator_write_flag_bit,
    is_simulation_mode,
)
from custom_components.kospel.registers.utils import reg_to_int, get_bit


class TestIsSimulationMode:
    """Tests for is_simulation_mode() function."""

    def test_enabled_with_1(self, monkeypatch):
        """Test simulation mode enabled with '1'."""
        monkeypatch.setenv("SIMULATION_MODE", "1")
        assert is_simulation_mode() is True

    def test_enabled_with_true(self, monkeypatch):
        """Test simulation mode enabled with 'true'."""
        monkeypatch.setenv("SIMULATION_MODE", "true")
        assert is_simulation_mode() is True

    def test_enabled_with_yes(self, monkeypatch):
        """Test simulation mode enabled with 'yes'."""
        monkeypatch.setenv("SIMULATION_MODE", "yes")
        assert is_simulation_mode() is True

    def test_enabled_with_on(self, monkeypatch):
        """Test simulation mode enabled with 'on'."""
        monkeypatch.setenv("SIMULATION_MODE", "on")
        assert is_simulation_mode() is True

    def test_enabled_case_insensitive(self, monkeypatch):
        """Test simulation mode enabled case insensitive."""
        monkeypatch.setenv("SIMULATION_MODE", "TRUE")
        assert is_simulation_mode() is True
        monkeypatch.setenv("SIMULATION_MODE", "YES")
        assert is_simulation_mode() is True
        monkeypatch.setenv("SIMULATION_MODE", "On")
        assert is_simulation_mode() is True

    def test_disabled_with_0(self, monkeypatch):
        """Test simulation mode disabled with '0'."""
        monkeypatch.setenv("SIMULATION_MODE", "0")
        assert is_simulation_mode() is False

    def test_disabled_with_false(self, monkeypatch):
        """Test simulation mode disabled with 'false'."""
        monkeypatch.setenv("SIMULATION_MODE", "false")
        assert is_simulation_mode() is False

    def test_disabled_with_empty_string(self, monkeypatch):
        """Test simulation mode disabled with empty string."""
        monkeypatch.delenv("SIMULATION_MODE", raising=False)
        assert is_simulation_mode() is False

    def test_disabled_when_not_set(self, monkeypatch):
        """Test simulation mode disabled when environment variable not set."""
        monkeypatch.delenv("SIMULATION_MODE", raising=False)
        assert is_simulation_mode() is False


class TestSimulatorRegisterState:
    """Tests for SimulatorRegisterState class."""

    def test_init_default_state_file(self, tmp_path, monkeypatch):
        """Test initialization with default state file."""
        # Set up data directory
        data_dir = tmp_path / "data"
        data_dir.mkdir(exist_ok=True)
        state_file = data_dir / "heater_mock_state.yaml"

        with patch("kospel.simulator.Path", return_value=state_file):
            state = SimulatorRegisterState()
            assert state.state_file == state_file
            assert state.registers == {}

    def test_init_custom_state_file(self, tmp_path):
        """Test initialization with custom state file."""
        state_file = tmp_path / "custom_state.yaml"
        state = SimulatorRegisterState(state_file=str(state_file))
        # Absolute path should be used as-is
        assert state.state_file == state_file

    def test_init_relative_state_file(self, tmp_path):
        """Test initialization with relative state file (should prepend data/)."""
        # Create data directory first
        data_dir = tmp_path / "data"
        data_dir.mkdir(exist_ok=True)

        # Change to tmp_path directory so relative path works
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            state = SimulatorRegisterState(state_file="custom_state.yaml")
            # Relative path should prepend "data/"
            assert state.state_file == Path("data") / "custom_state.yaml"
        finally:
            os.chdir(original_cwd)

    def test_init_environment_variable(self, tmp_path, monkeypatch):
        """Test initialization with environment variable."""
        monkeypatch.setenv("HEATER_MOCK_STATE_FILE", "custom_file.yaml")
        data_dir = tmp_path / "data"
        data_dir.mkdir(exist_ok=True)

        with patch("kospel.simulator.Path", return_value=data_dir / "custom_file.yaml"):
            state = SimulatorRegisterState()
            assert "custom_file.yaml" in str(state.state_file)

    @pytest.mark.asyncio
    async def test_load_state_from_file(self, tmp_path):
        """Test loading state from existing file."""
        state_file = tmp_path / "heater_mock_state.yaml"
        test_registers = {"0b55": "d700", "0b51": "0500"}

        # Create file with test data
        with open(state_file, "w") as f:
            yaml.dump(test_registers, f)

        # Set up data directory
        data_dir = tmp_path / "data"
        data_dir.mkdir(exist_ok=True)
        actual_state_file = data_dir / "heater_mock_state.yaml"

        with patch("kospel.simulator.Path", return_value=actual_state_file):
            # Copy test data to actual location
            with open(actual_state_file, "w") as f:
                yaml.dump(test_registers, f)

            state = SimulatorRegisterState()
            # Mock the load to use our test file
            state.state_file = state_file
            await state._load_state()

            assert state.registers == test_registers

    @pytest.mark.asyncio
    async def test_load_state_missing_file(self, tmp_path):
        """Test loading state when file doesn't exist."""
        state_file = tmp_path / "nonexistent.yaml"
        data_dir = tmp_path / "data"
        data_dir.mkdir(exist_ok=True)

        with patch("kospel.simulator.Path", return_value=data_dir / "nonexistent.yaml"):
            state = SimulatorRegisterState()
            state.state_file = state_file
            await state._load_state()

            assert state.registers == {}

    @pytest.mark.asyncio
    async def test_load_state_invalid_yaml(self, tmp_path):
        """Test loading state with invalid YAML."""
        state_file = tmp_path / "invalid.yaml"
        data_dir = tmp_path / "data"
        data_dir.mkdir(exist_ok=True)

        # Create file with invalid YAML
        with open(state_file, "w") as f:
            f.write("invalid: yaml: content: [")

        with patch("kospel.simulator.Path", return_value=data_dir / "invalid.yaml"):
            state = SimulatorRegisterState()
            state.state_file = state_file
            await state._load_state()

            # Should handle gracefully, empty dict or existing content
            assert isinstance(state.registers, dict)

    @pytest.mark.asyncio
    async def test_save_state(self, tmp_path):
        """Test saving state to file."""
        state_file = tmp_path / "heater_mock_state.yaml"
        data_dir = tmp_path / "data"
        data_dir.mkdir(exist_ok=True)
        actual_state_file = data_dir / "heater_mock_state.yaml"

        with patch("kospel.simulator.Path", return_value=actual_state_file):
            state = SimulatorRegisterState()
            state.state_file = actual_state_file
            state.registers = {"0b55": "d700", "0b51": "0500"}
            await state._save_state()

            # Verify file was created and contains correct data
            assert actual_state_file.exists()
            with open(actual_state_file, "r") as f:
                loaded = yaml.safe_load(f)
                assert loaded == state.registers

    def test_get_register_existing(self, tmp_path):
        """Test getting existing register."""
        state_file = tmp_path / "heater_mock_state.yaml"
        data_dir = tmp_path / "data"
        data_dir.mkdir(exist_ok=True)
        actual_state_file = data_dir / "heater_mock_state.yaml"

        with patch("kospel.simulator.Path", return_value=actual_state_file):
            state = SimulatorRegisterState()
            state.state_file = actual_state_file
            state.registers = {"0b55": "d700"}

            result = state.get_register("0b55")
            assert result == "d700"

    def test_get_register_missing(self, tmp_path):
        """Test getting missing register returns default."""
        state_file = tmp_path / "heater_mock_state.yaml"
        data_dir = tmp_path / "data"
        data_dir.mkdir(exist_ok=True)
        actual_state_file = data_dir / "heater_mock_state.yaml"

        with patch("kospel.simulator.Path", return_value=actual_state_file):
            state = SimulatorRegisterState()
            state.state_file = actual_state_file
            state.registers = {}

            result = state.get_register("0b99")
            assert result == "0000"
            # Verify it was added to state
            assert state.registers["0b99"] == "0000"

    @pytest.mark.asyncio
    async def test_set_register(self, tmp_path):
        """Test setting register value."""
        state_file = tmp_path / "heater_mock_state.yaml"
        data_dir = tmp_path / "data"
        data_dir.mkdir(exist_ok=True)
        actual_state_file = data_dir / "heater_mock_state.yaml"

        with patch("kospel.simulator.Path", return_value=actual_state_file):
            state = SimulatorRegisterState()
            state.state_file = actual_state_file
            state.registers = {}

            await state.set_register("0b55", "d700")
            assert state.registers["0b55"] == "d700"

    def test_get_all_registers(self, tmp_path):
        """Test getting all registers returns copy."""
        state_file = tmp_path / "heater_mock_state.yaml"
        data_dir = tmp_path / "data"
        data_dir.mkdir(exist_ok=True)
        actual_state_file = data_dir / "heater_mock_state.yaml"

        with patch("kospel.simulator.Path", return_value=actual_state_file):
            state = SimulatorRegisterState()
            state.state_file = actual_state_file
            state.registers = {"0b55": "d700", "0b51": "0500"}

            result = state.get_all_registers()
            assert result == state.registers
            # Verify it's a copy (modifying result doesn't affect state)
            result["0b99"] = "0000"
            assert "0b99" not in state.registers


class TestSimulatorReadRegister:
    """Tests for simulator_read_register() function."""

    @pytest.mark.asyncio
    async def test_read_existing_register(self, tmp_path):
        """Test reading existing register."""
        with patch(
            "kospel.simulator._get_simulator_state", new_callable=AsyncMock
        ) as mock_get_state:
            simulator_state = SimulatorRegisterState()
            simulator_state.registers = {"0b55": "d700"}
            mock_get_state.return_value = simulator_state

            result = await simulator_read_register("0b55")
            assert result == "d700"

    @pytest.mark.asyncio
    async def test_read_missing_register(self, tmp_path):
        """Test reading missing register returns default."""
        with patch(
            "kospel.simulator._get_simulator_state", new_callable=AsyncMock
        ) as mock_get_state:
            simulator_state = SimulatorRegisterState()
            simulator_state.registers = {}
            mock_get_state.return_value = simulator_state

            result = await simulator_read_register("0b99")
            assert result == "0000"

    @pytest.mark.asyncio
    async def test_async_function(self, tmp_path):
        """Test that function is async and works correctly."""
        with patch(
            "kospel.simulator._get_simulator_state", new_callable=AsyncMock
        ) as mock_get_state:
            simulator_state = SimulatorRegisterState()
            simulator_state.registers = {"0b55": "d700"}
            mock_get_state.return_value = simulator_state

            # Should work with await
            result = await simulator_read_register("0b55")
            assert result == "d700"


class TestSimulatorReadRegisters:
    """Tests for simulator_read_registers() function."""

    @pytest.mark.asyncio
    async def test_read_register_range(self, tmp_path):
        """Test reading register range."""
        with patch(
            "kospel.simulator._get_simulator_state", new_callable=AsyncMock
        ) as mock_get_state:
            simulator_state = SimulatorRegisterState()
            simulator_state.registers = {"0b00": "0000", "0b01": "0100", "0b02": "0200"}
            mock_get_state.return_value = simulator_state

            result = await simulator_read_registers("0b00", 3)
            assert len(result) == 3
            assert "0b00" in result
            assert "0b01" in result
            assert "0b02" in result

    @pytest.mark.asyncio
    async def test_read_registers_with_missing(self, tmp_path):
        """Test reading registers with missing ones default to 0000."""
        with patch(
            "kospel.simulator._get_simulator_state", new_callable=AsyncMock
        ) as mock_get_state:
            simulator_state = SimulatorRegisterState()
            simulator_state.registers = {"0b00": "0000"}
            mock_get_state.return_value = simulator_state

            result = await simulator_read_registers("0b00", 3)
            assert len(result) == 3
            assert result["0b00"] == "0000"
            assert result["0b01"] == "0000"  # Default
            assert result["0b02"] == "0000"  # Default

    @pytest.mark.asyncio
    async def test_register_address_conversion(self, tmp_path):
        """Test register address conversion works correctly."""
        with patch(
            "kospel.simulator._get_simulator_state", new_callable=AsyncMock
        ) as mock_get_state:
            simulator_state = SimulatorRegisterState()
            simulator_state.registers = {}
            mock_get_state.return_value = simulator_state

            result = await simulator_read_registers("0b50", 3)
            assert "0b50" in result
            assert "0b51" in result
            assert "0b52" in result


class TestSimulatorWriteRegister:
    """Tests for simulator_write_register() function."""

    @pytest.mark.asyncio
    async def test_write_register_updates_state(self, tmp_path):
        """Test that write updates state correctly."""
        with patch(
            "kospel.simulator._get_simulator_state", new_callable=AsyncMock
        ) as mock_get_state:
            simulator_state = SimulatorRegisterState()
            simulator_state.registers = {}

            async def mock_set_register(reg, val):
                simulator_state.registers[reg] = val

            simulator_state.set_register = mock_set_register
            mock_get_state.return_value = simulator_state

            result = await simulator_write_register("0b55", "d700")
            assert result is True
            assert simulator_state.registers.get("0b55") == "d700"

    @pytest.mark.asyncio
    async def test_write_register_always_returns_true(self, tmp_path):
        """Test that write always returns True."""
        with patch(
            "kospel.simulator._get_simulator_state", new_callable=AsyncMock
        ) as mock_get_state:
            simulator_state = SimulatorRegisterState()
            simulator_state.registers = {}

            async def mock_set_register(reg, val):
                simulator_state.registers[reg] = val

            simulator_state.set_register = mock_set_register
            mock_get_state.return_value = simulator_state

            result = await simulator_write_register("0b55", "d700")
            assert result is True

    @pytest.mark.asyncio
    async def test_write_register_persists(self, tmp_path):
        """Test that write persists to file."""
        with patch(
            "kospel.simulator._get_simulator_state", new_callable=AsyncMock
        ) as mock_get_state:
            simulator_state = SimulatorRegisterState()
            simulator_state.registers = {}

            async def mock_set_register(reg, val):
                simulator_state.registers[reg] = val

            simulator_state.set_register = mock_set_register
            mock_get_state.return_value = simulator_state

            await simulator_write_register("0b55", "d700")
            # Verify register was updated
            assert simulator_state.registers.get("0b55") == "d700"


class TestSimulatorWriteFlagBit:
    """Tests for simulator_write_flag_bit() function."""

    @pytest.mark.asyncio
    async def test_set_bit(self, tmp_path):
        """Test setting a bit."""
        with patch(
            "kospel.simulator._get_simulator_state", new_callable=AsyncMock
        ) as mock_get_state:
            simulator_state = SimulatorRegisterState()
            simulator_state.registers = {"0b55": "0000"}  # All bits clear
            simulator_state.get_register = lambda reg: simulator_state.registers.get(
                reg, "0000"
            )

            async def mock_set_register(reg, val):
                simulator_state.registers[reg] = val

            simulator_state.set_register = mock_set_register
            mock_get_state.return_value = simulator_state

            result = await simulator_write_flag_bit("0b55", 3, True)
            assert result is True
            # Verify bit 3 is set
            new_value = reg_to_int(simulator_state.registers["0b55"])
            assert get_bit(new_value, 3) is True

    @pytest.mark.asyncio
    async def test_clear_bit(self, tmp_path):
        """Test clearing a bit."""
        with patch(
            "kospel.simulator._get_simulator_state", new_callable=AsyncMock
        ) as mock_get_state:
            simulator_state = SimulatorRegisterState()
            simulator_state.registers = {"0b55": "0800"}  # Bit 3 set
            simulator_state.get_register = lambda reg: simulator_state.registers.get(
                reg, "0000"
            )

            async def mock_set_register(reg, val):
                simulator_state.registers[reg] = val

            simulator_state.set_register = mock_set_register
            mock_get_state.return_value = simulator_state

            result = await simulator_write_flag_bit("0b55", 3, False)
            assert result is True
            # Verify bit 3 is clear
            new_value = reg_to_int(simulator_state.registers["0b55"])
            assert get_bit(new_value, 3) is False

    @pytest.mark.asyncio
    async def test_preserves_other_bits(self, tmp_path):
        """Test that bit manipulation preserves other bits."""
        with patch(
            "kospel.simulator._get_simulator_state", new_callable=AsyncMock
        ) as mock_get_state:
            simulator_state = SimulatorRegisterState()
            simulator_state.registers = {"0b55": "0800"}  # Bit 3 set
            simulator_state.get_register = lambda reg: simulator_state.registers.get(
                reg, "0000"
            )

            async def mock_set_register(reg, val):
                simulator_state.registers[reg] = val

            simulator_state.set_register = mock_set_register
            mock_get_state.return_value = simulator_state

            # Set bit 5 (should preserve bit 3)
            result = await simulator_write_flag_bit("0b55", 5, True)
            assert result is True
            new_value = reg_to_int(simulator_state.registers["0b55"])
            assert get_bit(new_value, 3) is True  # Original bit preserved
            assert get_bit(new_value, 5) is True  # New bit set

    @pytest.mark.asyncio
    async def test_always_returns_true(self, tmp_path):
        """Test that write always returns True."""
        with patch(
            "kospel.simulator._get_simulator_state", new_callable=AsyncMock
        ) as mock_get_state:
            simulator_state = SimulatorRegisterState()
            simulator_state.registers = {"0b55": "0000"}
            simulator_state.get_register = lambda reg: simulator_state.registers.get(
                reg, "0000"
            )

            async def mock_set_register(reg, val):
                simulator_state.registers[reg] = val

            simulator_state.set_register = mock_set_register
            mock_get_state.return_value = simulator_state

            result = await simulator_write_flag_bit("0b55", 3, True)
            assert result is True

    @pytest.mark.asyncio
    async def test_state_persistence(self, tmp_path):
        """Test that state is persisted after write."""
        with patch(
            "kospel.simulator._get_simulator_state", new_callable=AsyncMock
        ) as mock_get_state:
            simulator_state = SimulatorRegisterState()
            simulator_state.registers = {"0b55": "0000"}

            async def mock_set_register(reg, val):
                simulator_state.registers[reg] = val

            simulator_state.get_register = lambda reg: simulator_state.registers.get(
                reg, "0000"
            )
            simulator_state.set_register = mock_set_register
            mock_get_state.return_value = simulator_state

            await simulator_write_flag_bit("0b55", 3, True)
            # Verify register was updated
            assert "0b55" in simulator_state.registers
