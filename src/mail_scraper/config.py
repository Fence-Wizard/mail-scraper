import json
from typing import Any

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MailboxConfig(BaseModel):
    key: str
    user_id: str
    root_folder_name: str = "msgfolderroot"
    location_filters: list[str] = Field(default_factory=list)
    include_filters: list[str] = Field(default_factory=list)
    exclude_filters: list[str] = Field(default_factory=list)
    traversal_mode: str = "recursive"
    job_folder_regex: str = r"^\d{5,8}$"
    max_folder_depth: int | None = None
    enabled: bool = True


class Settings(BaseSettings):
    tenant_id: str
    client_id: str
    client_secret: str
    user_id: str | None = None
    root_folder_name: str = "2024 Jobs"
    debug: bool = False
    graph_endpoint: str = "https://graph.microsoft.com/v1.0"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/mail_scraper"
    mailboxes_json: str | None = None
    graph_max_concurrency: int = 4
    attachment_batch_size: int = 500

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def mailbox_configs(self) -> list[MailboxConfig]:
        if self.mailboxes_json:
            raw: Any = json.loads(self.mailboxes_json)
            if isinstance(raw, dict):
                raw = [raw]
            return [MailboxConfig.model_validate(item) for item in raw]

        if not self.user_id:
            raise ValueError("Set USER_ID or MAILBOXES_JSON in .env")
        return [
            MailboxConfig(
                key=self.user_id.replace("@", "_at_"),
                user_id=self.user_id,
                root_folder_name=self.root_folder_name,
            )
        ]


settings = Settings()
