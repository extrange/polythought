from polythought import db


def test_add_link_round_trip() -> None:
    link = db.add_link("test-add", "https://example.com/add", "Add")

    assert link.sent is None
    assert link in db.get_unsent_links("test-add")
    assert link in db.get_links("test-add")


def test_mark_as_sent_removes_link_from_unsent() -> None:
    link = db.add_link("test-sent", "https://example.com/sent", "Sent")

    db.mark_as_sent(link)

    assert db.get_unsent_links("test-sent") == []
    stored = db.get_links("test-sent")
    assert len(stored) == 1
    assert stored[0].sent is not None


def test_delete_unsent_links_keeps_sent_links() -> None:
    user = "test-delete"
    sent = db.add_link(user, "https://example.com/keep", "Keep")
    db.mark_as_sent(sent)
    db.add_link(user, "https://example.com/remove", "Remove")

    assert db.delete_unsent_links(user) == 1
    assert [link.id for link in db.get_links(user)] == [sent.id]
