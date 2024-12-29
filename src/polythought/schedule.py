import asyncio
import logging
import os
import traceback

from telethon import TelegramClient

from polythought.links import send_links
from polythought.settings import Settings
from polythought.util import get_seconds_to_7am

_logger = logging.getLogger(__name__)


async def schedule(app: TelegramClient) -> None:
    """Run the scheduled daily sending."""
    # Send notifications daily at 7am
    if Settings.DEBUG:
        # When debugging, send immediately
        await send_links(app)
    else:
        # Initial run
        seconds_to_wait = get_seconds_to_7am()
        _logger.info("Waiting for %ss...", seconds_to_wait)
        await asyncio.sleep(seconds_to_wait)
        await send_links(app)

        while True:
            seconds_to_wait = get_seconds_to_7am(next_day=True)
            _logger.info("Waiting for %ss...", seconds_to_wait)
            await asyncio.sleep(seconds_to_wait)
            try:
                await send_links(app)
            except Exception as e:
                _logger.exception(
                    "Encountered an error while attempting to send scheduled jobs"
                )
                await app.send_message(
                    int(os.environ["MY_CHAT_ID"]),
                    f"Error while attempting to send scheduled jobs:\n\n<pre>{e}:\n{traceback.format_exc()}</pre>",
                    parse_mode="html",
                )
