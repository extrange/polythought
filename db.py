import sqlite3
import time
import uuid
from dataclasses import dataclass
from typing import Optional


@dataclass
class Link:
    id: str
    user: str
    url: str
    title: str
    sent: Optional[int]


con = sqlite3.connect("links.db")
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


def get_links(user: str) -> list[Link]:
    res = cur.execute("SELECT * FROM links WHERE user=:user", {"user": user})
    return [Link(*r) for r in res.fetchall()]


def mark_as_sent(link: Link):
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
