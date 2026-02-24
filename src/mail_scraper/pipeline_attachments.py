from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re
from typing import Any, Callable

import httpx
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from .attachments import decode_graph_attachment
from .config import MailboxConfig
from .db_schema import (
    Attachment,
    DeadLetter,
    Mailbox,
    Message,
    PipelineCheckpoint,
    PipelineError,
    PipelineRun,
)
from .graph_client import GraphClient

ProgressCb = Callable[[dict[str, Any]], None]
_WIN_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
}


def _get_or_create_attachment_checkpoint(session: Session, mailbox_id: int) -> PipelineCheckpoint:
    checkpoint = session.execute(
        select(PipelineCheckpoint).where(
            and_(
                PipelineCheckpoint.mailbox_id == mailbox_id,
                PipelineCheckpoint.pipeline_name == "download_attachments",
            )
        )
    ).scalar_one_or_none()
    if checkpoint:
        return checkpoint
    checkpoint = PipelineCheckpoint(mailbox_id=mailbox_id, pipeline_name="download_attachments")
    session.add(checkpoint)
    session.flush()
    return checkpoint


def _sanitize_windows_component(value: str | None, fallback: str) -> str:
    raw = (value or "").strip()
    if not raw:
        raw = fallback
    # Remove invalid Win32 path chars and control bytes.
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", raw).strip().strip(". ")
    if not cleaned:
        cleaned = fallback
    if cleaned.upper() in _WIN_RESERVED_NAMES:
        cleaned = f"_{cleaned}"
    return cleaned


def _make_message_dir(output_root: Path, mailbox_key: str, message_pk: int, graph_message_id: str) -> Path:
    mailbox_component = _sanitize_windows_component(mailbox_key, "mailbox")
    msg_hash = hashlib.sha1(graph_message_id.encode("utf-8")).hexdigest()[:12]
    # Keep message folder name compact and deterministic to avoid Windows MAX_PATH issues.
    return output_root / mailbox_component / f"m{message_pk}_{msg_hash}"


def _make_attachment_filename(
    original_name: str | None,
    attachment_id: str,
    *,
    max_len: int = 120,
) -> str:
    safe_name = _sanitize_windows_component(original_name, "attachment.bin")
    root, ext = os.path.splitext(safe_name)
    short_id = hashlib.sha1(attachment_id.encode("utf-8")).hexdigest()[:8]
    ext = ext[:12]
    suffix = f"_{short_id}"
    max_root_len = max(8, max_len - len(ext) - len(suffix))
    compact_root = (root or "attachment")[:max_root_len].rstrip(". ")
    if not compact_root:
        compact_root = "attachment"
    return f"{compact_root}{suffix}{ext}"


async def download_attachments_for_mailbox(
    client: GraphClient,
    session: Session,
    mailbox: MailboxConfig,
    mailbox_row: Mailbox,
    run: PipelineRun,
    output_root: Path,
    limit: int | None = None,
    batch_size: int = 500,
    progress_cb: ProgressCb | None = None,
) -> tuple[int, int, int]:
    processed = 0
    errors = 0
    skipped = 0
    scanned_messages = 0

    checkpoint = _get_or_create_attachment_checkpoint(session, mailbox_row.id)
    cursor = int((checkpoint.progress_cursor or {}).get("last_message_pk", 0))
    if progress_cb:
        total_messages = session.execute(
            select(func.count())
            .select_from(Message)
            .where(and_(Message.mailbox_id == mailbox_row.id, Message.has_attachments.is_(True)))
        ).scalar_one()
        progress_cb(
            {
                "stage": "attachments-start",
                "mailbox_key": mailbox.key,
                "total_messages": int(total_messages),
                "resume_after_message_pk": cursor,
            }
        )

    while True:
        if limit is not None and processed >= limit:
            break
        chunk_limit = batch_size
        if limit is not None:
            chunk_limit = max(1, min(chunk_limit, limit - processed))

        messages = (
            session.execute(
                select(Message).where(
                    and_(
                        Message.mailbox_id == mailbox_row.id,
                        Message.has_attachments.is_(True),
                        Message.id > cursor,
                    )
                ).order_by(Message.id.asc()).limit(chunk_limit)
            )
            .scalars()
            .all()
        )
        if not messages:
            break

        for message in messages:
            cursor = message.id
            scanned_messages += 1
            try:
                response = await client._get(
                    f"/users/{mailbox.user_id}/messages/{message.graph_message_id}/attachments"
                )
                message_dir = _make_message_dir(
                    output_root=output_root,
                    mailbox_key=mailbox.key,
                    message_pk=message.id,
                    graph_message_id=message.graph_message_id,
                )
                message_dir.mkdir(parents=True, exist_ok=True)
                for attachment_json in response.get("value", []):
                    graph_attachment_id = attachment_json.get("id")
                    if not graph_attachment_id:
                        continue
                    content_bytes = attachment_json.get("contentBytes")
                    if not content_bytes:
                        continue
                    name = attachment_json.get("name", graph_attachment_id)
                    safe_file_name = _make_attachment_filename(name, graph_attachment_id)
                    file_path = message_dir / safe_file_name
                    file_path.write_bytes(decode_graph_attachment(content_bytes))

                    row = session.execute(
                        select(Attachment).where(
                            and_(
                                Attachment.mailbox_id == mailbox_row.id,
                                Attachment.graph_attachment_id == graph_attachment_id,
                            )
                        )
                    ).scalar_one_or_none()
                    if row:
                        row.message_id = message.id
                        row.graph_message_id = message.graph_message_id
                        row.name = name
                        row.content_type = attachment_json.get("contentType")
                        row.size_bytes = attachment_json.get("size")
                        row.file_path = str(file_path)
                        row.download_status = "success"
                        row.error_message = None
                    else:
                        session.add(
                            Attachment(
                                mailbox_id=mailbox_row.id,
                                message_id=message.id,
                                graph_attachment_id=graph_attachment_id,
                                graph_message_id=message.graph_message_id,
                                name=name,
                                content_type=attachment_json.get("contentType"),
                                size_bytes=attachment_json.get("size"),
                                file_path=str(file_path),
                                download_status="success",
                            )
                        )
                    processed += 1
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 404:
                    # Message no longer resolvable (moved/deleted). Treat as skipped.
                    skipped += 1
                else:
                    errors += 1
                    session.add(
                        PipelineError(
                            run_id=run.id,
                            mailbox_id=mailbox_row.id,
                            message_graph_id=message.graph_message_id,
                            stage="download-attachments",
                            error_message=str(exc),
                            payload_json={"message_id": message.graph_message_id},
                        )
                    )
                    session.add(
                        DeadLetter(
                            mailbox_id=mailbox_row.id,
                            stage="download-attachments",
                            payload_json={"message_id": message.graph_message_id},
                            error_message=str(exc),
                        )
                    )
            except Exception as exc:  # pragma: no cover - error path
                errors += 1
                session.add(
                    PipelineError(
                        run_id=run.id,
                        mailbox_id=mailbox_row.id,
                        message_graph_id=message.graph_message_id,
                        stage="download-attachments",
                        error_message=str(exc),
                        payload_json={"message_id": message.graph_message_id},
                    )
                )
                session.add(
                    DeadLetter(
                        mailbox_id=mailbox_row.id,
                        stage="download-attachments",
                        payload_json={"message_id": message.graph_message_id},
                        error_message=str(exc),
                    )
                )

            if progress_cb:
                progress_cb(
                    {
                        "stage": "attachments-progress",
                        "mailbox_key": mailbox.key,
                        "processed_files": processed,
                        "errors": errors,
                        "skipped": skipped,
                        "scanned_messages": scanned_messages,
                        "resume_after_message_pk": cursor,
                        "current_message_id": message.graph_message_id,
                    }
                )

        checkpoint.progress_cursor = {
            "last_message_pk": cursor,
            "scanned_messages": scanned_messages,
        }
        # Persist cursor and partial progress to survive long-running interruptions.
        session.flush()
        session.commit()

    if progress_cb:
        progress_cb(
            {
                "stage": "attachments-complete",
                "mailbox_key": mailbox.key,
                "processed_files": processed,
                "errors": errors,
                "skipped": skipped,
                "scanned_messages": scanned_messages,
                "resume_after_message_pk": cursor,
            }
        )
    return processed, errors, skipped


def replay_dead_letters(session: Session, stage: str | None = None, limit: int = 100) -> int:
    query = select(DeadLetter).where(DeadLetter.resolved_at.is_(None))
    if stage:
        query = query.where(DeadLetter.stage == stage)
    rows = session.execute(query.order_by(DeadLetter.id.asc()).limit(limit)).scalars().all()
    now = datetime.now(timezone.utc)
    for row in rows:
        row.attempts += 1
        row.last_seen_at = now
        row.resolved_at = now
    return len(rows)
