"""Unit tests for registers.utils (encoding/decoding and bit utilities)."""

import pytest

from kospel_cmi.exceptions import RegisterValueInvalidError
from kospel_cmi.registers.utils import (
    int_to_reg,
    int_to_reg_address,
    reg_address_to_int,
    reg_to_int,
    validate_register_hex,
    get_bit,
    set_bit,
)


class TestRegToInt:
    """Tests for reg_to_int (little-endian hex string to signed 16-bit int)."""

    @pytest.mark.parametrize(
        ("hex_val", "expected"),
        [
            ("d700", 215),
            ("e100", 225),  # 225 = 0x00e1, little-endian low byte first
            ("0000", 0),
            ("b082", -32080),  # negative, two's complement
            ("ffff", -1),
            ("ff7f", 32767),
            ("0080", -32768),
        ],
    )
    def test_valid_hex_returns_signed_int(self, hex_val: str, expected: int) -> None:
        """Valid little-endian hex string decodes to correct signed integer."""
        assert reg_to_int(hex_val) == expected

    @pytest.mark.parametrize(
        "invalid",
        [
            "",
            "abcde",  # too long (5 chars)
            "ghij",  # non-hex
            "0x00",  # prefix not supported
        ],
    )
    def test_invalid_hex_returns_zero(self, invalid: str) -> None:
        """Invalid or malformed hex string returns 0 (error path)."""
        assert reg_to_int(invalid) == 0


class TestIntToReg:
    """Tests for int_to_reg (signed 16-bit int to little-endian hex string)."""

    @pytest.mark.parametrize(
        "value",
        [0, 215, 225, -1, -32080, 32767, -32768],
    )
    def test_round_trip_with_reg_to_int(self, value: int) -> None:
        """int_to_reg then reg_to_int returns original value."""
        hex_str = int_to_reg(value)
        assert reg_to_int(hex_str) == value

    @pytest.mark.parametrize(
        ("value", "expected_hex"),
        [
            (0, "0000"),
            (215, "d700"),
            (-1, "ffff"),
        ],
    )
    def test_specific_values(self, value: int, expected_hex: str) -> None:
        """Known values produce expected hex strings."""
        assert int_to_reg(value) == expected_hex

    def test_out_of_range_returns_0000(self) -> None:
        """Values outside -32768..32767 hit struct error path and return '0000'."""
        # struct.pack("h", ...) raises for values that don't fit in 16-bit
        assert int_to_reg(32768) == "0000"
        assert int_to_reg(-32769) == "0000"


class TestGetBit:
    """Tests for get_bit (check if bit is set)."""

    @pytest.mark.parametrize(
        ("value", "bit_index", "expected"),
        [
            (0b1010, 1, True),
            (0b1010, 0, False),
            (0b1010, 3, True),
            (0b1010, 2, False),
            (1, 0, True),
            (1, 1, False),
            (0xFFFF, 0, True),
            (0xFFFF, 15, True),
        ],
    )
    def test_bit_set_or_clear(self, value: int, bit_index: int, expected: bool) -> None:
        """get_bit returns True when bit is set, False when clear."""
        assert get_bit(value, bit_index) is expected


class TestSetBit:
    """Tests for set_bit (set or clear a bit)."""

    @pytest.mark.parametrize(
        ("value", "bit_index", "state", "expected_has_bit"),
        [
            (0, 0, True, True),
            (0, 0, False, False),
            (0b1000, 0, True, True),
            (0b1001, 0, False, False),
            (0b1010, 1, False, False),
            (0b1000, 1, True, True),
        ],
    )
    def test_set_bit_then_get_bit(
        self, value: int, bit_index: int, state: bool, expected_has_bit: bool
    ) -> None:
        """set_bit result has expected bit when read with get_bit."""
        result = set_bit(value, bit_index, state)
        assert get_bit(result, bit_index) is expected_has_bit

    def test_set_bit_does_not_affect_other_bits(self) -> None:
        """Setting or clearing one bit leaves other bits unchanged."""
        value = 0b1100
        result_set = set_bit(value, 0, True)
        assert result_set == 0b1101
        result_clear = set_bit(value, 2, False)
        assert result_clear == 0b1000


class TestRegAddressToInt:
    """Tests for reg_address_to_int (e.g. '0b51' -> int)."""

    @pytest.mark.parametrize(
        ("address", "expected"),
        [
            ("0b51", 0x51),
            ("0b00", 0),
            ("0b55", 0x55),
            ("0bff", 0xFF),
        ],
    )
    def test_valid_address_returns_int(self, address: str, expected: int) -> None:
        """Register address string (0bXX) converts to integer."""
        assert reg_address_to_int(address) == expected


class TestIntToRegAddress:
    """Tests for int_to_reg_address (int -> 4-char register address)."""

    @pytest.mark.parametrize(
        ("reg_int", "expected"),
        [
            (0, "0b00"),
            (0x51, "0b51"),
            (0xFF, "0bff"),
        ],
    )
    def test_valid_range_produces_4_char_address(
        self, reg_int: int, expected: str
    ) -> None:
        """Values 0-255 produce correct 4-character addresses."""
        assert int_to_reg_address("0b", reg_int) == expected

    def test_out_of_range_raises(self) -> None:
        """Values outside 0-255 raise ValueError."""
        with pytest.raises(ValueError, match="outside 8-bit address space"):
            int_to_reg_address("0b", 256)
        with pytest.raises(ValueError, match="outside 8-bit address space"):
            int_to_reg_address("0b", -1)


class TestValidateRegisterHex:
    """Tests for validate_register_hex (wire-format validation)."""

    def test_valid_returns_lowercase(self) -> None:
        """Valid hex is normalized to lowercase."""
        assert validate_register_hex("D700") == "d700"
        assert validate_register_hex("0000") == "0000"

    @pytest.mark.parametrize(
        "invalid",
        ["", "123", "12345", "d70g", "xxxx"],
    )
    def test_invalid_raises(self, invalid: str) -> None:
        """Malformed values raise RegisterValueInvalidError."""
        with pytest.raises(RegisterValueInvalidError):
            validate_register_hex(invalid)
