from polythought.bot import format_unsent_links
from polythought.db import Link


def test_format_unsent_links() -> None:
    links = [
        Link(
            id="1",
            user="user",
            url="https://example.com/one",
            title="One",
            sent=None,
        ),
        Link(
            id="2",
            user="user",
            url="https://example.com/two",
            title="Two",
            sent=None,
        ),
    ]

    assert format_unsent_links(links) == (
        "**Links to be shared:**\n\n"
        "1. [One](https://example.com/one)\n\n"
        "2. [Two](https://example.com/two)"
    )


def test_format_unsent_links_with_no_links() -> None:
    assert format_unsent_links([]) == "**Links to be shared:**\n\n"
