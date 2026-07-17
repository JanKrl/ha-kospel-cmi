"""Shared test fixtures for tools tests."""

from kospel_cmi.registers.utils import int_to_reg_address, reg_address_to_int


class MockRegisterBackend:
    """Mock backend that returns fixed register data.

    Implements only read_registers; sufficient for scan_register_range tests.
    Does not implement read_register or write_register.
    """

    def __init__(self, registers: dict[str, str] | None = None) -> None:
        self.registers = registers or {}

    async def read_registers(self, start_register: str, count: int) -> dict[str, str]:
        result: dict[str, str] = {}
        start_int = reg_address_to_int(start_register)
        prefix = start_register[:2]
        for i in range(count):
            reg_int = start_int + i
            reg_str = int_to_reg_address(prefix, reg_int)
            result[reg_str] = self.registers.get(reg_str, "0000")
        return result
