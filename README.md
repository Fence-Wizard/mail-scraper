# mail-scraper

Legacy mailbox scraping and purchasing-analysis toolkit, currently being modernized.

## Phase 1 Runtime

- Configure `.env` with Graph credentials and either `USER_ID` or `MAILBOXES_JSON`.
- Use local Postgres via `DATABASE_URL` (default in settings points to local `mail_scraper` DB).
- Canonical command surface:
  - `python -m mail_scraper.cli ingest`
  - `python -m mail_scraper.cli ingest --matrix`
  - `python -m mail_scraper.cli download-attachments`
  - `python -m mail_scraper.cli download-attachments --matrix`
  - `python -m mail_scraper.cli download-attachments --batch-size 250 --matrix`
  - `python -m mail_scraper.cli extract`
  - `python -m mail_scraper.cli load-extracted-csv --csv-path invoice_summary.csv`
  - `python -m mail_scraper.cli import-vendors --workbook "Vendors List.xlsx" --sheet Data`
  - `python -m mail_scraper.cli build-role-graph`
  - `python -m mail_scraper.cli derive-tasks`
  - `python -m mail_scraper.cli publish-role-insights --output-dir analysis_output`
  - `python -m mail_scraper.cli define-task-rules --output-dir analysis_output`
  - `python -m mail_scraper.cli seed-procurement-mvp`
  - `python -m mail_scraper.cli apply-low-risk-autopilot`
  - `python -m mail_scraper.cli validate-workflow-scenarios --output-dir analysis_output`
  - `python -m mail_scraper.cli export-score-profiles --output-dir analysis_output`
  - `python -m mail_scraper.cli score-decisions --speed-weight 1 --risk-weight 1 --cash-weight 1 --relationship-weight 1 --rework-weight 1`
  - `python -m mail_scraper.cli summarize`
  - `python -m mail_scraper.cli audit`
  - `python -m mail_scraper.cli reliability-report`

## Migrations

- Alembic config: `alembic.ini`
- Initial schema migration: `alembic/versions/20260223_0001_phase1_schema.py`
- Attachment checkpoint migration: `alembic/versions/20260223_0002_checkpoint_progress_cursor.py`
- Apply migrations: `alembic upgrade head`

## Development

- Install dependencies from `requirements.txt` or use `pip install -e .[dev]`.
- Run tests with `pytest`.
- Recommended Phase 1 validation command:
  - `python -m pytest && python -m mail_scraper.cli show-config`

## Procurement Webapp MVP

- Run schema updates first:
  - `alembic upgrade head`
- Seed MVP artifacts:
  - `python -m mail_scraper.cli seed-procurement-mvp`
- Start local webapp:
  - `uvicorn mail_scraper.webapp_main:app --host 127.0.0.1 --port 8080`
- Open:
  - UI: `http://127.0.0.1:8080/`
  - API docs: `http://127.0.0.1:8080/api/docs`
- Include request header for API calls:
  - `X-User-Email: buyer@hurricanefence.com` (or `approver@hurricanefence.com`, `admin@hurricanefence.com`)
- Hybrid workflow endpoints:
  - `GET /api/workflow/lanes`
  - `GET /api/approvals/financial`
  - `POST /api/approvals/financial/{task_id}`
  - `GET /api/workflow/actions/recent`
