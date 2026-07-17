"""Unit tests for registers.encoders."""

import pytest

from kospel_cmi.registers.decoders import decode_heater_mode
from kospel_cmi.registers.encoders import (
    encode_heater_mode,
    encode_bit_boolean,
    encode_map,
    encode_raw_int,
    encode_scaled_x10,
    encode_scaled_x100,
)
from kospel_cmi.registers.enums import HeaterMode, WaterHeaterEnabled
from kospel_cmi.registers.utils import reg_to_int, get_bit


class TestEncodeHeaterMode:
    """Tests for encode_heater_mode (read-modify-write bits 3, 5, 6, 7, 9)."""

    def test_requires_current_hex(self) -> None:
        """Returns None when current_hex is None."""
        assert encode_heater_mode(HeaterMode.SUMMER, current_hex=None) is None

    def test_invalid_current_hex_returns_none(self) -> None:
        """Returns None when current_hex has wrong length or non-hex."""
        assert encode_heater_mode(HeaterMode.SUMMER, current_hex="") is None
        assert encode_heater_mode(HeaterMode.SUMMER, current_hex="00") is None
        assert encode_heater_mode(HeaterMode.SUMMER, current_hex="ghij") is None

    @pytest.mark.parametrize(
        ("value", "current_hex"),
        [
            (HeaterMode.SUMMER, "0000"),
            (HeaterMode.WINTER, "0000"),
            (HeaterMode.OFF, "0000"),
            (HeaterMode.PARTY, "0000"),
            (HeaterMode.VACATION, "0000"),
            (HeaterMode.MANUAL, "0000"),
            (HeaterMode.SUMMER, "2000"),  # overwrite winter
            (HeaterMode.WINTER, "0800"),  # overwrite summer
            (HeaterMode.PARTY, "0800"),  # overwrite summer
        ],
    )
    def test_encodes_mode_bits(self, value: HeaterMode, current_hex: str) -> None:
        """Encoded hex decodes back to the same HeaterMode (round-trip)."""
        result = encode_heater_mode(value, current_hex=current_hex)
        assert result is not None
        assert decode_heater_mode(result) == value

    def test_preserves_other_bits(self) -> None:
        """Encoding heater mode preserves non-mode bits (e.g. bit 4) from current_hex."""
        # Set bit 4 (water heater) in current: 16 = 1<<4, LE "1000"
        current = "1000"
        result = encode_heater_mode(HeaterMode.SUMMER, current_hex=current)
        assert result is not None
        assert decode_heater_mode(result) == HeaterMode.SUMMER
        # Bit 4 should still be set (water heater preserved)
        decoded_int = reg_to_int(result)
        assert get_bit(decoded_int, 4) is True


class TestEncodeBitBoolean:
    """Tests for encode_bit_boolean (single bit read-modify-write)."""

    def test_requires_bit_index(self) -> None:
        """Returns None when bit_index is None."""
        assert encode_bit_boolean(True, bit_index=None, current_hex="0000") is None

    def test_requires_current_hex(self) -> None:
        """Returns None when current_hex is None."""
        assert encode_bit_boolean(True, bit_index=0, current_hex=None) is None

    def test_invalid_current_hex_returns_none(self) -> None:
        """Returns None when current_hex is invalid."""
        assert encode_bit_boolean(True, bit_index=0, current_hex="") is None
        assert encode_bit_boolean(True, bit_index=0, current_hex="ghij") is None

    @pytest.mark.parametrize(
        ("value", "bit_index", "current_hex", "expected_bit"),
        [
            (True, 0, "0000", True),
            (False, 0, "0100", False),
            (True, 5, "0000", True),
            (False, 5, "2000", False),
        ],
    )
    def test_encodes_bit(
        self,
        value: bool,
        bit_index: int,
        current_hex: str,
        expected_bit: bool,
    ) -> None:
        """Encoded hex has correct bit set/clear."""
        result = encode_bit_boolean(value, bit_index=bit_index, current_hex=current_hex)
        assert result is not None
        decoded = reg_to_int(result)
        assert get_bit(decoded, bit_index) == expected_bit


class TestEncodeMap:
    """Tests for encode_map (enum/bool to bit encoder factory)."""

    def test_requires_bit_index(self) -> None:
        """Returns None when bit_index is None."""
        encoder = encode_map(
            true_value=WaterHeaterEnabled.ENABLED,
            false_value=WaterHeaterEnabled.DISABLED,
        )
        assert encoder(WaterHeaterEnabled.ENABLED, bit_index=None, current_hex="0000") is None

    def test_requires_current_hex(self) -> None:
        """Returns None when current_hex is None."""
        encoder = encode_map(
            true_value=WaterHeaterEnabled.ENABLED,
            false_value=WaterHeaterEnabled.DISABLED,
        )
        assert encoder(WaterHeaterEnabled.ENABLED, bit_index=4, current_hex=None) is None

    @pytest.mark.parametrize(
        ("value", "expected_bit"),
        [
            (WaterHeaterEnabled.ENABLED, True),
            (WaterHeaterEnabled.DISABLED, False),
        ],
    )
    def test_enum_to_bit(self, value: WaterHeaterEnabled, expected_bit: bool) -> None:
        """Enum value encodes to correct bit."""
        encoder = encode_map(
            true_value=WaterHeaterEnabled.ENABLED,
            false_value=WaterHeaterEnabled.DISABLED,
        )
        result = encoder(value, bit_index=4, current_hex="0000")
        assert result is not None
        decoded = reg_to_int(result)
        assert get_bit(decoded, 4) == expected_bit

    def test_bool_accepted(self) -> None:
        """Bool value is accepted and encoded."""
        encoder = encode_map(
            true_value=WaterHeaterEnabled.ENABLED,
            false_value=WaterHeaterEnabled.DISABLED,
        )
        result = encoder(True, bit_index=4, current_hex="0000")
        assert result is not None
        decoded = reg_to_int(result)
        assert get_bit(decoded, 4) is True

    def test_unsupported_value_returns_none(self) -> None:
        """Value that is neither enum nor bool returns None."""
        encoder = encode_map(
            true_value=WaterHeaterEnabled.ENABLED,
            false_value=WaterHeaterEnabled.DISABLED,
        )
        assert encoder("invalid", bit_index=4, current_hex="0000") is None


class TestEncodeScaledX10:
    """Tests for encode_scaled_x10 (value * 10)."""

    @pytest.mark.parametrize(
        ("value", "expected_hex_int"),
        [
            (0.0, 0),
            (22.5, 225),
            (10.0, 100),
        ],
    )
    def test_encodes_value(self, value: float, expected_hex_int: int) -> None:
        """Value is scaled by 10 and encoded as register value."""
        result = encode_scaled_x10(value, bit_index=0)  # bit_index ignored
        assert result is not None
        assert reg_to_int(result) == expected_hex_int

    def test_invalid_returns_none(self) -> None:
        """Non-numeric value returns None."""
        # value * 10 will raise for non-numeric; encoder catches Exception
        assert encode_scaled_x10("not a number", bit_index=0) is None  # type: ignore[arg-type]


class TestEncodeScaledX100:
    """Tests for encode_scaled_x100 (value * 100)."""

    @pytest.mark.parametrize(
        ("value", "expected_hex_int"),
        [
            (0.0, 0),
            (5.0, 500),
            (1.0, 100),
        ],
    )
    def test_encodes_value(self, value: float, expected_hex_int: int) -> None:
        """Value is scaled by 100 and encoded as register value."""
        result = encode_scaled_x100(value, bit_index=0)  # bit_index ignored
        assert result is not None
        assert reg_to_int(result) == expected_hex_int

    def test_invalid_returns_none(self) -> None:
        """Non-numeric value returns None."""
        assert encode_scaled_x100("not a number", bit_index=0) is None  # type: ignore[arg-type]


class TestEncodeRawInt:
    """Tests for encode_raw_int (raw 16-bit signed integer)."""

    @pytest.mark.parametrize(
        ("value", "expected_hex"),
        [
            (0, "0000"),
            (1, "0100"),
            (-1, "ffff"),
            (795, "1b03"),
        ],
    )
    def test_encodes_int(self, value: int, expected_hex: str) -> None:
        """Integer encodes to correct hex string."""
        result = encode_raw_int(value, bit_index=0)
        assert result == expected_hex

    def test_invalid_returns_none(self) -> None:
        """Non-integer value returns None."""
        assert encode_raw_int("not an int", bit_index=0) is None  # type: ignore[arg-type]
