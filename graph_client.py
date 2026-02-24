"""Backward-compatible Graph client import shim.

Prefer importing from `mail_scraper.graph_client`.
"""

from pathlib import Path
import sys

SRC_PATH = Path(__file__).resolve().parent / "src"
if SRC_PATH.exists() and str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from mail_scraper.graph_client import GraphClient  # noqa: E402,F401

