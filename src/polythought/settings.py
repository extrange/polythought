"""Runtime settings, read from environment variables."""

from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class _Settings(BaseSettings):
    """All runtime configuration, supplied as environment variables."""

    model_config = SettingsConfigDict(extra="ignore")

    # Required: no sensible default.
    API_HASH: SecretStr
    API_ID: int
    BOT_TOKEN: SecretStr
    CHANNEL_ID: int
    MY_CHAT_ID: int

    # Optional: sane defaults, overridable from the environment.
    DEBUG: bool = False
    SESSION_FILE: Path = Path("credentials/account.session")
    DB_PATH: Path = Path("db/links.db")
    CAMOFOX_URL: str
    CAMOFOX_USER_ID: str = "polythought"
    TZ: str = "Asia/Singapore"


Settings = _Settings.model_validate({})
