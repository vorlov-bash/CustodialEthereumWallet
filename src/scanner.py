import asyncio

from src.core.config import w3_obj
from src.core.logger import setup_logging
from src.modules.scanner.service import (
    confirm_block,
    get_last_scanned_block,
    set_last_scanned_block,
)


async def run_scanner() -> None:
    last_scanned_block = await get_last_scanned_block()
    latest_block = await w3_obj.eth.get_block("latest")

    if last_scanned_block is None:
        # First run.
        last_scanned_block = latest_block["number"]
        await set_last_scanned_block(last_scanned_block)

    for block_number in range(last_scanned_block + 1, latest_block["number"] + 1):
        await confirm_block(block_number)
        await set_last_scanned_block(block_number)


async def scanner():
    setup_logging()

    while True:
        await run_scanner()
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(scanner())
