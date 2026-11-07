import html
import logging
from collections import defaultdict
from typing import TypedDict

import httpx
from telethon import TelegramClient
from telethon.tl.types import User

from polythought.db import get_unsent_links, mark_as_sent
from polythought.settings import Settings

_logger = logging.getLogger(__name__)

_CAMOFOX_TIMEOUT_SECONDS = 30.0
_CAMOFOX_WAIT_TIMEOUT_MS = 15_000


class SentLink(TypedDict):
    title: str
    url: str


class InvalidUserError(Exception):
    """Expected a User, but got something else."""


async def _camofox_request(
    client: httpx.AsyncClient,
    method: str,
    path: str,
    *,
    json_body: dict[str, object] | None = None,
    params: dict[str, str] | None = None,
) -> httpx.Response:
    """Send a request to camofox and return the response."""
    response = await client.request(method, path, json=json_body, params=params)
    response.raise_for_status()
    return response


async def _close_tab(client: httpx.AsyncClient, tab_id: str) -> None:
    """Close a camofox tab, logging instead of raising if it fails."""
    try:
        await _camofox_request(
            client,
            "DELETE",
            f"/tabs/{tab_id}",
            params={"userId": Settings.CAMOFOX_USER_ID},
        )
    except Exception:
        _logger.warning("Failed to close camofox tab '%s'", tab_id, exc_info=True)


async def fetch_page_title(url: str) -> str:
    """Fetch title of page as seen by a browser. Returns blank string if url title parsing failed."""
    # Attempt http by default
    url_with_prefix = (
        url if url.startswith(("http://", "https://")) else f"http://{url}"
    )

    tab_id: str | None = None
    title = ""

    try:
        async with httpx.AsyncClient(
            base_url=Settings.CAMOFOX_URL,
            timeout=_CAMOFOX_TIMEOUT_SECONDS,
        ) as client:
            try:
                _logger.info("Opening '%s' in camofox...", url_with_prefix)
                opened = (
                    await _camofox_request(
                        client,
                        "POST",
                        "/tabs/open",
                        json_body={
                            "userId": Settings.CAMOFOX_USER_ID,
                            "url": url_with_prefix,
                        },
                    )
                ).json()
                tab_id = opened["tabId"]

                waited = (
                    await _camofox_request(
                        client,
                        "POST",
                        f"/tabs/{tab_id}/wait",
                        json_body={
                            "userId": Settings.CAMOFOX_USER_ID,
                            "timeout": _CAMOFOX_WAIT_TIMEOUT_MS,
                        },
                    )
                ).json()
                if not waited.get("ready"):
                    _logger.warning("Camofox page not ready for url '%s'", url)

                tabs = (
                    await _camofox_request(
                        client,
                        "GET",
                        "/tabs",
                        params={"userId": Settings.CAMOFOX_USER_ID},
                    )
                ).json()
                title = next(
                    (tab["title"] for tab in tabs["tabs"] if tab["tabId"] == tab_id),
                    "",
                )
            finally:
                if tab_id is not None:
                    await _close_tab(client, tab_id)
    except Exception:
        _logger.exception("Error while fetching url '%s'", url)
        return ""

    if not title:
        _logger.warning("Blank title for url '%s'", url)
        return ""

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
        Settings.CHANNEL_ID,
        message,
        parse_mode="html",
        link_preview=False,
    )
