# fetch_config.py
import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Azure / Graph API
    tenant_id: str
    client_id: str
    client_secret: str
    # The mailbox we’re crawling
    user_id: str

    # The root folder name under which jobs are organized
    root_folder_name: str = "2024 Jobs"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# instantiate at import time
settings = Settings()
