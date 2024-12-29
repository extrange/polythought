import logging


def setup_logging() -> None:
    """Configure logging globally."""
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
