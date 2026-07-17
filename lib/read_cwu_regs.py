import asyncio
import aiohttp
from kospel_cmi.kospel.api import read_registers
from kospel_cmi.registers.utils import reg_to_int

async def main():
    url = 'http://192.168.101.49/api/dev/65'
    async with aiohttp.ClientSession() as session:
        regs = await read_registers(session, url, '0b2f', 25)
        for r in ['0b2f', '0b30', '0b31', '0b32', '0b4a', '0b66', '0b67', '0b8d']:
            v = regs.get(r, 'N/A')
            if v != 'N/A':
                i = reg_to_int(v)
                if 'temperature' in r or r in ['0b2f','0b31','0b4a','0b66','0b67','0b8d']:
                    print(f'{r}: hex={v} int={i} -> {i/10}°C' if r not in ['0b30','0b32'] else f'{r}: hex={v} int={i}')
                else:
                    print(f'{r}: hex={v} int={i}')

asyncio.run(main())
