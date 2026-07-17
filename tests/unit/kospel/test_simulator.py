"""Unit tests for kospel.simulator (function module: read_register, write_register, etc.)."""

from pathlib import Path

import pytest

from kospel_cmi.kospel import simulator


class TestSimulatorModule:
    """Simulator is a function module; all functions take state_file as first arg."""

    @pytest.mark.asyncio
    async def test_read_register_returns_default_when_empty(
        self, tmp_path: Path
    ) -> None:
        """read_register(state_file, register) returns '0000' when file empty/missing."""
        state_file = str(tmp_path / "state.yaml")
        value = await simulator.read_register(state_file, "0b55")
        assert value == "0000"

    @pytest.mark.asyncio
    async def test_write_register_and_read_roundtrip(self, tmp_path: Path) -> None:
        """write_register(state_file, ...) persists; read_register reads it back."""
        state_file = str(tmp_path / "state.yaml")
        await simulator.write_register(state_file, "0b55", "d700")
        value = await simulator.read_register(state_file, "0b55")
        assert value == "d700"

    @pytest.mark.asyncio
    async def test_read_registers_returns_range(self, tmp_path: Path) -> None:
        """read_registers(state_file, start, count) returns dict of hex values."""
        state_file = str(tmp_path / "state.yaml")
        await simulator.write_register(state_file, "0b00", "0100")
        await simulator.write_register(state_file, "0b01", "0200")
        regs = await simulator.read_registers(state_file, "0b00", 3)
        assert regs.get("0b00") == "0100"
        assert regs.get("0b01") == "0200"
        assert regs.get("0b02") == "0000"
