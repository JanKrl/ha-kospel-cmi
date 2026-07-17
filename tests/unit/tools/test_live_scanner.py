"""Unit tests for live scanner tool."""

import asyncio
from datetime import datetime
from pathlib import Path

import pytest
import yaml

from kospel_cmi.registers.utils import int_to_reg_address, reg_address_to_int
from kospel_cmi.tools.live_scanner import (
    _diff_scans,
    format_changes,
    run_live_scan,
    serialize_changes,
)
from kospel_cmi.tools.register_scanner import scan_register_range
from tests.unit.tools.fixtures import MockRegisterBackend


class ChangingMockBackend:
    """Mock backend that returns different data on each call."""

    def __init__(self, states: list[dict[str, str]]) -> None:
        self.states = states
        self.call_count = 0

    async def read_registers(self, start_register: str, count: int) -> dict[str, str]:
        state = self.states[min(self.call_count, len(self.states) - 1)]
        self.call_count += 1
        result: dict[str, str] = {}
        start_int = reg_address_to_int(start_register)
        prefix = start_register[:2]
        for i in range(count):
            reg_int = start_int + i
            reg_str = int_to_reg_address(prefix, reg_int)
            result[reg_str] = state.get(reg_str, "0000")
        return result


class TestDiffScans:
    """Tests for _diff_scans."""

    @pytest.mark.asyncio
    async def test_returns_only_registers_where_hex_changed(self) -> None:
        """_diff_scans returns pairs only for registers with different hex."""
        backend = MockRegisterBackend({"0b00": "d700", "0b01": "a401"})
        result = await scan_register_range(backend, "0b00", 2)
        prev = {reg.register: reg for reg in result.registers}

        backend.registers = {"0b00": "2000", "0b01": "a401"}
        curr = await scan_register_range(backend, "0b00", 2)
        changes = _diff_scans(prev, curr)
        assert len(changes) == 1
        assert changes[0][0].register == "0b00"
        assert changes[0][0].hex == "d700"
        assert changes[0][1].hex == "2000"

    @pytest.mark.asyncio
    async def test_includes_transitions_to_from_0000(self) -> None:
        """Transitions involving 0000 are included."""
        backend = MockRegisterBackend({"0b00": "d700", "0b01": "0000"})
        result = await scan_register_range(backend, "0b00", 2)
        prev = {reg.register: reg for reg in result.registers}

        backend.registers = {"0b00": "0000", "0b01": "e100"}
        curr = await scan_register_range(backend, "0b00", 2)
        changes = _diff_scans(prev, curr)
        assert len(changes) == 2
        regs_changed = {c[0].register for c in changes}
        assert "0b00" in regs_changed
        assert "0b01" in regs_changed

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_changes(self) -> None:
        """_diff_scans returns empty list when all hex values match."""
        backend = MockRegisterBackend({"0b00": "d700"})
        result = await scan_register_range(backend, "0b00", 1)
        prev = {reg.register: reg for reg in result.registers}
        curr = await scan_register_range(backend, "0b00", 1)
        changes = _diff_scans(prev, curr)
        assert changes == []


class TestFormatChanges:
    """Tests for format_changes."""

    @pytest.mark.asyncio
    async def test_produces_two_rows_per_change_with_grouping(self) -> None:
        """format_changes produces old/new rows with register header and separator."""
        backend = MockRegisterBackend({"0b00": "d700", "0b01": "a401"})
        result = await scan_register_range(backend, "0b00", 2)
        prev = {reg.register: reg for reg in result.registers}
        backend.registers = {"0b00": "2000", "0b01": "e600"}
        curr = await scan_register_range(backend, "0b00", 2)
        changes = _diff_scans(prev, curr)
        ts = datetime(2025, 2, 18, 12, 0, 8)
        formatted = format_changes(changes, ts)
        assert "2 change(s)" in formatted
        assert "0b00" in formatted
        assert "0b01" in formatted
        assert "old" in formatted
        assert "new" in formatted
        assert "d700" in formatted
        assert "2000" in formatted
        assert "a401" in formatted
        assert "e600" in formatted
        assert "─" in formatted

    def test_returns_empty_string_for_no_changes(self) -> None:
        """format_changes returns empty string when changes list is empty."""
        assert format_changes([], datetime.now()) == ""


class TestSerializeChanges:
    """Tests for serialize_changes."""

    @pytest.mark.asyncio
    async def test_produces_valid_yaml(self) -> None:
        """serialize_changes produces parseable YAML with timestamp and changes."""
        backend = MockRegisterBackend({"0b00": "d700"})
        result = await scan_register_range(backend, "0b00", 1)
        prev = {reg.register: reg for reg in result.registers}
        backend.registers = {"0b00": "2000"}
        curr = await scan_register_range(backend, "0b00", 1)
        changes = _diff_scans(prev, curr)
        ts = datetime(2025, 2, 18, 12, 0, 8)
        yaml_str = serialize_changes(changes, ts)
        assert "---" in yaml_str
        assert "timestamp" in yaml_str
        assert "changes" in yaml_str
        parts = yaml_str.strip().split("\n---\n")
        yaml_part = parts[-1] if len(parts) > 1 else yaml_str
        doc = yaml.safe_load(yaml_part)
        assert doc is not None
        assert "timestamp" in doc
        assert "changes" in doc
        assert len(doc["changes"]) == 1
        assert doc["changes"][0]["register"] == "0b00"
        assert doc["changes"][0]["old_hex"] == "d700"
        assert doc["changes"][0]["new_hex"] == "2000"

    def test_returns_empty_string_for_no_changes(self) -> None:
        """serialize_changes returns empty string when changes list is empty."""
        assert serialize_changes([], datetime.now()) == ""


class TestRunLiveScan:
    """Tests for run_live_scan."""

    @pytest.mark.asyncio
    async def test_initial_scan_printed_then_cancelled(self, capsys: pytest.CaptureFixture[str]) -> None:
        """run_live_scan prints initial state, then can be cancelled."""
        backend = MockRegisterBackend({"0b00": "d700", "0b01": "a401"})
        task = asyncio.create_task(
            run_live_scan(
                backend=backend,
                start_register="0b00",
                count=2,
                interval=0.1,
                output_path=None,
                include_empty=False,
            )
        )
        await asyncio.sleep(0.05)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        out = capsys.readouterr().out
        assert "Live Scan" in out
        assert "Initial state" in out
        assert "0b00" in out
        assert "d700" in out

    @pytest.mark.asyncio
    async def test_changes_printed_and_appended_to_file(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """When backend returns different data on poll, changes are printed and appended."""
        backend = ChangingMockBackend(
            [
                {"0b00": "d700", "0b01": "a401"},
                {"0b00": "2000", "0b01": "a401"},
            ]
        )
        out_file = tmp_path / "live.yaml"
        task = asyncio.create_task(
            run_live_scan(
                backend=backend,
                start_register="0b00",
                count=2,
                interval=0.05,
                output_path=out_file,
                include_empty=False,
            )
        )
        await asyncio.sleep(0.2)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        out = capsys.readouterr().out
        assert "change(s)" in out
        assert "0b00" in out
        assert "d700" in out
        assert "2000" in out
        assert out_file.exists()
        content = out_file.read_text(encoding="utf-8")
        assert "0b00" in content
        assert "d700" in content
        assert "2000" in content
