import logging
import sqlite3
import time
import uuid
from dataclasses import dataclass

from polythought.settings import Settings

_logger = logging.getLogger(__name__)


@dataclass
class Link:
    id: str
    user: str
    url: str
    title: str
    sent: int | None


db_path = f"file:{Settings.DB_PATH}"
_logger.info("Connecting to db %s", db_path)
con = sqlite3.connect(db_path, uri=True)
cur = con.cursor()
cur.execute(
    """--sql
    CREATE TABLE IF NOT EXISTS links (
    id TEXT PRIMARY KEY,
    user TEXT NOT NULL,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    sent REAL
    )
    """
)


def add_link(user: str, url: str, title: str) -> Link:
    """Add a link to the db."""
    user_uuid = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO links VALUES(:id, :user, :url, :title, NULL)",
        {"id": user_uuid, "user": user, "url": url, "title": title},
    )
    con.commit()
    return Link(id=user_uuid, user=user, url=url, title=title, sent=None)


def delete_unsent_links(user: str) -> int:
    """Delete unsent links for a user. Returns count of deleted links."""
    res = cur.execute(
        "DELETE FROM links WHERE user=:user AND sent IS NULL", {"user": user}
    )
    con.commit()
    return res.rowcount


def get_links(user: str) -> list[Link]:
    """Return all links from a user, regardless of sent status."""
    res = cur.execute("SELECT * FROM links WHERE user=:user", {"user": user})
    return [Link(*r) for r in res.fetchall()]


def mark_as_sent(link: Link) -> None:
    """Mark a link as sent."""
    cur.execute(
        "UPDATE links SET sent=:sent WHERE id=:id", {"id": link.id, "sent": time.time()}
    )
    con.commit()


def get_unsent_links(user_id: str | None = None) -> list[Link]:
    """Get unsent links from a user, or if not provided, all."""
    if user_id:
        res = cur.execute(
            "SELECT * FROM links WHERE user=:user AND sent IS NULL", {"user": user_id}
        )
    else:
        res = cur.execute("SELECT * FROM links WHERE sent is NULL")

    return [Link(*r) for r in res.fetchall()]
