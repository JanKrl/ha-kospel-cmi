import asyncio
import aiohttp
import os
from dotenv import load_dotenv
from kospel_cmi.controller.api import HeaterController
from kospel_cmi.kospel.backend import HttpRegisterBackend
from logging_config import setup_logging, get_logger

logger = get_logger("main")


async def main():
    heater_ip = os.getenv("HEATER_IP")
    device_id = os.getenv("DEVICE_ID")
    api_base_url = f"http://{heater_ip}/api/dev/{device_id}"

    async with aiohttp.ClientSession() as session:
        backend = HttpRegisterBackend(session, api_base_url)
        heater = HeaterController(backend=backend)
        await heater.refresh()
        heater.print_settings()


if __name__ == "__main__":
    load_dotenv(verbose=True)
    setup_logging()
    asyncio.run(main())
