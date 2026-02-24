import sqlite3
from pathlib import Path

from sqlalchemy import text

from .db import db_session, ensure_schema


def migrate_sqlite_to_postgres(sqlite_path: Path) -> None:
    if not sqlite_path.exists():
        raise FileNotFoundError(f"SQLite source not found: {sqlite_path}")

    ensure_schema()
    con = sqlite3.connect(sqlite_path)
    con.row_factory = sqlite3.Row
    try:
        docs = con.execute("SELECT * FROM documents").fetchall()
        with db_session() as session:
            for row in docs:
                payload = dict(row)
                session.execute(
                    text(
                        """
                        INSERT INTO documents (
                          file_path, vendor, vendor_canonical, po_number, job_number, invoice_number,
                          invoice_date, subtotal, tax, total, source_sender, source_received_at, source_subject, extract_notes
                        ) VALUES (
                          :file_path, :vendor, :vendor_canonical, :po_number, :job_number, :invoice_number,
                          :invoice_date, :subtotal, :tax, :total, :source_sender, :source_received_at, :source_subject, :extract_notes
                        )
                        ON CONFLICT (file_path) DO UPDATE SET
                          vendor = EXCLUDED.vendor,
                          vendor_canonical = EXCLUDED.vendor_canonical,
                          po_number = EXCLUDED.po_number,
                          job_number = EXCLUDED.job_number,
                          invoice_number = EXCLUDED.invoice_number,
                          invoice_date = EXCLUDED.invoice_date,
                          subtotal = EXCLUDED.subtotal,
                          tax = EXCLUDED.tax,
                          total = EXCLUDED.total,
                          source_sender = EXCLUDED.source_sender,
                          source_received_at = EXCLUDED.source_received_at,
                          source_subject = EXCLUDED.source_subject,
                          extract_notes = EXCLUDED.extract_notes
                        """
                    ),
                    payload,
                )
        print(f"Migrated {len(docs)} documents from {sqlite_path} to Postgres")
    finally:
        con.close()
