"""Unit tests for registers/utils.py - Low-level encoding/decoding utilities."""

from registers.utils import (
    reg_to_int,
    int_to_reg,
    get_bit,
    set_bit,
    reg_address_to_int,
)


class TestRegToInt:
    """Tests for reg_to_int() function."""

    def test_positive_value(self):
        """Test decoding positive hex value."""
        # "d700" -> 0x00d7 -> 215
        assert reg_to_int("d700") == 215

    def test_zero(self):
        """Test decoding zero value."""
        assert reg_to_int("0000") == 0

    def test_negative_value(self):
        """Test decoding negative value (two's complement)."""
        # "b082" -> 0x82b0 -> -32080 (unsigned 33456 as signed 16-bit)
        assert reg_to_int("b082") == -32080

    def test_boundary_max_positive(self):
        """Test maximum positive value."""
        # 32767 -> "ff7f" (little-endian) -> 32767
        assert reg_to_int("ff7f") == 32767

    def test_boundary_min_negative(self):
        """Test minimum negative value."""
        # -32768 -> "0080" (little-endian) -> -32768
        assert reg_to_int("0080") == -32768

    def test_small_positive(self):
        """Test small positive value."""
        # "0100" -> 0x0001 -> 1
        assert reg_to_int("0100") == 1

    def test_medium_positive(self):
        """Test medium positive value."""
        # "ff00" -> 0x00ff -> 255
        assert reg_to_int("ff00") == 255

    def test_roundtrip_positive(self):
        """Test roundtrip conversion for positive value."""
        original = 215
        hex_val = int_to_reg(original)
        decoded = reg_to_int(hex_val)
        assert decoded == original

    def test_roundtrip_negative(self):
        """Test roundtrip conversion for negative value."""
        original = -32080
        hex_val = int_to_reg(original)
        decoded = reg_to_int(hex_val)
        assert decoded == original

    def test_roundtrip_zero(self):
        """Test roundtrip conversion for zero."""
        original = 0
        hex_val = int_to_reg(original)
        decoded = reg_to_int(hex_val)
        assert decoded == original

    def test_invalid_hex_string(self):
        """Test handling of invalid hex string."""
        # Should return 0 and log error
        result = reg_to_int("invalid")
        assert result == 0

    def test_non_hex_characters(self):
        """Test handling of non-hex characters."""
        result = reg_to_int("gggg")
        assert result == 0

    def test_short_string(self):
        """Test handling of too-short string."""
        result = reg_to_int("123")
        # May raise exception or return 0 depending on implementation
        # Current implementation will try to swap and may fail
        assert isinstance(result, int)

    def test_empty_string(self):
        """Test handling of empty string."""
        result = reg_to_int("")
        assert result == 0

    def test_none_value(self):
        """Test handling of None value."""
        result = reg_to_int(None)  # type: ignore
        assert result == 0


class TestIntToReg:
    """Tests for int_to_reg() function."""

    def test_positive_value(self):
        """Test encoding positive integer."""
        # 215 -> 0x00d7 -> "00d7" -> "d700"
        assert int_to_reg(215) == "d700"

    def test_zero(self):
        """Test encoding zero."""
        assert int_to_reg(0) == "0000"

    def test_negative_value(self):
        """Test encoding negative integer."""
        # -32080 -> 0x82b0 (two's complement) -> "82b0" -> "b082"
        assert int_to_reg(-32080) == "b082"

    def test_boundary_max_positive(self):
        """Test maximum positive value."""
        assert int_to_reg(32767) == "ff7f"

    def test_boundary_min_negative(self):
        """Test minimum negative value."""
        assert int_to_reg(-32768) == "0080"

    def test_small_positive(self):
        """Test small positive value."""
        assert int_to_reg(1) == "0100"

    def test_medium_positive(self):
        """Test medium positive value."""
        assert int_to_reg(255) == "ff00"

    def test_roundtrip_positive(self):
        """Test roundtrip conversion for positive value."""
        original = 215
        hex_val = int_to_reg(original)
        decoded = reg_to_int(hex_val)
        assert decoded == original

    def test_roundtrip_negative(self):
        """Test roundtrip conversion for negative value."""
        original = -32080
        hex_val = int_to_reg(original)
        decoded = reg_to_int(hex_val)
        assert decoded == original

    def test_out_of_range_positive(self):
        """Test handling of out-of-range positive value."""
        # Values > 32767 will wrap around
        result = int_to_reg(32768)
        # Should wrap to -32768 or handle gracefully
        assert isinstance(result, str)
        assert len(result) == 4

    def test_out_of_range_negative(self):
        """Test handling of out-of-range negative value."""
        # Values < -32768 will wrap around
        result = int_to_reg(-32769)
        # Should wrap or handle gracefully
        assert isinstance(result, str)
        assert len(result) == 4

    def test_invalid_type(self):
        """Test handling of invalid type."""
        # Should return "0000" and log error
        result = int_to_reg("invalid")  # type: ignore
        assert result == "0000"


class TestRegToIntRoundtrip:
    """Tests for roundtrip conversion reg_to_int(int_to_reg())."""

    def test_various_values(self):
        """Test roundtrip conversion for various values."""
        test_values = [
            0,
            1,
            255,
            215,
            32767,
            -1,
            -128,
            -32768,
            -32080,
            1000,
            -1000,
        ]
        for value in test_values:
            hex_val = int_to_reg(value)
            decoded = reg_to_int(hex_val)
            assert decoded == value, (
                f"Roundtrip failed for {value}: {hex_val} -> {decoded}"
            )

    def test_roundtrip_consistency(self):
        """Test that roundtrip conversion is consistent."""
        for i in range(-32768, 32768, 1000):  # Sample values
            hex_val = int_to_reg(i)
            decoded = reg_to_int(hex_val)
            assert decoded == i, f"Roundtrip failed for {i}"


class TestGetBit:
    """Tests for get_bit() function."""

    def test_bit_0_set(self):
        """Test bit 0 is set."""
        # Value 1 has bit 0 set
        assert get_bit(1, 0) is True

    def test_bit_0_clear(self):
        """Test bit 0 is clear."""
        # Value 0 has bit 0 clear
        assert get_bit(0, 0) is False

    def test_bit_1_set(self):
        """Test bit 1 is set."""
        # Value 2 has bit 1 set
        assert get_bit(2, 1) is True

    def test_bit_1_clear(self):
        """Test bit 1 is clear."""
        # Value 1 has bit 1 clear
        assert get_bit(1, 1) is False

    def test_bit_3_set(self):
        """Test bit 3 is set (used in heater mode)."""
        # Value 8 (0x08) has bit 3 set
        assert get_bit(8, 3) is True

    def test_bit_5_set(self):
        """Test bit 5 is set (used in heater mode)."""
        # Value 32 (0x20) has bit 5 set
        assert get_bit(32, 5) is True

    def test_bit_9_set(self):
        """Test bit 9 is set (used for manual mode)."""
        # Value 512 (0x200) has bit 9 set
        assert get_bit(512, 9) is True

    def test_bit_15_set(self):
        """Test bit 15 is set (MSB)."""
        # Value 32768 (0x8000) has bit 15 set
        value = 32768  # 1 << 15
        assert get_bit(value, 15) is True

    def test_multiple_bits(self):
        """Test multiple bits set."""
        # Value 520 = 512 + 8 has bits 3 and 9 set
        assert get_bit(520, 3) is True
        assert get_bit(520, 9) is True
        assert get_bit(520, 0) is False
        assert get_bit(520, 1) is False

    def test_all_bits_clear(self):
        """Test all bits clear."""
        for i in range(16):
            assert get_bit(0, i) is False

    def test_all_bits_set(self):
        """Test all bits set (for 16-bit value)."""
        value = 0xFFFF  # All bits set
        for i in range(16):
            assert get_bit(value, i) is True


class TestSetBit:
    """Tests for set_bit() function."""

    def test_set_bit_0(self):
        """Test setting bit 0."""
        result = set_bit(0, 0, True)
        assert result == 1
        assert get_bit(result, 0) is True

    def test_clear_bit_0(self):
        """Test clearing bit 0."""
        result = set_bit(1, 0, False)
        assert result == 0
        assert get_bit(result, 0) is False

    def test_set_bit_3(self):
        """Test setting bit 3."""
        result = set_bit(0, 3, True)
        assert result == 8
        assert get_bit(result, 3) is True

    def test_clear_bit_3(self):
        """Test clearing bit 3."""
        result = set_bit(8, 3, False)
        assert result == 0
        assert get_bit(result, 3) is False

    def test_set_bit_5(self):
        """Test setting bit 5."""
        result = set_bit(0, 5, True)
        assert result == 32
        assert get_bit(result, 5) is True

    def test_set_bit_9(self):
        """Test setting bit 9."""
        result = set_bit(0, 9, True)
        assert result == 512
        assert get_bit(result, 9) is True

    def test_preserve_other_bits_set(self):
        """Test that setting a bit preserves other bits."""
        original = 8  # Bit 3 set
        result = set_bit(original, 5, True)
        assert result == 40  # Bits 3 and 5 set
        assert get_bit(result, 3) is True  # Original bit preserved
        assert get_bit(result, 5) is True  # New bit set

    def test_preserve_other_bits_clear(self):
        """Test that clearing a bit preserves other bits."""
        original = 40  # Bits 3 and 5 set
        result = set_bit(original, 5, False)
        assert result == 8  # Only bit 3 set
        assert get_bit(result, 3) is True  # Original bit preserved
        assert get_bit(result, 5) is False  # Bit cleared

    def test_multiple_bit_operations(self):
        """Test multiple bit operations."""
        value = 0
        value = set_bit(value, 0, True)  # Set bit 0
        value = set_bit(value, 3, True)  # Set bit 3
        value = set_bit(value, 5, True)  # Set bit 5
        value = set_bit(value, 9, True)  # Set bit 9
        assert value == 1 + 8 + 32 + 512  # 553
        assert get_bit(value, 0) is True
        assert get_bit(value, 3) is True
        assert get_bit(value, 5) is True
        assert get_bit(value, 9) is True

    def test_no_change_when_already_set(self):
        """Test no change when bit is already set."""
        original = 8  # Bit 3 set
        result = set_bit(original, 3, True)
        assert result == original

    def test_no_change_when_already_clear(self):
        """Test no change when bit is already clear."""
        original = 0  # Bit 3 clear
        result = set_bit(original, 3, False)
        assert result == original


class TestRegAddressToInt:
    """Tests for reg_address_to_int() function."""

    def test_valid_address(self):
        """Test valid register address conversion."""
        assert reg_address_to_int("0b51") == 0x51
        assert reg_address_to_int("0b51") == 81

    def test_minimum_address(self):
        """Test minimum address."""
        assert reg_address_to_int("0b00") == 0x00
        assert reg_address_to_int("0b00") == 0

    def test_maximum_address(self):
        """Test maximum address."""
        assert reg_address_to_int("0bff") == 0xFF
        assert reg_address_to_int("0bff") == 255

    def test_various_addresses(self):
        """Test various address conversions."""
        test_cases = [
            ("0b00", 0),
            ("0b01", 1),
            ("0b0a", 10),
            ("0b10", 16),
            ("0b51", 81),
            ("0b55", 85),
            ("0b68", 104),
            ("0b8a", 138),
            ("0b8d", 141),
            ("0bff", 255),
        ]
        for address, expected in test_cases:
            assert reg_address_to_int(address) == expected
