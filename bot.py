import os

from pyrogram import filters
from pyrogram.client import Client
from pyrogram.enums import MessageEntityType, ParseMode
from pyrogram.types import BotCommand, Message

from db import Link, add_link, delete_unsent_links, get_unsent_links
from links import fetch_page_title

MY_CHAT_ID = os.environ["MY_CHAT_ID"]
HELP_STR = """Forward me links that you'd like to share with your friends! Links will be posted daily on @Polythought at 7am."""

from log import logger


def format_unsent_links(links: list[Link]):
    return f"""**Links to be shared:**\n\n{'\n\n'.join([f"{n+1}. [{l.title}]({l.url})" for n,l in enumerate(links)])}"""


async def register_handlers(app: Client):
    await app.start()

    await app.set_bot_commands(
        [
            BotCommand("links", "Show unsent links"),
            BotCommand("clear", "Clear unsent links"),
        ]
    )

    @app.on_message(filters.command("start"))
    async def handle_start(client, message: Message):
        await message.reply(f"Welcome!\n\n{HELP_STR}")

    @app.on_message(filters.command("links"))
    async def handle_links(client, message: Message):
        unsent_links = get_unsent_links(str(message.from_user.id))
        if not unsent_links:
            await message.reply("You have no links to be shared.")
        else:
            await message.reply(
                format_unsent_links(unsent_links),
                quote=True,
                disable_web_page_preview=True,
            )

    @app.on_message(filters.command("clear"))
    async def handle_clear(client, message: Message):
        rows = delete_unsent_links(str(message.from_user.id))
        await message.reply(
            f"Deleted {rows} link{'' if rows == 1 else 's'}.", quote=True
        )

    @app.on_message(filters.text)
    async def handle_text(client, message: Message):
        """Extract urls from messages, get titles, and save to DB."""
        try:
            if not message.entities:
                return await message.reply(HELP_STR)

            extracted_urls: list[str] = []

            for entity in message.entities:
                # There are 2 types of possible links: URLs and TEXT_LINKs
                if entity.type == MessageEntityType.TEXT_LINK:
                    extracted_urls.append(entity.url)
                if entity.type == MessageEntityType.URL:
                    extracted_urls.append(
                        message.text[entity.offset : entity.offset + entity.length]
                    )

            if not extracted_urls:
                await message.reply("Sorry, I couldn't find any links in this message.")
                return

            user_id = str(message.from_user.id)

            reply = await message.reply(
                "Processing links...", quote=True, disable_web_page_preview=True
            )

            for url in extracted_urls:
                fetched_title = await fetch_page_title(url)

                # If title can't be parsed, use the url as title
                title = fetched_title or url

                # Add links to database
                add_link(user_id, url, title)

            # Reply user with currently unsent links
            unsent_links = get_unsent_links(user_id)

            await reply.edit(
                format_unsent_links(unsent_links), disable_web_page_preview=True
            )

        except Exception as e:
            msg = f"Sorry, encountered an error:\n\n<pre>{e}</pre>"
            await message.reply(
                msg,
                parse_mode=ParseMode.HTML,
            )
            await app.send_message(
                int(MY_CHAT_ID),
                f"Encountered error for {message.from_user.first_name}: {msg})",
                parse_mode=ParseMode.HTML,
            )
