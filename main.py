import asyncio

import uvloop
from dotenv import load_dotenv


async def main():
    if not load_dotenv():
        raise FileNotFoundError("Failed to load environment variables")

    from pyrogram.client import Client

    from bot import register_handlers
    from links import send_links
    from log import logger
    from util import get_seconds_to_7am

    # Start Telegram bot
    app = Client("polythought")
    await register_handlers(app)

    # Send notifications daily at 7am
    DEBUG = False
    if DEBUG:
        # When debugging, send immediately
        await send_links(app)
    else:
        # Initial run
        seconds_to_wait = get_seconds_to_7am()
        logger.info(f"Waiting for {seconds_to_wait}s...")
        await asyncio.sleep(seconds_to_wait)
        await send_links(app)

        while True:
            seconds_to_wait = get_seconds_to_7am(next_day=True)
            logger.info(f"Waiting for {seconds_to_wait}s...")
            await asyncio.sleep(seconds_to_wait)
            await send_links(app)


if __name__ == "__main__":
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    asyncio.run(main())
