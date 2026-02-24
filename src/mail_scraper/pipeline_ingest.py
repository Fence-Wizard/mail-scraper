import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Any, Callable

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from .config import MailboxConfig
from .db_schema import DeadLetter, Folder, Mailbox, Message, PipelineCheckpoint, PipelineError, PipelineRun
from .graph_client import GraphClient

SELECT_FIELDS = "$select=id,from,subject,receivedDateTime,bodyPreview,hasAttachments,conversationId,parentFolderId"
PAGE_SIZE = "$top=50"
ProgressCb = Callable[[dict[str, Any]], None]


def _to_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _path_matches(path_parts: list[str], include_filters: list[str], exclude_filters: list[str]) -> bool:
    path = "/".join(path_parts).lower()
    if include_filters and not all(token.lower() in path for token in include_filters):
        return False
    if exclude_filters and any(token.lower() in path for token in exclude_filters):
        return False
    return True


async def _list_all_folders(client: GraphClient, mailbox: MailboxConfig) -> list[dict[str, Any]]:
    if mailbox.traversal_mode.lower() == "active_jobs":
        return await _list_active_jobs_folders(client, mailbox)

    out: list[dict[str, Any]] = []
    root = await client._get(f"/users/{mailbox.user_id}/mailFolders/{mailbox.root_folder_name}")
    out.append(
        {
            "id": root["id"],
            "path_parts": [mailbox.root_folder_name],
            "display_name": root.get("displayName", mailbox.root_folder_name),
            "parent_id": None,
            "total_item_count": root.get("totalItemCount", 0),
        }
    )

    async def walk(folder_id: str, path_parts: list[str], depth: int) -> None:
        if mailbox.max_folder_depth is not None and depth >= mailbox.max_folder_depth:
            return
        url = f"/users/{mailbox.user_id}/mailFolders/{folder_id}/childFolders"
        while url:
            resp = await client._get(url)
            for child in resp.get("value", []):
                child_path = path_parts + [child.get("displayName", "")]
                out.append(
                    {
                        "id": child["id"],
                        "path_parts": child_path,
                        "display_name": child.get("displayName", ""),
                        "parent_id": folder_id,
                        "total_item_count": child.get("totalItemCount", 0),
                    }
                )
                await walk(child["id"], child_path, depth + 1)
            url = resp.get("@odata.nextLink")
            if url:
                url = url.split("v1.0")[-1]

    await walk(root["id"], [mailbox.root_folder_name], depth=1)
    return out


async def _list_active_jobs_folders(client: GraphClient, mailbox: MailboxConfig) -> list[dict[str, Any]]:
    """Optimized traversal for Active Jobs -> Location -> Job folder structure."""
    out: list[dict[str, Any]] = []
    root = await client._get(f"/users/{mailbox.user_id}/mailFolders/{mailbox.root_folder_name}")
    root_name = root.get("displayName", mailbox.root_folder_name)
    out.append(
        {
            "id": root["id"],
            "path_parts": [root_name],
            "display_name": root_name,
            "parent_id": None,
            "total_item_count": root.get("totalItemCount", 0),
        }
    )

    # Level 1: locations (e.g., North Carolina, Nova, Richmond)
    location_url = f"/users/{mailbox.user_id}/mailFolders/{root['id']}/childFolders"
    while location_url:
        loc_resp = await client._get(location_url)
        for location in loc_resp.get("value", []):
            location_name = location.get("displayName", "")
            if mailbox.location_filters and not any(
                token.lower() in location_name.lower() for token in mailbox.location_filters
            ):
                continue
            location_path = [root_name, location_name]
            out.append(
                {
                    "id": location["id"],
                    "path_parts": location_path,
                    "display_name": location_name,
                    "parent_id": root["id"],
                    "total_item_count": location.get("totalItemCount", 0),
                }
            )

            # Level 2: job folders under each location.
            job_url = f"/users/{mailbox.user_id}/mailFolders/{location['id']}/childFolders"
            while job_url:
                job_resp = await client._get(job_url)
                for job in job_resp.get("value", []):
                    job_name = job.get("displayName", "")
                    if not re.match(mailbox.job_folder_regex, job_name):
                        continue
                    out.append(
                        {
                            "id": job["id"],
                            "path_parts": [root_name, location_name, job_name],
                            "display_name": job_name,
                            "parent_id": location["id"],
                            "total_item_count": job.get("totalItemCount", 0),
                        }
                    )
                job_url = job_resp.get("@odata.nextLink")
                if job_url:
                    job_url = job_url.split("v1.0")[-1]

        location_url = loc_resp.get("@odata.nextLink")
        if location_url:
            location_url = location_url.split("v1.0")[-1]
    return out


def _upsert_folder(session: Session, mailbox_row: Mailbox, folder_data: dict[str, Any]) -> None:
    existing = session.execute(
        select(Folder).where(
            and_(
                Folder.mailbox_id == mailbox_row.id,
                Folder.graph_folder_id == folder_data["id"],
            )
        )
    ).scalar_one_or_none()
    if existing:
        existing.path = "/".join(folder_data["path_parts"])
        existing.display_name = folder_data["display_name"]
        existing.parent_graph_folder_id = folder_data["parent_id"]
        existing.total_item_count = folder_data["total_item_count"]
        return
    session.add(
        Folder(
            mailbox_id=mailbox_row.id,
            graph_folder_id=folder_data["id"],
            parent_graph_folder_id=folder_data["parent_id"],
            display_name=folder_data["display_name"],
            path="/".join(folder_data["path_parts"]),
            total_item_count=folder_data["total_item_count"],
        )
    )


def _upsert_message(session: Session, mailbox_id: int, payload: dict[str, Any]) -> bool:
    existing = session.execute(
        select(Message).where(
            and_(
                Message.mailbox_id == mailbox_id,
                Message.graph_message_id == payload["id"],
            )
        )
    ).scalar_one_or_none()
    sender = ((payload.get("from") or {}).get("emailAddress") or {}).get("address")
    received = _to_dt(payload.get("receivedDateTime"))
    if existing:
        existing.graph_folder_id = payload.get("parentFolderId")
        existing.conversation_id = payload.get("conversationId")
        existing.source_sender = sender
        existing.source_subject = payload.get("subject")
        existing.source_received_at = received
        existing.body_preview = payload.get("bodyPreview")
        existing.has_attachments = bool(payload.get("hasAttachments"))
        existing.raw_json = payload
        return False

    session.add(
        Message(
            mailbox_id=mailbox_id,
            graph_message_id=payload["id"],
            graph_folder_id=payload.get("parentFolderId"),
            conversation_id=payload.get("conversationId"),
            source_sender=sender,
            source_subject=payload.get("subject"),
            source_received_at=received,
            body_preview=payload.get("bodyPreview"),
            has_attachments=bool(payload.get("hasAttachments")),
            raw_json=payload,
        )
    )
    return True


def _get_or_create_checkpoint(session: Session, mailbox_id: int, pipeline_name: str) -> PipelineCheckpoint:
    checkpoint = session.execute(
        select(PipelineCheckpoint).where(
            and_(
                PipelineCheckpoint.mailbox_id == mailbox_id,
                PipelineCheckpoint.pipeline_name == pipeline_name,
            )
        )
    ).scalar_one_or_none()
    if checkpoint:
        return checkpoint
    checkpoint = PipelineCheckpoint(mailbox_id=mailbox_id, pipeline_name=pipeline_name)
    session.add(checkpoint)
    session.flush()
    return checkpoint


@dataclass
class IngestResult:
    processed: int
    errors: int
    max_received_at: datetime | None


async def _pull_folder_messages(
    client: GraphClient,
    mailbox: MailboxConfig,
    mailbox_id: int,
    folder_id: str,
    checkpoint_at: datetime | None,
    session: Session,
    run: PipelineRun,
    hard_limit: int | None,
) -> IngestResult:
    params = [SELECT_FIELDS, PAGE_SIZE, "$orderby=receivedDateTime desc"]
    if checkpoint_at:
        checkpoint_iso = checkpoint_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        params.append(f"$filter=receivedDateTime ge {checkpoint_iso}")
    url = f"/users/{mailbox.user_id}/mailFolders/{folder_id}/messages?{'&'.join(params)}"

    processed = 0
    errors = 0
    max_received_at = checkpoint_at
    while url:
        resp = await client._get(url)
        for message_json in resp.get("value", []):
            try:
                inserted = _upsert_message(session, mailbox_id, message_json)
                if inserted:
                    processed += 1
                received_at = _to_dt(message_json.get("receivedDateTime"))
                if received_at and (max_received_at is None or received_at > max_received_at):
                    max_received_at = received_at
            except Exception as exc:  # pragma: no cover - error path
                errors += 1
                session.add(
                    PipelineError(
                        run_id=run.id,
                        mailbox_id=mailbox_id,
                        message_graph_id=message_json.get("id"),
                        stage="ingest-message",
                        error_message=str(exc),
                        payload_json=message_json,
                    )
                )
                session.add(
                    DeadLetter(
                        mailbox_id=mailbox_id,
                        stage="ingest-message",
                        payload_json=message_json,
                        error_message=str(exc),
                    )
                )

            if hard_limit and processed >= hard_limit:
                session.flush()
                return IngestResult(processed=processed, errors=errors, max_received_at=max_received_at)

        url = resp.get("@odata.nextLink")
        if url:
            url = url.split("v1.0")[-1]
        await asyncio.sleep(0.02)
        session.flush()
    return IngestResult(processed=processed, errors=errors, max_received_at=max_received_at)


async def ingest_mailbox(
    client: GraphClient,
    session: Session,
    mailbox: MailboxConfig,
    mailbox_row: Mailbox,
    run: PipelineRun,
    hard_limit: int | None = None,
    max_concurrency: int = 4,
    progress_cb: ProgressCb | None = None,
) -> IngestResult:
    checkpoint = _get_or_create_checkpoint(session, mailbox_row.id, "ingest")
    if progress_cb:
        progress_cb(
            {
                "stage": "discovering-folders",
                "mailbox_key": mailbox.mailbox_key if hasattr(mailbox, "mailbox_key") else mailbox.key,
                "mailbox_user": mailbox.user_id,
            }
        )
    folders = await _list_all_folders(client, mailbox)
    for folder_data in folders:
        _upsert_folder(session, mailbox_row, folder_data)
    session.flush()

    target_folders = [
        folder
        for folder in folders
        if _path_matches(folder["path_parts"], mailbox.include_filters, mailbox.exclude_filters)
    ]
    if progress_cb:
        progress_cb(
            {
                "stage": "folder-discovery-complete",
                "mailbox_key": mailbox.key,
                "total_folders": len(folders),
                "target_folders": len(target_folders),
            }
        )

    semaphore = asyncio.Semaphore(max(1, max_concurrency))
    results: list[IngestResult] = []
    completed = 0

    async def process_folder(folder_data: dict[str, Any]) -> None:
        nonlocal completed
        if not _path_matches(folder_data["path_parts"], mailbox.include_filters, mailbox.exclude_filters):
            return
        async with semaphore:
            result = await _pull_folder_messages(
                client=client,
                mailbox=mailbox,
                mailbox_id=mailbox_row.id,
                folder_id=folder_data["id"],
                checkpoint_at=checkpoint.last_successful_sync_at,
                session=session,
                run=run,
                hard_limit=hard_limit,
            )
            results.append(result)
            completed += 1
            if progress_cb:
                progress_cb(
                    {
                        "stage": "ingesting-folders",
                        "mailbox_key": mailbox.key,
                        "completed_folders": completed,
                        "target_folders": len(target_folders),
                        "processed_messages": sum(item.processed for item in results),
                        "errors": sum(item.errors for item in results),
                        "current_folder": "/".join(folder_data.get("path_parts", [])),
                    }
                )

    await asyncio.gather(*(process_folder(folder) for folder in target_folders))
    processed = sum(item.processed for item in results)
    errors = sum(item.errors for item in results)
    latest = max((item.max_received_at for item in results if item.max_received_at is not None), default=None)
    if latest:
        checkpoint.last_successful_sync_at = latest
    checkpoint.last_run_id = run.id
    if progress_cb:
        progress_cb(
            {
                "stage": "completed",
                "mailbox_key": mailbox.key,
                "target_folders": len(target_folders),
                "processed_messages": processed,
                "errors": errors,
            }
        )
    return IngestResult(processed=processed, errors=errors, max_received_at=latest)
