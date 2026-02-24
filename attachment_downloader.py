import asyncio
from pathlib import Path
import sys

SRC_PATH = Path(__file__).resolve().parent / "src"
if SRC_PATH.exists() and str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

import argparse

from mail_scraper.operations import run_download_attachments


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="max attachments to download")
    parser.add_argument("--mailbox-key", type=str, default=None, help="optional mailbox key")
    args = parser.parse_args()

    processed = asyncio.run(run_download_attachments(limit=args.limit, mailbox_key=args.mailbox_key))
    print(f"✅ Attachment download complete. Files processed: {processed}")


if __name__ == "__main__":
    main()
