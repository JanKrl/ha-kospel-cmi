import asyncio
import aiohttp
import os
from dotenv import load_dotenv
from custom_components.kospel.kospel.simulator import is_simulation_mode
from custom_components.kospel.controller.api import HeaterController
from logging_config import setup_logging, get_logger

logger = get_logger("main")


async def main():
    if is_simulation_mode():
        logger.warning("SIMULATION MODE: ON")
    else:
        logger.debug("SIMULATION MODE: OFF")

    heater_ip = os.getenv("HEATER_IP")
    device_id = os.getenv("DEVICE_ID")
    api_base_url = f"http://{heater_ip}/api/dev/{device_id}"

    async with aiohttp.ClientSession() as session:
        heater = HeaterController(session, api_base_url)
        await heater.refresh()
        heater.print_settings()


if __name__ == "__main__":
    load_dotenv(verbose=True)
    setup_logging()
    asyncio.run(main())
