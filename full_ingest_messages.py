"""Legacy wrapper for incremental ingest.

This script now delegates to the package CLI implementation.
"""

import argparse
import asyncio
from pathlib import Path
import sys

SRC_PATH = Path(__file__).resolve().parent / "src"
if SRC_PATH.exists() and str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from mail_scraper.operations import run_ingest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="max new messages to ingest per folder task")
    parser.add_argument("--mailbox-key", type=str, default=None, help="optional mailbox key")
    parser.add_argument("--include", nargs="*", default=None, help="deprecated: use MAILBOXES_JSON include_filters")
    parser.add_argument("--exclude", nargs="*", default=None, help="deprecated: use MAILBOXES_JSON exclude_filters")
    parser.add_argument("--no-matrix", action="store_true", help="deprecated and ignored")
    args = parser.parse_args()

    if args.include or args.exclude:
        print("Note: --include/--exclude are deprecated; configure include/exclude per mailbox in MAILBOXES_JSON.")
    processed = asyncio.run(run_ingest(limit=args.limit, mailbox_key=args.mailbox_key))
    print(f"✅ Ingest complete. New messages processed: {processed}")


if __name__ == "__main__":
    main()
