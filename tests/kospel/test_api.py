"""Unit tests for kospel/api.py - HTTP API client with simulator support."""

import pytest
from aioresponses import aioresponses

import aiohttp

from kospel.api import (
    read_register,
    read_registers,
    write_register,
    write_flag_bit,
)


class TestReadRegister:
    """Tests for read_register() function."""

    @pytest.mark.asyncio
    async def test_successful_read(self, api_base_url):
        """Test successful register read."""
        register = "0b55"
        expected_value = "d700"
        url = f"{api_base_url}/{register}/1"

        with aioresponses() as m:
            m.get(url, payload={"regs": {register: expected_value}})

            async with aiohttp.ClientSession() as session:
                result = await read_register(session, api_base_url, register)
                assert result == expected_value

    @pytest.mark.asyncio
    async def test_register_not_in_response(self, api_base_url):
        """Test when register is not in response."""
        register = "0b55"
        url = f"{api_base_url}/{register}/1"

        with aioresponses() as m:
            m.get(url, payload={"regs": {}})

            async with aiohttp.ClientSession() as session:
                result = await read_register(session, api_base_url, register)
                assert result is None

    @pytest.mark.asyncio
    async def test_empty_response(self, api_base_url):
        """Test handling of empty response."""
        register = "0b55"
        url = f"{api_base_url}/{register}/1"

        with aioresponses() as m:
            m.get(url, payload={})

            async with aiohttp.ClientSession() as session:
                result = await read_register(session, api_base_url, register)
                assert result is None

    @pytest.mark.asyncio
    async def test_client_error(self, api_base_url):
        """Test handling of ClientError."""
        register = "0b55"
        url = f"{api_base_url}/{register}/1"

        with aioresponses() as m:
            m.get(url, exception=aiohttp.ClientError("Connection error"))

            async with aiohttp.ClientSession() as session:
                result = await read_register(session, api_base_url, register)
                assert result is None

    @pytest.mark.asyncio
    async def test_client_response_error(self, api_base_url):
        """Test handling of ClientResponseError."""
        register = "0b55"
        url = f"{api_base_url}/{register}/1"

        with aioresponses() as m:
            m.get(url, status=404, payload={"error": "Not found"})

            async with aiohttp.ClientSession() as session:
                result = await read_register(session, api_base_url, register)
                assert result is None

    @pytest.mark.asyncio
    async def test_timeout(self, api_base_url):
        """Test handling of timeout."""
        register = "0b55"
        url = f"{api_base_url}/{register}/1"

        with aioresponses() as m:
            m.get(url, exception=aiohttp.ServerTimeoutError())

            async with aiohttp.ClientSession() as session:
                result = await read_register(session, api_base_url, register)
                assert result is None

    @pytest.mark.asyncio
    async def test_simulation_mode_routing(self, api_base_url, enable_simulation_mode):
        """Test that simulation mode routes to simulator implementation without HTTP calls."""
        register = "0b55"

        # Verify no HTTP calls are made when simulation mode is enabled
        with aioresponses() as m:
            async with aiohttp.ClientSession() as session:
                result = await read_register(session, api_base_url, register)
                # Should use simulator state (returns default "0000" if register not in state)
                assert result is not None
                # Verify no HTTP requests were made in simulation mode
                assert len(m.requests) == 0


class TestReadRegisters:
    """Tests for read_registers() function."""

    @pytest.mark.asyncio
    async def test_successful_batch_read(self, api_base_url):
        """Test successful batch register read."""
        start_register = "0b00"
        count = 3
        expected_regs = {"0b00": "0000", "0b01": "0100", "0b02": "0200"}
        url = f"{api_base_url}/{start_register}/{count}"

        with aioresponses() as m:
            m.get(url, payload={"regs": expected_regs})

            async with aiohttp.ClientSession() as session:
                result = await read_registers(
                    session, api_base_url, start_register, count
                )
                assert result == expected_regs
                assert len(result) == 3

    @pytest.mark.asyncio
    async def test_empty_response(self, api_base_url):
        """Test handling of empty response."""
        start_register = "0b00"
        count = 3
        url = f"{api_base_url}/{start_register}/{count}"

        with aioresponses() as m:
            m.get(url, payload={"regs": {}})

            async with aiohttp.ClientSession() as session:
                result = await read_registers(
                    session, api_base_url, start_register, count
                )
                assert result == {}

    @pytest.mark.asyncio
    async def test_client_error(self, api_base_url):
        """Test handling of ClientError."""
        start_register = "0b00"
        count = 3
        url = f"{api_base_url}/{start_register}/{count}"

        with aioresponses() as m:
            m.get(url, exception=aiohttp.ClientError("Connection error"))

            async with aiohttp.ClientSession() as session:
                result = await read_registers(
                    session, api_base_url, start_register, count
                )
                assert result == {}

    @pytest.mark.asyncio
    async def test_client_response_error(self, api_base_url):
        """Test handling of ClientResponseError."""
        start_register = "0b00"
        count = 3
        url = f"{api_base_url}/{start_register}/{count}"

        with aioresponses() as m:
            m.get(url, status=500, payload={"error": "Internal server error"})

            async with aiohttp.ClientSession() as session:
                result = await read_registers(
                    session, api_base_url, start_register, count
                )
                assert result == {}

    @pytest.mark.asyncio
    async def test_simulation_mode_routing(self, api_base_url, enable_simulation_mode):
        """Test that simulation mode routes to simulator implementation without HTTP calls."""
        start_register = "0b00"
        count = 3

        # Verify no HTTP calls are made when simulation mode is enabled
        with aioresponses() as m:
            async with aiohttp.ClientSession() as session:
                result = await read_registers(
                    session, api_base_url, start_register, count
                )
                # Should use simulator state (returns dict with default "0000" values)
                assert isinstance(result, dict)
                assert len(result) == count
                # Verify no HTTP requests were made in simulation mode
                assert len(m.requests) == 0


class TestWriteRegister:
    """Tests for write_register() function."""

    @pytest.mark.asyncio
    async def test_successful_write(self, api_base_url):
        """Test successful register write."""
        register = "0b55"
        hex_value = "d700"
        url = f"{api_base_url}/{register}"

        with aioresponses() as m:
            m.post(url, payload={"status": "0"})

            async with aiohttp.ClientSession() as session:
                result = await write_register(
                    session, api_base_url, register, hex_value
                )
                assert result is True

    @pytest.mark.asyncio
    async def test_failed_write_non_zero_status(self, api_base_url):
        """Test failed write with non-zero status."""
        register = "0b55"
        hex_value = "d700"
        url = f"{api_base_url}/{register}"

        with aioresponses() as m:
            m.post(url, payload={"status": "1"})

            async with aiohttp.ClientSession() as session:
                result = await write_register(
                    session, api_base_url, register, hex_value
                )
                assert result is False

    @pytest.mark.asyncio
    async def test_client_error(self, api_base_url):
        """Test handling of ClientError."""
        register = "0b55"
        hex_value = "d700"
        url = f"{api_base_url}/{register}"

        with aioresponses() as m:
            m.post(url, exception=aiohttp.ClientError("Connection error"))

            async with aiohttp.ClientSession() as session:
                result = await write_register(
                    session, api_base_url, register, hex_value
                )
                assert result is False

    @pytest.mark.asyncio
    async def test_client_response_error(self, api_base_url):
        """Test handling of ClientResponseError."""
        register = "0b55"
        hex_value = "d700"
        url = f"{api_base_url}/{register}"

        with aioresponses() as m:
            m.post(url, status=500, payload={"error": "Internal server error"})

            async with aiohttp.ClientSession() as session:
                result = await write_register(
                    session, api_base_url, register, hex_value
                )
                assert result is False

    @pytest.mark.asyncio
    async def test_simulation_mode_routing(self, api_base_url, enable_simulation_mode):
        """Test that simulation mode routes to simulator implementation without HTTP calls."""
        register = "0b55"
        hex_value = "d700"

        # Verify no HTTP calls are made when simulation mode is enabled
        with aioresponses() as m:
            async with aiohttp.ClientSession() as session:
                result = await write_register(
                    session, api_base_url, register, hex_value
                )
                # Should use simulator implementation (always returns True)
                assert result is True
                # Verify no HTTP requests were made in simulation mode
                assert len(m.requests) == 0


class TestWriteFlagBit:
    """Tests for write_flag_bit() function."""

    @pytest.mark.asyncio
    async def test_successful_bit_set(self, api_base_url):
        """Test successful flag bit set."""
        register = "0b55"
        bit_index = 3
        state = True
        current_hex = "0000"  # Bit 3 not set

        with aioresponses() as m:
            # Mock read_register call
            read_url = f"{api_base_url}/{register}/1"
            m.get(read_url, payload={"regs": {register: current_hex}})
            # Mock write_register call
            m.post(f"{api_base_url}/{register}", payload={"status": "0"})

            async with aiohttp.ClientSession() as session:
                result = await write_flag_bit(
                    session, api_base_url, register, bit_index, state
                )
                assert result is True

    @pytest.mark.asyncio
    async def test_successful_bit_clear(self, api_base_url):
        """Test successful flag bit clear."""
        register = "0b55"
        bit_index = 3
        state = False
        current_hex = "0800"  # Bit 3 set

        with aioresponses() as m:
            # Mock read_register call
            read_url = f"{api_base_url}/{register}/1"
            m.get(read_url, payload={"regs": {register: current_hex}})
            # Mock write_register call
            m.post(f"{api_base_url}/{register}", payload={"status": "0"})

            async with aiohttp.ClientSession() as session:
                result = await write_flag_bit(
                    session, api_base_url, register, bit_index, state
                )
                assert result is True

    @pytest.mark.asyncio
    async def test_read_failure_returns_false(self, api_base_url):
        """Test that read failure returns False."""
        register = "0b55"
        bit_index = 3
        state = True

        with aioresponses() as m:
            # Mock read_register call failure
            read_url = f"{api_base_url}/{register}/1"
            m.get(read_url, exception=aiohttp.ClientError("Connection error"))

            async with aiohttp.ClientSession() as session:
                result = await write_flag_bit(
                    session, api_base_url, register, bit_index, state
                )
                assert result is False

    @pytest.mark.asyncio
    async def test_bit_already_in_desired_state(self, api_base_url):
        """Test that bit already in desired state returns True without write."""
        register = "0b55"
        bit_index = 3
        state = True
        current_hex = "0800"  # Bit 3 already set

        with aioresponses() as m:
            # Mock read_register call
            read_url = f"{api_base_url}/{register}/1"
            m.get(read_url, payload={"regs": {register: current_hex}})
            # Note: We don't mock POST because write should not be called

            async with aiohttp.ClientSession() as session:
                result = await write_flag_bit(
                    session, api_base_url, register, bit_index, state
                )
                assert result is True
                # Verify write was not called - only GET request should be made
                # aioresponses stores requests as (method, URL) tuples
                post_requests = [req for req in m.requests.keys() if req[0] == "POST"]
                assert len(post_requests) == 0, (
                    "POST request should not be made when bit is already in desired state"
                )

    @pytest.mark.asyncio
    async def test_write_failure_returns_false(self, api_base_url):
        """Test that write failure returns False."""
        register = "0b55"
        bit_index = 3
        state = True
        current_hex = "0000"

        with aioresponses() as m:
            # Mock read_register call
            read_url = f"{api_base_url}/{register}/1"
            m.get(read_url, payload={"regs": {register: current_hex}})
            # Mock write_register call failure
            write_url = f"{api_base_url}/{register}"
            m.post(write_url, exception=aiohttp.ClientError("Write error"))

            async with aiohttp.ClientSession() as session:
                result = await write_flag_bit(
                    session, api_base_url, register, bit_index, state
                )
                assert result is False

    @pytest.mark.asyncio
    async def test_simulation_mode_routing(self, api_base_url, enable_simulation_mode):
        """Test that simulation mode routes to simulator implementation without HTTP calls."""
        register = "0b55"
        bit_index = 3
        state = True

        # Verify no HTTP calls are made when simulation mode is enabled
        with aioresponses() as m:
            async with aiohttp.ClientSession() as session:
                result = await write_flag_bit(
                    session, api_base_url, register, bit_index, state
                )
                # Should use simulator implementation (always returns True)
                assert result is True
                # Verify no HTTP requests were made in simulation mode
                assert len(m.requests) == 0
