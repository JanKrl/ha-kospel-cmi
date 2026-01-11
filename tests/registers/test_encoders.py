"""Unit tests for registers/encoders.py - Encode functions (Python values → hex)."""

from registers.encoders import (
    encode_scaled_temp,
    encode_scaled_pressure,
    encode_heater_mode,
    encode_bit_boolean,
    encode_map,
)
from registers.enums import HeaterMode, ManualMode, WaterHeaterEnabled
from registers.utils import reg_to_int, get_bit


class TestEncodeScaledTemp:
    """Tests for encode_scaled_temp() function."""

    def test_valid_temperature(self):
        """Test encoding valid temperature value."""
        # 21.5°C -> 215 (×10) -> "d700"
        result = encode_scaled_temp(21.5, None, None)
        assert result == "d700"

    def test_zero_temperature(self):
        """Test encoding zero temperature."""
        result = encode_scaled_temp(0.0, None, None)
        assert result == "0000"

    def test_rounding_truncates(self):
        """Test that rounding truncates to int."""
        # 21.56°C -> 215.6 -> truncates to 215 -> "d700"
        result = encode_scaled_temp(21.56, None, None)
        assert result == "d700"

    def test_small_temperature(self):
        """Test encoding small temperature value."""
        # 0.1°C -> 1 -> "0100"
        result = encode_scaled_temp(0.1, None, None)
        assert result == "0100"

    def test_large_temperature(self):
        """Test encoding large temperature value."""
        # 3276.7°C -> 32767 (max) -> "ff7f"
        result = encode_scaled_temp(3276.7, None, None)
        assert result == "ff7f"

    def test_negative_temperature(self):
        """Test encoding negative temperature."""
        # -20.0°C -> -200 -> "38ff"
        result = encode_scaled_temp(-20.0, None, None)
        assert result == "38ff"

    def test_roundtrip_encoding(self):
        """Test roundtrip encoding and decoding."""
        from registers.decoders import decode_scaled_temp
        
        original_temp = 21.5
        encoded = encode_scaled_temp(original_temp, None, None)
        decoded = decode_scaled_temp(encoded, None)
        assert decoded == original_temp

    def test_invalid_type_none(self):
        """Test handling of None value."""
        result = encode_scaled_temp(None, None, None)  # type: ignore
        assert result is None

    def test_invalid_type_string(self):
        """Test handling of string value."""
        result = encode_scaled_temp("invalid", None, None)  # type: ignore
        assert result is None


class TestEncodeScaledPressure:
    """Tests for encode_scaled_pressure() function."""

    def test_valid_pressure(self):
        """Test encoding valid pressure value."""
        # 50.0 -> 5000 (×100) -> "8813"
        result = encode_scaled_pressure(50.0, None, None)
        assert result == "8813"

    def test_zero_pressure(self):
        """Test encoding zero pressure."""
        result = encode_scaled_pressure(0.0, None, None)
        assert result == "0000"

    def test_small_pressure(self):
        """Test encoding small pressure value."""
        # 0.01 -> 1 -> "0100"
        result = encode_scaled_pressure(0.01, None, None)
        assert result == "0100"

    def test_large_pressure(self):
        """Test encoding large pressure value."""
        # 327.67 -> 32767 (max) -> "ff7f"
        result = encode_scaled_pressure(327.67, None, None)
        assert result == "ff7f"

    def test_roundtrip_encoding(self):
        """Test roundtrip encoding and decoding."""
        from registers.decoders import decode_scaled_pressure
        
        original_pressure = 50.0
        encoded = encode_scaled_pressure(original_pressure, None, None)
        decoded = decode_scaled_pressure(encoded, None)
        assert decoded == original_pressure

    def test_invalid_type_none(self):
        """Test handling of None value."""
        result = encode_scaled_pressure(None, None, None)  # type: ignore
        assert result is None

    def test_invalid_type_string(self):
        """Test handling of string value."""
        result = encode_scaled_pressure("invalid", None, None)  # type: ignore
        assert result is None


class TestEncodeHeaterMode:
    """Tests for encode_heater_mode() function."""

    def test_summer_mode(self):
        """Test encoding SUMMER mode."""
        # Current hex: "0000", should set bit 3, clear bit 5
        # Result: bit 3=1, bit 5=0 -> 0x0008 = 8 -> "0800"
        result = encode_heater_mode(HeaterMode.SUMMER, None, "0000")
        assert result == "0800"
        # Verify bits are correct
        value = reg_to_int(result)
        assert get_bit(value, 3) is True
        assert get_bit(value, 5) is False

    def test_winter_mode(self):
        """Test encoding WINTER mode."""
        # Current hex: "0000", should clear bit 3, set bit 5
        # Result: bit 3=0, bit 5=1 -> 0x0020 = 32 -> "2000"
        result = encode_heater_mode(HeaterMode.WINTER, None, "0000")
        assert result == "2000"
        # Verify bits are correct
        value = reg_to_int(result)
        assert get_bit(value, 3) is False
        assert get_bit(value, 5) is True

    def test_off_mode(self):
        """Test encoding OFF mode."""
        # Current hex: "0800" (summer mode), should clear bits 3 and 5
        # Result: bit 3=0, bit 5=0 -> "0000"
        result = encode_heater_mode(HeaterMode.OFF, None, "0800")
        assert result == "0000"
        # Verify bits are correct
        value = reg_to_int(result)
        assert get_bit(value, 3) is False
        assert get_bit(value, 5) is False

    def test_preserves_other_bits_summer(self):
        """Test that SUMMER mode preserves other bits."""
        # Current hex with other bits set: "0200" (bit 9 set)
        # After encoding SUMMER: bit 3 set, bit 5 clear, bit 9 preserved
        # Result: 0x0208 = 520 -> "0802"
        current_hex = "0002"  # Bit 9 set (0x0200)
        result = encode_heater_mode(HeaterMode.SUMMER, None, current_hex)
        value = reg_to_int(result)
        assert get_bit(value, 3) is True  # SUMMER bit set
        assert get_bit(value, 5) is False  # WINTER bit clear
        assert get_bit(value, 9) is True  # Other bit preserved

    def test_preserves_other_bits_winter(self):
        """Test that WINTER mode preserves other bits."""
        # Current hex with other bits set: "0200" (bit 9 set)
        # After encoding WINTER: bit 3 clear, bit 5 set, bit 9 preserved
        current_hex = "0002"  # Bit 9 set
        result = encode_heater_mode(HeaterMode.WINTER, None, current_hex)
        value = reg_to_int(result)
        assert get_bit(value, 3) is False  # SUMMER bit clear
        assert get_bit(value, 5) is True  # WINTER bit set
        assert get_bit(value, 9) is True  # Other bit preserved

    def test_preserves_other_bits_off(self):
        """Test that OFF mode preserves other bits."""
        # Current hex with bits 3 and 9 set: "0802"
        # After encoding OFF: bits 3 and 5 clear, bit 9 preserved
        current_hex = "0802"  # Bits 3 and 9 set
        result = encode_heater_mode(HeaterMode.OFF, None, current_hex)
        value = reg_to_int(result)
        assert get_bit(value, 3) is False  # SUMMER bit clear
        assert get_bit(value, 5) is False  # WINTER bit clear
        assert get_bit(value, 9) is True  # Other bit preserved

    def test_missing_current_hex_returns_none(self):
        """Test that missing current_hex returns None."""
        result = encode_heater_mode(HeaterMode.SUMMER, None, None)
        assert result is None

    def test_read_modify_write_pattern(self):
        """Test read-modify-write pattern verification."""
        # Start with value that has multiple bits set
        current_hex = "1802"  # Bits 3, 4, and 9 set
        result = encode_heater_mode(HeaterMode.WINTER, None, current_hex)
        value = reg_to_int(result)
        # Verify only mode bits changed
        assert get_bit(value, 3) is False  # Cleared
        assert get_bit(value, 5) is True  # Set
        # Other bits should be preserved (bits 4 and 9)
        assert get_bit(value, 4) is True
        assert get_bit(value, 9) is True


class TestEncodeBitBoolean:
    """Tests for encode_bit_boolean() function."""

    def test_set_bit(self):
        """Test setting a bit."""
        # Current hex: "0000", set bit 3 -> "0800"
        result = encode_bit_boolean(True, 3, "0000")
        assert result == "0800"
        value = reg_to_int(result)
        assert get_bit(value, 3) is True

    def test_clear_bit(self):
        """Test clearing a bit."""
        # Current hex: "0800" (bit 3 set), clear bit 3 -> "0000"
        result = encode_bit_boolean(False, 3, "0800")
        assert result == "0000"
        value = reg_to_int(result)
        assert get_bit(value, 3) is False

    def test_set_bit_5(self):
        """Test setting bit 5."""
        result = encode_bit_boolean(True, 5, "0000")
        assert result == "2000"
        value = reg_to_int(result)
        assert get_bit(value, 5) is True

    def test_clear_bit_5(self):
        """Test clearing bit 5."""
        result = encode_bit_boolean(False, 5, "2000")
        assert result == "0000"
        value = reg_to_int(result)
        assert get_bit(value, 5) is False

    def test_set_bit_9(self):
        """Test setting bit 9."""
        result = encode_bit_boolean(True, 9, "0000")
        assert result == "0002"
        value = reg_to_int(result)
        assert get_bit(value, 9) is True

    def test_preserves_other_bits_set(self):
        """Test that setting a bit preserves other bits."""
        # Current hex: "0800" (bit 3 set), set bit 5
        result = encode_bit_boolean(True, 5, "0800")
        value = reg_to_int(result)
        assert get_bit(value, 3) is True  # Original bit preserved
        assert get_bit(value, 5) is True  # New bit set

    def test_preserves_other_bits_clear(self):
        """Test that clearing a bit preserves other bits."""
        # Current hex: "2800" (bits 3 and 5 set), clear bit 5
        result = encode_bit_boolean(False, 5, "2800")
        value = reg_to_int(result)
        assert get_bit(value, 3) is True  # Original bit preserved
        assert get_bit(value, 5) is False  # Bit cleared

    def test_missing_bit_index_returns_none(self):
        """Test that missing bit_index returns None."""
        result = encode_bit_boolean(True, None, "0000")  # type: ignore
        assert result is None

    def test_missing_current_hex_returns_none(self):
        """Test that missing current_hex returns None."""
        result = encode_bit_boolean(True, 3, None)  # type: ignore
        assert result is None

    def test_invalid_current_hex_returns_none(self):
        """Test that invalid current_hex returns None."""
        result = encode_bit_boolean(True, 3, "invalid")
        assert result is None


class TestEncodeMap:
    """Tests for encode_map() factory function."""

    def test_returns_encoder_function(self):
        """Test that encode_map returns a callable encoder function."""
        encoder = encode_map(ManualMode.ENABLED, ManualMode.DISABLED)
        assert callable(encoder)

    def test_enum_to_bit_true_value(self):
        """Test that enum matching true_value encodes to bit set."""
        encoder = encode_map(ManualMode.ENABLED, ManualMode.DISABLED)
        result = encoder(ManualMode.ENABLED, 9, "0000")
        assert result == "0002"  # Bit 9 set
        value = reg_to_int(result)
        assert get_bit(value, 9) is True

    def test_enum_to_bit_false_value(self):
        """Test that enum matching false_value encodes to bit clear."""
        encoder = encode_map(ManualMode.ENABLED, ManualMode.DISABLED)
        result = encoder(ManualMode.DISABLED, 9, "0002")  # Bit 9 set
        assert result == "0000"  # Bit 9 clear
        value = reg_to_int(result)
        assert get_bit(value, 9) is False

    def test_boolean_to_bit_true(self):
        """Test that boolean True encodes to bit set."""
        encoder = encode_map(ManualMode.ENABLED, ManualMode.DISABLED)
        result = encoder(True, 9, "0000")
        assert result == "0002"  # Bit 9 set
        value = reg_to_int(result)
        assert get_bit(value, 9) is True

    def test_boolean_to_bit_false(self):
        """Test that boolean False encodes to bit clear."""
        encoder = encode_map(ManualMode.ENABLED, ManualMode.DISABLED)
        result = encoder(False, 9, "0002")  # Bit 9 set
        assert result == "0000"  # Bit 9 clear
        value = reg_to_int(result)
        assert get_bit(value, 9) is False

    def test_with_water_heater_enabled(self):
        """Test encode_map with WaterHeaterEnabled enum."""
        encoder = encode_map(WaterHeaterEnabled.ENABLED, WaterHeaterEnabled.DISABLED)
        # Encode ENABLED
        result = encoder(WaterHeaterEnabled.ENABLED, 4, "0000")
        value = reg_to_int(result)
        assert get_bit(value, 4) is True
        # Encode DISABLED
        result = encoder(WaterHeaterEnabled.DISABLED, 4, "1000")
        value = reg_to_int(result)
        assert get_bit(value, 4) is False

    def test_preserves_other_bits(self):
        """Test that encode_map preserves other bits."""
        encoder = encode_map(ManualMode.ENABLED, ManualMode.DISABLED)
        # Current hex with bit 3 set: "0800"
        result = encoder(ManualMode.ENABLED, 9, "0800")
        value = reg_to_int(result)
        assert get_bit(value, 3) is True  # Original bit preserved
        assert get_bit(value, 9) is True  # New bit set

    def test_missing_bit_index_returns_none(self):
        """Test that missing bit_index returns None."""
        encoder = encode_map(ManualMode.ENABLED, ManualMode.DISABLED)
        result = encoder(ManualMode.ENABLED, None, "0000")  # type: ignore
        assert result is None

    def test_missing_current_hex_returns_none(self):
        """Test that missing current_hex returns None."""
        encoder = encode_map(ManualMode.ENABLED, ManualMode.DISABLED)
        result = encoder(ManualMode.ENABLED, 9, None)  # type: ignore
        assert result is None

    def test_invalid_value_type_returns_none(self):
        """Test that invalid value type returns None."""
        encoder = encode_map(ManualMode.ENABLED, ManualMode.DISABLED)
        result = encoder("invalid", 9, "0000")  # type: ignore
        assert result is None

    def test_unsupported_value_type_returns_none(self):
        """Test that unsupported value type returns None."""
        encoder = encode_map(ManualMode.ENABLED, ManualMode.DISABLED)
        result = encoder(123, 9, "0000")  # type: ignore
        assert result is None

