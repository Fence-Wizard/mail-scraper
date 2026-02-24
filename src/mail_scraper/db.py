from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator

from sqlalchemy import create_engine, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .config import MailboxConfig, settings
from .db_schema import Base, Mailbox, PipelineRun

_ENGINE: Engine | None = None
_SessionFactory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = create_engine(settings.database_url, future=True, pool_pre_ping=True)
    return _ENGINE


def get_session_factory() -> sessionmaker[Session]:
    global _SessionFactory
    if _SessionFactory is None:
        _SessionFactory = sessionmaker(bind=get_engine(), expire_on_commit=False, future=True)
    return _SessionFactory


@contextmanager
def db_session() -> Iterator[Session]:
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def ensure_schema() -> None:
    Base.metadata.create_all(get_engine())


def bootstrap_mailboxes(session: Session, mailbox_configs: list[MailboxConfig]) -> dict[str, Mailbox]:
    known = {
        mb.mailbox_key: mb for mb in session.execute(select(Mailbox)).scalars().all()
    }
    for config in mailbox_configs:
        if config.key in known:
            mb = known[config.key]
            mb.user_id = config.user_id
            mb.root_folder_name = config.root_folder_name
            mb.include_filters = config.include_filters
            mb.exclude_filters = config.exclude_filters
            mb.is_active = config.enabled
        else:
            mb = Mailbox(
                mailbox_key=config.key,
                user_id=config.user_id,
                root_folder_name=config.root_folder_name,
                include_filters=config.include_filters,
                exclude_filters=config.exclude_filters,
                is_active=config.enabled,
            )
            session.add(mb)
            known[config.key] = mb
    session.flush()
    return known


def start_run(session: Session, pipeline_name: str, mailbox_id: int | None, metadata: dict | None = None) -> PipelineRun:
    run = PipelineRun(
        pipeline_name=pipeline_name,
        mailbox_id=mailbox_id,
        status="running",
        started_at=datetime.now(timezone.utc),
        metadata_json=metadata or {},
    )
    session.add(run)
    session.flush()
    return run


def finish_run(session: Session, run: PipelineRun, *, status: str, processed_count: int, error_count: int) -> None:
    run.status = status
    run.processed_count = processed_count
    run.error_count = error_count
    run.ended_at = datetime.now(timezone.utc)


def rolling_failure_rate(session: Session, pipeline_name: str, limit: int = 20) -> float:
    runs = (
        session.query(PipelineRun)
        .filter(PipelineRun.pipeline_name == pipeline_name)
        .order_by(PipelineRun.id.desc())
        .limit(limit)
        .all()
    )
    if not runs:
        return 0.0
    failed = sum(1 for run in runs if run.status != "success")
    return failed / float(len(runs))
