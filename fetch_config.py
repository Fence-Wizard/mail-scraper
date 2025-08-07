# fetch_config.py
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    # Azure / Graph API
    tenant_id: str
    client_id: str
    client_secret: str
    # The mailbox we’re crawling
    user_id: str

    # The root folder name under which jobs are organized
    root_folder_name: str = "2024 Jobs"

    # load from .env file
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # Toggle verbose debug logging
    debug: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# instantiate at import time
settings = Settings()
