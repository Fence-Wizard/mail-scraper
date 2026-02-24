# Procurement Webapp Implementation

## Scope Delivered

- Local-first FastAPI procurement app scaffold mounted at `mail_scraper.webapp_main:app`.
- API modules for:
  - RFQ/Quote intake (`/api/rfqs`)
  - PO creation/approval (`/api/purchase-orders`)
  - Order confirmations (`/api/order-confirmations`)
  - Invoice matching/exceptions (`/api/invoice-matches`)
  - Vendor management and KPIs (`/api/vendors`, `/api/vendors/kpis`)
  - Spend and queue dashboards (`/api/dashboard/summary`)
  - Decision ranking and rescoring (`/api/decisions/top`, `/api/decisions/rescore`)
- Header-based auth bootstrap and RBAC (viewer, buyer, approver, admin).

## Database Extensions

Added tables:
- `app_users`
- `rfq_quotes`
- `purchase_orders`
- `order_confirmations`
- `invoice_matches`
- `vendor_kpis`

Migration:
- `alembic/versions/20260224_0004_procurement_webapp_core.py`

## Plan Phase Mapping

- **validate-role-model**: re-ran import + graph + task + score over current corpus.
- **publish-role-insights**: added `publish-role-insights` command to generate CSV/MD artifacts.
- **define-task-completion-rules**: added `define-task-rules` command to generate proposed completion/escalation criteria in `analysis_output/task_completion_rules.md`.
- **build-procurement-mvp**: implemented local-first API + simple UI shell, plus seed command to materialize MVP queues.
- **integrate-policy-scoring**: added `export-score-profiles` and `/api/decisions/rescore`.
- **prepare-render-deploy**: added `render.yaml` and runbook/readme updates for Render/Neon parity.

## Run Commands

1. `pip install -e .[dev]`
2. `alembic upgrade head`
3. `python -m mail_scraper.cli seed-procurement-mvp`
4. `uvicorn mail_scraper.webapp_main:app --host 127.0.0.1 --port 8080`

## Notes

- Seeded app users are placeholders (`changeme-*` hashes). Replace with proper hashing and credential workflow before production.
- Current UI is minimal shell; workflow is exposed through API docs and endpoints first.
