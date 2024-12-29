import asyncio

import uvloop
from telethon import TelegramClient

from polythought.bot import register_handlers
from polythought.log import setup_logging
from polythought.schedule import schedule
from polythought.settings import Settings


async def _main() -> None:
    # Start Telegram bot
    app = TelegramClient(
        Settings.SESSION_FILE,
        Settings.API_ID,
        Settings.API_HASH.get_secret_value(),
    )
    await register_handlers(app)

    async with asyncio.TaskGroup() as tg:
        _run_app = tg.create_task(app.run_until_disconnected())  # pyright: ignore[reportArgumentType]
        _run_schedule = tg.create_task(schedule(app))


if __name__ == "__main__":
    setup_logging()
    uvloop.run(_main())
