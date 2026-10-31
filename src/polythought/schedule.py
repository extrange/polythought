import asyncio
import logging
import traceback

from telethon import TelegramClient

from polythought.links import send_links
from polythought.settings import Settings
from polythought.util import get_seconds_to_7am

_logger = logging.getLogger(__name__)


async def _send_links_and_report_errors(app: TelegramClient) -> None:
    """Send links, reporting failures to the admin chat instead of crashing the bot."""
    try:
        await send_links(app)
    except Exception as e:
        _logger.exception(
            "Encountered an error while attempting to send scheduled jobs"
        )
        await app.send_message(
            Settings.MY_CHAT_ID,
            f"Error while attempting to send scheduled jobs:\n\n<pre>{e}:\n{traceback.format_exc()}</pre>",
            parse_mode="html",
        )


async def schedule(app: TelegramClient) -> None:
    """Run the scheduled daily sending."""
    # Send notifications daily at 7am
    if Settings.DEBUG:
        # When debugging, send immediately
        await _send_links_and_report_errors(app)
        return

    # Initial run
    seconds_to_wait = get_seconds_to_7am()
    _logger.debug("Waiting for %ss...", seconds_to_wait)
    await asyncio.sleep(seconds_to_wait)
    await _send_links_and_report_errors(app)

    while True:
        seconds_to_wait = get_seconds_to_7am(next_day=True)
        _logger.debug("Waiting for %ss...", seconds_to_wait)
        await asyncio.sleep(seconds_to_wait)
        await _send_links_and_report_errors(app)
