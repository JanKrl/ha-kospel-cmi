"""Unit tests for registers/decoders.py - Decode functions (hex → Python values)."""

import pytest

from registers.decoders import (
    decode_scaled_temp,
    decode_scaled_pressure,
    decode_heater_mode,
    decode_bit_boolean,
    decode_map,
)
from registers.enums import HeaterMode, ManualMode, WaterHeaterEnabled, PumpStatus, ValvePosition


class TestDecodeScaledTemp:
    """Tests for decode_scaled_temp() function."""

    def test_valid_temperature(self):
        """Test decoding valid temperature value."""
        # "d700" -> 215 -> 21.5°C (scaled by 10) (little-endian format)
        result = decode_scaled_temp("d700", None)
        assert result == 21.5

    def test_zero_temperature(self):
        """Test decoding zero temperature."""
        result = decode_scaled_temp("0000", None)
        assert result == 0.0

    def test_negative_temperature(self):
        """Test decoding negative temperature."""
        # "38ff" -> -200 -> -20.0°C (scaled by 10) (little-endian format)
        result = decode_scaled_temp("38ff", None)
        assert result == -20.0

    def test_small_temperature(self):
        """Test decoding small temperature value."""
        # "0100" -> 1 -> 0.1°C
        result = decode_scaled_temp("0100", None)
        assert result == 0.1

    def test_large_temperature(self):
        """Test decoding large temperature value."""
        # "ff7f" -> 32767 -> 3276.7°C (max value)
        result = decode_scaled_temp("ff7f", None)
        assert result == 3276.7

    def test_invalid_hex(self):
        """Test handling of invalid hex string."""
        result = decode_scaled_temp("invalid", None)
        assert result is None

    def test_malformed_hex(self):
        """Test handling of malformed hex string."""
        result = decode_scaled_temp("123", None)
        assert result is None

    def test_empty_string(self):
        """Test handling of empty string."""
        result = decode_scaled_temp("", None)
        assert result is None

    def test_none_value(self):
        """Test handling of None value."""
        result = decode_scaled_temp(None, None)  # type: ignore
        assert result is None


class TestDecodeScaledPressure:
    """Tests for decode_scaled_pressure() function."""

    def test_valid_pressure(self):
        """Test decoding valid pressure value."""
        # "8813" -> 5000 -> 50.0 (scaled by 100) (little-endian format)
        result = decode_scaled_pressure("8813", None)
        assert result == 50.0

    def test_zero_pressure(self):
        """Test decoding zero pressure."""
        result = decode_scaled_pressure("0000", None)
        assert result == 0.0

    def test_small_pressure(self):
        """Test decoding small pressure value."""
        # "0100" -> 1 -> 0.01
        result = decode_scaled_pressure("0100", None)
        assert result == 0.01

    def test_large_pressure(self):
        """Test decoding large pressure value."""
        # "ff7f" -> 32767 -> 327.67 (max value)
        result = decode_scaled_pressure("ff7f", None)
        assert result == 327.67

    def test_invalid_hex(self):
        """Test handling of invalid hex string."""
        result = decode_scaled_pressure("invalid", None)
        assert result is None

    def test_malformed_hex(self):
        """Test handling of malformed hex string."""
        result = decode_scaled_pressure("123", None)
        assert result is None


class TestDecodeHeaterMode:
    """Tests for decode_heater_mode() function."""

    def test_summer_mode(self):
        """Test decoding SUMMER mode (bit 3=1, bit 5=0)."""
        # Value with bit 3 set: 0x0008 = 8 (binary: 0b1000)
        # Little-endian: "0800"
        result = decode_heater_mode("0800", None)
        assert result == HeaterMode.SUMMER

    def test_winter_mode(self):
        """Test decoding WINTER mode (bit 3=0, bit 5=1)."""
        # Value with bit 5 set: 0x0020 = 32 (binary: 0b100000)
        # Little-endian: "2000"
        result = decode_heater_mode("2000", None)
        assert result == HeaterMode.WINTER

    def test_off_mode(self):
        """Test decoding OFF mode (bit 3=0, bit 5=0)."""
        result = decode_heater_mode("0000", None)
        assert result == HeaterMode.OFF

    def test_off_mode_with_other_bits(self):
        """Test OFF mode when other bits are set but 3 and 5 are clear."""
        # Value with other bits set but 3 and 5 clear: 0x0001 (bit 0 set)
        result = decode_heater_mode("0100", None)
        assert result == HeaterMode.OFF

    def test_summer_mode_preserves_other_bits(self):
        """Test that SUMMER mode works even when other bits are set."""
        # Value with bit 3 set and other bits: 0x0208 = 520 (bits 3 and 9 set)
        # Little-endian: "0802"
        result = decode_heater_mode("0802", None)
        assert result == HeaterMode.SUMMER

    def test_winter_mode_preserves_other_bits(self):
        """Test that WINTER mode works even when other bits are set."""
        # Value with bit 5 set and other bits: 0x0220 = 544 (bits 5 and 9 set)
        # Little-endian: "2002"
        result = decode_heater_mode("2002", None)
        assert result == HeaterMode.WINTER

    def test_invalid_hex(self):
        """Test handling of invalid hex string."""
        result = decode_heater_mode("invalid", None)
        assert result is None

    def test_malformed_hex(self):
        """Test handling of malformed hex string."""
        result = decode_heater_mode("123", None)
        assert result is None

    def test_exception_handling(self):
        """Test exception handling returns None."""
        result = decode_heater_mode(None, None)  # type: ignore
        assert result is None


class TestDecodeBitBoolean:
    """Tests for decode_bit_boolean() function."""

    def test_bit_set_returns_true(self):
        """Test that set bit returns True."""
        # Value 1 has bit 0 set
        result = decode_bit_boolean("0100", 0)  # "0100" -> 1
        assert result is True

    def test_bit_clear_returns_false(self):
        """Test that clear bit returns False."""
        # Value 0 has bit 0 clear
        result = decode_bit_boolean("0000", 0)
        assert result is False

    def test_bit_1_set(self):
        """Test bit 1 set."""
        # Value 2 has bit 1 set
        result = decode_bit_boolean("0200", 1)  # "0200" -> 2
        assert result is True

    def test_bit_1_clear(self):
        """Test bit 1 clear."""
        # Value 1 has bit 1 clear
        result = decode_bit_boolean("0100", 1)
        assert result is False

    def test_bit_3_set(self):
        """Test bit 3 set."""
        # Value 8 has bit 3 set
        result = decode_bit_boolean("0800", 3)
        assert result is True

    def test_bit_5_set(self):
        """Test bit 5 set."""
        # Value 32 has bit 5 set
        result = decode_bit_boolean("2000", 5)
        assert result is True

    def test_bit_9_set(self):
        """Test bit 9 set."""
        # Value 512 has bit 9 set
        result = decode_bit_boolean("0002", 9)  # "0002" -> 512 in little-endian? No, "0002" = 2
        # Actually: 512 = 0x0200, little-endian: "0002"
        # Wait, let me recalculate: 512 = 0x0200, so bytes are [0x00, 0x02]
        # Little-endian string: "0002" -> swap to "0200" -> 512
        # But get_bit needs the integer value, not the hex string
        # decode_bit_boolean calls reg_to_int("0002") -> swaps to "0200" -> 512
        # So "0002" is correct for bit 9
        result = decode_bit_boolean("0002", 9)
        # Actually wait, reg_to_int("0002") swaps bytes to "0200" which is 512
        # But I need to check the actual implementation
        # Let me use a known value: 520 = 512 + 8 has bits 3 and 9 set
        # 520 = 0x0208, little-endian: "0802"
        result = decode_bit_boolean("0802", 9)
        assert result is True

    def test_missing_bit_index_raises_value_error(self):
        """Test that missing bit_index raises ValueError."""
        with pytest.raises(ValueError, match="Bit index is required"):
            decode_bit_boolean("0100", None)  # type: ignore

    def test_invalid_hex_returns_none(self):
        """Test that invalid hex returns None."""
        result = decode_bit_boolean("invalid", 0)
        assert result is None

    def test_malformed_hex_returns_none(self):
        """Test that malformed hex returns None."""
        result = decode_bit_boolean("123", 0)
        assert result is None

    def test_exception_handling_returns_none(self):
        """Test that exceptions return None."""
        result = decode_bit_boolean(None, 0)  # type: ignore
        assert result is None


class TestDecodeMap:
    """Tests for decode_map() factory function."""

    def test_returns_decoder_function(self):
        """Test that decode_map returns a callable decoder function."""
        decoder = decode_map(ManualMode.ENABLED, ManualMode.DISABLED)
        assert callable(decoder)

    def test_bit_set_returns_true_value(self):
        """Test that set bit returns true_value enum."""
        decoder = decode_map(ManualMode.ENABLED, ManualMode.DISABLED)
        # Value 512 has bit 9 set
        result = decoder("0002", 9)  # Bit 9 set
        assert result == ManualMode.ENABLED

    def test_bit_clear_returns_false_value(self):
        """Test that clear bit returns false_value enum."""
        decoder = decode_map(ManualMode.ENABLED, ManualMode.DISABLED)
        # Value 0 has bit 9 clear
        result = decoder("0000", 9)
        assert result == ManualMode.DISABLED

    def test_with_pump_status(self):
        """Test decode_map with PumpStatus enum."""
        decoder = decode_map(PumpStatus.RUNNING, PumpStatus.IDLE)
        # Bit 0 set
        result = decoder("0100", 0)
        assert result == PumpStatus.RUNNING
        # Bit 0 clear
        result = decoder("0000", 0)
        assert result == PumpStatus.IDLE

    def test_with_valve_position(self):
        """Test decode_map with ValvePosition enum."""
        decoder = decode_map(ValvePosition.CO, ValvePosition.DHW)
        # Bit 2 set
        result = decoder("0400", 2)
        assert result == ValvePosition.CO
        # Bit 2 clear
        result = decoder("0000", 2)
        assert result == ValvePosition.DHW

    def test_with_water_heater_enabled(self):
        """Test decode_map with WaterHeaterEnabled enum."""
        decoder = decode_map(WaterHeaterEnabled.ENABLED, WaterHeaterEnabled.DISABLED)
        # Bit 4 set
        result = decoder("1000", 4)
        assert result == WaterHeaterEnabled.ENABLED
        # Bit 4 clear
        result = decoder("0000", 4)
        assert result == WaterHeaterEnabled.DISABLED

    def test_handles_none_value(self):
        """Test that None value returns None."""
        decoder = decode_map(ManualMode.ENABLED, ManualMode.DISABLED)
        result = decoder("invalid", 9)
        assert result is None

    def test_custom_enum_values(self):
        """Test decode_map with custom enum values."""
        class TestEnum:
            YES = "yes"
            NO = "no"
        
        decoder = decode_map(TestEnum.YES, TestEnum.NO)
        result = decoder("0100", 0)  # Bit 0 set
        assert result == TestEnum.YES
        result = decoder("0000", 0)  # Bit 0 clear
        assert result == TestEnum.NO

