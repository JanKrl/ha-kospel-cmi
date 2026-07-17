"""Unit tests for registers.decoders."""

import pytest

from kospel_cmi.registers.decoders import (
    decode_heater_mode,
    decode_bit_boolean,
    decode_map,
    decode_raw_int,
    decode_scaled_x10,
    decode_scaled_x100,
)
from kospel_cmi.registers.enums import HeaterMode, WaterHeaterEnabled


class TestDecodeHeaterMode:
    """Tests for decode_heater_mode (register 0b55, bits 3, 5, 6, 7, 9)."""

    @pytest.mark.parametrize(
        ("hex_val", "expected"),
        [
            # Summer: bit 3=1. 1<<3 = 8. "0800" = 8 in LE
            ("0800", HeaterMode.SUMMER),
            # Winter: bit 5=1. 1<<5 = 32. "2000" = 32 in LE
            ("2000", HeaterMode.WINTER),
            # Off: all mode bits cleared
            ("0000", HeaterMode.OFF),
            ("1000", HeaterMode.OFF),  # 16 = bit 4 only (water heater), no mode bits
            # Party: bit 6=1. 1<<6 = 64. "4000" = 64 in LE
            ("4000", HeaterMode.PARTY),
            # Vacation: bit 7=1. 1<<7 = 128. "8000" = 128 in LE
            ("8000", HeaterMode.VACATION),
            # Manual: bit 9=1. 1<<9 = 512. "0002" = 512 in LE
            ("0002", HeaterMode.MANUAL),
            # 215 = 0xd7 has bits 3,5,6,7 set -> PARTY (highest priority)
            ("d700", HeaterMode.PARTY),
        ],
    )
    def test_valid_hex_returns_heater_mode(
        self, hex_val: str, expected: HeaterMode
    ) -> None:
        """Valid 4-char hex decodes to correct HeaterMode."""
        assert decode_heater_mode(hex_val) == expected

    @pytest.mark.parametrize(
        "invalid",
        [None, "", "00", "00000", "ghij"],
    )
    def test_invalid_hex_returns_none(self, invalid: str) -> None:
        """None, wrong length, or non-hex returns None."""
        assert decode_heater_mode(invalid) is None


class TestDecodeBitBoolean:
    """Tests for decode_bit_boolean (single bit to bool)."""

    def test_requires_bit_index(self) -> None:
        """Raises ValueError when bit_index is None."""
        with pytest.raises(ValueError, match="Bit index is required"):
            decode_bit_boolean("0000", bit_index=None)

    @pytest.mark.parametrize(
        ("hex_val", "bit_index", "expected"),
        [
            ("0100", 0, True),   # bit 0 set in LE "0100" -> 1
            ("0000", 0, False),
            ("0200", 1, True),  # bit 1 set
            ("0000", 1, False),
            ("ffff", 0, True),
            ("ffff", 15, True),
        ],
    )
    def test_valid_hex_returns_bool(
        self, hex_val: str, bit_index: int, expected: bool
    ) -> None:
        """Valid 4-char hex and bit_index return correct bool."""
        assert decode_bit_boolean(hex_val, bit_index) == expected

    @pytest.mark.parametrize(
        "invalid",
        [None, "", "00", "00000", "zzzz"],
    )
    def test_invalid_hex_returns_none(self, invalid: str) -> None:
        """Invalid hex returns None."""
        assert decode_bit_boolean(invalid, 0) is None


class TestDecodeMap:
    """Tests for decode_map (bit to enum true/false)."""

    def test_returns_decoder_callable(self) -> None:
        """decode_map returns a callable that accepts hex_val and bit_index."""
        decoder = decode_map(
            true_value=WaterHeaterEnabled.ENABLED,
            false_value=WaterHeaterEnabled.DISABLED,
        )
        assert callable(decoder)
        # Bit 4 set -> True -> ENABLED
        assert decoder("1000", 4) == WaterHeaterEnabled.ENABLED
        # Bit 4 clear -> False -> DISABLED
        assert decoder("0000", 4) == WaterHeaterEnabled.DISABLED

    def test_invalid_hex_returns_none(self) -> None:
        """When decode_bit_boolean returns None, decode_map returns None."""
        decoder = decode_map(
            true_value=WaterHeaterEnabled.ENABLED,
            false_value=WaterHeaterEnabled.DISABLED,
        )
        assert decoder("", 4) is None


class TestDecodeScaledX10:
    """Tests for decode_scaled_x10 (value / 10)."""

    @pytest.mark.parametrize(
        ("hex_val", "expected"),
        [
            ("0000", 0.0),
            ("e100", 22.5),   # 225 -> 22.5
            ("6400", 10.0),  # 100 -> 10.0
        ],
    )
    def test_valid_hex_returns_value(
        self, hex_val: str, expected: float
    ) -> None:
        """Valid 4-char hex decodes to value (value/10)."""
        assert decode_scaled_x10(hex_val) == pytest.approx(expected)

    @pytest.mark.parametrize(
        "invalid",
        [None, "", "00", "00000", "ghij"],
    )
    def test_invalid_hex_returns_none(self, invalid: str) -> None:
        """Invalid hex returns None."""
        assert decode_scaled_x10(invalid) is None


class TestDecodeScaledX100:
    """Tests for decode_scaled_x100 (value / 100)."""

    @pytest.mark.parametrize(
        ("hex_val", "expected"),
        [
            ("0000", 0.0),
            ("f401", 5.0),   # 500 in LE -> 5.0
            ("6400", 1.0),   # 100 in LE -> 1.0
        ],
    )
    def test_valid_hex_returns_value(
        self, hex_val: str, expected: float
    ) -> None:
        """Valid 4-char hex decodes to value (value/100)."""
        assert decode_scaled_x100(hex_val) == pytest.approx(expected)

    @pytest.mark.parametrize(
        "invalid",
        [None, "", "00", "00000", "ghij"],
    )
    def test_invalid_hex_returns_none(self, invalid: str) -> None:
        """Invalid hex returns None."""
        assert decode_scaled_x100(invalid) is None


class TestDecodeRawInt:
    """Tests for decode_raw_int (raw 16-bit signed integer)."""

    @pytest.mark.parametrize(
        ("hex_val", "expected"),
        [
            ("0000", 0),
            ("0100", 1),
            ("ffff", -1),
            ("1b03", 795),
            ("efff", -17),
        ],
    )
    def test_valid_hex_returns_int(self, hex_val: str, expected: int) -> None:
        """Valid 4-char hex decodes to raw signed integer."""
        assert decode_raw_int(hex_val) == expected

    @pytest.mark.parametrize(
        "invalid",
        [None, "", "00", "00000", "ghij"],
    )
    def test_invalid_hex_returns_none(self, invalid: str) -> None:
        """Invalid hex returns None."""
        assert decode_raw_int(invalid) is None
