import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from log import logger

from main import DEBUG


@dataclass
class Link:
    id: str
    user: str
    url: str
    title: str
    sent: Optional[int]


db_path = f"file:{Path(__file__).parent / 'links.db'}{'?mode=ro' if DEBUG else ''}"
logger.info(f"Connecting to db {db_path}")
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
    user_uuid = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO links VALUES(:id, :user, :url, :title, NULL)",
        {"id": user_uuid, "user": user, "url": url, "title": title},
    )
    con.commit()
    return Link(id=user_uuid, user=user, url=url, title=title, sent=None)


def delete_unsent_links(user: str):
    if DEBUG:
        return 0
    res = cur.execute(
        "DELETE FROM links WHERE user=:user AND sent IS NULL", {"user": user}
    )
    con.commit()
    return res.rowcount


def get_links(user: str) -> list[Link]:
    res = cur.execute("SELECT * FROM links WHERE user=:user", {"user": user})
    return [Link(*r) for r in res.fetchall()]


def mark_as_sent(link: Link):
    if DEBUG:
        return
    cur.execute(
        "UPDATE links SET sent=:sent WHERE id=:id", {"id": link.id, "sent": time.time()}
    )
    con.commit()


def get_unsent_links(user_id: Optional[str] = None) -> list[Link]:
    """Get unsent links from a user, or if not provided, all"""
    if user_id:
        res = cur.execute(
            "SELECT * FROM links WHERE user=:user AND sent IS NULL", {"user": user_id}
        )
    else:
        res = cur.execute("SELECT * FROM links WHERE sent is NULL")

    return [Link(*r) for r in res.fetchall()]
