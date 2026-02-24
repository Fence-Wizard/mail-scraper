import json

from mail_scraper.config import MailboxConfig, Settings


def test_mailboxes_json_parses_multiple() -> None:
    payload = [
        {"key": "ops", "user_id": "ops@example.com", "root_folder_name": "msgfolderroot"},
        {"key": "sales", "user_id": "sales@example.com", "include_filters": ["inbox"]},
    ]
    settings = Settings(
        tenant_id="t",
        client_id="c",
        client_secret="s",
        mailboxes_json=json.dumps(payload),
    )
    mailboxes = settings.mailbox_configs()
    assert len(mailboxes) == 2
    assert mailboxes[0].key == "ops"
    assert mailboxes[1].include_filters == ["inbox"]


def test_mailboxes_fallback_single_user() -> None:
    settings = Settings(
        tenant_id="t",
        client_id="c",
        client_secret="s",
        user_id="owner@example.com",
        root_folder_name="2024 Jobs",
    )
    mailboxes = settings.mailbox_configs()
    assert len(mailboxes) == 1
    assert isinstance(mailboxes[0], MailboxConfig)
    assert mailboxes[0].user_id == "owner@example.com"
