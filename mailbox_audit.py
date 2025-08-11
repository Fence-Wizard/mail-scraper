# mailbox_audit.py
import asyncio, json, sqlite3, sys
from pathlib import Path
from graph_client import GraphClient
from fetch_config import settings

async def list_folders(client, user_id):
    out = []
    async def walk(folder_id, path):
        # page folders
        url = f"/users/{user_id}/mailFolders/{folder_id}/childFolders"
        while url:
            resp = await client._get(url)
            for f in resp.get("value", []):
                out.append((f["id"], path + [f.get("displayName","")], f.get("totalItemCount",0)))
                await walk(f["id"], path + [f.get("displayName","")])
            url = resp.get("@odata.nextLink", None)
            if url: url = url.split("v1.0")[-1]
    # root
    root = await client._get(f"/users/{user_id}/mailFolders/msgfolderroot")
    root_id = root["id"]
    out.append((root_id, ["msgfolderroot"], root.get("totalItemCount", 0)))
    await walk(root_id, ["msgfolderroot"])
    return out

async def main():
    client = GraphClient()
    await client.authenticate()
    user = settings.user_id
    folders = await list_folders(client, user)
    print("Folder, totalItemCount")
    for fid, path, cnt in folders:
        print("/".join(path), cnt)
    # DB count
    db = Path("purchasing.db")
    if db.exists():
        con = sqlite3.connect(db)
        try:
            cur = con.execute("SELECT COUNT(*) FROM documents")
            n = cur.fetchone()[0]
            print(f"\nDB documents rows: {n}")
        finally:
            con.close()
    else:
        print("\nDB not found.")

if __name__ == "__main__":
    asyncio.run(main())
