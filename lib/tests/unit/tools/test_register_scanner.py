"""Unit tests for register scanner tool."""

from pathlib import Path

import aiofiles
import pytest
import yaml

from kospel_cmi.tools.register_scanner import (
    format_scan_result,
    scan_register_range,
    serialize_scan_result,
    write_scan_result,
)
from tests.unit.tools.fixtures import MockRegisterBackend


class TestScanRegisterRange:
    """Tests for scan_register_range."""

    @pytest.mark.asyncio
    async def test_returns_register_interpretations(self) -> None:
        """scan_register_range returns RegisterScanResult with parsed data."""
        backend = MockRegisterBackend({"0b00": "d700", "0b01": "a401"})
        result = await scan_register_range(backend, "0b00", 2)
        assert result.start_register == "0b00"
        assert result.count == 2
        assert len(result.registers) == 2

        reg0 = result.registers[0]
        assert reg0.register == "0b00"
        assert reg0.hex == "d700"
        assert reg0.raw_int == 215
        assert reg0.scaled_x10 == 21.5
        assert reg0.scaled_x100 == 2.15
        assert reg0.bits == {i: ((215 >> i) & 1) != 0 for i in range(16)}

        reg1 = result.registers[1]
        assert reg1.register == "0b01"
        assert reg1.hex == "a401"
        assert reg1.raw_int == 420
        assert reg1.scaled_x10 == 42.0
        assert reg1.scaled_x100 == 4.2

    @pytest.mark.asyncio
    async def test_missing_register_defaults_to_0000(self) -> None:
        """Registers not in backend response get hex '0000'."""
        backend = MockRegisterBackend()
        result = await scan_register_range(backend, "0b00", 1)
        reg = result.registers[0]
        assert reg.hex == "0000"
        assert reg.raw_int == 0
        assert reg.scaled_x10 == 0.0
        assert reg.scaled_x100 == 0.0

    @pytest.mark.asyncio
    async def test_overflow_raises_value_error(self) -> None:
        """When start+count exceeds 256, int_to_reg_address raises ValueError."""
        backend = MockRegisterBackend()
        with pytest.raises(ValueError, match="outside 8-bit address space"):
            await scan_register_range(backend, "0b80", 256)

    @pytest.mark.asyncio
    async def test_scaled_x100_register_parsed(self) -> None:
        """scaled_x100 parser: f401 (little-endian 500) -> 5.00."""
        backend = MockRegisterBackend({"0b4e": "f401"})
        result = await scan_register_range(backend, "0b4e", 1)
        reg = result.registers[0]
        assert reg.scaled_x100 == 5.0


class TestFormatScanResult:
    """Tests for format_scan_result."""

    @pytest.mark.asyncio
    async def test_produces_non_empty_string_with_expected_fields(self) -> None:
        """format_scan_result produces human-readable output with hex, int, etc."""
        backend = MockRegisterBackend({"0b00": "d700"})
        result = await scan_register_range(backend, "0b00", 1)
        formatted = format_scan_result(result)
        assert "Register Scan" in formatted
        assert "0b00" in formatted
        assert "d700" in formatted
        assert "215" in formatted
        assert "21.5" in formatted
        assert "Bits" in formatted
        assert "\u25CF" in formatted or "\u00B7" in formatted

    @pytest.mark.asyncio
    async def test_multi_register_format(self) -> None:
        """Multiple registers appear in output."""
        backend = MockRegisterBackend({"0b00": "d700", "0b01": "a401"})
        result = await scan_register_range(backend, "0b00", 2)
        formatted = format_scan_result(result)
        assert "0b00" in formatted
        assert "0b01" in formatted

    @pytest.mark.asyncio
    async def test_hides_empty_registers_by_default(self) -> None:
        """Empty registers (hex 0000) are omitted by default."""
        backend = MockRegisterBackend({"0b00": "0000", "0b01": "d700", "0b02": "0000"})
        result = await scan_register_range(backend, "0b00", 3)
        formatted = format_scan_result(result)
        assert "0b01     d700" in formatted
        assert "0b00     0000" not in formatted
        assert "0b02     0000" not in formatted
        assert "empty hidden" in formatted

    @pytest.mark.asyncio
    async def test_show_empty_includes_all_registers(self) -> None:
        """include_empty=True shows registers with hex 0000."""
        backend = MockRegisterBackend({"0b00": "0000", "0b01": "d700"})
        result = await scan_register_range(backend, "0b00", 2)
        formatted = format_scan_result(result, include_empty=True)
        assert "0b00" in formatted
        assert "0b01" in formatted
        assert "empty hidden" not in formatted

    @pytest.mark.asyncio
    async def test_format_scan_result_end_register_4_char(self) -> None:
        """format_scan_result displays end_register in 4-char format (0bXX)."""
        backend = MockRegisterBackend({"0b00": "d700", "0b7f": "a401"})
        result = await scan_register_range(backend, "0b00", 128)
        formatted = format_scan_result(result, include_empty=True)
        assert "0b00 - 0b7f" in formatted


class TestSerializeScanResult:
    """Tests for serialize_scan_result."""

    @pytest.mark.asyncio
    async def test_produces_valid_yaml(self) -> None:
        """serialize_scan_result produces parseable YAML."""
        backend = MockRegisterBackend({"0b00": "d700"})
        result = await scan_register_range(backend, "0b00", 1)
        yaml_str = serialize_scan_result(result)
        parsed = yaml.safe_load(yaml_str)
        assert parsed is not None
        assert "format_version" in parsed
        assert parsed["format_version"] == "1"
        assert "scan" in parsed
        assert parsed["scan"]["start_register"] == "0b00"
        assert parsed["scan"]["count"] == 1
        assert "timestamp" in parsed["scan"]
        assert "registers" in parsed
        assert "0b00" in parsed["registers"]
        reg_data = parsed["registers"]["0b00"]
        assert reg_data["hex"] == "d700"
        assert reg_data["raw_int"] == 215
        assert reg_data["scaled_x10"] == 21.5
        assert reg_data["scaled_x100"] == 2.15
        assert "bits" in reg_data
        assert reg_data["bits"][3] is False

    @pytest.mark.asyncio
    async def test_hides_empty_in_yaml_by_default(self) -> None:
        """Empty registers omitted in YAML; scan includes hide_empty."""
        backend = MockRegisterBackend({"0b00": "0000", "0b01": "d700"})
        result = await scan_register_range(backend, "0b00", 2)
        yaml_str = serialize_scan_result(result)
        parsed = yaml.safe_load(yaml_str)
        assert "0b00" not in parsed["registers"]
        assert "0b01" in parsed["registers"]
        assert parsed["scan"].get("hide_empty") is True
        assert parsed["scan"]["registers_shown"] == 1

    @pytest.mark.asyncio
    async def test_null_for_failed_parsers(self) -> None:
        """Invalid hex (e.g. wrong length) yields null for scaled parsers in YAML."""
        backend = MockRegisterBackend(
            {"0b00": "ab"}
        )  # len != 4 triggers decoder failure
        result = await scan_register_range(backend, "0b00", 1)
        yaml_str = serialize_scan_result(result)
        parsed = yaml.safe_load(yaml_str)
        assert parsed["registers"]["0b00"]["scaled_x10"] is None
        assert parsed["registers"]["0b00"]["scaled_x100"] is None


class TestWriteScanResult:
    """Tests for write_scan_result."""

    @pytest.mark.asyncio
    async def test_writes_yaml_file(self, tmp_path: Path) -> None:
        """write_scan_result writes valid YAML to file."""
        backend = MockRegisterBackend({"0b55": "d700"})
        result = await scan_register_range(backend, "0b55", 1)
        out_file = tmp_path / "scan.yaml"
        await write_scan_result(out_file, result)
        assert out_file.exists()
        async with aiofiles.open(out_file, "r", encoding="utf-8") as f:
            content = await f.read()
        parsed = yaml.safe_load(content)
        assert parsed["registers"]["0b55"]["hex"] == "d700"


@pytest.fixture
def yaml_state_with_registers(tmp_path: Path) -> Path:
    """Create YAML state file with register data for YamlRegisterBackend tests."""
    state_file = tmp_path / "state.yaml"
    state_file.write_text('"0b31": "e100"\n"0b4e": "f401"\n')
    return state_file


class TestRegisterScannerWithYamlBackend:
    """Integration-style tests with YamlRegisterBackend (no network)."""

    @pytest.mark.asyncio
    async def test_scan_with_yaml_backend(
        self, yaml_state_with_registers: Path
    ) -> None:
        """scan_register_range works with YamlRegisterBackend."""
        from kospel_cmi.kospel.backend import YamlRegisterBackend

        backend = YamlRegisterBackend(state_file=str(yaml_state_with_registers))
        result = await scan_register_range(backend, "0b00", 256)
        assert result.count == 256
        reg_31 = next(r for r in result.registers if r.register == "0b31")
        assert reg_31.hex == "e100"
        assert reg_31.scaled_x10 == 22.5
        reg_4e = next(r for r in result.registers if r.register == "0b4e")
        assert reg_4e.scaled_x100 == 5.0
