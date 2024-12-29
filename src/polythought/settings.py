from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class _Settings(BaseSettings):
    DEBUG: bool = False
    SESSION_FILE: Path
    DB_PATH: Path
    DISK_CACHE_DIR: Path
    API_ID: int
    API_HASH: SecretStr
    BOT_TOKEN: SecretStr
    CHANNEL_ID: int
    MY_CHAT_ID: int


Settings = _Settings.model_validate({})
