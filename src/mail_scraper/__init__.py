"""Core package for mailbox ingestion and analysis."""

from .config import settings
from .graph_client import GraphClient

__all__ = ["GraphClient", "settings"]
