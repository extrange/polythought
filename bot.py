from pyrogram import filters
from pyrogram.client import Client
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message

from db import add_link, get_unsent_links
from links import fetch_page_title

HELP_STR = """Send me links that you'd like to share with your friends at https://t.me/polythought! I'll post them on the group at 7am daily."""

from log import logger


async def register_handlers(app: Client):
    await app.start()

    @app.on_message(filters.command("start"))
    async def handle_start(client, message: Message):
        await message.reply(f"Welcome!\n\n{HELP_STR}")

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

            reply = await message.reply("Processing links...", quote=True, disable_web_page_preview=True)

            for url in extracted_urls:
                fetched_title = await fetch_page_title(url)

                # If title can't be parsed, use the url as title
                title = fetched_title or url

                # Add links to database
                add_link(user_id, url, title)

            # Reply user with currently unsent links
            unsent_links = get_unsent_links(user_id)

            await reply.edit(
                f"**Links to be shared:**\n\n{'\n\n'.join([f"{n+1}. [{l.title}]({l.url})" for n,l in enumerate(unsent_links)])} "
            )

        except Exception as e:
            await message.reply(f"Error: {e}")
