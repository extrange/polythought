import html
import logging
import os
from collections import defaultdict
from typing import TypedDict

from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from telethon import TelegramClient
from telethon.tl.types import User

from polythought.db import get_unsent_links, mark_as_sent
from polythought.settings import Settings

_logger = logging.getLogger(__name__)


class SentLink(TypedDict):
    title: str
    url: str


class InvalidUserError(Exception):
    """Expected a User, but got something else."""


async def fetch_page_title(url: str) -> str:
    """Fetch title of page as seen by a browser. Returns blank string if url title parsing failed."""
    async with async_playwright() as p:
        try:
            _logger.info("Connecting to browser...")
            browser = await p.chromium.connect_over_cdp(
                f"ws://browserless:3000?token={Settings.BROWSERLESS_TOKEN.get_secret_value()}"
            )
            page = await browser.new_page()
            await stealth_async(page)

            # Attempt http by default
            url_with_prefix = (
                url if url.startswith(("http://", "https://")) else f"http://{url}"
            )

            _logger.info("Navigating to '%s'...", url_with_prefix)

            await page.goto(url_with_prefix, timeout=10_000)
            title = await page.title()
            if not title:
                _logger.warning("Blank title for url '%s'", url)
                title = ""
        except Exception:
            _logger.exception("Error while fetching url '%s'", url)
            return ""
        else:
            _logger.info("Parsed title '%s' for url '%s'", title, url)
            return title


async def send_links(app: TelegramClient) -> None:
    """Send out unsent links to the group."""
    # Dict of user's resolved name: SentLink
    links: defaultdict[str, list[SentLink]] = defaultdict(list)

    # Fetch links from @PolythoughtBot
    unsent_links = get_unsent_links()
    for link in unsent_links:
        # Resolve user's first name
        user = await app.get_entity(int(link.user))
        if not isinstance(user, User):
            _logger.error("Invalid entity when looking up %s: %s", link.user, user)
            raise InvalidUserError

        first_name = user.first_name or "Unknown"

        links[first_name].append({"title": link.title, "url": link.url})

        # Mark as sent
        mark_as_sent(link)

    if not unsent_links:
        _logger.debug("No unsent links from @PolythoughtBot")

    # If there were no links today, skip sending
    if not links:
        _logger.debug("No links from @PolythoughtBot to be sent, skipping send job")
        return

    # Craft message
    message = ""
    for user_name in links:
        message += f"\n<b>{html.escape(user_name)}</b>:\n"
        for count, user_link in enumerate(links[user_name], 1):
            message += f'[{count}]: <a href="{html.escape(user_link["url"])}">{html.escape(user_link["title"])}</a>\n'

    message += "\n<i>Forward your links to @PolythoughtBot</i>"

    await app.send_message(
        int(os.environ["CHANNEL_ID"]),
        message,
        parse_mode="html",
        link_preview=False,
    )
