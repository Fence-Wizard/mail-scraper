import os
import json
import asyncio
import logging
from pathlib import Path
from graph_client import GraphClient
from fetch_config import settings

OUTPUT_DIR = Path("raw_data")
logger = logging.getLogger(__name__)

async def download_attachments():
    client = GraphClient()
    await client.authenticate()

    # Walk all message JSON files
    for root, dirs, files in os.walk(OUTPUT_DIR):
        for file in files:
            if file.endswith(".json") and file != "_folder.json":
                file_path = Path(root) / file
                with open(file_path, "r", encoding="utf-8") as f:
                    msg_json = json.load(f)

                message_id = msg_json["id"]
                folder_path = Path(root)
                attachment_dir = folder_path / f"{message_id}_attachments"
                attachment_dir.mkdir(exist_ok=True)

                try:
                    logger.info(f"Fetching attachments for message {message_id}")
                    url = f"/users/{settings.user_id}/messages/{message_id}/attachments"
                    resp = await client._get(url)

                    for attachment in resp.get("value", []):
                        name = attachment.get("name", "unnamed")
                        content_bytes = attachment.get("contentBytes")

                        if content_bytes is None:
                            logger.warning(f"Skipping non-file attachment: {name}")
                            continue

                        file_path = attachment_dir / name
                        with open(file_path, "wb") as f:
                            f.write(bytes(content_bytes, encoding="utf-8"))

                        logger.info(f"Saved attachment: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to fetch or save attachment for {message_id}: {e}")

    await client.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(download_attachments())
