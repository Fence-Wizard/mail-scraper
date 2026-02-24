"""Legacy wrapper for extraction.

Use `python -m mail_scraper.cli extract` for the canonical entrypoint.
"""

from pathlib import Path
import sys

SRC_PATH = Path(__file__).resolve().parent / "src"
if SRC_PATH.exists() and str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from mail_scraper.operations import run_legacy_extract


def main() -> None:
    run_legacy_extract()


if __name__ == "__main__":
    main()
