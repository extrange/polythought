import logging
import traceback
from typing import cast

from telethon import TelegramClient, events, functions
from telethon.tl.custom.message import Message
from telethon.tl.types import MessageEntityTextUrl, MessageEntityUrl
from telethon.types import BotCommand, BotCommandScopeDefault

from polythought.cache import cache
from polythought.db import Link, add_link, delete_unsent_links, get_unsent_links
from polythought.links import fetch_page_title
from polythought.settings import Settings

_HELP_STR = """Forward me links that you'd like to share with your friends! Links will be posted daily on @Polythought at 7am."""

_logger = logging.getLogger(__name__)


def format_unsent_links(links: list[Link]) -> str:
    """Format links for sharing."""
    return f"""**Links to be shared:**\n\n{'\n\n'.join([f"{idx+1}. [{link.title}]({link.url})" for idx,link in enumerate(links)])}"""


async def is_user_in_channel(app: TelegramClient, user_id: str) -> bool:
    """Check if a user is in our channel."""
    # Check cache first
    key = "users"
    if key not in cache:
        _logger.debug("user_id %s not in cache, fetching", user_id)
        chat_users = await app.get_participants(Settings.CHANNEL_ID)
        if chat_users is None:
            msg = f"{user_id=} Failed to fetch channel users!"
            raise RuntimeError(msg)
        cache.set(
            key=key,
            value=[str(user.id) for user in chat_users],
            expire=60,  # 1 min
        )
        _logger.debug("user_id %s: updated cache")
    users = cast(list[int], cache[key])
    return user_id in users


async def register_handlers(app: TelegramClient) -> None:
    """Register handlers and start listening."""
    await app.start(bot_token=Settings.BOT_TOKEN.get_secret_value())  # pyright: ignore[reportGeneralTypeIssues]

    command_result = await app(
        functions.bots.SetBotCommandsRequest(
            scope=BotCommandScopeDefault(),
            lang_code="en",
            commands=[
                BotCommand(command="links", description="Show unsent links"),
                BotCommand(command="clear", description="Clear unsent links"),
            ],
        )
    )
    _logger.info("Bot commands set, result=%s", command_result)

    app.add_event_handler(handle_start, events.NewMessage(pattern="^/start$"))
    app.add_event_handler(handle_links, events.NewMessage(pattern="^/links$"))
    app.add_event_handler(handle_clear, events.NewMessage(pattern="^/clear$"))
    app.add_event_handler(handle_text, events.NewMessage())


async def handle_start(message: Message) -> None:
    """Handle the /start command."""
    await message.reply(f"Welcome!\n\n{_HELP_STR}")
    raise events.StopPropagation


async def handle_links(message: Message) -> None:
    """Handle the /links command by showing links to be shared."""

    unsent_links = get_unsent_links(str(message.sender_id))
    if not unsent_links:
        await message.reply("You have no links to be shared.")
    else:
        await message.reply(
            format_unsent_links(unsent_links),
            link_preview=False,
        )
    raise events.StopPropagation


async def handle_clear(message: Message) -> None:
    """Handle the /clear command by deleting unsent links."""
    rows = delete_unsent_links(str(message.sender_id))
    await message.reply(f"Deleted {rows} link{'' if rows == 1 else 's'}.")
    raise events.StopPropagation


async def handle_text(message: Message) -> None:
    """Extract urls from messages, get titles, and save to DB."""
    if not message.text:
        _logger.warning("Received empty message from %s", message.sender_id)
        return None

    _logger.info(
        "Received message from %s: %s",
        message.sender.first_name if message.sender else "Unknown sender",
        message.text,
    )
    app = cast(TelegramClient, message.client)
    try:
        if not await is_user_in_channel(app, str(message.sender_id)):
            _logger.info(
                "User %s} is not in channel, refusing",
                message.sender.first_name if message.sender else "Unknown sender",
            )
            return await message.reply(
                "Join the @Polythought channel to forward me links! (if you just joined, this may take up to a minute to be updated)"
            )

        if not message.entities:
            return await message.reply(_HELP_STR)

        extracted_urls: list[str] = []

        for entity in message.entities:
            # There are 2 types of possible links: URLs and TEXT_LINKs
            if isinstance(entity, MessageEntityTextUrl):
                extracted_urls.append(entity.url)
            if isinstance(entity, MessageEntityUrl):
                extracted_urls.append(
                    message.text[entity.offset : entity.offset + entity.length]
                )

        if not extracted_urls:
            await message.reply("Sorry, I couldn't find any links in this message.")
            _logger.info("No links in message for %s", message.sender_id)
            return None

        user_id = str(message.sender_id)

        reply = cast(
            Message,
            await message.reply("Processing links...", link_preview=False),
        )

        for url in extracted_urls:
            fetched_title = await fetch_page_title(url)

            # If title can't be parsed, use the url as title
            title = fetched_title or url

            # Add links to database
            add_link(user_id, url, title)

        # Reply user with currently unsent links
        unsent_links = get_unsent_links(user_id)
        _logger.info("Discovered links: %s", unsent_links)

        await reply.edit(format_unsent_links(unsent_links), link_preview=False)

    except Exception as e:
        _logger.exception("Encountered an error while handling message %s", message)
        msg = (
            f"Sorry, encountered an error:\n\n<pre>{e}: {traceback.format_exc()}</pre>"
        )
        await message.reply(
            msg,
            parse_mode="html",
        )
        await app.send_message(
            Settings.MY_CHAT_ID,
            f"Encountered error for {message.sender.first_name if message.sender else "Unknown sender"}: {msg})",
            parse_mode="html",
        )
