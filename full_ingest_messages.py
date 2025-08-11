# full_ingest_messages.py
import asyncio, sqlite3, sys, time, argparse
from pathlib import Path
from graph_client import GraphClient
from fetch_config import settings
from matrix_rain import matrix_rain

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS documents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  message_id TEXT UNIQUE,
  vendor TEXT,
  vendor_canonical TEXT,
  total REAL,
  job_number TEXT,
  po_number TEXT,
  invoice_number TEXT,
  source_sender TEXT,
  source_subject TEXT,
  source_received_at TEXT,
  body_preview TEXT,
  has_attachments INTEGER
);
"""

UPSERT_SQL = """
INSERT INTO documents (message_id, source_sender, source_subject, source_received_at, body_preview, has_attachments)
VALUES (?, ?, ?, ?, ?, ?)
ON CONFLICT(message_id) DO UPDATE SET
  source_sender=excluded.source_sender,
  source_subject=excluded.source_subject,
  source_received_at=excluded.source_received_at,
  body_preview=excluded.body_preview,
  has_attachments=excluded.has_attachments;
"""

SELECT_FIELDS = "$select=id,from,subject,receivedDateTime,bodyPreview,hasAttachments"
PAGE_SIZE = "$top=50"

async def pull_folder_messages(client: GraphClient, user_id: str, folder_id: str, con: sqlite3.Connection, hard_limit: int|None):
    url = f"/users/{user_id}/mailFolders/{folder_id}/messages?{SELECT_FIELDS}&{PAGE_SIZE}&$orderby=receivedDateTime desc"
    seen = 0
    while url:
        resp = await client._get(url)
        for m in resp.get("value", []):
            mid = m.get("id")
            frm = (m.get("from") or {}).get("emailAddress") or {}
            sender = frm.get("address", "")
            subj = m.get("subject","")
            rcvd = m.get("receivedDateTime","")
            bprev = m.get("bodyPreview","")
            hatt = 1 if m.get("hasAttachments") else 0
            con.execute(UPSERT_SQL, (mid, sender, subj, rcvd, bprev, hatt))
            seen += 1
            if hard_limit and seen >= hard_limit:
                con.commit()
                return seen
        url = resp.get("@odata.nextLink", None)
        if url:
            url = url.split("v1.0")[-1]
        await asyncio.sleep(0.02)
        con.commit()
    return seen

async def list_all_folders(client: GraphClient, user_id: str):
    out = []
    root = await client._get(f"/users/{user_id}/mailFolders/msgfolderroot")
    out.append((root["id"], ["msgfolderroot"]))
    async def walk(fid, path):
        url = f"/users/{user_id}/mailFolders/{fid}/childFolders"
        while url:
            resp = await client._get(url)
            for f in resp.get("value", []):
                path2 = path + [f.get("displayName","")]
                out.append((f["id"], path2))
                await walk(f["id"], path2)
            url = resp.get("@odata.nextLink", None)
            if url: url = url.split("v1.0")[-1]
    await walk(root["id"], ["msgfolderroot"])
    return out

def path_matches(path_parts, filters):
    if not filters: return True
    p = "/".join(path_parts).lower()
    return all(f.lower() in p for f in filters)

async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="messages per folder (test mode)")
    ap.add_argument("--include", nargs="*", default=None, help='only folders whose path contains all these terms')
    ap.add_argument("--exclude", nargs="*", default=None, help='skip folders whose path contains any of these terms')
    ap.add_argument("--no-matrix", action="store_true", help="disable Matrix rain animation")
    args = ap.parse_args()

    client = GraphClient()
    await client.authenticate()
    user = settings.user_id

    dbp = Path("purchasing.db")
    con = sqlite3.connect(dbp)
    con.execute(CREATE_SQL)
    con.commit()

    folders = await list_all_folders(client, user)

    with matrix_rain(enabled=not args.no_matrix):
        total_seen = 0
        for fid, path in folders:
            if args.include and not path_matches(path, args.include):
                continue
            if args.exclude and path_matches(path, args.exclude):
                continue
            print(f"→ {'/'.join(path)}")
            got = await pull_folder_messages(client, user, fid, con, args.limit)
            total_seen += got

    con.commit()
    con.close()
    print(f"\n✅ Ingest complete. Messages upserted: {total_seen}")

if __name__ == "__main__":
    asyncio.run(main())
