import asyncio
import os

import uvloop
from dotenv import load_dotenv
from pyrogram.enums import ParseMode

# If true, database will be opened readonly
DEBUG = False


async def main():
    if not load_dotenv():
        raise FileNotFoundError("Failed to load environment variables")

    from pyrogram.client import Client

    # Import later so environment variables are resolved
    from bot import register_handlers
    from links import send_links
    from log import logger
    from util import get_seconds_to_7am

    # Start Telegram bot
    app = Client("polythought")
    await register_handlers(app)

    # Send notifications daily at 7am
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
            try:
                await send_links(app)
            except Exception as e:
                await app.send_message(
                    int(os.environ["MY_CHAT_ID"]),
                    f"Error:\n\n<pre>{e}</pre>",
                    parse_mode=ParseMode.HTML,
                )


if __name__ == "__main__":
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    asyncio.run(main())
