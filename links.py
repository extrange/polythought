import datetime
import html
import os
import xml.etree.ElementTree as ET
from collections import defaultdict
from typing import TypedDict, cast
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

import requests
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from pyrogram.client import Client
from pyrogram.enums import ParseMode
from pyrogram.types import User

from db import get_unsent_links, mark_as_sent

FEED_URLS = {
    "Chanel": os.environ["CHANEL_FEED_URL"],
    "Nicholas": os.environ["NICHOLAS_FEED_URL"],
}

# Necessary for xml element search
# https://stackoverflow.com/a/14853417
NAMESPACE = {"ns": "http://www.w3.org/2005/Atom"}

from log import logger


class SentLink(TypedDict):
    title: str
    url: str


async def fetch_page_title(url: str):
    """Returns blank string if url title parsing failed"""
    async with async_playwright() as p:
        try:
            logger.info("Connecting to browser...")
            browser = await p.chromium.connect_over_cdp("ws://browserless:3000")
            page = await browser.new_page()
            await stealth_async(page)

            # Attempt http by default
            url_with_prefix = (
                url if url.startswith(("http://", "https://")) else f"http://{url}"
            )

            logger.info(f"Navigating to '{url_with_prefix}'...")
            
            await page.goto(url_with_prefix, timeout=5000)
            title = await page.title()
            if not title:
                raise ValueError("Blank title")
            logger.info(f"Title: {title}")

            return title
        except Exception as e:
            logger.error(f"Error while fetching {url}: {e}")
            return ""


def get_wallabag_entries(feed_url) -> list[SentLink]:
    data = requests.get(feed_url)
    xml = ET.fromstring(data.text)
    entries: list[SentLink] = []

    for el in xml.findall("ns:entry", namespaces=NAMESPACE):
        el_updated = el.find("ns:updated", namespaces=NAMESPACE)

        # Elements evaluate to false if they have no children
        # https://stackoverflow.com/questions/20129996/why-does-boolxml-etree-elementtree-element-evaluate-to-false
        if el_updated is None or not el_updated.text:
            raise RuntimeError("Couldn't find ns:updated, or it is blank")

        # 'updated' is updated when article is archived
        updated_date = (
            datetime.datetime.fromisoformat(el_updated.text)
            .astimezone()  # Use container TZ
            .date()
        )

        # 'now' will be when the job runs, so we don't have to set the time
        yesterday_date = (
            datetime.datetime.now(tz=ZoneInfo(os.environ["TZ"]))
            - datetime.timedelta(days=1)
        ).date()

        # Only continue if article was archived yesterday, ignoring time
        if updated_date != yesterday_date:
            continue

        # Get article title
        el_title = el.find("ns:title", namespaces=NAMESPACE)
        if el_title is None or not el_title.text:
            raise RuntimeError("Couldn't find ns:title, or it is blank")
        title = html.unescape(el_title.text)

        # Get URL
        el_url = el.find("ns:link", namespaces=NAMESPACE)
        if el_url is None:
            raise RuntimeError("Couldn't find ns:link")
        url = el_url.attrib["href"]

        entries.append({"title": title, "url": url})

    return entries


async def send_links(app: Client):
    # Dict of user's resolved name: SentLink
    links: defaultdict[str, list[SentLink]] = defaultdict(list)

    # Fetch links from Wallabag
    for name, feed_url in FEED_URLS.items():
        for entry in get_wallabag_entries(feed_url):
            links[name].append(entry)

    # Fetch links from @PolythoughtBot
    unsent_links = get_unsent_links()
    for link in unsent_links:
        # Resolve user's first name
        first_name = cast(User, await app.get_users(int(link.user))).first_name
        links[first_name].append({"title": link.title, "url": link.url})

        # Mark as sent
        mark_as_sent(link)

    # If there were no links today, skip sending
    if not links:
        return

    # Craft message
    message = ""
    for user_name in links:
        message += f"\n<b>{html.escape(user_name)}</b>:\n"
        for count, user_link in enumerate(links[user_name], 1):
            message += f'[{count}]: <a href="{html.escape(user_link["url"])}">{html.escape(user_link["title"])}</a>\n'

    await app.send_message(
        int(os.environ["CHANNEL_ID"]),
        message,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )
