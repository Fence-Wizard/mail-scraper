from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from mail_scraper.db_schema import Base, DeadLetter
from mail_scraper.pipeline_attachments import replay_dead_letters


def test_replay_dead_letters_marks_resolved() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(DeadLetter(stage="ingest-message", error_message="boom", attempts=1))
        session.commit()

        replayed = replay_dead_letters(session, stage="ingest-message", limit=10)
        session.commit()

        row = session.execute(select(DeadLetter)).scalar_one()
        assert replayed == 1
        assert row.resolved_at is not None
        assert row.attempts == 2
