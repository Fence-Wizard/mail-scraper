# Migration Notes

## SQLite to Postgres

Phase 1 uses Postgres as the primary store. Legacy SQLite data can be ported with:

`python -m mail_scraper.cli port-sqlite --sqlite-path purchasing.db`

This imports `documents` rows into Postgres `documents` with conflict-safe upserts on `file_path`.

## Backward Compatibility

Legacy script names remain available as wrappers:

- `full_ingest_messages.py`
- `attachment_downloader.py`
- `extract_deep.py`
- `post_run_summary.py`
- `mailbox_audit.py`

Canonical runtime should use `python -m mail_scraper.cli ...` commands.
