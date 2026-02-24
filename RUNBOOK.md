# Runbook

## Daily Run Sequence

1. Ensure Postgres is reachable at `DATABASE_URL`.
2. Run migrations: `alembic upgrade head`.
3. Ingest mailbox deltas: `python -m mail_scraper.cli ingest`.
4. Download attachments: `python -m mail_scraper.cli download-attachments`.
5. Optional extract/summarize:
   - `python -m mail_scraper.cli extract`
   - `python -m mail_scraper.cli summarize`
6. Check reliability:
   - `python -m mail_scraper.cli reliability-report`
   - `python -m mail_scraper.cli audit`

## Discovery + Webapp Sequence

1. Build/validate role model:
   - `python -m mail_scraper.cli import-vendors --workbook "Vendors List.xlsx" --sheet Data`
   - `python -m mail_scraper.cli build-role-graph`
   - `python -m mail_scraper.cli derive-tasks`
   - `python -m mail_scraper.cli score-decisions --speed-weight 1 --risk-weight 1 --cash-weight 1 --relationship-weight 1 --rework-weight 1`
2. Publish role insights + rules:
   - `python -m mail_scraper.cli publish-role-insights --output-dir analysis_output`
   - `python -m mail_scraper.cli define-task-rules --output-dir analysis_output`
   - `python -m mail_scraper.cli export-score-profiles --output-dir analysis_output`
3. Prepare procurement webapp DB:
   - `alembic upgrade head`
   - `python -m mail_scraper.cli seed-procurement-mvp`
   - `python -m mail_scraper.cli apply-low-risk-autopilot`
   - `python -m mail_scraper.cli validate-workflow-scenarios --output-dir analysis_output`
4. Run local API/UI:
   - `uvicorn mail_scraper.webapp_main:app --host 127.0.0.1 --port 8080`

## Retry/Replay Steps

- Inspect unresolved dead letters:
  - `python -m mail_scraper.cli audit`
- Replay and resolve them:
  - `python -m mail_scraper.cli replay-dead-letters --limit 100`
  - optional stage filter: `--stage ingest-message`

## Failure Triage

1. If ingest fails, re-run `ingest` first (idempotent writes by mailbox+message keys).
2. If attachment download fails, run `download-attachments` again.
3. Use `reliability-report` to confirm rolling failure rate trend.
4. If DB errors persist, run `alembic upgrade head` and verify schema drift.

## Expected Artifacts and Logs

- DB tables: `mailboxes`, `messages`, `attachments`, `pipeline_runs`, `pipeline_errors`, `dead_letters`.
- File artifacts under `raw_data/`.
- Analysis artifacts under `analysis_output/`.
