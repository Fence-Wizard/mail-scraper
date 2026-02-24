from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from mail_scraper.db_schema import Base, Mailbox, PipelineCheckpoint, PipelineRun


def test_schema_create_and_checkpoint_roundtrip() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        mailbox = Mailbox(mailbox_key="ops", user_id="ops@example.com", root_folder_name="msgfolderroot")
        session.add(mailbox)
        session.flush()

        run = PipelineRun(pipeline_name="ingest", mailbox_id=mailbox.id, status="success")
        session.add(run)
        session.flush()

        checkpoint = PipelineCheckpoint(mailbox_id=mailbox.id, pipeline_name="ingest", last_run_id=run.id)
        session.add(checkpoint)
        session.commit()

        found = session.execute(select(PipelineCheckpoint)).scalar_one()
        assert found.mailbox_id == mailbox.id
        assert found.last_run_id == run.id
