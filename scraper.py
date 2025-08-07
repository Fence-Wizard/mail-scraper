# scraper.py
import os
import json
import asyncio
from pathlib import Path
from graph_client import GraphClient
from models import Folder, Message, Attachment
from fetch_config import settings

OUTPUT_DIR = Path("raw_data")

async def get_child_folders(client: GraphClient, folder_id: str) -> list[Folder]:
    resp = await client._get(f"/users/{settings.user_id}/mailFolders/{folder_id}/childFolders")
    return [Folder(**f) for f in resp.get("value", [])]

async def crawl_folder_tree():
    client = GraphClient()
    # find root by displayName
    resp = await client._get(f"/users/{settings.user_id}/mailFolders")
    root = next(f for f in resp["value"] if f["displayName"] == settings.root_folder_name)
    async def recurse(folder_obj, path_parts):
        folder = Folder(**folder_obj)
        path = OUTPUT_DIR.joinpath(*path_parts, folder.displayName)
        path.mkdir(parents=True, exist_ok=True)
        # dump folder metadata
        (path / "_folder.json").write_text(json.dumps(folder_obj, indent=2))
        # fetch messages in this folder
        async for page in client.list_items_paged(f"/users/{settings.user_id}/mailFolders/{folder.id}/messages", {"$top": 50}):
            for msg_json in page.get("value", []):
                msg = Message(**msg_json)
                (path / f"{msg.id}.json").write_text(json.dumps(msg_json))
        # recurse into children
        children = await get_child_folders(client, folder.id)
        for child in children:
            await recurse(child.dict(), path_parts + [folder.displayName])
    await recurse(root, [])
    await client.close()

if __name__ == "__main__":
    asyncio.run(crawl_folder_tree())
