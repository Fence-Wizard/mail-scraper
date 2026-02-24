import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import nullcontext
import re
import hashlib
import json

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import aliased

from .config import settings
from .db import bootstrap_mailboxes, db_session, ensure_schema, finish_run, get_engine, rolling_failure_rate, start_run
from .db_schema import (
    AppUser,
    Actor,
    ActorAlias,
    Attachment,
    DeadLetter,
    DecisionScore,
    Document,
    Folder,
    InvoiceMatch,
    Interaction,
    Mailbox,
    Message,
    PipelineError,
    PurchaseOrder,
    RfqQuote,
    OrderConfirmation,
    Task,
    TaskEvent,
    VendorKpi,
    VendorReference,
    WorkflowAction,
)
from .graph_client import GraphClient
from .pipeline_attachments import download_attachments_for_mailbox, replay_dead_letters
from .pipeline_ingest import ingest_mailbox

try:
    from matrix_rain import matrix_rain as matrix_rain_context
except Exception:  # pragma: no cover - cosmetic fallback
    matrix_rain_context = None


def _clean_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.lower() in {"nan", "none", "null"}:
        return None
    return text


def _parse_money(value: object) -> float | None:
    text = _clean_text(value)
    if not text:
        return None
    normalized = re.sub(r"[^0-9\.\-]", "", text)
    if not normalized:
        return None
    try:
        return float(normalized)
    except ValueError:
        return None


def _parse_dt(value: object) -> datetime | None:
    text = _clean_text(value)
    if not text:
        return None
    dt = pd.to_datetime(text, errors="coerce", utc=True)
    if pd.isna(dt):
        return None
    return dt.to_pydatetime()


def _canonicalize_vendor(vendor: object) -> str | None:
    text = _clean_text(vendor)
    if not text:
        return None
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _canonicalize_name(value: object) -> str | None:
    text = _clean_text(value)
    if not text:
        return None
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _extract_domain(email: str | None) -> str | None:
    if not email or "@" not in email:
        return None
    return email.split("@", 1)[1].lower().strip()


def _make_actor_key(*parts: object) -> str:
    normalized = "|".join((_clean_text(part) or "") for part in parts)
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()


def _contains_any(value: str | None, tokens: list[str]) -> bool:
    if not value:
        return False
    s = value.lower()
    return any(token in s for token in tokens)


async def run_ingest(limit: int | None = None, mailbox_key: str | None = None, matrix: bool = False) -> int:
    ensure_schema()
    matrix_ctx = (
        matrix_rain_context(enabled=True)
        if matrix and matrix_rain_context is not None
        else nullcontext()
    )
    with db_session() as session:
        mailbox_configs = settings.mailbox_configs()
        mailbox_rows = bootstrap_mailboxes(session, mailbox_configs)
        selected_configs = [cfg for cfg in mailbox_configs if cfg.enabled and (mailbox_key is None or cfg.key == mailbox_key)]
        if mailbox_key and not selected_configs:
            raise ValueError(f"Mailbox key not found or disabled: {mailbox_key}")

        total_processed = 0
        with matrix_ctx as rain:
            async with GraphClient() as client:
                for mailbox_cfg in selected_configs:
                    mailbox_row = mailbox_rows[mailbox_cfg.key]
                    run = start_run(session, pipeline_name="ingest", mailbox_id=mailbox_row.id)
                    session.flush()
                    if rain is not None and hasattr(rain, "set_status"):
                        rain.set_status(f"starting ingest | mailbox={mailbox_cfg.key}")

                    def on_progress(evt: dict) -> None:
                        if rain is None or not hasattr(rain, "set_status"):
                            return
                        stage = evt.get("stage", "")
                        if stage == "discovering-folders":
                            rain.set_status(f"discovering folders | mailbox={mailbox_cfg.key}")
                            return
                        if stage == "folder-discovery-complete":
                            rain.set_status(
                                "folders discovered "
                                f"| mailbox={mailbox_cfg.key} "
                                f"| total={evt.get('total_folders', 0)} "
                                f"| targeted={evt.get('target_folders', 0)}"
                            )
                            return
                        if stage == "ingesting-folders":
                            rain.set_status(
                                "ingesting "
                                f"| mailbox={mailbox_cfg.key} "
                                f"| folders={evt.get('completed_folders', 0)}/{evt.get('target_folders', 0)} "
                                f"| new_msgs={evt.get('processed_messages', 0)} "
                                f"| errors={evt.get('errors', 0)}"
                            )
                            return
                        if stage == "completed":
                            rain.set_status(
                                "completed "
                                f"| mailbox={mailbox_cfg.key} "
                                f"| folders={evt.get('target_folders', 0)} "
                                f"| new_msgs={evt.get('processed_messages', 0)} "
                                f"| errors={evt.get('errors', 0)}"
                            )

                    try:
                        result = await ingest_mailbox(
                            client=client,
                            session=session,
                            mailbox=mailbox_cfg,
                            mailbox_row=mailbox_row,
                            run=run,
                            hard_limit=limit,
                            max_concurrency=settings.graph_max_concurrency,
                            progress_cb=on_progress,
                        )
                        finish_run(
                            session,
                            run,
                            status="success" if result.errors == 0 else "partial_success",
                            processed_count=result.processed,
                            error_count=result.errors,
                        )
                        total_processed += result.processed
                    except Exception as exc:
                        session.add(
                            PipelineError(
                                run_id=run.id,
                                mailbox_id=mailbox_row.id,
                                stage="ingest-mailbox",
                                error_message=str(exc),
                                payload_json={"mailbox_key": mailbox_cfg.key},
                            )
                        )
                        session.add(
                            DeadLetter(
                                mailbox_id=mailbox_row.id,
                                stage="ingest-mailbox",
                                payload_json={"mailbox_key": mailbox_cfg.key},
                                error_message=str(exc),
                            )
                        )
                        finish_run(session, run, status="failed", processed_count=0, error_count=1)
                        continue
        return total_processed


async def run_download_attachments(
    limit: int | None = None,
    mailbox_key: str | None = None,
    matrix: bool = False,
    batch_size: int | None = None,
) -> int:
    ensure_schema()
    output_root = Path("raw_data")
    matrix_ctx = (
        matrix_rain_context(enabled=True)
        if matrix and matrix_rain_context is not None
        else nullcontext()
    )
    with db_session() as session:
        mailbox_configs = settings.mailbox_configs()
        mailbox_rows = bootstrap_mailboxes(session, mailbox_configs)
        selected_configs = [cfg for cfg in mailbox_configs if cfg.enabled and (mailbox_key is None or cfg.key == mailbox_key)]
        total_processed = 0
        effective_batch_size = max(1, batch_size or settings.attachment_batch_size)
        with matrix_ctx as rain:
            async with GraphClient() as client:
                for mailbox_cfg in selected_configs:
                    mailbox_row = mailbox_rows[mailbox_cfg.key]
                    run = start_run(session, pipeline_name="download_attachments", mailbox_id=mailbox_row.id)
                    session.flush()
                    if rain is not None and hasattr(rain, "set_status"):
                        rain.set_status(f"starting attachment download | mailbox={mailbox_cfg.key}")

                    def on_progress(evt: dict) -> None:
                        if rain is None or not hasattr(rain, "set_status"):
                            return
                        stage = evt.get("stage", "")
                        if stage == "attachments-start":
                            rain.set_status(
                                "attachments start "
                                f"| mailbox={mailbox_cfg.key} "
                                f"| messages={evt.get('total_messages', 0)} "
                                f"| resume_pk>{evt.get('resume_after_message_pk', 0)}"
                            )
                            return
                        if stage == "attachments-progress":
                            rain.set_status(
                                "attachments downloading "
                                f"| mailbox={mailbox_cfg.key} "
                                f"| files={evt.get('processed_files', 0)} "
                                f"| errors={evt.get('errors', 0)} "
                                f"| skipped={evt.get('skipped', 0)} "
                                f"| scanned={evt.get('scanned_messages', 0)}"
                            )
                            return
                        if stage == "attachments-complete":
                            rain.set_status(
                                "attachments complete "
                                f"| mailbox={mailbox_cfg.key} "
                                f"| files={evt.get('processed_files', 0)} "
                                f"| errors={evt.get('errors', 0)} "
                                f"| skipped={evt.get('skipped', 0)} "
                                f"| scanned={evt.get('scanned_messages', 0)}"
                            )

                    try:
                        processed, errors, skipped = await download_attachments_for_mailbox(
                            client=client,
                            session=session,
                            mailbox=mailbox_cfg,
                            mailbox_row=mailbox_row,
                            run=run,
                            output_root=output_root,
                            limit=limit,
                            batch_size=effective_batch_size,
                            progress_cb=on_progress,
                        )
                        finish_run(
                            session,
                            run,
                            status="success" if errors == 0 else "partial_success",
                            processed_count=processed,
                            error_count=errors,
                        )
                        run.metadata_json = {
                            "skipped_messages": skipped,
                            "batch_size": effective_batch_size,
                        }
                        total_processed += processed
                    except Exception as exc:
                        session.add(
                            PipelineError(
                                run_id=run.id,
                                mailbox_id=mailbox_row.id,
                                stage="download-attachments-mailbox",
                                error_message=str(exc),
                                payload_json={"mailbox_key": mailbox_cfg.key, "batch_size": effective_batch_size},
                            )
                        )
                        session.add(
                            DeadLetter(
                                mailbox_id=mailbox_row.id,
                                stage="download-attachments-mailbox",
                                payload_json={"mailbox_key": mailbox_cfg.key, "batch_size": effective_batch_size},
                                error_message=str(exc),
                            )
                        )
                        finish_run(session, run, status="failed", processed_count=0, error_count=1)
                        continue
        return total_processed


def run_reliability_report(window: int = 20) -> dict[str, float | int]:
    ensure_schema()
    with db_session() as session:
        ingest_rate = rolling_failure_rate(session, "ingest", limit=window)
        attachments_rate = rolling_failure_rate(session, "download_attachments", limit=window)
        open_dead_letters = session.execute(
            select(func.count()).select_from(DeadLetter).where(DeadLetter.resolved_at.is_(None))
        ).scalar_one()
        return {
            "ingest_failure_rate": ingest_rate,
            "attachment_failure_rate": attachments_rate,
            "open_dead_letters": int(open_dead_letters),
        }


def run_replay_dead_letters(stage: str | None = None, limit: int = 100) -> int:
    ensure_schema()
    with db_session() as session:
        return replay_dead_letters(session, stage=stage, limit=limit)


def run_audit() -> dict[str, int]:
    ensure_schema()
    with db_session() as session:
        mailboxes = session.execute(select(func.count()).select_from(Mailbox)).scalar_one()
        dead_letters = session.execute(
            select(func.count()).select_from(DeadLetter).where(DeadLetter.resolved_at.is_(None))
        ).scalar_one()
        errors = session.execute(select(func.count()).select_from(PipelineError)).scalar_one()
        return {
            "mailboxes": int(mailboxes),
            "open_dead_letters": int(dead_letters),
            "pipeline_errors": int(errors),
        }


def run_legacy_extract() -> None:
    import parse_pdfs_batch

    parse_pdfs_batch.main()


def run_load_extracted_csv(csv_path: Path = Path("invoice_summary.csv")) -> dict[str, int]:
    ensure_schema()
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    if df.empty:
        return {"rows_read": 0, "inserted": 0, "updated": 0, "skipped": 0}

    records = df.to_dict(orient="records")
    file_paths = {
        path for path in (_clean_text(record.get("File")) for record in records) if path is not None
    }

    with db_session() as session:
        attachment_map: dict[str, int | None] = {}
        if file_paths:
            attachment_rows = session.execute(
                select(Attachment.file_path, Attachment.message_id).where(Attachment.file_path.in_(list(file_paths)))
            ).all()
            attachment_map = {path: message_id for path, message_id in attachment_rows if path}

        inserted = 0
        updated = 0
        skipped = 0

        for record in records:
            file_path = _clean_text(record.get("File"))
            if not file_path:
                skipped += 1
                continue

            existing = session.execute(select(Document).where(Document.file_path == file_path)).scalar_one_or_none()

            payload = {
                "message_id": attachment_map.get(file_path),
                "file_path": file_path,
                "vendor": _clean_text(record.get("Vendor")),
                "vendor_canonical": _canonicalize_vendor(record.get("Vendor")),
                "po_number": _clean_text(record.get("PO Number")),
                "job_number": _clean_text(record.get("Job Number")),
                "invoice_number": None,
                "invoice_date": _parse_dt(record.get("Invoice Date")),
                "subtotal": None,
                "tax": None,
                "total": _parse_money(record.get("Total Amount")),
                "source_sender": _clean_text(record.get("Sender")),
                "source_received_at": _parse_dt(record.get("Received")),
                "source_subject": _clean_text(record.get("Subject")),
                "extract_notes": "Imported from invoice_summary.csv",
            }

            if existing:
                for key, value in payload.items():
                    setattr(existing, key, value)
                updated += 1
                continue

            session.add(Document(**payload))
            inserted += 1

        return {"rows_read": len(records), "inserted": inserted, "updated": updated, "skipped": skipped}


def run_import_vendors(vendor_workbook: Path = Path("Vendors List.xlsx"), sheet_name: str = "Data") -> dict[str, int]:
    ensure_schema()
    if not vendor_workbook.exists():
        raise FileNotFoundError(f"Vendor workbook not found: {vendor_workbook}")

    df = pd.read_excel(vendor_workbook, sheet_name=sheet_name)
    if df.empty:
        return {"rows_read": 0, "inserted": 0, "updated": 0, "skipped": 0}

    inserted = 0
    updated = 0
    skipped = 0

    with db_session() as session:
        for record in df.to_dict(orient="records"):
            vendor_code = _clean_text(record.get("Vendor"))
            vendor_name = _clean_text(record.get("Vendor Name"))
            if not vendor_code or not vendor_name:
                skipped += 1
                continue

            existing = session.execute(
                select(VendorReference).where(VendorReference.vendor_code == vendor_code)
            ).scalar_one_or_none()

            payload = {
                "vendor_code": vendor_code,
                "vendor_name": vendor_name,
                "vendor_name_canonical": _canonicalize_name(vendor_name) or vendor_name.lower(),
                "vendor_class": _clean_text(record.get("Vendor Class")),
                "vendor_status": _clean_text(record.get("Vendor Status")),
                "country": _clean_text(record.get("Country")),
                "city": _clean_text(record.get("City")),
                "state": _clean_text(record.get("State")),
                "currency_id": _clean_text(record.get("Currency ID")),
                "terms": _clean_text(record.get("Terms")),
                "default_contact": _clean_text(record.get("Default Contact")),
                "metadata_json": {
                    "address_line_1": _clean_text(record.get("Address Line 1")),
                    "address_line_2": _clean_text(record.get("Address Line 2")),
                    "address_line_3": _clean_text(record.get("Address Line 3")),
                    "postal_code": _clean_text(record.get("Postal Code")),
                },
            }

            if existing:
                for key, value in payload.items():
                    setattr(existing, key, value)
                updated += 1
                continue

            session.add(VendorReference(**payload))
            inserted += 1

    return {"rows_read": len(df), "inserted": inserted, "updated": updated, "skipped": skipped}


def run_build_role_graph() -> dict[str, int]:
    ensure_schema()
    with db_session() as session:
        vendors = session.execute(select(VendorReference)).scalars().all()
        vendor_names = [item.vendor_name_canonical for item in vendors if item.vendor_name_canonical]
        vendor_lookup = {item.vendor_name_canonical: item for item in vendors if item.vendor_name_canonical}

        session.query(Interaction).delete()

        messages = session.execute(select(Message).where(Message.source_sender.is_not(None))).scalars().all()
        actor_cache: dict[str, Actor] = {}

        def get_or_create_actor(email: str | None, display_name: str | None) -> Actor:
            domain = _extract_domain(email)
            canonical_display = _canonicalize_name(display_name)
            canonical_email = (_clean_text(email) or "").lower()
            actor_key = _make_actor_key(canonical_email, canonical_display or "")
            if actor_key in actor_cache:
                return actor_cache[actor_key]

            existing = session.execute(select(Actor).where(Actor.actor_key == actor_key)).scalar_one_or_none()
            if existing:
                actor_cache[actor_key] = existing
                return existing

            actor_type = "other_external"
            vendor_reference_id = None
            if domain == "hurricanefence.com":
                actor_type = "internal_employee"
            elif _contains_any(canonical_display, ["gc", "general contractor", "prime contractor"]):
                actor_type = "general_contractor"
            elif canonical_display and any(vn in canonical_display for vn in vendor_names):
                actor_type = "vendor"
                for vn in vendor_names:
                    if vn in canonical_display:
                        vendor_reference_id = vendor_lookup[vn].id
                        break
            elif domain and domain != "hurricanefence.com":
                actor_type = "vendor"

            actor = Actor(
                actor_key=actor_key,
                display_name=_clean_text(display_name) or canonical_email or "Unknown",
                actor_type=actor_type,
                email=canonical_email or None,
                email_domain=domain,
                vendor_reference_id=vendor_reference_id,
                metadata_json={},
            )
            session.add(actor)
            session.flush()

            aliases = [alias for alias in {canonical_email, canonical_display} if alias]
            for alias in aliases:
                exists_alias = session.execute(select(ActorAlias).where(ActorAlias.alias == alias)).scalar_one_or_none()
                if exists_alias is None:
                    session.add(
                        ActorAlias(actor_id=actor.id, alias=alias, alias_type="email" if "@" in alias else "name")
                    )

            actor_cache[actor_key] = actor
            return actor

        internal_system_actor = get_or_create_actor("system@hurricanefence.com", "Hurricane Fence System")

        created_interactions = 0
        for msg in messages:
            sender_email = _clean_text(msg.source_sender)
            sender_actor = get_or_create_actor(sender_email, sender_email)
            session.add(
                Interaction(
                    mailbox_id=msg.mailbox_id,
                    message_id=msg.id,
                    document_id=None,
                    from_actor_id=sender_actor.id,
                    to_actor_id=internal_system_actor.id,
                    channel="email",
                    interaction_type="message",
                    direction="inbound" if sender_actor.actor_type != "internal_employee" else "internal",
                    occurred_at=msg.source_received_at,
                    subject=msg.source_subject,
                    metadata_json={"conversation_id": msg.conversation_id},
                )
            )
            created_interactions += 1

        documents = session.execute(select(Document).where(Document.source_sender.is_not(None))).scalars().all()
        for doc in documents:
            sender_email = _clean_text(doc.source_sender)
            sender_actor = get_or_create_actor(sender_email, sender_email)
            session.add(
                Interaction(
                    mailbox_id=None,
                    message_id=doc.message_id,
                    document_id=doc.id,
                    from_actor_id=sender_actor.id,
                    to_actor_id=internal_system_actor.id,
                    channel="document",
                    interaction_type="document",
                    direction="inbound" if sender_actor.actor_type != "internal_employee" else "internal",
                    occurred_at=doc.source_received_at or doc.invoice_date,
                    subject=doc.source_subject,
                    metadata_json={"vendor_canonical": doc.vendor_canonical, "job_number": doc.job_number},
                )
            )
            created_interactions += 1

        return {
            "actors_total": int(session.execute(select(func.count()).select_from(Actor)).scalar_one()),
            "aliases_total": int(session.execute(select(func.count()).select_from(ActorAlias)).scalar_one()),
            "interactions_created": created_interactions,
        }


def run_derive_tasks() -> dict[str, int]:
    ensure_schema()
    with db_session() as session:
        session.query(WorkflowAction).delete()
        session.query(TaskEvent).delete()
        session.query(Task).delete()

        docs = session.execute(select(Document)).scalars().all()
        created = 0
        open_count = 0
        completed_count = 0
        seen_message_ids: set[int] = set()

        messages_by_id: dict[int, Message] = {
            row.id: row for row in session.execute(select(Message)).scalars().all()
        }
        folders_by_key: dict[tuple[int | None, str | None], Folder] = {}
        for folder in session.execute(select(Folder)).scalars().all():
            folders_by_key[(folder.mailbox_id, folder.graph_folder_id)] = folder

        stage_sla_days = {
            "job_setup": 1,
            "budget_review": 2,
            "task_assignment": 1,
            "material_check": 1,
            "pricing_validation": 2,
            "vendor_coordination": 3,
            "order_placement": 1,
            "order_confirmation": 2,
            "yard_pull": 1,
            "material_receiving": 5,
            "completion_check": 1,
            "completed": 0,
        }

        stage_task_type = {
            "job_setup": "job_setup",
            "budget_review": "budget_review",
            "task_assignment": "task_assignment",
            "material_check": "material_check",
            "pricing_validation": "pricing_validation",
            "vendor_coordination": "vendor_coordination",
            "order_placement": "order_placement",
            "order_confirmation": "order_confirmation",
            "yard_pull": "yard_pull",
            "material_receiving": "material_receiving",
            "completion_check": "completion_check",
            "completed": "completed",
        }

        def derive_stage(doc: Document) -> tuple[str, str | None]:
            po_number = _clean_text(doc.po_number)
            total = doc.total
            if po_number is None and total is None:
                return "job_setup", "No PO or pricing — needs initial setup"
            if po_number is None and total is not None:
                return "vendor_coordination", "Has pricing but missing PO — needs vendor coordination"
            if po_number is not None and total is None:
                return "order_confirmation", "PO issued but no confirmed total — awaiting confirmation"
            if po_number is not None and total is not None and float(total) >= 25000:
                return "budget_review", "High-value PO requires budget approval"
            if po_number is not None and total is not None:
                return "completed", None
            return "job_setup", "Insufficient document signals"

        for doc in docs:
            stage, blocked_reason = derive_stage(doc)
            task_type = stage_task_type.get(stage, "triage_tagging")

            human_required = stage in {"budget_review", "pricing_validation"}
            auto_allowed = stage in {
                "job_setup",
                "material_check",
                "order_confirmation",
                "yard_pull",
                "material_receiving",
                "completion_check",
            }
            status = "completed" if stage == "completed" else "open"
            if status == "open":
                open_count += 1
            else:
                completed_count += 1

            source_message_id = doc.message_id
            # Keep unique constraint safe when many docs map to one message.
            if source_message_id is not None:
                if source_message_id in seen_message_ids:
                    source_message_id = None
                else:
                    seen_message_ids.add(source_message_id)

            source_folder_path = None
            if doc.message_id is not None and doc.message_id in messages_by_id:
                msg = messages_by_id[doc.message_id]
                folder = folders_by_key.get((msg.mailbox_id, msg.graph_folder_id))
                if folder is not None:
                    source_folder_path = folder.path

            task = Task(
                mailbox_id=None,
                task_type=task_type,
                status=status,
                priority="high" if doc.total is not None and doc.total >= 25000 else "normal",
                job_number=doc.job_number,
                owner_actor_id=None,
                counterparty_actor_id=None,
                source_message_id=source_message_id,
                source_document_id=doc.id,
                workflow_spine="hybrid",
                workflow_stage=stage,
                human_required=human_required,
                auto_allowed=auto_allowed,
                blocked_reason=blocked_reason,
                source_folder_path=source_folder_path,
                due_at=(
                    (doc.source_received_at + timedelta(days=stage_sla_days.get(stage, 2)))
                    if doc.source_received_at is not None
                    else None
                ),
                completed_at=doc.updated_at if status == "completed" else None,
                last_event_at=doc.updated_at,
                details_json={
                    "vendor": doc.vendor_canonical or doc.vendor,
                    "po_number": doc.po_number,
                    "total": doc.total,
                    "workflow_stage": stage,
                    "human_required": human_required,
                    "auto_allowed": auto_allowed,
                },
            )
            session.add(task)
            session.flush()
            session.add(
                TaskEvent(
                    task_id=task.id,
                    event_type="task_created",
                    message_id=doc.message_id,
                    document_id=doc.id,
                    notes="Derived from hybrid job/lifecycle signals",
                    payload_json={
                        "status": status,
                        "workflow_stage": stage,
                        "workflow_spine": "hybrid",
                        "human_required": human_required,
                        "auto_allowed": auto_allowed,
                    },
                )
            )
            session.add(
                WorkflowAction(
                    task_id=task.id,
                    action_type="task_derived",
                    action_mode="auto",
                    action_status="applied",
                    actor_email="system@hurricanefence.com",
                    notes="Hybrid derivation from document + job context",
                    payload_json={
                        "stage": stage,
                        "blocked_reason": blocked_reason,
                    },
                )
            )
            if status == "completed":
                session.add(
                    TaskEvent(
                        task_id=task.id,
                        event_type="task_completed",
                        message_id=doc.message_id,
                        document_id=doc.id,
                        notes="Has PO and total parsed",
                        payload_json={},
                    )
                )
            elif human_required:
                session.add(
                    TaskEvent(
                        task_id=task.id,
                        event_type="approval_required",
                        message_id=doc.message_id,
                        document_id=doc.id,
                        notes="Human financial approval required",
                        payload_json={"threshold_model": "human_loop_all_financial"},
                    )
                )
            created += 1

        return {
            "tasks_created": created,
            "open_tasks": open_count,
            "completed_tasks": completed_count,
        }


def run_score_decisions(
    speed_weight: float = 1.0,
    risk_weight: float = 1.0,
    cash_weight: float = 1.0,
    relationship_weight: float = 1.0,
    rework_weight: float = 1.0,
) -> dict[str, int]:
    ensure_schema()
    with db_session() as session:
        session.query(DecisionScore).delete()

        tasks = session.execute(select(Task)).scalars().all()
        scored = 0

        for task in tasks:
            details = task.details_json or {}
            total = float(details.get("total") or 0.0)
            is_open = 1.0 if task.status == "open" else 0.0
            speed = 0.3 if task.human_required else is_open
            risk = 1.0 if total >= 50000 else 0.4 if total >= 10000 else 0.1
            cash = min(1.0, total / 100000.0)
            relationship = 0.6 if details.get("vendor") else 0.2
            rework = 0.8 if task.status == "open" and not details.get("po_number") else 0.2
            if task.human_required:
                risk = min(1.0, risk + 0.3)
                rework = min(1.0, rework + 0.2)

            weighted_total = (
                speed * speed_weight
                + risk * risk_weight
                + cash * cash_weight
                + relationship * relationship_weight
                + rework * rework_weight
            )

            if task.human_required and task.status == "open":
                action = "human_approval_required"
            elif task.status == "open":
                action = "follow_up_for_po_or_total"
            else:
                action = "archive_completed"

            session.add(
                DecisionScore(
                    task_id=task.id,
                    action_label=action,
                    score_total=weighted_total,
                    score_speed=speed,
                    score_risk=risk,
                    score_cash=cash,
                    score_relationship=relationship,
                    score_rework=rework,
                    weights_json={
                        "speed": speed_weight,
                        "risk": risk_weight,
                        "cash": cash_weight,
                        "relationship": relationship_weight,
                        "rework": rework_weight,
                    },
                    rationale="Weighted score from task openness, value, and completeness signals.",
                )
            )
            scored += 1

        return {"tasks_scored": scored}


def run_publish_role_insights(output_dir: Path = Path("analysis_output")) -> dict[str, int]:
    ensure_schema()
    output_dir.mkdir(parents=True, exist_ok=True)
    from_actor = aliased(Actor)
    to_actor = aliased(Actor)

    with db_session() as session:
        task_type_rows = session.execute(
            select(Task.task_type, func.count().label("task_count"))
            .group_by(Task.task_type)
            .order_by(func.count().desc())
        ).all()
        task_status_rows = session.execute(
            select(Task.status, func.count().label("task_count"))
            .group_by(Task.status)
            .order_by(func.count().desc())
        ).all()
        open_priority_rows = session.execute(
            select(Task.priority, func.count().label("task_count"))
            .where(Task.status == "open")
            .group_by(Task.priority)
            .order_by(func.count().desc())
        ).all()
        handoff_rows = session.execute(
            select(
                from_actor.actor_type.label("from_type"),
                to_actor.actor_type.label("to_type"),
                func.count().label("interaction_count"),
            )
            .select_from(Interaction)
            .join(from_actor, Interaction.from_actor_id == from_actor.id, isouter=True)
            .join(to_actor, Interaction.to_actor_id == to_actor.id, isouter=True)
            .group_by("from_type", "to_type")
            .order_by(func.count().desc())
        ).all()

    engine = get_engine()
    top_vendor_sql = """
        SELECT
            COALESCE(vendor_canonical, vendor, '(unknown)') AS vendor,
            COUNT(*) AS doc_count,
            SUM(total) AS total_spend
        FROM documents
        GROUP BY 1
        ORDER BY total_spend DESC NULLS LAST
        LIMIT 100
    """
    top_vendors = pd.read_sql(top_vendor_sql, engine)
    if not top_vendors.empty:
        top_vendors.to_csv(output_dir / "role_vendor_burden.csv", index=False)

    task_type_df = pd.DataFrame(task_type_rows, columns=["task_type", "task_count"])
    task_status_df = pd.DataFrame(task_status_rows, columns=["status", "task_count"])
    open_priority_df = pd.DataFrame(open_priority_rows, columns=["priority", "task_count"])
    handoff_df = pd.DataFrame(handoff_rows, columns=["from_type", "to_type", "interaction_count"])

    task_type_df.to_csv(output_dir / "role_task_volume_by_type.csv", index=False)
    task_status_df.to_csv(output_dir / "role_task_status_counts.csv", index=False)
    open_priority_df.to_csv(output_dir / "role_open_task_priority_counts.csv", index=False)
    handoff_df.to_csv(output_dir / "role_handoff_matrix.csv", index=False)

    lines = [
        "# Role Insights",
        "",
        f"_Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC_",
        "",
        f"- Tasks total: **{int(task_type_df['task_count'].sum()) if not task_type_df.empty else 0}**",
        f"- Open tasks: **{int(task_status_df.loc[task_status_df['status'] == 'open', 'task_count'].sum()) if not task_status_df.empty else 0}**",
        f"- Decision scores: **{len(pd.read_sql('SELECT id FROM decision_scores', engine))}**",
        "",
        "## Top Task Types",
    ]
    if task_type_df.empty:
        lines.append("- (none)")
    else:
        for _, row in task_type_df.head(10).iterrows():
            lines.append(f"- {row['task_type']}: {int(row['task_count'])}")

    lines.extend(["", "## Open Task Priority Mix"])
    if open_priority_df.empty:
        lines.append("- (none)")
    else:
        for _, row in open_priority_df.iterrows():
            lines.append(f"- {row['priority']}: {int(row['task_count'])}")

    lines.extend(["", "## Top Vendor Burden"])
    if top_vendors.empty:
        lines.append("- (none)")
    else:
        for _, row in top_vendors.head(10).iterrows():
            amount = float(row["total_spend"]) if row.get("total_spend") is not None else 0.0
            lines.append(f"- {row['vendor']}: docs={int(row['doc_count'])}, spend=${amount:,.2f}")

    (output_dir / "role_insights.md").write_text("\n".join(lines), encoding="utf-8")
    return {
        "task_type_rows": int(len(task_type_df)),
        "task_status_rows": int(len(task_status_df)),
        "handoff_rows": int(len(handoff_df)),
        "vendor_rows": int(len(top_vendors)),
    }


def run_define_task_completion_rules(output_dir: Path = Path("analysis_output")) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    rules_md = output_dir / "task_completion_rules.md"
    lines = [
        "# Task Completion Rules",
        "",
        "_Proposed baseline rules. Confirm before enforcement._",
        "",
        "## invoice_review",
        "- Complete when both `po_number` and `total` are present.",
        "- Open when either value is missing.",
        "- Escalate when open > 3 business days or total >= $25,000.",
        "",
        "## rfq_quote_collection",
        "- Complete when at least one quote amount is captured.",
        "- Escalate when no quote after 2 business days from request.",
        "",
        "## po_approval",
        "- Complete when PO status is `approved` and has issue date.",
        "- Escalate when draft PO older than 2 business days.",
        "",
        "## order_confirmation_tracking",
        "- Complete when order confirmation status is `confirmed`.",
        "- Escalate when no confirmation within 2 business days after PO issue.",
        "",
        "## invoice_match_exception",
        "- Complete when invoice match is `matched` or exception resolved.",
        "- Escalate when unmatched invoice older than 5 business days.",
    ]
    rules_md.write_text("\n".join(lines), encoding="utf-8")
    return rules_md


def run_seed_procurement_mvp() -> dict[str, int]:
    ensure_schema()
    with db_session() as session:
        session.query(VendorKpi).delete()
        session.query(InvoiceMatch).delete()
        session.query(OrderConfirmation).delete()
        session.query(PurchaseOrder).delete()
        session.query(RfqQuote).delete()
        session.query(AppUser).delete()

        users = [
            AppUser(email="admin@hurricanefence.com", password_hash="changeme-admin", role="admin", is_active=True),
            AppUser(email="buyer@hurricanefence.com", password_hash="changeme-buyer", role="buyer", is_active=True),
            AppUser(email="approver@hurricanefence.com", password_hash="changeme-approver", role="approver", is_active=True),
        ]
        for user in users:
            session.add(user)
        session.flush()

        tasks = session.execute(select(Task)).scalars().all()
        vendors = session.execute(select(VendorReference).order_by(VendorReference.id.asc())).scalars().all()

        rfq_created = 0
        po_created = 0
        confirmations_created = 0
        invoice_matches_created = 0
        vendor_kpis_created = 0

        for idx, task in enumerate(tasks):
            vendor = vendors[idx % len(vendors)] if vendors else None
            total = float((task.details_json or {}).get("total") or 0.0)
            quote_amount = total if total > 0 else None

            session.add(
                RfqQuote(
                    job_number=task.job_number,
                    vendor_reference_id=vendor.id if vendor else None,
                    requested_by_actor_id=task.counterparty_actor_id,
                    status="quoted" if quote_amount else "requested",
                    request_date=task.created_at,
                    quote_amount=quote_amount,
                    currency="USD",
                    notes="Seeded from hybrid workflow task",
                    source_task_id=task.id,
                )
            )
            rfq_created += 1

            po_number = (task.details_json or {}).get("po_number")
            po = None
            if po_number:
                po = PurchaseOrder(
                    po_number=f"{po_number}-{task.id}",
                    job_number=task.job_number,
                    vendor_reference_id=vendor.id if vendor else None,
                    created_by_user_id=users[1].id,
                    approved_by_user_id=users[2].id if task.status == "completed" else None,
                    status="approved" if task.status == "completed" else "draft",
                    total_amount=total if total > 0 else None,
                    approved_at=task.completed_at if task.status == "completed" else None,
                    issued_at=task.completed_at if task.status == "completed" else None,
                    source_task_id=task.id,
                    notes="Seeded PO from task",
                )
                session.add(po)
                session.flush()
                po_created += 1

                session.add(
                    OrderConfirmation(
                        purchase_order_id=po.id,
                        status="confirmed" if task.status == "completed" else "pending",
                        confirmed_at=task.completed_at if task.status == "completed" else None,
                        source_document_id=task.source_document_id,
                        notes="Seeded order confirmation",
                    )
                )
                confirmations_created += 1

            if task.source_document_id:
                match_status = "matched" if task.status == "completed" and po is not None else "unmatched"
                session.add(
                    InvoiceMatch(
                        document_id=task.source_document_id,
                        purchase_order_id=po.id if po is not None else None,
                        match_status=match_status,
                        variance_amount=0.0 if match_status == "matched" else None,
                        exception_reason=None if match_status == "matched" else "PO/total mismatch or missing",
                        resolved_at=task.completed_at if match_status == "matched" else None,
                    )
                )
                invoice_matches_created += 1

        vendor_spend = pd.read_sql(
            """
            SELECT
                vr.id AS vendor_reference_id,
                COALESCE(SUM(d.total), 0.0) AS total_spend
            FROM vendor_references vr
            LEFT JOIN documents d
                ON POSITION(vr.vendor_name_canonical IN COALESCE(d.vendor_canonical, '')) > 0
            GROUP BY vr.id
            ORDER BY total_spend DESC
            LIMIT 200
            """,
            get_engine(),
        )
        now = datetime.utcnow()
        period_start = datetime(now.year, max(1, now.month - 1), 1)
        for _, row in vendor_spend.iterrows():
            session.add(
                VendorKpi(
                    vendor_reference_id=int(row["vendor_reference_id"]),
                    period_start=period_start,
                    period_end=now,
                    on_time_rate=0.85,
                    avg_cycle_days=14.0,
                    exception_rate=0.15,
                    total_spend=float(row.get("total_spend") or 0.0),
                )
            )
            vendor_kpis_created += 1

    return {
        "users_seeded": 3,
        "rfq_quotes_created": rfq_created,
        "purchase_orders_created": po_created,
        "order_confirmations_created": confirmations_created,
        "invoice_matches_created": invoice_matches_created,
        "vendor_kpis_created": vendor_kpis_created,
    }


def run_apply_low_risk_autopilot() -> dict[str, int]:
    ensure_schema()
    with db_session() as session:
        candidates = session.execute(
            select(Task).where(
                Task.status == "open",
                Task.auto_allowed.is_(True),
                Task.human_required.is_(False),
            )
        ).scalars().all()
        applied = 0
        completed = 0
        now = datetime.utcnow()

        for task in candidates:
            stage = task.workflow_stage or "triage"
            notes = None
            if stage in {"triage", "rfq_quote_collection", "order_confirmation_tracking", "po_creation"}:
                notes = "Low-risk autopilot applied triage/routing/sync action."
                task.last_event_at = now
                task.blocked_reason = None
                if task.due_at is None:
                    task.due_at = now + timedelta(days=2)
            elif stage == "invoice_match_exception":
                details = task.details_json or {}
                has_total = details.get("total") is not None
                has_po = _clean_text(details.get("po_number")) is not None
                if has_total and has_po:
                    task.status = "completed"
                    task.completed_at = now
                    completed += 1
                    notes = "Low-risk autopilot closed invoice-match task with complete signals."
                else:
                    notes = "Low-risk autopilot generated follow-up draft requirement."

            if notes is None:
                continue

            session.add(
                TaskEvent(
                    task_id=task.id,
                    event_type="autopilot_applied",
                    message_id=task.source_message_id,
                    document_id=task.source_document_id,
                    notes=notes,
                    payload_json={"workflow_stage": stage},
                )
            )
            session.add(
                WorkflowAction(
                    task_id=task.id,
                    action_type="low_risk_autopilot",
                    action_mode="auto",
                    action_status="applied",
                    actor_email="system@hurricanefence.com",
                    notes=notes,
                    payload_json={"workflow_stage": stage},
                )
            )
            applied += 1

    return {"autopilot_applied": applied, "tasks_auto_completed": completed}


def run_validate_workflow_scenarios(output_dir: Path = Path("analysis_output")) -> dict[str, int]:
    ensure_schema()
    output_dir.mkdir(parents=True, exist_ok=True)
    with db_session() as session:
        total_tasks = int(session.execute(select(func.count()).select_from(Task)).scalar_one())
        open_tasks = int(session.execute(select(func.count()).select_from(Task).where(Task.status == "open")).scalar_one())
        human_required_open = int(
            session.execute(
                select(func.count()).select_from(Task).where(Task.status == "open", Task.human_required.is_(True))
            ).scalar_one()
        )
        auto_allowed_open = int(
            session.execute(
                select(func.count()).select_from(Task).where(Task.status == "open", Task.auto_allowed.is_(True))
            ).scalar_one()
        )
        stage_rows = session.execute(
            select(Task.workflow_stage, func.count().label("n")).group_by(Task.workflow_stage).order_by(func.count().desc())
        ).all()
        actions_logged = int(session.execute(select(func.count()).select_from(WorkflowAction)).scalar_one())

    report_path = output_dir / "workflow_validation.md"
    lines = [
        "# Workflow Scenario Validation",
        "",
        f"_Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC_",
        "",
        f"- Total tasks: **{total_tasks}**",
        f"- Open tasks: **{open_tasks}**",
        f"- Open tasks requiring human action: **{human_required_open}**",
        f"- Open tasks eligible for low-risk autopilot: **{auto_allowed_open}**",
        f"- Workflow actions logged: **{actions_logged}**",
        "",
        "## Stage Distribution",
    ]
    for stage, n in stage_rows:
        lines.append(f"- {stage or '(unset)'}: {int(n)}")
    report_path.write_text("\n".join(lines), encoding="utf-8")

    return {
        "total_tasks": total_tasks,
        "open_tasks": open_tasks,
        "human_required_open": human_required_open,
        "auto_allowed_open": auto_allowed_open,
        "actions_logged": actions_logged,
    }


def run_export_score_profiles(output_dir: Path = Path("analysis_output")) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    profiles_json = output_dir / "decision_policy_profiles.json"
    payload = {
        "profiles": [
            {
                "name": "conservative",
                "weights": {"speed": 0.8, "risk": 1.8, "cash": 1.2, "relationship": 1.4, "rework": 1.6},
            },
            {
                "name": "balanced",
                "weights": {"speed": 1.0, "risk": 1.0, "cash": 1.0, "relationship": 1.0, "rework": 1.0},
            },
            {
                "name": "aggressive",
                "weights": {"speed": 1.8, "risk": 0.8, "cash": 1.4, "relationship": 0.8, "rework": 0.7},
            },
        ],
        "policy_constraints": {
            "must_approve": ["po_approval when total_amount >= 25000"],
            "auto_actions": ["invoice_followup_draft for unmatched invoices below 5000"],
            "escalations": ["invoice_match_exception unresolved >5 business days"],
        },
    }
    profiles_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return profiles_json


def run_legacy_summarize() -> None:
    ensure_schema()
    out_dir = Path("analysis_output")
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_md = out_dir / "purchasing_summary.md"

    with db_session() as session:
        doc_count = session.execute(select(func.count()).select_from(Document)).scalar_one()

    engine = get_engine()
    top_vendors = pd.read_sql(
        """
        SELECT COALESCE(vendor_canonical, vendor, '(unknown)') AS vendor, COUNT(*) AS doc_count, SUM(total) AS total_spent
        FROM documents
        GROUP BY 1
        ORDER BY total_spent DESC NULLS LAST
        LIMIT 25
        """,
        engine,
    )
    if not top_vendors.empty:
        top_vendors.to_csv(out_dir / "top_vendors.csv", index=False)

    lines = [
        "# Purchasing Summary",
        "",
        f"_Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC_",
        "",
        f"- Documents: **{doc_count}**",
    ]
    if not top_vendors.empty:
        lines.append("")
        lines.append("## Top Vendors by Spend")
        for _, row in top_vendors.head(10).iterrows():
            amount = row.get("total_spent")
            amount = float(amount) if amount is not None else 0.0
            lines.append(f"- {row['vendor']}: ${amount:,.2f}")
    summary_md.write_text("\n".join(lines), encoding="utf-8")
    print("✅ Analysis complete.")
    print(f"• CSVs: {out_dir}\\*.csv")
    print(f"• Summary: {summary_md}")


def run_legacy_mailbox_audit() -> None:
    counters = run_audit()
    print("Mailbox/Pipeline Audit")
    for key, value in counters.items():
        print(f"- {key}: {value}")
